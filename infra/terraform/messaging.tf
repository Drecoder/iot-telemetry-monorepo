resource "aws_kinesis_stream" "telemetry_stream" {
  name             = "robot-telemetry-ingestion-stream"
  retention_period = 24

  stream_mode_details {
    stream_mode = "ON_DEMAND"
  }

  tags = {
    Environment = "production"
    Project     = "cnh-telemetry"
  }
}

output "kinesis_stream_arn" {
  value = aws_kinesis_stream.telemetry_stream.arn
}