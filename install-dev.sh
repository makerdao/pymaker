
#!/usr/bin/env bash

cd "$(dirname "$0")"

set -e

rm -rf _virtualenv
python3 -m venv _virtualenv
source _virtualenv/bin/activate

# install production requirements (no lib submodules here so no need to go through a lib directory)
pip install -r requirements.txt

# install development requirements
pip install -r requirements-dev.txt
