FROM python:3.8

RUN mkdir /code
WORKDIR /code

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY src/ .
COPY Config.json .

CMD ["python", "main.py"]
