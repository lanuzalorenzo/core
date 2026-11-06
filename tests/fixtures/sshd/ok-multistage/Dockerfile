FROM alpine:3.24 AS build

RUN apk add --no-cache openssh-server

FROM debian:13-slim AS final

COPY --from=build /bin/sh /bin/sh

EXPOSE 22
