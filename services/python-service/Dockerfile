FROM eu.gcr.io/strange-metrics-258802/images/python:python-3.8.0-alpine3.10-NG-1
ENV TZ=Etc/UTC
WORKDIR /srv/app
RUN apk --update add ca-certificates tzdata \
    && pip install --upgrade pip
COPY requirements.txt ./
RUN pip install -v -r requirements.txt
COPY . .
CMD ["python", "/srv/app/main.py"]
