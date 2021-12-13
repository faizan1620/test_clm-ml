#!/usr/bin/env python
# coding: utf-8
import pandas as pd
import numpy as np
from PIL import Image

from pdf2image import convert_from_path, convert_from_bytes
from pdf2image.exceptions import (
    PDFInfoNotInstalledError,
    PDFPageCountError,
    PDFSyntaxError
)

output_folder_name = 'output/'

def orientation_check(size):
    width, height = size
    if(width > height):
        return 'landscape'
    else:
        return 'portrait'


def pdf_to_images_with_orient(pdf, out):
    images = convert_from_path(pdf, fmt='jpeg')
 
    i = 1
    j = 2
    k = 1
    for image in images:
        orient = orientation_check(image.size)
        if orient == 'landscape':
            double_split(image, i, j, pdf, out)
            i = i + 2
            j = i + 1
        else:
            image.save(out + '/'+ str(k) + '.jpg', 'JPEG')
            k = k + 1

def double_split(original, a_side, b_side, filename, output_folder):
    # Downscale
    DOWNSCALED_WIDTH = 400

    def downscale(img):
        o_width, o_height = img.size
        height = round((DOWNSCALED_WIDTH / o_width) * o_height)

        ds_img = img.convert('L').resize((DOWNSCALED_WIDTH, height), resample=Image.BILINEAR)

        return ds_img

    def pixels_df(img):
        pixels = list(img.getdata())
        width, height = img.size
        pixels = [pixels[i * width:(i + 1) * width] for i in range(height)]

        return pd.DataFrame(pixels)

    def rescale(serie):
      
        serie -= serie.min()
        return serie / serie.max()

    def middle(df, replacement):
        df2 = df.copy()

        if df.__class__ == pd.DataFrame:
            third = int(len(df.columns) / 3)

            df2.loc[:, :third] = replacement
            df2.loc[:, 2 * third:] = replacement
        else:
            third = int(len(df) / 3)
            df2.loc[:third] = replacement
            df2.loc[2 * third:] = replacement

        return df2

    img = downscale(original)
    df = pixels_df(img)
    # 0 = white, 1 = black pixels
    contrasted = df.applymap(lambda x: int(np.sqrt(x) if x < 127 else x ** 2) / (255 ** 2))
    means = middle(contrasted, np.nan).mean()

    def apply_func_factory(serie):
        center = len(serie) / 2

        def apply_func(x):
            idx = x.name
            return 1 - (abs(center - idx) ** 1.618) / center ** 1.618

        return apply_func

    apply_func = apply_func_factory(means)

    center_amplifier = means.reset_index().apply(apply_func, axis=1)

    low_std_amplifier = rescale(means / (1 - means.std()))
    signal = rescale(rescale(means) * center_amplifier * low_std_amplifier)
    normalized = (signal * 10).round()
    grouped = pd.DataFrame([normalized]).T.groupby(normalized, as_index=False)

    # luminosity distinct sorted values (10 at max = whitest)
    lum_val = grouped[0].last().round().values.flatten()
    lum_val.sort()
    whitest = lum_val[-1]
    darkest = lum_val[0]

    # whitests columns (maximum of luminosity)
    white_cols = pd.Series(grouped.get_group(whitest).index)
    dark_cols = pd.Series(grouped.get_group(darkest).index)

    if len(white_cols) < 0.01 * DOWNSCALED_WIDTH and lum_val[-2] >= whitest - 1:
        next_group = pd.Series(grouped.get_group(lum_val[-2]).index)
        if len(next_group) < 0.02 * DOWNSCALED_WIDTH:
            white_cols = white_cols.append(next_group).sort_values()

    first_idx, last_idx = white_cols.min(), white_cols.max()

    white_band = normalized.loc[first_idx:last_idx]
    if white_band.min() > white_band.max() - 2:
        margin = max(1, round(0.01 * DOWNSCALED_WIDTH))
        white_band = normalized.loc[first_idx - margin:last_idx + margin]

    # we have a dark local minimum in the white band
    band_min = white_band.min()
    if whitest == 10 and (last_idx - first_idx + 1) == len(white_cols) and len(white_cols) >= 0.02 * DOWNSCALED_WIDTH:
        binding_point = white_cols.median()
    elif band_min <= whitest - 5:
        dark_inside_median = white_band[white_band == band_min].reset_index()['index']

        binding_point = dark_inside_median.median()
    elif darkest == 0 and len(dark_cols) <= 0.01 * DOWNSCALED_WIDTH:
        binding_point = dark_cols.median()
    else:
        # binding as median of indexes
        binding_point = white_cols.median()
    o_width, _ = original.size
    cut_x = round(o_width * (binding_point / DOWNSCALED_WIDTH))

    def splitted_pages_numbers(filename):
        return {"left": a_side, "right": b_side}

    def output_path(page_n):
        
        return output_folder + '/' + "%s.jpg" % page_n

    def split_pages_paths(original_filename):
        pages_numbers = splitted_pages_numbers(original_filename)

        return {
            "left": output_path(pages_numbers["left"]),
            "right": output_path(pages_numbers["right"]),
        }

    def horizontal_split(img, cut_x):
        dim_left = (0, 0, cut_x - 1, img.height)
        img_left = img.crop(dim_left)

        dim_right = (cut_x, 0, img.width, img.height)
        img_right = img.crop(dim_right)

        file_paths = split_pages_paths(img.filename)

        img_left.save(file_paths['left'])
        img_right.save(file_paths['right'])

    horizontal_split(original, cut_x)
