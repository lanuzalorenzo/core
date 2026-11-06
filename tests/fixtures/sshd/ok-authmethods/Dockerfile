FROM alpine:3.24

RUN apk add --no-cache openssh-server \
    && printf '\nAuthenticationMethods publickey\n' >> /etc/ssh/sshd_config

EXPOSE 22
