FROM eu.gcr.io/strange-metrics-258802/base/node:10.15.3-alpine
ADD build.sh build.sh
RUN chmod +x build.sh && ./build.sh && rm build.sh
