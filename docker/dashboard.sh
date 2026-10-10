#!/bin/sh
# Start the cockpit with one named volume so a new container keeps the same records.
set -eu
root=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
build=$(git -C "$root" rev-parse --short HEAD 2>/dev/null || printf 'dev')
docker volume create pr-agent-data >/dev/null
exec docker run --name gitee-dashboard \
  --user 10001:10001 \
  -p 3010:3000 \
  -v pr-agent-data:/data \
  -e "PR_AGENT_BUILD=${build}" \
  "$@" \
  gitee-pr-agent:dashboard
