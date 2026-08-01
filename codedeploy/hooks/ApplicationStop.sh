#!/bin/bash
set -euox pipefail

cd /var/lib/codedeploy-apps/hexxy-weblate

docker compose down || echo "Warning: Failed to stop application"
