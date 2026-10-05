#!/usr/bin/env bash
set -euo pipefail

config="$(cat /home/kong/kong.template.yml)"
config="${config//\$SUPABASE_ANON_KEY/$SUPABASE_ANON_KEY}"
config="${config//\$SUPABASE_SERVICE_KEY/$SUPABASE_SERVICE_KEY}"
printf '%s\n' "$config" > /tmp/kong.yml
exec /entrypoint.sh kong docker-start
