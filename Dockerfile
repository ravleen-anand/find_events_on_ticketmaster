FROM python:3.6

RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

COPY requirements_dev.txt /usr/src/app/
RUN pip install -r requirements_dev.txt

COPY app.py /usr/src/app

CMD uvicorn app --reload
