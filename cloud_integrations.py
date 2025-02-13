import subprocess
import json

def valid_azure_credentials():
    """
    Checks if there's a valid Azure CLI session by running "az account show".
    Returns True if credentials are found, False otherwise.
    """
    try:
        output = subprocess.check_output(
            ["az", "account", "show"],
            stderr=subprocess.STDOUT
        )
        data = json.loads(output.decode())
        if data.get("tenantId"):
            return True
    except Exception as e:
        print("Azure CLI authentication check failed:", e)
    return False

def valid_aws_credentials():
    """
    Checks if there's a valid AWS CLI session by running "aws sts get-caller-identity".
    Returns True if credentials are found, False otherwise.
    """
    try:
        output = subprocess.check_output(
            ["aws", "sts", "get-caller-identity"],
            stderr=subprocess.STDOUT
        )
        data = json.loads(output.decode())
        if data.get("Account"):
            return True
    except Exception as e:
        print("AWS CLI authentication check failed:", e)
    return False

def valid_gcp_credentials():
    """
    Checks if there's a valid GCP CLI session by running "gcloud auth list".
    Returns True if at least one active account exists, False otherwise.
    """
    try:
        output = subprocess.check_output(
            ["gcloud", "auth", "list", "--filter=status:ACTIVE", "--format=json"],
            stderr=subprocess.STDOUT
        )
        data = json.loads(output.decode())
        if data and len(data) > 0:
            return True
    except Exception as e:
        print("GCP CLI authentication check failed:", e)
    return False

def load_aws_integration():
    # Initialize and import your AWS cost optimization integration here.
    print("AWS integration loaded (via CLI session)")
    return "aws_integration"

def load_azure_integration():
    # Initialize and import your Azure cost optimization integration here.
    print("Azure integration loaded (via CLI session)")
    return "azure_integration"

def load_gcp_integration():
    # Initialize and import your GCP cost optimization integration here.
    print("GCP integration loaded (via CLI session)")
    return "gcp_integration"

def load_cloud_integrations():
    """
    Loads cloud integrations dynamically using CLI-authenticated sessions.
    Only integrations with an active CLI session will be loaded.
    """
    integrations = {}
    
    if valid_aws_credentials():
        integrations["aws"] = load_aws_integration()
    else:
        print("AWS CLI session not detected; skipping AWS integration.")
    
    if valid_azure_credentials():
        integrations["azure"] = load_azure_integration()
    else:
        print("Azure CLI session not detected; skipping Azure integration.")
    
    if valid_gcp_credentials():
        integrations["gcp"] = load_gcp_integration()
    else:
        print("GCP CLI session not detected; skipping GCP integration.")
    
    print("Active cloud integrations based on CLI sessions:", list(integrations.keys()))
    return integrations

if __name__ == "__main__":
    loaded_integrations = load_cloud_integrations()
    print("Loaded integrations:", loaded_integrations)
