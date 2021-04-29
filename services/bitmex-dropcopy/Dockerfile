FROM alpine:latest AS builder
RUN apk --update add ca-certificates tzdata

FROM scratch
ENV TZ=Etc/UTC
COPY --from=builder /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/
COPY --from=builder /usr/share/zoneinfo /usr/share/zoneinfo
COPY bin/main /
CMD ["/main"]
