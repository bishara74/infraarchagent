# Least-privilege IRSA roles for microservices needing AWS access
data "tls_certificate" "eks" {
  url = aws_eks_cluster.main.identity[0].oidc[0].issuer
}

resource "aws_iam_openid_connect_provider" "eks" {
  client_id_list  = ["sts.amazonaws.com"]
  thumbprint_list = [data.tls_certificate.eks.certificates[0].sha1_fingerprint]
  url             = aws_eks_cluster.main.identity[0].oidc[0].issuer
}

resource "aws_iam_role" "microservice_a_irsa" {
  name = "${local.name_prefix}-microservice-a-irsa"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = { Federated = aws_iam_openid_connect_provider.eks.arn }
      Action = "sts:AssumeRoleWithWebIdentity"
      Condition = {
        StringEquals = {
          "${replace(aws_iam_openid_connect_provider.eks.url, "https://", "")}:sub" = "system:serviceaccount:default:microservice-a"
        }
      }
    }]
  })
}

resource "aws_iam_role_policy" "microservice_a_secrets" {
  name = "${local.name_prefix}-microservice-a-secrets-policy"
  role = aws_iam_role.microservice_a_irsa.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["secretsmanager:GetSecretValue"]
      Resource = [aws_secretsmanager_secret.rds.arn]
    }]
  })
}

data "tls_certificate" "eks_unused" {
  url = aws_eks_cluster.main.identity[0].oidc[0].issuer
}
