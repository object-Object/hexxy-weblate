#!/bin/bash
set -euox pipefail

cd /var/lib/codedeploy-apps/weblate.hexxy.media

docker login ghcr.io --username object-Object --password-stdin < /var/lib/codedeploy-apps/.cr_pat

docker compose pull
