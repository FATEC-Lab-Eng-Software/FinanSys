#!/bin/sh
set -eu
if [ ! -f "$HOME/.env" ]; then
    : > "$HOME/.env"
fi
if grep -q '^API_SERVER_KEY=' "$HOME/.env"; then
    sed -i "s|^API_SERVER_KEY=.*|API_SERVER_KEY=${API_SERVER_KEY}|" "$HOME/.env"
else
    printf '\nAPI_SERVER_KEY=%s\n' "$API_SERVER_KEY" >> "$HOME/.env"
fi
hermes config set platform_toolsets.api_server '[]' >/dev/null
exec hermes gateway run
