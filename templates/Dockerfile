FROM python:3.12

WORKDIR /app

COPY . .

RUN pip install -r requirements.txt


EXPOSE 8080


CMD ["python", "bot.py", "runserver", "0.0.0.0:8080"]

