#!/usr/bin/env bash
set -euo pipefail

###############################################################################
# Determine version
###############################################################################

if git describe --tags --abbrev=0 >/dev/null 2>&1; then
    VERSION="$(git describe --tags --abbrev=0)"
    VERSION="${VERSION#v}"
elif [[ -f VERSION ]]; then
    VERSION="$(tr -d '\r\n' < VERSION)"
else
    echo "ERROR: Unable to determine version."
    echo "Create a VERSION file or create a Git tag."
    exit 1
fi

echo "Building version ${VERSION}"

###############################################################################
# Prepare build directory
###############################################################################

mkdir -p build

###############################################################################
# Generate manifest
###############################################################################

cat > build/smseagle.manifest <<MANIFEST
{
 'author': 'Reinier Kops',
 'description': 'CheckMK SNMP monitoring plugin for the SMSEagle SMS gateway.',
 'download_url': 'https://github.com/reinierkops/checkmk-smseagle',
 'files': {
     'checkman': [
         'smseagle_environment',
         'smseagle_folders',
         'smseagle_gsm',
         'smseagle_sms_count',
     ],

     'cmk_addons_plugins': [
         'smseagle/agent_based/smseagle.py',
         'smseagle/checkman/smseagle_environment',
         'smseagle/checkman/smseagle_folders',
         'smseagle/checkman/smseagle_gsm',
         'smseagle/checkman/smseagle_sms_count',
         'smseagle/graphing/smseagle.py',
         'smseagle/rulesets/smseagle.py',
     ]
 },

 'name': 'smseagle',
 'title': 'SMSEagle',
 'version': '${VERSION}',
 'version.min_required': '2.4.0',
 'version.packaged': 'cmk-mkp-tool',
 'version.usable_until': None,
}
MANIFEST

###############################################################################
# Done
###############################################################################

echo
echo "==============================================="
echo "Manifest generated:"
echo "  build/smseagle.manifest"
echo "Version : ${VERSION}"
echo "==============================================="
echo

cat build/smseagle.manifest
