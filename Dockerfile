FROM python:3.7-slim

WORKDIR /contact-app

RUN apt-get clean \
     && apt-get --no-install-recommends --yes update \
     && apt-get install tesseract-ocr --no-install-recommends --yes \
     && apt-get install python3-poppler-qt5 poppler-utils --no-install-recommends --yes \
     && rm -rf /var/lib/apt/lists/* \
     && apt-get clean \
     && apt-get autoremove -y

COPY requirements.txt ./

RUN pip install -r requirements.txt \
    && rm -rf /root/.cache/pip

COPY . .

EXPOSE 80

CMD ["gunicorn", "-b", "0.0.0.0:80", "-k", "uvicorn.workers.UvicornWorker", "app_.app:api"]

