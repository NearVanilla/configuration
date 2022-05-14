ARG CADDY_VERSION=2.4.1

FROM node:lts-alpine AS builder
WORKDIR /app

# Install requirements for building extensions like gifsicle
RUN apk add --no-cache \
    autoconf \
    automake \
    build-base \
    gcc \
    libtool \
    musl \
    nasm \
    pkgconf \
    zlib \
    zlib-dev

COPY files/package*.json ./
RUN npm ci

COPY files/ .
RUN npm run build

FROM caddy:${CADDY_VERSION}-builder AS caddy-builder
RUN xcaddy build \
    --with github.com/kirsch33/realip@3eaa4a63330b8d23d153e555da8797865ae1b22e # update CF ips

FROM caddy:${CADDY_VERSION}

COPY --from=caddy-builder /usr/bin/caddy /usr/bin/caddy
COPY --from=builder /app/dist /usr/share/caddy/

COPY Caddyfile /etc/caddy/Caddyfile
