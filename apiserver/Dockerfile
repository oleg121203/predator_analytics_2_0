FROM python:3.11

WORKDIR /app
COPY ./app.py /app/app.py
COPY ./requirements.txt /app/requirements.txt

RUN pip install --upgrade pip==25.0.1 --no-cache-dir && \
    pip install --no-cache-dir -r /app/requirements.txt

CMD ["python", "-u", "/app/app.py"]