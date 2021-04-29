FROM eu.gcr.io/strange-metrics-258802/base/redis:5.0.7-alpine
ADD build.sh build.sh
RUN chmod +x build.sh && ./build.sh && rm build.sh
CMD ["sh", "-c", "exec redis-server --requirepass \"$REDIS_PASSWORD\""]
