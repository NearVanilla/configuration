ARG CADDY_VERSION=2.4.1
FROM caddy:${CADDY_VERSION}-builder AS builder

RUN xcaddy build \
    --with github.com/kirsch33/realip@8fd479b5fe674d3d611838754cd697c36af859c0 # update CF ips

ARG CADDY_VERSION
FROM caddy:${CADDY_VERSION}

COPY --from=builder /usr/bin/caddy /usr/bin/caddy
