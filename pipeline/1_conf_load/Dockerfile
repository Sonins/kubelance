FROM python:3.8-alpine

RUN pip install -r requirements.txt
RUN mkdir -p /app
COPY . /app
WORKDIR /app

ENTRYPOINT [ "python", "load_conf.py" ]