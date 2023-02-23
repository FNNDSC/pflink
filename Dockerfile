FROM tiangolo/uvicorn-gunicorn-fastapi:python3.8-slim


WORKDIR /app

# 


COPY ./requirements.txt /app/requirements.txt

# 


RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

# 


COPY . /app/

# 


CMD ["python", "app/main.py"]
