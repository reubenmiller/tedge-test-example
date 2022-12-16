#!/bin/bash
#
# Configure python virtual environment
# * Add workspace path to site-packages so the roo
#
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
pushd "$SCRIPT_DIR" >/dev/null || exit 1

python3 -m venv env
source env/bin/activate
python3 -m pip install -r requirements.txt
python3 -m pip install -r requirements-dev.txt

SITE_LIB=$(python3 -c 'import sysconfig; print(sysconfig.get_paths()["purelib"])')
PROJECT_DIR=$( cd --  "$SCRIPT_DIR/../" && pwd )

echo "Creating .pth file for workspace: $SITE_LIB/workspace.pth"
# Add one path per line
cat << EOT > "$SITE_LIB/workspace.pth"
$PROJECT_DIR
$PROJECT_DIR/src
$PROJECT_DIR/lib
EOT

popd >/dev/null || exit 1
