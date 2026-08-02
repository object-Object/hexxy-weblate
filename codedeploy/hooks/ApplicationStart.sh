#!/bin/bash
set -euox pipefail

cd /var/lib/codedeploy-apps/hexxy-weblate

if ! docker compose up --detach --wait --wait-timeout 480 ; then
    docker compose logs
    exit 1
fi
