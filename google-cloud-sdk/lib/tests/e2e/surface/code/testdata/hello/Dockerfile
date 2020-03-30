FROM python:3.7.4-slim-buster

COPY requirements.txt /requirements.txt
RUN pip install wheel -r requirements.txt

COPY main.py /

CMD python main.py
