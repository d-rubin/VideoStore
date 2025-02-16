FROM --platform=linux/amd64 python:3.10-alpine

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

RUN apk update && \
    apk add --no-cache \
    build-base \
    ffmpeg \
    libpq-dev \
    gettext

WORKDIR /app

COPY ./requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD python ./manage.py collectstatic --noinput && \
    python3 ./manage.py makemigrations && \
    python3 ./manage.py migrate && \
    gunicorn --bind 0.0.0.0:8000 videostore.wsgi

#FROM --platform=linux/amd64 python:3.10-alpine
#
#ENV PYTHONUNBUFFERED 1
#ENV PYTHONDONTWRITEBYTECODE 1
#
#RUN apk update && \
#     apk add --no-cache \
#     build-base \
#     ffmpeg \
#     libpq-dev \
#     gettext
#
#WORKDIR /app
#
#COPY ./requirements.txt .
#RUN pip install --no-cache-dir -r requirements.txt
#
#COPY . .
#
#CMD celery -A videostore worker -l INFO
