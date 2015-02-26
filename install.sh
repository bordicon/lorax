#!/bin/bash -e

# Bash safe mode
set -e
set -u
set -o pipefail
set -o verbose

# Reference everything relative to directory install.sh script is in.
script_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo "Installing..."
cd $script_dir
sudo python ./setup.py install || { echo "ERROR: Installing lorax library"; exit 1; }