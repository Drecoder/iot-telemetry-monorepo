terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# ==============================================================================
# NETWORKING LAYER (VPC & Subnets)
# ==============================================================================

# Dedicated VPC for the Fleet Telemetry Subsystem
resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name        = "iot-fleet-vpc-${var.environment}"
    Environment = var.environment
  }
}

# Public Subnets (For Internet Ingress & Load Balancer)
resource "aws_subnet" "public_1" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.1.0/24"
  availability_zone = "${var.aws_region}a"
  map_public_ip_on_launch = true

  tags = { Name = "iot-public-subnet-1a" }
}

resource "aws_subnet" "public_2" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.2.0/24"
  availability_zone = "${var.aws_region}b"
  map_public_ip_on_launch = true

  tags = { Name = "iot-public-subnet-1b" }
}

# Private Subnets (For Isolated Compute Application Layer)
resource "aws_subnet" "private_1" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.10.0/24"
  availability_zone = "${var.aws_region}a"

  tags = { Name = "iot-private-subnet-1a" }
}

# ==============================================================================
# PERSISTENCE LAYER (NoSQL Telemetry Store)
# ==============================================================================

# NoSQL database optimized for massive horizontal concurrent device writes
resource "aws_dynamodb_table" "telemetry_store" {
  name         = "FleetTelemetry"
  billing_mode = "PAY_PER_REQUEST" # Serverless On-Demand pricing for variable IoT spikes
  hash_key     = "robotId"        # Partition Key: Uniformly distributes data across clusters
  range_key    = "timestamp"      # Sort Key: High-performance chronological lookups

  attribute {
    name = "robotId"
    type = "S"
  }

  attribute {
    name = "timestamp"
    type = "N"
  }

  # Crucial disaster recovery rule for production safety audits
  point_in_time_recovery {
    enabled = true
  }

  tags = {
    Environment = var.environment
    Subsystem   = "Telemetry"
  }
}

# ==============================================================================
# COMPUTE LAYER (Serverless ECS Fargate Cluster Setup)
# ==============================================================================

resource "aws_ecs_cluster" "telemetry_cluster" {
  name = "iot-fleet-cluster-${var.environment}"

  setting {
    name  = "containerInsights"
    value = "enabled" # Feeds infrastructure metrics natively to CloudWatch/DataDog
  }

  tags = {
    Environment = var.environment
  }
}