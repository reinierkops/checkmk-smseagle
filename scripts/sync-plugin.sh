#!/usr/bin/env bash
set -euo pipefail

CONTAINER="checkmk"
SITE="xapps"
PLUGIN="smseagle"

BASE="/omd/sites/${SITE}/local/lib/python3/cmk_addons/plugins/${PLUGIN}"

# Plugin directories die automatisch gesynchroniseerd worden
PLUGIN_DIRS=(
    agent_based
    checkman
    graphing
    rulesets
    inventory
    server_side_calls
    bakery
)

echo "==> Synchronizing plugin files"

for dir in "${PLUGIN_DIRS[@]}"; do

    # Sla directories over die niet bestaan
    [[ -d "$dir" ]] || continue

    echo " -> $dir"

    docker exec "$CONTAINER" mkdir -p "$BASE/$dir"

    docker cp "$dir/." \
        "$CONTAINER:$BASE/$dir/"

done

echo
echo "Plugin synchronized."
