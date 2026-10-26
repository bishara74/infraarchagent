#!/usr/bin/env bash
# AUTHOR ONLY. No deployment claim follows from static checking this file.
set -euo pipefail
if [ "$#" -ne 4 ]; then
  echo 'Usage: bash clean-ubuntu.sh REPOSITORY FULL_COMMIT NEW_CHECKOUT NEW_EVIDENCE'
  exit 2
fi
repository=$1
revision=$2
checkout=$3
evidence=$4
[[ "$revision" =~ ^[0-9a-f]{40}$ ]] || { echo 'Supply a full commit hash.'; exit 2; }
[[ "$repository" != *'@'* && "$repository" != *'?'* ]] || {
  echo 'Use a public HTTPS or local repository address without credentials.'; exit 2;
}
test ! -e "$checkout"
test ! -e "$evidence"
sudo apt-get update
sudo apt-get install -y --no-install-recommends git ca-certificates
git clone --no-checkout -- "$repository" "$checkout"
git -C "$checkout" checkout --detach "$revision"
bash "$checkout/tools/deployment/install-prerequisites.sh"
export PATH="$HOME/.local/bin:$PATH"
python3 "$checkout/tools/deployment/clean_deploy.py" --checkout "$checkout" \
  --evidence "$evidence" --run
