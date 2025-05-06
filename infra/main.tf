provider "aws" {
  region = "us-east-1"
}

# SNS Topic for Alerts
resource "aws_sns_topic" "alerts" {
  name = "cloudwatch-alerts"
}

# EC2 Security Group
resource "aws_security_group" "allow_ssh" {
  name_prefix = "allow_ssh_"

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# EC2 Instance
resource "aws_instance" "example" {
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t2.micro"
  security_groups = [aws_security_group.allow_ssh.name]

  tags = {
    Name = "TerraformExample"
  }
}

output "instance_id" {
  value = aws_instance.example.id
}
