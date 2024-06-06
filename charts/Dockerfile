FROM python:latest

WORKDIR /code

COPY . .

RUN pip install -U pip
RUN pip install -r requirements.txt

CMD ["python","-u","main.py"]