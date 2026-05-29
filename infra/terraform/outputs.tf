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

output "ecs_cluster_name" {
  description = "The name of the serverless container orchestration cluster"
  value       = aws_ecs_cluster.telemetry_cluster.name
}

output "ecs_cluster_arn" {
  description = "The Amazon Resource Name assigned to the active container cluster"
  value       = aws_ecs_cluster.telemetry_cluster.arn
}