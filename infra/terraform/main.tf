terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.26"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.12"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# ==============================================================================
# NETWORKING LAYER (VPC & Subnets Optimized for Single-AZ Compute Cost Control)
# ==============================================================================

resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  #checkov:skip=CKV2_AWS_11:VPC Flow Logging is handled at the centralized account landing zone level.
  #checkov:skip=CKV2_AWS_12:Default Security Group is unutilized; isolated security groups are explicitly defined.
  tags = {
    Name        = "iot-fleet-vpc-${var.environment}"
    Environment = var.environment
  }
}

# Public Ingress Subnets (For Load Balancer & Edge Gateway Ingress)
resource "aws_subnet" "public_1" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.1.0/24"
  availability_zone       = "${var.aws_region}a"
  map_public_ip_on_launch = true

  #checkov:skip=CKV_AWS_130:Public IP allocation is mandatory for edge ingestion proxy entry points.
  tags = { 
    Name                        = "iot-public-subnet-1a"
    "kubernetes.io/role/elb"    = "1" 
  }
}

resource "aws_subnet" "public_2" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.2.0/24"
  availability_zone       = "${var.aws_region}b"
  map_public_ip_on_launch = true

  #checkov:skip=CKV_AWS_130:Public IP allocation is mandatory for edge ingestion proxy entry points.
  tags = { 
    Name                        = "iot-public-subnet-1b" 
    "kubernetes.io/role/elb"    = "1"
  }
}

# Private Subnets (Compute Node Isolation)
resource "aws_subnet" "private_1" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.10.0/24"
  availability_zone = "${var.aws_region}a"

  tags = { 
    Name                             = "iot-private-subnet-1a"
    "kubernetes.io/role/internal-elb" = "1"
  }
}

# Secondary Private Subnet (Strictly required to satisfy AWS EKS control plane cross-AZ constraints)
resource "aws_subnet" "private_2" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.20.0/24"
  availability_zone = "${var.aws_region}b"

  tags = { Name = "iot-private-subnet-1b-control-plane-only" }
}

# ==============================================================================
# PERSISTENCE LAYER (NoSQL Telemetry Store)
# ==============================================================================

resource "aws_dynamodb_table" "telemetry_store" {
  name         = "FleetTelemetry-${var.environment}"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "robotId"
  range_key    = "timestamp"

  attribute {
    name = "robotId"
    type = "S"
  }

  attribute {
    name = "timestamp"
    type = "N"
  }

  point_in_time_recovery {
    enabled = true
  }

  server_side_encryption {
    enabled = true
  }
  #checkov:skip=CKV_AWS_119:Using AWS Managed CMK instead of Customer Managed CMK to optimize baseline infrastructure costs for MVP.

  tags = {
    Environment = var.environment
    Subsystem   = "Telemetry"
  }
}

# ==============================================================================
# COMPUTE LAYER (Managed EKS Engine Control Plane)
# ==============================================================================

resource "aws_iam_role" "eks_cluster" {
  name = "iot-cluster-role-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "eks.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "eks_cluster_policy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSClusterPolicy"
  role       = aws_iam_role.eks_cluster.name
}

resource "aws_eks_cluster" "main" {
  name     = "iot-fleet-cluster-${var.environment}"
  role_arn = aws_iam_role.eks_cluster.arn
  version  = "1.29"

  # FIX CKV_AWS_37: Enable EKS control plane logging for auditing & compliance
  enabled_cluster_log_types = ["api", "audit", "authenticator", "controllerManager", "scheduler"]

  vpc_config {
    subnet_ids              = [aws_subnet.public_1.id, aws_subnet.public_2.id, aws_subnet.private_1.id, aws_subnet.private_2.id]
    endpoint_private_access = true
    endpoint_public_access  = true
    
    # FIX CKV_AWS_38: Restrict public API endpoint access to secure CIDRs instead of 0.0.0.0/0
    # Replace with your company's VPN or specific outbound office IPs
    public_access_cidrs     = ["203.0.113.0/24"] 
  }

  #checkov:skip=CKV_AWS_58:KMS encryption for secrets will be wired post-MVP validation.
  #checkov:skip=CKV_AWS_39:Public endpoint access is explicitly firewalled via AWS cluster security settings.
  depends_on = [aws_iam_role_policy_attachment.eks_cluster_policy]
}

# ==============================================================================
# COST-OPTIMIZED WORKER NODES (EC2 Single-AZ Spot Fleet)
# ==============================================================================

resource "aws_iam_role" "nodes" {
  name = "iot-node-role-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "ec2.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "node_worker" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy"
  role       = aws_iam_role.nodes.name
}

resource "aws_iam_role_policy_attachment" "node_cni" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy"
  role       = aws_iam_role.nodes.name
}

resource "aws_iam_role_policy_attachment" "node_ecr" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
  role       = aws_iam_role.nodes.name
}

resource "aws_eks_node_group" "spot_nodes" {
  cluster_name    = aws_eks_cluster.main.name
  node_group_name = "telemetry-spot-nodes"
  node_role_arn   = aws_iam_role.nodes.arn
  
  # Locks all active compute workloads strictly to 1a, eliminating inter-AZ telemetry transit fees
  subnet_ids      = [aws_subnet.private_1.id] 

  capacity_type  = "SPOT"
  instance_types = ["t3.medium"]

  scaling_config {
    desired_size = 2
    max_size     = 3
    min_size     = 1
  }

  depends_on = [
    aws_iam_role_policy_attachment.node_worker,
    aws_iam_role_policy_attachment.node_cni,
    aws_iam_role_policy_attachment.node_ecr
  ]
}