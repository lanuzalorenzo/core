FROM alpine:3.24

RUN apk add --no-cache openssh-server

EXPOSE 22
CMD ["/usr/sbin/sshd", "-D"]
