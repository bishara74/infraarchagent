#!/usr/bin/env bash
# AUTHOR ONLY: clean Ubuntu 24.04 amd64; requires network and sudo.
set -euo pipefail
test "$(. /etc/os-release; echo "$ID:$VERSION_ID")" = ubuntu:24.04
test "$(uname -m)" = x86_64
sudo apt-get update
sudo apt-get install -y --no-install-recommends ca-certificates curl git make \
  python3 python3-venv pipx docker.io docker-compose-v2 unzip xz-utils
sudo systemctl start docker
task_work=$(mktemp -d)
trap 'rm -rf "$task_work"' EXIT
cd "$task_work"

# Release files are verified before extraction. These are explicit versions.
trivy_version=0.69.3
trivy_archive="trivy_${trivy_version}_Linux-64bit.tar.gz"
curl -fsSLO "https://github.com/aquasecurity/trivy/releases/download/v${trivy_version}/${trivy_archive}"
curl -fsSLO "https://github.com/aquasecurity/trivy/releases/download/v${trivy_version}/trivy_${trivy_version}_checksums.txt"
awk -v name="$trivy_archive" '$2 == name || $2 == "*"name {print}' \
  "trivy_${trivy_version}_checksums.txt" > trivy.sha256
test "$(wc -l < trivy.sha256)" -eq 1
sha256sum -c trivy.sha256
tar -xzf "$trivy_archive" trivy
sudo install -m 0755 trivy /usr/local/bin/trivy

terraform_version=1.16.4
terraform_archive="terraform_${terraform_version}_linux_amd64.zip"
curl -fsSLO "https://releases.hashicorp.com/terraform/${terraform_version}/${terraform_archive}"
curl -fsSLO "https://releases.hashicorp.com/terraform/${terraform_version}/terraform_${terraform_version}_SHA256SUMS"
awk -v name="$terraform_archive" '$2 == name {print}' \
  "terraform_${terraform_version}_SHA256SUMS" > terraform.sha256
test "$(wc -l < terraform.sha256)" -eq 1
sha256sum -c terraform.sha256
unzip -q "$terraform_archive" terraform
sudo install -m 0755 terraform /usr/local/bin/terraform

node_version=24.21.0
node_archive="node-v${node_version}-linux-x64.tar.xz"
curl -fsSLO "https://nodejs.org/dist/v${node_version}/${node_archive}"
curl -fsSLO "https://nodejs.org/dist/v${node_version}/SHASUMS256.txt"
awk -v name="$node_archive" '$2 == name {print}' SHASUMS256.txt > node.sha256
test "$(wc -l < node.sha256)" -eq 1
sha256sum -c node.sha256
tar -xJf "$node_archive"
sudo cp -a "node-v${node_version}-linux-x64/." /usr/local/
pipx install 'checkov==3.3.21'
# Optional validators use the existing pinned/checksummed author installer.
# Run tools/install_validators.sh separately if their coverage is desired.
