FROM python:3.6-slim

WORKDIR /opt/app

RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc \
        libmysqlclient-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /opt/app/
RUN pip install --no-cache-dir -r /opt/app/requirements.txt

COPY . /opt/app

CMD ["python", "main.py"]