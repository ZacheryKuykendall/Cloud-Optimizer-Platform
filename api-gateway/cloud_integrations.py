import subprocess
import json
import os
import logging
from typing import Dict, List, Optional, Any, Union
import random
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("cloud_integrations")

# Check if we're in simulation mode
SIMULATION_MODE = os.getenv("CLOUD_OPTIMIZER_SIMULATION", "false").lower() == "true"

class CloudProviderBase:
    """Base class for cloud provider integrations."""
    
    def __init__(self, provider_name: str):
        self.provider_name = provider_name
        self.authenticated = False
        self.simulation_mode = SIMULATION_MODE
        logger.info(f"Initializing {provider_name} integration")
    
    def authenticate(self) -> bool:
        """Authenticate with the cloud provider. To be implemented by subclasses."""
        raise NotImplementedError("Subclasses must implement this method")
    
    def get_resources(self, resource_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get resources of the specified type. To be implemented by subclasses."""
        raise NotImplementedError("Subclasses must implement this method")
    
    def get_cost_data(self, 
                     start_date: Optional[str] = None, 
                     end_date: Optional[str] = None, 
                     granularity: str = "daily") -> List[Dict[str, Any]]:
        """Get cost data for the specified period. To be implemented by subclasses."""
        raise NotImplementedError("Subclasses must implement this method")
    
    def _load_mock_data(self, provider: str) -> Dict[str, Any]:
        """Load mock data from JSON file."""
        try:
            mock_file_path = f"mock_data/{provider.lower()}_data.json"
            logger.info(f"Attempting to load mock data from {mock_file_path}")
            
            # Check if the file exists
            if os.path.exists(mock_file_path):
                logger.info(f"Mock data file found at {mock_file_path}")
                with open(mock_file_path, 'r') as file:
                    logger.info(f"Loading mock data from {mock_file_path}")
                    data = json.load(file)
                    logger.info(f"Successfully loaded {len(data)} top-level keys from mock data file: {list(data.keys())}")
                    if "resources" in data:
                        logger.info(f"Resources section contains {len(data['resources'])} resource types")
                        for resource_type, resources in data["resources"].items():
                            logger.info(f"  - {resource_type}: {len(resources)} resources")
                    return data
            else:
                logger.warning(f"Mock data file {mock_file_path} not found, absolute path: {os.path.abspath(mock_file_path)}")
                # Try to list available files in the directory
                dir_path = os.path.dirname(mock_file_path)
                if os.path.exists(dir_path):
                    logger.info(f"Directory {dir_path} exists, contents: {os.listdir(dir_path)}")
                else:
                    logger.warning(f"Directory {dir_path} does not exist")
                return {}
        except Exception as e:
            logger.error(f"Failed to load mock data: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return {}
    
    def simulate_resources(self, resource_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Generate simulated resources or load from mock data files."""
        logger.info(f"Using SIMULATION mode for {self.provider_name} resources")
        provider = self.provider_name.lower()
        
        # Try to load from mock data file first
        mock_data = self._load_mock_data(provider)
        if mock_data and "resources" in mock_data:
            logger.info(f"Using mock data file for {provider} resources")
            
            # Filter by resource type if specified
            if resource_type and resource_type in mock_data["resources"]:
                return mock_data["resources"][resource_type]
            else:
                # Flatten all resource types into a single list
                resources = []
                for resource_list in mock_data["resources"].values():
                    resources.extend(resource_list)
                return resources
        
        # Fall back to generated data if mock data not available
        logger.info(f"No mock data found for {provider} resources, generating simulated data")
        if provider == "aws":
            return self._simulate_aws_resources(resource_type)
        elif provider == "azure":
            return self._simulate_azure_resources(resource_type)
        elif provider == "gcp":
            return self._simulate_gcp_resources(resource_type)
        return []
    
    def simulate_costs(self, 
                      start_date: Optional[str] = None, 
                      end_date: Optional[str] = None, 
                      granularity: str = "daily") -> List[Dict[str, Any]]:
        """Generate simulated cost data or load from mock data files."""
        logger.info(f"Using SIMULATION mode for {self.provider_name} costs")
        provider = self.provider_name.lower()
        
        # Try to load from mock data file first
        mock_data = self._load_mock_data(provider)
        if mock_data and "costs" in mock_data:
            logger.info(f"Using mock data file for {provider} costs")
            
            # Filter by granularity
            if granularity == "daily" and "daily" in mock_data["costs"]:
                costs = mock_data["costs"]["daily"]
            else:
                costs = mock_data["costs"]["monthly"]
            
            # Filter by date range if specified
            if start_date or end_date:
                filtered_costs = []
                for cost in costs:
                    cost_date = cost.get("date", cost.get("start_date"))
                    if start_date and cost_date < start_date:
                        continue
                    if end_date and cost_date > end_date:
                        continue
                    filtered_costs.append(cost)
                return filtered_costs
            else:
                return costs
        
        # Fall back to generated data if mock data not available
        logger.info(f"No mock data found for {provider} costs, generating simulated data")
        if provider == "aws":
            return self._simulate_aws_costs(start_date, end_date, granularity)
        elif provider == "azure":
            return self._simulate_azure_costs(start_date, end_date, granularity)
        elif provider == "gcp":
            return self._simulate_gcp_costs(start_date, end_date, granularity)
        return []
    
    def _simulate_aws_resources(self, resource_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Simulate AWS resources."""
        resources = []
        
        if resource_type == "ec2" or resource_type is None:
            # Simulate EC2 instances
            instance_types = ["t2.micro", "t2.small", "t3.medium", "m5.large", "c5.xlarge"]
            states = ["running", "stopped", "terminated"]
            regions = ["us-east-1", "us-west-2", "eu-west-1", "ap-southeast-1"]
            
            for i in range(5):
                resources.append({
                    "provider": "aws",
                    "type": "ec2",
                    "id": f"i-{random.randint(10000000, 99999999)}",
                    "name": f"simulated-ec2-{i+1}",
                    "size": random.choice(instance_types),
                    "state": random.choice(states),
                    "region": random.choice(regions),
                    "simulated": True
                })
        
        if resource_type == "s3" or resource_type is None:
            # Simulate S3 buckets
            regions = ["us-east-1", "us-west-2", "eu-west-1", "ap-southeast-1"]
            
            for i in range(3):
                bucket_name = f"simulated-bucket-{i+1}-{random.randint(1000, 9999)}"
                resources.append({
                    "provider": "aws",
                    "type": "s3",
                    "id": bucket_name,
                    "name": bucket_name,
                    "created": (datetime.now() - timedelta(days=random.randint(10, 500))).isoformat(),
                    "region": random.choice(regions),
                    "simulated": True
                })
        
        return resources
    
    def _simulate_azure_resources(self, resource_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Simulate Azure resources."""
        resources = []
        
        if resource_type == "vm" or resource_type is None:
            # Simulate Azure VMs
            vm_sizes = ["Standard_B1s", "Standard_D2s_v3", "Standard_F4s_v2", "Standard_E8s_v3"]
            locations = ["eastus", "westeurope", "southeastasia", "centralus"]
            states = ["running", "deallocated", "stopped"]
            
            for i in range(4):
                resources.append({
                    "provider": "azure",
                    "type": "vm",
                    "id": f"/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/sim-rg/providers/Microsoft.Compute/virtualMachines/sim-vm-{i+1}",
                    "name": f"sim-vm-{i+1}",
                    "size": random.choice(vm_sizes),
                    "location": random.choice(locations),
                    "state": random.choice(states),
                    "simulated": True
                })
        
        if resource_type == "storage" or resource_type is None:
            # Simulate Azure Storage accounts
            locations = ["eastus", "westeurope", "southeastasia", "centralus"]
            skus = ["Standard_LRS", "Standard_GRS", "Premium_LRS"]
            kinds = ["StorageV2", "BlobStorage", "FileStorage"]
            
            for i in range(3):
                resources.append({
                    "provider": "azure",
                    "type": "storage",
                    "id": f"/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/sim-rg/providers/Microsoft.Storage/storageAccounts/simstorage{i+1}",
                    "name": f"simstorage{i+1}",
                    "location": random.choice(locations),
                    "kind": random.choice(kinds),
                    "sku": random.choice(skus),
                    "simulated": True
                })
        
        return resources
    
    def _simulate_gcp_resources(self, resource_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Simulate GCP resources."""
        resources = []
        
        if resource_type == "compute" or resource_type is None:
            # Simulate GCP Compute instances
            machine_types = ["e2-micro", "e2-small", "n1-standard-1", "n1-standard-2", "c2-standard-4"]
            zones = ["us-central1-a", "us-east1-b", "europe-west1-c", "asia-east1-a"]
            statuses = ["RUNNING", "TERMINATED", "STOPPED"]
            
            for i in range(4):
                instance_id = random.randint(1000000000000000000, 9999999999999999999)
                resources.append({
                    "provider": "gcp",
                    "type": "compute",
                    "id": str(instance_id),
                    "name": f"sim-instance-{i+1}",
                    "machine_type": random.choice(machine_types),
                    "zone": random.choice(zones),
                    "status": random.choice(statuses),
                    "simulated": True
                })
        
        if resource_type == "storage" or resource_type is None:
            # Simulate GCP Storage buckets
            locations = ["us-central1", "us-east1", "europe-west1", "asia-east1"]
            storage_classes = ["STANDARD", "NEARLINE", "COLDLINE", "ARCHIVE"]
            
            for i in range(3):
                bucket_name = f"sim-bucket-{i+1}-{random.randint(1000, 9999)}"
                resources.append({
                    "provider": "gcp",
                    "type": "storage",
                    "id": f"gs://{bucket_name}",
                    "name": bucket_name,
                    "location": random.choice(locations),
                    "storage_class": random.choice(storage_classes),
                    "simulated": True
                })
        
        return resources
    
    def _simulate_aws_costs(self, start_date: Optional[str] = None, end_date: Optional[str] = None, granularity: str = "daily") -> List[Dict[str, Any]]:
        """Simulate AWS cost data."""
        services = ["Amazon Elastic Compute Cloud", "Amazon Simple Storage Service", "Amazon RDS Service", "AWS Lambda", "Amazon DynamoDB"]
        
        # Generate dates for the period
        if not start_date:
            start = datetime.now() - timedelta(days=30)
        else:
            start = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        
        if not end_date:
            end = datetime.now()
        else:
            end = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        
        days = (end - start).days
        
        costs = []
        for day in range(days):
            current_date = start + timedelta(days=day)
            date_str = current_date.strftime("%Y-%m-%d")
            
            for service in services:
                # Generate a random but somewhat realistic cost amount
                base_amount = random.uniform(5.0, 100.0)
                if service == "Amazon Elastic Compute Cloud":
                    base_amount *= 2.5  # EC2 is usually more expensive
                elif service == "Amazon Simple Storage Service":
                    base_amount *= 0.8  # S3 is usually cheaper
                
                # Add some random variation day to day
                amount = base_amount * random.uniform(0.8, 1.2)
                
                costs.append({
                    "provider": "aws",
                    "service": service,
                    "start_date": date_str,
                    "end_date": (current_date + timedelta(days=1)).strftime("%Y-%m-%d"),
                    "amount": round(amount, 2),
                    "currency": "USD",
                    "simulated": True
                })
        
        return costs
    
    def _simulate_azure_costs(self, start_date: Optional[str] = None, end_date: Optional[str] = None, granularity: str = "daily") -> List[Dict[str, Any]]:
        """Simulate Azure cost data."""
        services = ["Virtual Machines", "Storage", "Azure SQL Database", "App Service", "Azure Functions"]
        
        # Generate dates for the period
        if not start_date:
            start = datetime.now() - timedelta(days=30)
        else:
            start = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        
        if not end_date:
            end = datetime.now()
        else:
            end = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        
        days = (end - start).days
        
        costs = []
        for day in range(days):
            current_date = start + timedelta(days=day)
            date_str = current_date.strftime("%Y-%m-%d")
            
            for service in services:
                # Generate a random but somewhat realistic cost amount
                base_amount = random.uniform(5.0, 90.0)
                if service == "Virtual Machines":
                    base_amount *= 2.2  # VMs are usually more expensive
                elif service == "Azure Functions":
                    base_amount *= 0.5  # Functions are usually cheaper
                
                # Add some random variation day to day
                amount = base_amount * random.uniform(0.8, 1.2)
                
                costs.append({
                    "provider": "azure",
                    "service": service,
                    "date": date_str,
                    "resource_id": f"/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/sim-rg/providers/Microsoft.{service.replace(' ', '')}",
                    "amount": round(amount, 2),
                    "currency": "USD",
                    "simulated": True
                })
        
        return costs
    
    def _simulate_gcp_costs(self, start_date: Optional[str] = None, end_date: Optional[str] = None, granularity: str = "daily") -> List[Dict[str, Any]]:
        """Simulate GCP cost data."""
        services = ["Compute Engine", "Cloud Storage", "Cloud SQL", "Cloud Functions", "BigQuery"]
        
        # Generate dates for the period
        if not start_date:
            start = datetime.now() - timedelta(days=30)
        else:
            start = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        
        if not end_date:
            end = datetime.now()
        else:
            end = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        
        days = (end - start).days
        
        costs = []
        for day in range(days):
            current_date = start + timedelta(days=day)
            date_str = current_date.strftime("%Y-%m-%d")
            
            # Just return one entry for GCP as a placeholder
            costs.append({
                "provider": "gcp",
                "service": "Compute Engine",
                "project_id": "simulated-project",
                "date": date_str,
                "amount": round(random.uniform(50.0, 200.0), 2),
                "currency": "USD",
                "simulated": True,
                "note": "This is simulated data"
            })
        
        return costs

class AWSIntegration(CloudProviderBase):
    """AWS cloud provider integration."""
    
    def __init__(self):
        super().__init__("AWS")
        self.region = os.getenv("AWS_REGION", "us-east-1")
        self.access_key = os.getenv("AWS_ACCESS_KEY_ID")
        self.secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        self.authenticated = self.authenticate()
    
    def authenticate(self) -> bool:
        """Check if AWS authentication is valid using CLI or environment variables."""
        # If in simulation mode, auth is always successful
        if self.simulation_mode:
            logger.info("AWS authentication successful (SIMULATION MODE)")
            return True
            
        # First try using environment variables
        if self.access_key and self.secret_key:
            logger.info("AWS credentials found in environment variables")
            return True
            
        # Fall back to CLI authentication
        try:
            logger.info("Checking AWS CLI authentication...")
            output = subprocess.check_output(
                ["aws", "sts", "get-caller-identity"],
                stderr=subprocess.STDOUT
            )
            data = json.loads(output.decode())
            if data.get("Account"):
                logger.info(f"AWS CLI authentication successful. Account ID: {data.get('Account')}")
                return True
        except Exception as e:
            logger.error(f"AWS CLI authentication failed: {e}")
            
        logger.warning("No valid AWS authentication method found")
        return False
    
    def get_resources(self, resource_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get AWS resources of specified type."""
        if not self.authenticated:
            logger.error("AWS not authenticated. Cannot retrieve resources.")
            return []
            
        # If in simulation mode, return simulated resources
        if self.simulation_mode:
            return self.simulate_resources(resource_type)
        
        resources = []
        try:
            if resource_type == "ec2" or resource_type is None:
                # Get EC2 instances
                output = subprocess.check_output(
                    ["aws", "ec2", "describe-instances", "--region", self.region, "--output", "json"],
                    stderr=subprocess.STDOUT
                )
                data = json.loads(output.decode())
                
                for reservation in data.get("Reservations", []):
                    for instance in reservation.get("Instances", []):
                        resources.append({
                            "provider": "aws",
                            "type": "ec2",
                            "id": instance.get("InstanceId"),
                            "name": next((tag["Value"] for tag in instance.get("Tags", []) if tag["Key"] == "Name"), ""),
                            "size": instance.get("InstanceType"),
                            "state": instance.get("State", {}).get("Name"),
                            "region": self.region,
                            "raw": instance
                        })
            
            if resource_type == "s3" or resource_type is None:
                # Get S3 buckets
                output = subprocess.check_output(
                    ["aws", "s3api", "list-buckets", "--output", "json"],
                    stderr=subprocess.STDOUT
                )
                data = json.loads(output.decode())
                
                for bucket in data.get("Buckets", []):
                    resources.append({
                        "provider": "aws",
                        "type": "s3",
                        "id": bucket.get("Name"),
                        "name": bucket.get("Name"),
                        "created": bucket.get("CreationDate"),
                        "region": self.region,
                        "raw": bucket
                    })
            
            logger.info(f"Retrieved {len(resources)} AWS resources of type {resource_type or 'all'}")
        except Exception as e:
            logger.error(f"Failed to retrieve AWS resources: {e}")
        
        return resources
    
    def get_cost_data(self, 
                     start_date: Optional[str] = None, 
                     end_date: Optional[str] = None, 
                     granularity: str = "daily") -> List[Dict[str, Any]]:
        """Get AWS cost data using Cost Explorer API."""
        if not self.authenticated:
            logger.error("AWS not authenticated. Cannot retrieve cost data.")
            return []
            
        # If in simulation mode, return simulated cost data
        if self.simulation_mode:
            return self.simulate_costs(start_date, end_date, granularity)
        
        cost_data = []
        try:
            cmd = [
                "aws", "ce", "get-cost-and-usage",
                "--time-period", f"Start={start_date or 'now-30d'},End={end_date or 'now'}",
                "--granularity", granularity.upper(),
                "--metrics", "BlendedCost",
                "--group-by", "Type=DIMENSION,Key=SERVICE",
                "--output", "json"
            ]
            
            output = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
            data = json.loads(output.decode())
            
            for result in data.get("ResultsByTime", []):
                time_period = result.get("TimePeriod", {})
                for group in result.get("Groups", []):
                    service = group.get("Keys", ["Unknown"])[0]
                    amount = group.get("Metrics", {}).get("BlendedCost", {}).get("Amount", "0")
                    unit = group.get("Metrics", {}).get("BlendedCost", {}).get("Unit", "USD")
                    
                    cost_data.append({
                        "provider": "aws",
                        "service": service,
                        "start_date": time_period.get("Start"),
                        "end_date": time_period.get("End"),
                        "amount": float(amount),
                        "currency": unit
                    })
            
            logger.info(f"Retrieved {len(cost_data)} AWS cost entries")
        except Exception as e:
            logger.error(f"Failed to retrieve AWS cost data: {e}")
        
        return cost_data

class AzureIntegration(CloudProviderBase):
    """Azure cloud provider integration."""
    
    def __init__(self):
        super().__init__("Azure")
        self.subscription_id = os.getenv("AZURE_SUBSCRIPTION_ID")
        self.client_id = os.getenv("AZURE_CLIENT_ID")
        self.client_secret = os.getenv("AZURE_CLIENT_SECRET")
        self.tenant_id = os.getenv("AZURE_TENANT_ID")
        self.authenticated = self.authenticate()
    
    def authenticate(self) -> bool:
        """Check if Azure authentication is valid using CLI or environment variables."""
        # If in simulation mode, auth is always successful
        if self.simulation_mode:
            logger.info("Azure authentication successful (SIMULATION MODE)")
            return True
            
        # Check if we have environment variables for authentication
        if self.subscription_id and self.client_id and self.client_secret and self.tenant_id:
            logger.info("Azure credentials found in environment variables")
            return True
            
        # Fall back to CLI authentication
        try:
            logger.info("Checking Azure CLI authentication...")
            output = subprocess.check_output(
                ["az", "account", "show"],
                stderr=subprocess.STDOUT
            )
            data = json.loads(output.decode())
            if data.get("id"):
                self.subscription_id = data.get("id")
                logger.info(f"Azure CLI authentication successful. Subscription ID: {self.subscription_id}")
                return True
        except Exception as e:
            logger.error(f"Azure CLI authentication failed: {e}")
            
        logger.warning("No valid Azure authentication method found")
        return False
    
    def get_resources(self, resource_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get Azure resources of specified type."""
        if not self.authenticated:
            logger.error("Azure not authenticated. Cannot retrieve resources.")
            return []
            
        # If in simulation mode, return simulated resources
        if self.simulation_mode:
            return self.simulate_resources(resource_type)
        
        resources = []
        try:
            if resource_type == "vm" or resource_type is None:
                # Get Azure VMs
                output = subprocess.check_output(
                    ["az", "vm", "list", "--output", "json"],
                    stderr=subprocess.STDOUT
                )
                data = json.loads(output.decode())
                
                for vm in data:
                    resources.append({
                        "provider": "azure",
                        "type": "vm",
                        "id": vm.get("id"),
                        "name": vm.get("name"),
                        "size": vm.get("hardwareProfile", {}).get("vmSize"),
                        "location": vm.get("location"),
                        "state": vm.get("powerState", "unknown"),
                        "raw": vm
                    })
            
            if resource_type == "storage" or resource_type is None:
                # Get Azure Storage Accounts
                output = subprocess.check_output(
                    ["az", "storage", "account", "list", "--output", "json"],
                    stderr=subprocess.STDOUT
                )
                data = json.loads(output.decode())
                
                for storage in data:
                    resources.append({
                        "provider": "azure",
                        "type": "storage",
                        "id": storage.get("id"),
                        "name": storage.get("name"),
                        "location": storage.get("location"),
                        "kind": storage.get("kind"),
                        "sku": storage.get("sku", {}).get("name"),
                        "raw": storage
                    })
            
            logger.info(f"Retrieved {len(resources)} Azure resources of type {resource_type or 'all'}")
        except Exception as e:
            logger.error(f"Failed to retrieve Azure resources: {e}")
        
        return resources
    
    def get_cost_data(self, 
                     start_date: Optional[str] = None, 
                     end_date: Optional[str] = None, 
                     granularity: str = "daily") -> List[Dict[str, Any]]:
        """Get Azure cost data using Cost Management API."""
        if not self.authenticated or not self.subscription_id:
            logger.error("Azure not authenticated or subscription ID not available. Cannot retrieve cost data.")
            return []
            
        # If in simulation mode, return simulated cost data
        if self.simulation_mode:
            return self.simulate_costs(start_date, end_date, granularity)
        
        cost_data = []
        try:
            cmd = [
                "az", "consumption", "usage", "list",
                "--subscription", self.subscription_id,
                "--start-date", start_date or "2023-01-01",
                "--end-date", end_date or "2023-12-31",
                "--output", "json"
            ]
            
            output = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
            data = json.loads(output.decode())
            
            for item in data:
                cost_data.append({
                    "provider": "azure",
                    "service": item.get("consumedService", "Unknown"),
                    "resource_id": item.get("instanceId"),
                    "date": item.get("date"),
                    "amount": float(item.get("cost", 0)),
                    "currency": item.get("billingCurrency", "USD")
                })
            
            logger.info(f"Retrieved {len(cost_data)} Azure cost entries")
        except Exception as e:
            logger.error(f"Failed to retrieve Azure cost data: {e}")
        
        return cost_data

class GCPIntegration(CloudProviderBase):
    """GCP cloud provider integration."""
    
    def __init__(self):
        super().__init__("GCP")
        self.project_id = os.getenv("GCP_PROJECT_ID")
        self.credentials_file = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        self.authenticated = self.authenticate()
    
    def authenticate(self) -> bool:
        """Check if GCP authentication is valid using CLI or environment variables."""
        # If in simulation mode, auth is always successful
        if self.simulation_mode:
            logger.info("GCP authentication successful (SIMULATION MODE)")
            # Set a default project ID for simulation mode to avoid authentication issues
            if not self.project_id:
                self.project_id = "simulated-gcp-project"
                logger.info(f"Using default project ID in simulation mode: {self.project_id}")
            return True
            
        # Check if we have environment variables for authentication
        if self.project_id and self.credentials_file:
            logger.info("GCP credentials found in environment variables")
            return True
            
        # Fall back to CLI authentication
        try:
            logger.info("Checking GCP CLI authentication...")
            output = subprocess.check_output(
                ["gcloud", "auth", "list", "--filter=status:ACTIVE", "--format=json"],
                stderr=subprocess.STDOUT
            )
            data = json.loads(output.decode())
            if data and len(data) > 0:
                # Get project ID if not set in environment
                if not self.project_id:
                    project_output = subprocess.check_output(
                        ["gcloud", "config", "get-value", "project"],
                        stderr=subprocess.STDOUT
                    )
                    self.project_id = project_output.decode().strip()
                
                logger.info(f"GCP CLI authentication successful. Project ID: {self.project_id}")
                return True
        except Exception as e:
            logger.error(f"GCP CLI authentication failed: {e}")
            
        logger.warning("No valid GCP authentication method found")
        return False
    
    def get_resources(self, resource_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get GCP resources of specified type."""
        # If in simulation mode, return simulated resources regardless of project_id
        if self.simulation_mode:
            return self.simulate_resources(resource_type)
            
        # Only check authentication and project_id for real API calls
        if not self.authenticated or not self.project_id:
            logger.error("GCP not authenticated or project ID not available. Cannot retrieve resources.")
            return []
        
        resources = []
        try:
            if resource_type == "compute" or resource_type is None:
                # Get GCP Compute instances
                output = subprocess.check_output(
                    ["gcloud", "compute", "instances", "list", "--project", self.project_id, "--format=json"],
                    stderr=subprocess.STDOUT
                )
                data = json.loads(output.decode())
                
                for instance in data:
                    resources.append({
                        "provider": "gcp",
                        "type": "compute",
                        "id": instance.get("id"),
                        "name": instance.get("name"),
                        "machine_type": instance.get("machineType", "").split("/")[-1],
                        "zone": instance.get("zone", "").split("/")[-1],
                        "status": instance.get("status"),
                        "raw": instance
                    })
            
            if resource_type == "storage" or resource_type is None:
                # Get GCP Storage buckets
                output = subprocess.check_output(
                    ["gsutil", "ls", "-p", self.project_id, "-L", "-b"],
                    stderr=subprocess.STDOUT
                )
                # Parse gsutil output (not JSON by default)
                lines = output.decode().split("\n\n")
                for block in lines:
                    if not block.strip():
                        continue
                    
                    bucket_data = {}
                    for line in block.split("\n"):
                        if ":" in line:
                            key, value = line.split(":", 1)
                            bucket_data[key.strip()] = value.strip()
                    
                    if "gs://" in block:
                        bucket_name = next((line for line in block.split("\n") if line.startswith("gs://")), "").strip()
                        resources.append({
                            "provider": "gcp",
                            "type": "storage",
                            "id": bucket_name,
                            "name": bucket_name.replace("gs://", "").rstrip("/"),
                            "location": bucket_data.get("Location constraint", "unknown"),
                            "storage_class": bucket_data.get("Storage class", "STANDARD"),
                            "raw": bucket_data
                        })
            
            logger.info(f"Retrieved {len(resources)} GCP resources of type {resource_type or 'all'}")
        except Exception as e:
            logger.error(f"Failed to retrieve GCP resources: {e}")
        
        return resources
    
    def get_cost_data(self, 
                     start_date: Optional[str] = None, 
                     end_date: Optional[str] = None, 
                     granularity: str = "daily") -> List[Dict[str, Any]]:
        """Get GCP cost data using Billing API."""
        # If in simulation mode, return simulated costs regardless of project_id
        if self.simulation_mode:
            return self.simulate_costs(start_date, end_date, granularity)
            
        # Only check authentication and project_id for real API calls
        if not self.authenticated or not self.project_id:
            logger.error("GCP not authenticated or project ID not available. Cannot retrieve cost data.")
            return []
        
        cost_data = []
        logger.warning("GCP cost data retrieval via CLI is limited. Consider using the Google Cloud Billing API directly.")
        
        try:
            # This is a simplified example, as GCP billing requires more setup
            logger.info(f"To get detailed GCP billing data, please use the Google Cloud Console Billing Export to BigQuery.")
            
            # Return some placeholder data for demonstration
            cost_data = [{
                "provider": "gcp",
                "service": "Compute Engine",
                "project_id": self.project_id,
                "date": start_date or "2023-01-01",
                "amount": 0.0,
                "currency": "USD",
                "note": "This is placeholder data. Real data requires BigQuery export setup."
            }]
        except Exception as e:
            logger.error(f"Failed to retrieve GCP cost data: {e}")
        
        return cost_data

def valid_cloud_provider_credentials(provider: str) -> bool:
    """
    Check if credentials are valid for the specified cloud provider.
    
    Args:
        provider: The cloud provider to check ('aws', 'azure', or 'gcp')
    
    Returns:
        bool: True if credentials are valid, False otherwise
    """
    provider = provider.lower()
    
    if provider == "aws":
        integration = AWSIntegration()
        return integration.authenticated
    elif provider == "azure":
        integration = AzureIntegration()
        return integration.authenticated
    elif provider == "gcp":
        integration = GCPIntegration()
        return integration.authenticated
    else:
        logger.error(f"Unsupported cloud provider: {provider}")
        return False

def load_cloud_integrations() -> Dict[str, CloudProviderBase]:
    """
    Load cloud integrations for providers with valid credentials.
    
    Returns:
        Dict[str, CloudProviderBase]: Dictionary of provider integrations
    """
    # Enable simulation mode if requested or if no cloud integrations can be authenticated
    global SIMULATION_MODE
    if os.getenv("CLOUD_OPTIMIZER_FORCE_SIMULATION", "false").lower() == "true":
        SIMULATION_MODE = True
        logger.warning("FORCING SIMULATION MODE for all cloud providers")
    
    integrations = {}
    
    # Try to load AWS integration
    aws_integration = AWSIntegration()
    if aws_integration.authenticated:
        integrations["aws"] = aws_integration
    else:
        logger.warning("AWS integration not loaded due to missing or invalid credentials")
    
    # Try to load Azure integration
    azure_integration = AzureIntegration()
    if azure_integration.authenticated:
        integrations["azure"] = azure_integration
    else:
        logger.warning("Azure integration not loaded due to missing or invalid credentials")
    
    # Try to load GCP integration
    gcp_integration = GCPIntegration()
    if gcp_integration.authenticated:
        integrations["gcp"] = gcp_integration
    else:
        logger.warning("GCP integration not loaded due to missing or invalid credentials")
    
    # If no integrations are loaded, force simulation mode and try again
    if not integrations and not SIMULATION_MODE:
        logger.warning("No cloud integrations loaded. Enabling SIMULATION MODE automatically.")
        SIMULATION_MODE = True
        return load_cloud_integrations()
    
    logger.info(f"Loaded {len(integrations)} cloud provider integrations: {', '.join(integrations.keys())}")
    
    if SIMULATION_MODE:
        logger.warning("Running in SIMULATION MODE. All data is simulated.")
    
    return integrations

if __name__ == "__main__":
    # Example usage
    loaded_integrations = load_cloud_integrations()
    
    if not loaded_integrations:
        logger.error("No cloud provider integrations could be loaded. Please check your credentials.")
        exit(1)
    
    for provider, integration in loaded_integrations.items():
        print(f"\n===== {provider.upper()} Resources =====")
        resources = integration.get_resources()
        for i, resource in enumerate(resources[:5]):  # Show first 5 resources
            print(f"{i+1}. {resource['type']}: {resource['name']} ({resource['id']})")
        
        if len(resources) > 5:
            print(f"...and {len(resources) - 5} more resources")
        
        print(f"\n===== {provider.upper()} Cost Data =====")
        costs = integration.get_cost_data()
        for i, cost in enumerate(costs[:5]):  # Show first 5 cost entries
            print(f"{i+1}. {cost.get('service', 'Unknown')}: {cost.get('amount', 0)} {cost.get('currency', 'USD')}")
        
        if len(costs) > 5:
            print(f"...and {len(costs) - 5} more cost entries")
