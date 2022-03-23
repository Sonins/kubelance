FROM python:3.8-alpine

RUN mkdir -p /app
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
ENTRYPOINT [ "python", "test_train_split.py" ]