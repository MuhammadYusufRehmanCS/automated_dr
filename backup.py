import os
import logging
import automationassets
from datetime import datetime
from azure.identity import ManagedIdentityCredential
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.compute.models import Snapshot, CreationData

# Import Azure Automation assets library to read variables dynamically
try:
    from automationassets import get_automation_variable
except ImportError:
    # Fallback for local testing via os.environ
    def get_automation_variable(name):
        return os.environ.get(name)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

def main():
    # 1. Fetch Subscription ID provided automatically by Azure execution environment
    subscription_id = get_automation_variable("AZURE_SUBSCRIPTION_ID")
    
    # 2. Fetch configuration dynamically from Azure Automation Variables
    resource_group = get_automation_variable("AZURE_RESOURCE_GROUP")
    disk_name = get_automation_variable("AZURE_DISK_NAME")
    location = get_automation_variable("AZURE_LOCATION")

    if not all([subscription_id, resource_group, disk_name, location]):
        raise ValueError("Missing required environment configuration variables.")

    logging.info(f"Authenticating via System-Assigned Managed Identity...")
    credential = ManagedIdentityCredential()
    compute_client = ComputeManagementClient(credential, subscription_id)

    logging.info(f"Fetching target disk '{disk_name}' from group '{resource_group}'...")
    disk = compute_client.disks.get(resource_group, disk_name)

    timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    snapshot_name = f"snapshot-{disk_name}-{timestamp}"

    snapshot_params = Snapshot(
        location=location,
        creation_data=CreationData(
            create_option="Copy",
            source_resource_id=disk.id
        ),
        tags={"ManagedBy": "AzureAutomation", "Environment": "Production"}
    )

    logging.info(f"Creating snapshot '{snapshot_name}'...")
    poller = compute_client.snapshots.begin_create_or_update(
        resource_group,
        snapshot_name,
        snapshot_params
    )
    result = poller.result()
    logging.info(f"Successfully created snapshot: {result.id}")

if __name__ == "__main__":
    main()