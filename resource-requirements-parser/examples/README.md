# Resource Requirements Parser Examples

This directory contains example infrastructure definitions and demonstration scripts showing how to use the Resource Requirements Parser library.

## Directory Structure

```
examples/
├── parse_infrastructure.py     # Example script demonstrating parser usage
├── terraform/                  # Terraform example
│   ├── main.tf                # Main Terraform configuration
│   └── variables.tf           # Terraform variables definition
└── cloudformation/            # CloudFormation example
    └── template.yaml          # CloudFormation template
```

## Example Infrastructure

Both the Terraform and CloudFormation examples define equivalent infrastructure consisting of:

### Compute Resources
- Web server (t3.micro) in a public subnet
- Application server (t3.small) in a private subnet

### Storage Resources
- S3 bucket for data storage with versioning enabled
- EBS volume (100GB, gp3) for application data

### Network Resources
- VPC with public and private subnets
- Security groups for web, application, and database tiers
- Network ACLs and routing configuration

### Database Resources
- RDS MySQL instance with:
  - 50GB storage
  - Encryption enabled
  - Backup retention for 7 days
  - Multi-AZ deployment in production

### Common Features
- Resource tagging for environment and cost tracking
- Security group rules for proper tier isolation
- Encrypted storage for sensitive data
- Environment-specific configurations

## Using the Examples

1. Run the example script:
   ```bash
   python examples/parse_infrastructure.py
   ```

   This will:
   - List supported infrastructure definition types
   - Parse both Terraform and CloudFormation examples
   - Display detailed resource analysis
   - Show dependencies between resources
   - Report any potential issues or warnings

2. Experiment with modifications:
   - Try modifying the infrastructure definitions
   - Add new resources or change existing ones
   - See how the parser handles different configurations
   - Test error handling with invalid definitions

## Parser Features Demonstrated

1. **Resource Type Detection**
   - Automatic identification of resource types
   - Handling of cloud provider-specific resource names
   - Support for custom resource types

2. **Dependency Analysis**
   - Explicit dependencies (depends_on, DependsOn)
   - Implicit dependencies (reference expressions)
   - Dependency graph construction

3. **Resource Requirements Extraction**
   - Compute requirements (CPU, memory, instance types)
   - Storage requirements (size, IOPS, encryption)
   - Network requirements (CIDR blocks, security rules)
   - Database requirements (engine, version, storage)

4. **Tag Management**
   - Resource-specific tags
   - Global/inherited tags
   - Environment-based tagging

5. **Variable Resolution**
   - Terraform variables
   - CloudFormation parameters
   - Default values and constraints

6. **Error Handling**
   - Validation errors
   - Missing required fields
   - Invalid configurations
   - Resource conflicts

## Customizing Examples

Feel free to modify these examples to:

1. Test different resource configurations
2. Add more complex dependencies
3. Implement additional resource types
4. Test error handling and validation
5. Experiment with different tagging strategies

## Notes

- The examples use placeholder values for sensitive data
- Some resource configurations are simplified for demonstration
- Error handling and validation are emphasized
- Both IaC formats define equivalent infrastructure for comparison

## CloudFormation Template Notes

The CloudFormation template uses several intrinsic functions:

- `!Ref`: References parameters and resources
- `!Sub`: String substitution for dynamic values
- `!GetAtt`: Gets resource attributes
- `!Select`: Selects items from lists
- `!GetAZs`: Gets availability zones
- `!Equals`: Conditional evaluation

While these may show as YAML validation errors in some editors, they are valid CloudFormation syntax and will be properly handled by the parser.

## Terraform Configuration Notes

The Terraform configuration demonstrates:

- Resource block syntax
- Variable declarations and usage
- Tag merging with defaults
- Provider configuration
- Security group rules
- Resource dependencies

Both examples follow infrastructure best practices including:

- Proper resource isolation
- Security group layering
- Encrypted storage
- Environment-based configuration
- Consistent tagging
