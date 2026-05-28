# Golden Bot Infrastructure as Code (Terraform)
# Deploys High-Availability Trading Cluster on AWS/GCP
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.0"
    }
  }
}

provider "aws" {
  region = var.region
}

variable "region" { default = "us-east-1" }
variable "instance_type" { default = "c5.2xlarge" }
variable "key_name" { default = "golden-bot-key" }

# Trading Node (Head)
resource "aws_instance" "head_node" {
  ami           = "ami-0c55b159cbfafe1f0" # Amazon Linux 2
  instance_type = var.instance_type
  key_name      = var.key_name

  vpc_security_group_ids = [aws_security_group.golden_bot_sg.id]
  user_data              = <<-EOF
      #!/bin/bash
      curl -fsSL https://get.docker.com -o get-docker.sh
      sh get-docker.sh
      usermod -aG docker ec2-user
      pip install docker-compose
  EOF

  tags = {
    Name = "golden-bot-head"
    Role = "trading-engine"
  }
}

# Security Group
resource "aws_security_group" "golden_bot_sg" {
  name        = "golden-bot-sg"
  description = "Allow inbound traffic for Golden Bot"

  ingress {
    from_port   = 8080
    to_port     = 8080
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

output "head_node_ip" {
  value = aws_instance.head_node.public_ip
}
