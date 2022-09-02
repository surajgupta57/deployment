# pull official base image
FROM python:3.7.6

# set work directory
WORKDIR /usr/src/app

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# install psycopg2 dependencies
RUN apt-get update \
    && apt-get install python3-dev -y

RUN pip3 install --upgrade pip
RUN pip3 install virtualenv
RUN virtualenv venv
RUN . venv/bin/activate
COPY ./requirements /usr/src/app/requirements/
COPY ./requirements.txt /usr/src/app/requirements.txt
RUN pip3 install -r requirements.txt

COPY . /usr/src/app/