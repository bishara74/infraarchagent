terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "= 6.68.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "= 3.9.1"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "= 2.38.0"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "= 2.17.0"
    }
    tls = {
      source  = "hashicorp/tls"
      version = "= 4.4.1"
    }
    null = {
      source  = "hashicorp/null"
      version = "= 3.3.2"
    }
  }
}
