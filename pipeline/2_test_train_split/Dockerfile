FROM python:3.8-alpine

RUN mkdir -p /app
COPY requirements.txt /app
RUN pip install -r /app/requirements.txt
COPY . /app
WORKDIR /app

ENTRYPOINT [ "python", "test_train_split.py" ]