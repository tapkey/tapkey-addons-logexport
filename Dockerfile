FROM python:3.11-slim
ENV PYTHONUNBUFFERED=1
WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app.py .

EXPOSE 3000

CMD [ "python3", "-m" , "flask", "run", "--host=0.0.0.0", "--port=3000"]