#!/usr/bin/env bash
set -euo pipefail

CONTAINER="checkmk"
SITE="xapps"

echo "==> Sync plugin"
bash scripts/sync-plugin.sh

echo "==> Remove Python cache"

docker exec "$CONTAINER" bash -c "
find /omd/sites/$SITE/local/lib/python3/cmk_addons/plugins/smseagle \
-name '__pycache__' -type d -exec rm -rf {} +
"

echo "==> Reload Checkmk"

docker exec "$CONTAINER" su - "$SITE" -c "cmk -R"

echo
echo "==> Registered plugins"

docker exec "$CONTAINER" su - "$SITE" -c "cmk -L | grep smseagle"

echo
echo "Deployment completed."
