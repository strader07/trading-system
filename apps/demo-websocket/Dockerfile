FROM alpine:latest AS builder
RUN apk --update add ca-certificates tzdata

FROM eu.gcr.io/strange-metrics-258802/images/nodejs:node-10.15.3-alpine-NG-1
ENV TZ=Etc/UTC
COPY --from=builder /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/
COPY --from=builder /usr/share/zoneinfo /usr/share/zoneinfo
COPY build/ /srv/app
COPY server.js /srv/app
COPY package.json /srv/app
WORKDIR /srv/app
RUN npm install
CMD ["npm", "run", "serve"]
