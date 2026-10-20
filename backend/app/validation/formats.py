"""D-56 author-approved lossless Grafana envelopes and standard Helm helpers."""

import hashlib
import json
import re
from pathlib import PurePosixPath
from typing import Any

import yaml  # type: ignore[import-untyped]

HELPERS = {
    "name": (
        '{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}'
    ),
    "fullname": """{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}""",
    "chart": (
        '{{- printf "%s-%s" .Chart.Name .Chart.Version | re'
        'place "+" "_" | trunc 63 | trimSuffix "-" }}'
    ),
    "selectorLabels": """app.kubernetes.io/name: {{ include "PREFIX.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}""",
    "labels": """helm.sh/chart: {{ include "PREFIX.chart" . }}
{{ include "PREFIX.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}""",
}
NAMED = re.compile(r'\b(include|template|define)\s+"([a-zA-Z0-9_.-]{1,128})"')


def format_record(
    path: str, kind: str, name: str, before: str, after: str
) -> dict[str, Any]:
    return {
        "file": path,
        "kind": kind,
        "name": name,
        "before_hash": hashlib.sha256(before.encode()).hexdigest(),
        "after_hash": hashlib.sha256(after.encode()).hexdigest(),
    }


def repair_formats(
    files: dict[str, str],
) -> tuple[dict[str, str], list[dict[str, Any]]]:
    result, records = dict(files), []
    for path, source in sorted(files.items()):
        if path.startswith("monitoring/grafana/") and path.endswith(".json"):
            try:
                data = json.loads(source)
            except (ValueError, TypeError):
                continue
            if (
                isinstance(data, dict)
                and isinstance(data.get("dashboard"), dict)
                and set(data) <= {"dashboard", "overwrite", "meta"}
                and ("overwrite" not in data or type(data["overwrite"]) is bool)
                and ("meta" not in data or isinstance(data["meta"], dict))
            ):
                dashboard = data["dashboard"]
                if not isinstance(dashboard.get("panels"), list):
                    continue
                content = json.dumps(dashboard, ensure_ascii=False, indent=2) + "\n"
                result[path] = content
                records.append(
                    format_record(
                        path, "grafana_envelope", "dashboard", source, content
                    )
                )
    charts = [
        p
        for p in files
        if p.startswith("helm/") and PurePosixPath(p).name == "Chart.yaml"
    ]
    for chart in sorted(charts):
        root = str(PurePosixPath(chart).parent)
        try:
            data = yaml.safe_load(files[chart])
        except yaml.YAMLError:
            continue
        prefix = data.get("name") if isinstance(data, dict) else None
        if not isinstance(prefix, str) or not re.fullmatch(
            r"[a-zA-Z0-9_.-]{1,100}", prefix
        ):
            continue
        defined: set[str] = set()
        referenced: set[str] = set()
        for path, source in files.items():
            if not path.startswith(root + "/templates/"):
                continue
            source = re.sub(r"\{\{-?/\*.*?\*/-?\}\}", "", source, flags=re.S)
            for action in re.findall(r"\{\{(.*?)\}\}", source, flags=re.S):
                for kind, name in NAMED.findall(action):
                    (defined if kind == "define" else referenced).add(name)
        additions = []
        pending = sorted(referenced - defined)
        while pending:
            name = pending.pop(0)
            if name in defined:
                continue
            stem, _, suffix = name.rpartition(".")
            if stem != prefix or suffix not in HELPERS:
                continue
            body = HELPERS[suffix].replace("PREFIX", prefix)
            additions.append(
                '{{- define "' + name + '" -}}\n' + body + "\n{{- end }}\n"
            )
            defined.add(name)
            pending.extend(
                ref
                for kind, ref in NAMED.findall(body)
                if kind != "define" and ref not in defined
            )
        if additions:
            target = root + "/templates/_helpers.tpl"
            old = result.get(target, "")
            content = old + ("\n" if old else "") + "\n".join(additions)
            result[target] = content
            records.append(format_record(target, "helm_helpers", prefix, old, content))
    return result, records
