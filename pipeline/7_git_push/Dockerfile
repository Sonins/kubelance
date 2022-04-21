FROM python:3.8-alpine

RUN mkdir -p /app
COPY requirements.txt /app
RUN pip install -r /app/requirements.txt
RUN apk update
RUN apk add git
RUN git config --global user.name "Heegwan Son"
RUN git config --global user.email "gmlrhks95@gmail.com"
COPY . /app
WORKDIR /app

ENTRYPOINT [ "tail", "-f", "/dev/null" ]