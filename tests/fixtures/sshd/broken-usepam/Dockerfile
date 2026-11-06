FROM alpine:3.24

RUN apk add --no-cache openssh-server-pam \
    && printf 'UsePAM no\n' > /etc/ssh/sshd_config.d/00-baseline.conf

EXPOSE 22
CMD ["/usr/sbin/sshd", "-D"]
