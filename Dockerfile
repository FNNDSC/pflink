FROM tiangolo/uvicorn-gunicorn-fastapi:python3.10

# set working directory
WORKDIR /app

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# copy requirements file
COPY ./requirements.txt /app/requirements.txt

# install dependencies
RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

# copy project
COPY . /app
