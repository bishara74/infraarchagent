# Terraform provider mirror

Exact pins cover both AWS majors in the original Phase 3 packages; random
also appears in those packages. Kubernetes and Helm preserve their saved
major-2 constraints. TLS and null provide the requested minimum coverage.

Provision with `make providers` using existing Terraform. This is the only
online step. Runtime init uses the mirror with network access disabled.
Separate configuration roots allow AWS 5 and 6 in the same shared mirror.
The mirror is gitignored; lock records and the hashes below are committed.

Captured UTC: 2026-10-09T12:59:52.981433+00:00
Mirror file bytes: 391710515 (373.56 MiB).

| Archive | SHA-256 |
|---|---|
| `registry.terraform.io/hashicorp/aws/terraform-provider-aws_5.100.0_linux_amd64.zip` | `1589a2266af699cbd5d80737a0fe02e54ec9cf2ca54e7e00ac51c7359056f274` |
| `registry.terraform.io/hashicorp/aws/terraform-provider-aws_6.68.0_linux_amd64.zip` | `b2511842cb6b23036c72babbaf12b4984835bb2824f938882330b51c68bdaecd` |
| `registry.terraform.io/hashicorp/helm/terraform-provider-helm_2.17.0_linux_amd64.zip` | `88644260090aa621e7e8083585c468c8dd5e09a3c01a432fb05da5c4623af940` |
| `registry.terraform.io/hashicorp/kubernetes/terraform-provider-kubernetes_2.38.0_linux_amd64.zip` | `d39861aa21077f1bc899bc53e7233262e530ba8a3a2d737449b100daeb303e4d` |
| `registry.terraform.io/hashicorp/null/terraform-provider-null_3.3.2_linux_amd64.zip` | `d2855b922ea345dbd89ea287e4c6c4757e38bc0aaffeb2b79aa0b8004f9c53ff` |
| `registry.terraform.io/hashicorp/random/terraform-provider-random_3.9.1_linux_amd64.zip` | `60b4f8a8ef18f52bf8e19215229dae408bee732825964092db7c989fd2de4097` |
| `registry.terraform.io/hashicorp/tls/terraform-provider-tls_4.4.1_linux_amd64.zip` | `debc830ec123f27944c6170d76cb4ea3542845896960bb9fc530702774df328e` |

## Terraform signature-verification output

```text
- Mirroring hashicorp/null...
  - Selected v3.3.2 to meet constraints 3.3.2
  - Downloading package for linux_amd64...
  - Package authenticated: signed by HashiCorp
- Mirroring hashicorp/aws...
  - Selected v6.68.0 to meet constraints 6.68.0
  - Downloading package for linux_amd64...
  - Package authenticated: signed by HashiCorp
- Mirroring hashicorp/random...
  - Selected v3.9.1 to meet constraints 3.9.1
  - Downloading package for linux_amd64...
  - Package authenticated: signed by HashiCorp
- Mirroring hashicorp/kubernetes...
  - Selected v2.38.0 to meet constraints 2.38.0
  - Downloading package for linux_amd64...
  - Package authenticated: signed by HashiCorp
- Mirroring hashicorp/helm...
  - Selected v2.17.0 to meet constraints 2.17.0
  - Downloading package for linux_amd64...
  - Package authenticated: signed by HashiCorp
- Mirroring hashicorp/tls...
  - Selected v4.4.1 to meet constraints 4.4.1
  - Downloading package for linux_amd64...
  - Package authenticated: signed by HashiCorp

- Mirroring hashicorp/aws...
  - Selected v5.100.0 to meet constraints 5.100.0
  - Downloading package for linux_amd64...
  - Package authenticated: signed by HashiCorp

```

Lock records were derived with `terraform providers lock
-fs-mirror=<mirror> -platform=linux_amd64`; that command uses local archives.
