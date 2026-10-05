ARG CADDY_VERSION=2.6.4

FROM oven/bun:1 AS builder
WORKDIR /app

COPY files/package.json files/bun.lock ./
RUN bun install --frozen-lockfile

COPY files/ .
RUN bunx svelte-kit sync && bun run build

FROM caddy:${CADDY_VERSION}-builder AS caddy-builder
RUN xcaddy build \
    --with github.com/kirsch33/realip@83c6d2c726eeb33b1b33270774dcbf78060bcfc5

FROM caddy:${CADDY_VERSION}

COPY --from=caddy-builder /usr/bin/caddy /usr/bin/caddy
COPY --from=builder /app/build /usr/share/caddy/

COPY Caddyfile /etc/caddy/Caddyfile
