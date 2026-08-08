import os
import sys
import logging
from azure.identity import ManagedIdentityCredential
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.compute.models import Disk, CreationData

try:
    from automationassets import get_automation_variable
except ImportError:
    def get_automation_variable(name):
        return os.environ.get(name)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

def restore_disk(snapshot_name, new_disk_name):
    subscription_id = os.environ.get("AZURE_SUBSCRIPTION_ID")
    resource_group = get_automation_variable("AZURE_RESOURCE_GROUP")
    location = get_automation_variable("AZURE_LOCATION")

    credential = ManagedIdentityCredential()
    compute_client = ComputeManagementClient(credential, subscription_id)

    logging.info(f"Fetching snapshot '{snapshot_name}'...")
    snapshot = compute_client.snapshots.get(resource_group, snapshot_name)

    disk_params = Disk(
        location=location,
        creation_data=CreationData(
            create_option="Copy",
            source_resource_id=snapshot.id
        ),
        tags={"ManagedBy": "AzureAutomation", "Type": "RestoredDisk"}
    )

    logging.info(f"Restoring snapshot to new managed disk '{new_disk_name}'...")
    poller = compute_client.disks.begin_create_or_update(
        resource_group,
        new_disk_name,
        disk_params
    )
    restored_disk = poller.result()
    logging.info(f"SUCCESS: Disk restored. ID: {restored_disk.id}")

if __name__ == "__main__":
    # In Azure Runbooks, arguments passed via Portal arrive in sys.argv
    if len(sys.argv) > 2:
        restore_disk(sys.argv[1], sys.argv[2])
    else:
        logging.error("Missing arguments: snapshot_name and new_disk_name required.")