FROM python:3.12

WORKDIR /app

COPY . .

RUN pip install -r requirements.txt


EXPOSE 8000

CMD python app.py migrate

CMD ["python", "-m", "flask", "run", "--host=0.0.0.0"]

