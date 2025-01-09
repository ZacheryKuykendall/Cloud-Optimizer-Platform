# Example Terraform configuration demonstrating various resource types

provider "aws" {
  region = var.aws_region
}

# VPC and Network Resources
resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = merge(var.common_tags, {
    Name = "${var.environment}-vpc"
  })
}

resource "aws_subnet" "public" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.1.0/24"
  availability_zone = "${var.aws_region}a"

  tags = merge(var.common_tags, {
    Name = "${var.environment}-public-subnet"
    Type = "Public"
  })
}

resource "aws_subnet" "private" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.2.0/24"
  availability_zone = "${var.aws_region}b"

  tags = merge(var.common_tags, {
    Name = "${var.environment}-private-subnet"
    Type = "Private"
  })
}

# Compute Resources
resource "aws_instance" "web" {
  ami           = var.ami_id
  instance_type = "t3.micro"
  subnet_id     = aws_subnet.public.id

  root_block_device {
    volume_size = 20
    volume_type = "gp3"
    encrypted   = true
  }

  tags = merge(var.common_tags, {
    Name = "${var.environment}-web-server"
    Role = "Web"
  })

  depends_on = [aws_vpc.main, aws_subnet.public]
}

resource "aws_instance" "app" {
  ami           = var.ami_id
  instance_type = "t3.small"
  subnet_id     = aws_subnet.private.id

  root_block_device {
    volume_size = 30
    volume_type = "gp3"
    encrypted   = true
  }

  tags = merge(var.common_tags, {
    Name = "${var.environment}-app-server"
    Role = "Application"
  })

  depends_on = [aws_vpc.main, aws_subnet.private]
}

# Storage Resources
resource "aws_s3_bucket" "data" {
  bucket = "${var.environment}-data-bucket"

  tags = merge(var.common_tags, {
    Name = "${var.environment}-data-bucket"
  })
}

resource "aws_s3_bucket_versioning" "data" {
  bucket = aws_s3_bucket.data.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_ebs_volume" "app_data" {
  availability_zone = "${var.aws_region}b"
  size             = 100
  type             = "gp3"
  encrypted        = true

  tags = merge(var.common_tags, {
    Name = "${var.environment}-app-data"
  })
}

# Database Resources
resource "aws_db_instance" "main" {
  identifier        = "${var.environment}-db"
  engine           = "mysql"
  engine_version   = "8.0"
  instance_class   = "db.t3.small"
  allocated_storage = 50
  storage_type      = "gp3"
  storage_encrypted = true
  multi_az         = var.environment == "production"

  db_name  = "appdb"
  username = var.db_username
  password = var.db_password

  backup_retention_period = 7
  skip_final_snapshot    = true

  vpc_security_group_ids = [aws_security_group.db.id]
  db_subnet_group_name   = aws_db_subnet_group.main.name

  tags = merge(var.common_tags, {
    Name = "${var.environment}-database"
  })

  depends_on = [aws_vpc.main]
}

# Security Groups
resource "aws_security_group" "web" {
  name_prefix = "${var.environment}-web-sg"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(var.common_tags, {
    Name = "${var.environment}-web-sg"
  })
}

resource "aws_security_group" "db" {
  name_prefix = "${var.environment}-db-sg"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port       = 3306
    to_port         = 3306
    protocol        = "tcp"
    security_groups = [aws_security_group.app.id]
  }

  tags = merge(var.common_tags, {
    Name = "${var.environment}-db-sg"
  })
}

resource "aws_security_group" "app" {
  name_prefix = "${var.environment}-app-sg"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port       = 8080
    to_port         = 8080
    protocol        = "tcp"
    security_groups = [aws_security_group.web.id]
  }

  tags = merge(var.common_tags, {
    Name = "${var.environment}-app-sg"
  })
}

# DB Subnet Group
resource "aws_db_subnet_group" "main" {
  name       = "${var.environment}-db-subnet-group"
  subnet_ids = [aws_subnet.private.id]

  tags = merge(var.common_tags, {
    Name = "${var.environment}-db-subnet-group"
  })
}
