FROM alpine:3.24

RUN apk --no-cache add openssh-server

EXPOSE 22
CMD ["/usr/sbin/sshd", "-D"]
