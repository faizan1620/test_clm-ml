import os
import glob
from fastapi import FastAPI, File, UploadFile
from pathlib import Path
import shutil
from app_.modules.pdf_to_image.singleImage import pdf_to_images_with_orient
from app_.modules.ocr.image_ocr import find_text
import logging, shutil

logging.basicConfig(format='%(asctime)s %(message)s')
logger = logging.getLogger()
logger.setLevel(logging.INFO)

api = FastAPI(docs_url='/contract-upload/docs')

@api.post('/contract-upload/pdf_to_text')
def pdf_to_text(file: UploadFile = File(...)):
 response = {}
 try:
    contract_name = Path(file.filename).stem
    save_path =contract_name
    pdf_file = contract_name+'/'+contract_name+'.pdf'
    response.update({'contract_file_name':contract_name})
    if(not os.path.exists(save_path)):
        os.mkdir(save_path)
    try:
        with open(pdf_file, 'wb') as f:
            shutil.copyfileobj(file.file,f)
    finally:
        file.file.close()
    logger.info("Converting file into images")
    pdf_to_images_with_orient(pdf_file, save_path)
    logger.info("Images created from pdf")
    files = glob.glob(glob.escape(save_path)+'/*.jpg')
    files = [x.split('/')[-1] for x in files]
    files = sorted(files, key=lambda x: int(os.path.splitext(os.path.basename(x))[0]))
    logger.info("Running ocr")
    contract_pages_list = []
    for img in files:
        page_text = find_text(save_path + '/' + img)
        contract_pages_list.append(page_text)
    contract_text = "\n".join(contract_pages_list)
    output = {'output':{contract_text}}
    response.update(output)
    remove(contract_name)
    return response
 except Exception as e:
     logger.info(e)
     return {'contract_file_name':'Unknown'}


def remove(path):
    """ param <path> could either be relative or absolute. """
    if os.path.isfile(path) or os.path.islink(path):
        os.remove(path)  # remove the file
        logger.info('file deleted')
    elif os.path.isdir(path):
        shutil.rmtree(path)  # remove dir and all contains
        logger.info('folder deleted')
    else:
        raise ValueError("file {} is not a file or dir.".format(path))