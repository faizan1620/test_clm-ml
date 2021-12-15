#FROM nginx/unit:1.26.1-minimal
FROM nginx/unit:1.25.0-python3.9


WORKDIR /contract-app
# #Install poppler required for PDF conversion

COPY --chown=unit:unit ./config/config.json /docker-entrypoint.d/config.json

COPY --chown=unit:unit . .

RUN apt-get clean \
     && apt-get --no-install-recommends --yes update \
     && apt-get install tesseract-ocr --no-install-recommends --yes \
     && apt-get install python3-poppler-qt5 poppler-utils --no-install-recommends --yes \
     && rm -rf /var/lib/apt/lists/* \
     && apt-get clean \
     && apt-get autoremove -y 


COPY requirements.txt .

RUN pip3 install -r requirements.txt

RUN chown -R unit:unit /contract-app

EXPOSE 80






