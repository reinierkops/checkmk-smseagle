#!/usr/bin/env bash
set -euo pipefail

CONTAINER="checkmk"
BUILD_SITE="mkpbuild"

echo "==> Generate manifest"
bash scripts/build-manifest.sh

echo
echo "==> Create temporary build site"

docker exec "$CONTAINER" bash -c "
omd sites | grep -q '^${BUILD_SITE}[[:space:]]' && omd rm -f ${BUILD_SITE} || true
omd create ${BUILD_SITE}
"

echo
echo "==> Create plugin directories"

docker exec "$CONTAINER" bash -c "
mkdir -p /omd/sites/${BUILD_SITE}/local/lib/python3/cmk_addons/plugins/smseagle
"

echo
echo "==> Copy plugin"

for dir in agent_based checkman graphing rulesets
do
    [ -d "$dir" ] || continue

    docker exec "$CONTAINER" mkdir -p \
        /omd/sites/${BUILD_SITE}/local/lib/python3/cmk_addons/plugins/smseagle/$dir

    docker cp "$dir/." \
        "$CONTAINER:/omd/sites/${BUILD_SITE}/local/lib/python3/cmk_addons/plugins/smseagle/$dir/"
done

echo
echo "==> Copy legacy checkman"

docker exec "$CONTAINER" mkdir -p \
    /omd/sites/${BUILD_SITE}/local/share/check_mk/checkman

docker cp checkman/. \
    "$CONTAINER:/omd/sites/${BUILD_SITE}/local/share/check_mk/checkman/"

echo
echo "==> Copy manifest"

docker cp build/smseagle.manifest \
    "$CONTAINER:/omd/sites/${BUILD_SITE}/tmp/smseagle.manifest"

echo
echo "==> Build package"

docker exec "$CONTAINER" su - "$BUILD_SITE" -c \
    "mkp package /omd/sites/${BUILD_SITE}/tmp/smseagle.manifest"

echo
echo "==> Copy MKP"

mkdir -p build

MKP=$(docker exec "$CONTAINER" find /omd/sites/${BUILD_SITE} -name "*.mkp" | head -1)

docker cp "$CONTAINER:$MKP" build/

echo
echo "==> Cleanup"

docker exec "$CONTAINER" omd rm -f "$BUILD_SITE"

echo
echo "========================================"
echo "Package created:"
ls -lh build/*.mkp
echo "========================================"
