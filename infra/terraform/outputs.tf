# ==============================================================================
# NETWORKING OUTPUTS
# ==============================================================================

output "vpc_id" {
  description = "The unique identifier of the provisioned IoT Fleet VPC"
  value       = aws_vpc.main.id
}

output "public_subnet_ids" {
  description = "List of public subnet identifiers used for network ingress routing"
  value       = [aws_subnet.public_1.id, aws_subnet.public_2.id]
}

output "private_subnet_ids" {
  description = "List of private subnet identifiers where application containers execute safely"
  value       = [aws_subnet.private_1.id]
}

# ==============================================================================
# DATA SUBSYSTEM OUTPUTS
# ==============================================================================

output "dynamodb_table_name" {
  description = "The target database table name required by application runtime environments"
  value       = aws_dynamodb_table.telemetry_store.name
}

output "dynamodb_table_arn" {
  description = "The Amazon Resource Name of the table used to configure explicit IAM policies"
  value       = aws_dynamodb_table.telemetry_store.arn
}

# ==============================================================================
# COMPUTE ORCHESTRATION OUTPUTS
# ==============================================================================

output "eks_cluster_name" {
  description = "The name of the provisioned enterprise EKS cluster"
  value       = aws_eks_cluster.main.name
}

output "eks_cluster_arn" {
  description = "The Amazon Resource Name (ARN) of the EKS cluster"
  value       = aws_eks_cluster.main.arn
}

output "eks_cluster_endpoint" {
  description = "The endpoint URL for the EKS Kubernetes API server"
  value       = aws_eks_cluster.main.endpoint
}

output "eks_cluster_certificate_authority" {
  description = "The base64 encoded certificate data required to communicate with the cluster"
  value       = aws_eks_cluster.main.certificate_authority[0].data
  sensitive   = true
}