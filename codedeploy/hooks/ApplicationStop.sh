#!/bin/bash
set -euox pipefail

cd /var/lib/codedeploy-apps/weblate.hexxy.media

docker compose down || echo "Warning: Failed to stop application"
