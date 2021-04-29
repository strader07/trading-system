FROM eu.gcr.io/strange-metrics-258802/base/python:3.7.5-slim-buster
ENV TZ=Etc/UTC
WORKDIR /srv/app
COPY . .
RUN pip install -r requirements.txt
CMD ["python", "/srv/app/main.py"]
