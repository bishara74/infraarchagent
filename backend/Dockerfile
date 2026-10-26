# Author-built recipe; image availability/build/runtime remain unverified.
FROM curlimages/curl:8.12.1 AS scanner-binaries
USER 0
WORKDIR /tmp/tools
SHELL ["/bin/ash", "-eo", "pipefail", "-c"]
RUN curl -fsSLO https://github.com/aquasecurity/trivy/releases/download/v0.69.3/trivy_0.69.3_Linux-64bit.tar.gz \
    && curl -fsSLO https://github.com/aquasecurity/trivy/releases/download/v0.69.3/trivy_0.69.3_checksums.txt \
    && awk '$2 == "trivy_0.69.3_Linux-64bit.tar.gz" {print}' trivy_0.69.3_checksums.txt > trivy.sha256 \
    && test "$(wc -l < trivy.sha256)" -eq 1 \
    && sha256sum -c trivy.sha256 \
    && tar -xzf trivy_0.69.3_Linux-64bit.tar.gz trivy \
    && curl -fsSLO https://releases.hashicorp.com/terraform/1.16.4/terraform_1.16.4_linux_amd64.zip \
    && curl -fsSLO https://releases.hashicorp.com/terraform/1.16.4/terraform_1.16.4_SHA256SUMS \
    && awk '$2 == "terraform_1.16.4_linux_amd64.zip" {print}' terraform_1.16.4_SHA256SUMS > terraform.sha256 \
    && test "$(wc -l < terraform.sha256)" -eq 1 \
    && sha256sum -c terraform.sha256 \
    && unzip -q terraform_1.16.4_linux_amd64.zip terraform

USER 100

FROM python:3.12.3-slim-bookworm
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 \
    PATH="/opt/backend/bin:/opt/checkov/bin:$PATH"
WORKDIR /srv/infraarch/backend
COPY backend/pyproject.toml backend/requirements.lock backend/alembic.ini ./
COPY backend/app ./app
COPY backend/scripts ./scripts
RUN python -m venv /opt/backend \
    && /opt/backend/bin/pip install --no-cache-dir setuptools==80.9.0 \
    && /opt/backend/bin/pip install --no-cache-dir --no-build-isolation -c requirements.lock -e . \
    && python -m venv /opt/checkov \
    && /opt/checkov/bin/pip install --no-cache-dir checkov==3.3.21 \
    && useradd --uid 10001 --create-home infraarch \
    && mkdir -p /srv/infraarch/.cache/terraform-providers /srv/infraarch/.cache/terraform-provider-schemas \
    && chown -R infraarch:infraarch /srv/infraarch
COPY --from=scanner-binaries /tmp/tools/trivy /tmp/tools/terraform /usr/local/bin/
USER 10001:10001
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/health',timeout=4).read()"]
CMD ["python", "-m", "app.server", "--host", "0.0.0.0", "--port", "8000"]
