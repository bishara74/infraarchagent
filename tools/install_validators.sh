#!/usr/bin/env bash
# Installs the external validators used by the ValidatorAgent (Phase 6):
#   helm v4.3.0, hadolint v2.15.1, promtool (Prometheus v3.15.0), ansible-lint 26.9.0.
# All versions are pinned to the ones used for the thesis (verified 2026-10-09).
# Every binary download is verified against the checksum published with its release.
# Prints the exact installed versions at the end -> record them in the thesis (Appendix A).
set -euo pipefail

WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT
cd "$WORK"

echo "== helm (pinned v4.3.0)"
HELM_V=v4.3.0
curl -fsSLO "https://get.helm.sh/helm-${HELM_V}-linux-amd64.tar.gz"
curl -fsSLO "https://get.helm.sh/helm-${HELM_V}-linux-amd64.tar.gz.sha256sum"
sha256sum -c "helm-${HELM_V}-linux-amd64.tar.gz.sha256sum"
tar -xzf "helm-${HELM_V}-linux-amd64.tar.gz"
sudo install -m 0755 linux-amd64/helm /usr/local/bin/helm

echo "== hadolint (pinned v2.15.1, checksum-verified)"
HADOLINT_V=v2.15.1
BIN=hadolint-linux-x86_64
curl -fsSLO "https://github.com/hadolint/hadolint/releases/download/${HADOLINT_V}/${BIN}"
# Newer releases publish one combined checksums.sha256; older ones a per-binary ${BIN}.sha256.
# Strip CR (the file may have Windows line endings) and accept "name", "*name" or "./name".
if curl -fsSLO "https://github.com/hadolint/hadolint/releases/download/${HADOLINT_V}/checksums.sha256"; then
  EXPECTED=$(tr -d '\r' < checksums.sha256 | grep -E "[ */]${BIN}\$" | awk '{print $1}' | head -1 || true)
else
  curl -fsSLO "https://github.com/hadolint/hadolint/releases/download/${HADOLINT_V}/${BIN}.sha256"
  EXPECTED=$(tr -d '\r' < "${BIN}.sha256" | awk '{print $1}' | head -1 || true)
fi
ACTUAL=$(sha256sum "$BIN" | awk '{print $1}')
[ -n "$EXPECTED" ] || { echo "hadolint checksum for ${BIN} not found - aborting"; exit 1; }
[ "$EXPECTED" = "$ACTUAL" ] || { echo "hadolint checksum MISMATCH - aborting"; exit 1; }
echo "${BIN}: OK"
sudo install -m 0755 "$BIN" /usr/local/bin/hadolint

echo "== promtool (from the pinned Prometheus v3.15.0 release, checksum-verified)"
PROM_V=v3.15.0
PROM_N=${PROM_V#v}
PROM_TGZ="prometheus-${PROM_N}.linux-amd64.tar.gz"
curl -fsSLO "https://github.com/prometheus/prometheus/releases/download/${PROM_V}/${PROM_TGZ}"
curl -fsSLO "https://github.com/prometheus/prometheus/releases/download/${PROM_V}/sha256sums.txt"
grep " ${PROM_TGZ}\$" sha256sums.txt | sha256sum -c -
tar -xzf "$PROM_TGZ"
sudo install -m 0755 "prometheus-${PROM_N}.linux-amd64/promtool" /usr/local/bin/promtool

echo "== ansible-lint (pinned 26.9.0 via pipx)"
ANSIBLE_LINT_V=26.9.0
pipx install --force "ansible-lint==${ANSIBLE_LINT_V}"

echo
echo "=========== Installed versions (record these for Appendix A) ==========="
echo "helm:         $(helm version --short)"
echo "hadolint:     $(hadolint --version)"
echo "promtool:     $(promtool --version 2>&1 | head -1)"
echo "ansible-lint: $(ansible-lint --version 2>/dev/null | head -1)"
