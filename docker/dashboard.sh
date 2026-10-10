#!/bin/sh
# Start the cockpit with one named volume so a new container keeps the same records.
#
# Build the image first:
#   docker build -f docker/Dockerfile --target gitee_app -t pr-agent:gitee_app .
#
# Then pass the two required secrets. Either export them, or use --env-file:
#   GITEE__PERSONAL_ACCESS_TOKEN=<Gitee 令牌> OPENAI__KEY=<模型密钥> docker/dashboard.sh
#   docker/dashboard.sh --env-file /path/to/secrets.env
# Optional: OPENAI__API_BASE=<模型地址>
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
