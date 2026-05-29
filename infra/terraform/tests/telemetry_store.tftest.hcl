# Setup variables specifically for the test run
variables {
  aws_region  = "us-west-2"
  environment = "test-env"
}

# Run block executes a plan or apply phase to evaluate assertions
run "validate_dynamodb_payload_configuration" {
  command = plan # "plan" tests configuration logic; change to "apply" for actual sandbox deployment

  # Assertions act like unit test expectations
  assert {
    condition     = aws_dynamodb_table.telemetry_store.hash_key == "robotId"
    error_message = "The DynamoDB Partition Key must be exactly 'robotId' for fleet routing."
  }

  assert {
    condition     = aws_dynamodb_table.telemetry_store.range_key == "timestamp"
    error_message = "The DynamoDB Sort Key must be exactly 'timestamp' for time-series metrics."
  }

  assert {
    condition     = aws_dynamodb_table.telemetry_store.billing_mode == "PAY_PER_REQUEST"
    error_message = "MVP database scaling mode must be serverless On-Demand (PAY_PER_REQUEST)."
  }

  assert {
    condition     = aws_dynamodb_table.telemetry_store.point_in_time_recovery[0].enabled == true
    error_message = "Disaster recovery warning: Point-in-time recovery (PITR) must be enabled."
  }
}