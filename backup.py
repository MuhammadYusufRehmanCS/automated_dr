import os
import logging
import automationassets
from datetime import datetime
from azure.identity import ManagedIdentityCredential
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.compute.models import Snapshot, CreationData

try:
    from automationassets import get_automation_variable
except ImportError:
    def get_automation_variable(name):
        return os.environ.get(name)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

def main():
    # Strip potential hidden whitespaces from variable inputs
    subscription_id = str(get_automation_variable("AZURE_SUBSCRIPTION_ID")).strip()
    resource_group = str(get_automation_variable("AZURE_RESOURCE_GROUP")).strip()
    disk_name = str(get_automation_variable("AZURE_DISK_NAME")).strip()
    location = str(get_automation_variable("AZURE_LOCATION")).strip()

    logging.info("Authenticating via System-Assigned Managed Identity...")
    credential = ManagedIdentityCredential()
    compute_client = ComputeManagementClient(credential, subscription_id)

    logging.info(f"Searching for disk '{disk_name}' inside group '{resource_group}'...")
    
    # List disks in the resource group to grab the exact source resource ID dynamically
    disks = list(compute_client.disks.list_by_resource_group(resource_group))
    target_disk = next((d for d in disks if d.name.strip().lower() == disk_name.lower()), None)

    if not target_disk:
        available_names = [d.name for d in disks]
        raise ValueError(f"Disk '{disk_name}' not found in RG '{resource_group}'. Found disks: {available_names}")

    logging.info(f"Target disk resolved: {target_disk.id}")

    timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    snapshot_name = f"snapshot-{disk_name}-{timestamp}"

    snapshot_params = Snapshot(
        location=location,
        creation_data=CreationData(
            create_option="Copy",
            source_resource_id=target_disk.id
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