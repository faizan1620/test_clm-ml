import pytesseract
import cv2
import numpy as np


def find_text(filename):
    print(filename)
    print(type(filename))
    img = cv2.imread(filename)
    img = cv2.resize(img, None, fx=1.9, fy=1.9, interpolation=cv2.INTER_CUBIC)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    kernel = np.ones((1, 1), np.uint8)
    img = cv2.dilate(img, kernel, iterations=1)
    img = cv2.erode(img, kernel, iterations=1)
    ret, gray=cv2.threshold(cv2.bilateralFilter(img, 5, 75, 75), 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    text = pytesseract.image_to_string(gray, lang="pol+eng")
    text = text.split("\n")
    r_text = []
    for line in text:
        if not line.isspace() and line != "\n":
                r_text.append(line)
    text = "\n".join(r_text[1:])
    return text.replace('|', "I")

