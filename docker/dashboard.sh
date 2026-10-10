#!/bin/sh
# Start the cockpit with one named volume so a new container keeps the same records.
#
# Build the image first:
#   docker build -f docker/Dockerfile --target gitee_app -t pr-agent:gitee_app .
#
# Then export the two required secrets. The script forwards them into the container.
#   GITEE__PERSONAL_ACCESS_TOKEN=<Gitee 令牌> OPENAI__KEY=<模型密钥> docker/dashboard.sh
# Optional: OPENAI__API_BASE=<模型地址>
# Or pass a file instead of exporting: docker/dashboard.sh --env-file /path/to/secrets.env
set -eu
if [ -z "${GITEE__PERSONAL_ACCESS_TOKEN:-}" ] || [ -z "${OPENAI__KEY:-}" ]; then
  case " $* " in
    *" --env-file "*|*" -e "*|*" --env "*) ;;
    *)
      echo "需要 GITEE__PERSONAL_ACCESS_TOKEN 和 OPENAI__KEY。" >&2
      echo "GITEE__PERSONAL_ACCESS_TOKEN=<令牌> OPENAI__KEY=<密钥> docker/dashboard.sh" >&2
      exit 1
      ;;
  esac
fi
# Prepend -e so exported secrets reach the container. Skip empty values so --env-file is not wiped.
if [ -n "${OPENAI__API_BASE:-}" ]; then
  set -- -e "OPENAI__API_BASE=${OPENAI__API_BASE}" "$@"
fi
if [ -n "${OPENAI__KEY:-}" ]; then
  set -- -e "OPENAI__KEY=${OPENAI__KEY}" "$@"
fi
if [ -n "${GITEE__PERSONAL_ACCESS_TOKEN:-}" ]; then
  set -- -e "GITEE__PERSONAL_ACCESS_TOKEN=${GITEE__PERSONAL_ACCESS_TOKEN}" "$@"
fi
root=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
build=$(git -C "$root" rev-parse --short HEAD 2>/dev/null || printf 'dev')
image="${PR_AGENT_IMAGE:-pr-agent:gitee_app}"
docker volume create pr-agent-data >/dev/null
exec docker run --name gitee-dashboard \
  --user 10001:10001 \
  -p 3010:3000 \
  -v pr-agent-data:/data \
  -e "PR_AGENT_BUILD=${build}" \
  "$@" \
  "$image"
