FROM python:3.8-alpine

RUN mkdir -p /app
COPY requirements.txt /app
RUN pip install -r /app/requirements.txt
RUN apk update
RUN apk add git
COPY . /app
WORKDIR /app

CMD [ "python", "load_conf.py" ]