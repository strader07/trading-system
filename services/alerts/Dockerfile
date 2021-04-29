FROM eu.gcr.io/strange-metrics-258802/images/python:python-3.8.0-alpine3.10-NG-1
ENV TZ=Etc/UTC
WORKDIR /srv/app
COPY . .
RUN pip install -r requirements.txt
CMD ["python", "/srv/app/main.py"]
