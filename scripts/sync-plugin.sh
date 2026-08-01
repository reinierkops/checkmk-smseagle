cat > scripts/sync-plugin.sh <<'EOF'
#!/usr/bin/env bash
set -euo pipefail

###############################################################################
# Configuration
###############################################################################

CONTAINER="${CONTAINER:-checkmk}"
SITE="${SITE:-xapps}"
PLUGIN="smseagle"

PLUGIN_BASE="/omd/sites/${SITE}/local/lib/python3/cmk_addons/plugins/${PLUGIN}"
CHECKMAN_BASE="/omd/sites/${SITE}/local/share/check_mk/checkman"

PLUGIN_DIRS=(
    agent_based
    checkman
    graphing
    rulesets
    inventory
    server_side_calls
    bakery
)

###############################################################################
# Synchronize
###############################################################################

echo "==> Synchronizing plugin files"

docker exec "$CONTAINER" mkdir -p "$PLUGIN_BASE"
docker exec "$CONTAINER" mkdir -p "$CHECKMAN_BASE"

for dir in "${PLUGIN_DIRS[@]}"; do

    [[ -d "$dir" ]] || continue

    echo " -> $dir"

    docker exec "$CONTAINER" mkdir -p "$PLUGIN_BASE/$dir"

    docker cp "$dir/." \
        "$CONTAINER:$PLUGIN_BASE/$dir/"
done

###############################################################################
# Legacy checkman
###############################################################################

if [[ -d checkman ]]; then
    echo " -> legacy checkman"

    docker cp checkman/. \
        "$CONTAINER:$CHECKMAN_BASE/"
fi

###############################################################################
# Fix ownership
###############################################################################

docker exec "$CONTAINER" chown -R "${SITE}:${SITE}" \
    "/omd/sites/${SITE}/local"

###############################################################################
# Debug
###############################################################################

echo
echo "Installed plugin files:"
docker exec "$CONTAINER" find "$PLUGIN_BASE" -type f | sort

echo
echo "Installed legacy checkman:"
docker exec "$CONTAINER" find "$CHECKMAN_BASE" -type f | sort

echo
echo "Plugin synchronized."
EOF

chmod +x scripts/sync-plugin.sh
