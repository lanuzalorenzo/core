FROM alpine:3.24

RUN apk add --no-cache openssh-server \
    && printf '\nPasswordAuthentication no\n' >> /etc/ssh/sshd_config

EXPOSE 22
CMD ["/usr/sbin/sshd", "-D"]
