#!/bin/sh
# Build the CLI image and push it to Tencent Cloud TCR.
#
# Usage: docker/push.sh [tag]
# The default tag is the short git revision. Log in before running:
#   docker login ecloud-tcr.tencentcloudcr.com

set -eu

registry_image="ecloud-tcr.tencentcloudcr.com/ecloud_project/pr-agent"
tag="${1:-$(git -C "$(dirname "$0")/.." rev-parse --short HEAD)}"
root="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"

docker build \
    --file "$root/docker/Dockerfile" \
    --target cli \
    --tag "$registry_image:$tag" \
    --tag "$registry_image:latest" \
    "$root"

docker push "$registry_image:$tag"
docker push "$registry_image:latest"

printf 'pushed %s:%s and %s:latest\n' "$registry_image" "$tag" "$registry_image"
