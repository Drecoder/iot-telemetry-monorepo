resource "aws_kinesis_stream" "telemetry_stream" {
  name             = "robot-telemetry-ingestion-stream"
  retention_period = 24

  stream_mode_details {
    stream_mode = "ON_DEMAND"
  }

  # Activating server-side encryption using the standard AWS Kinesis master key
  encryption_type = "KMS"
  kms_key_id      = "alias/aws/kinesis"
  
  #checkov:skip=CKV_AWS_185:AWS Managed Key utilized; avoids custom KMS pricing tier overhead during MVP phase.

  tags = {
    Environment = "production"
    Project     = "cnh-telemetry"
  }
}