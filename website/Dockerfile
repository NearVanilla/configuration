ARG CADDY_VERSION=2.6.4

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
    --with github.com/kirsch33/realip@83c6d2c726eeb33b1b33270774dcbf78060bcfc5

FROM caddy:${CADDY_VERSION}

COPY --from=caddy-builder /usr/bin/caddy /usr/bin/caddy
COPY --from=builder /app/dist /usr/share/caddy/

COPY Caddyfile /etc/caddy/Caddyfile
