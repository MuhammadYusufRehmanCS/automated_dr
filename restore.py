import os
import logging
from azure.identity import DefaultAzureCredential
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.compute.models import Disk, CreationData
from azure.core.exceptions import AzureError
from dotenv import load_dotenv

# Load variables from .env file
load_dotenv()

# Configure logging to console and file
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("dr_operations.log"),
        logging.StreamHandler()
    ]
)

# Load configuration from environment
SUBSCRIPTION_ID = os.getenv("AZURE_SUBSCRIPTION_ID")
RESOURCE_GROUP = os.getenv("AZURE_RESOURCE_GROUP")
LOCATION = os.getenv("AZURE_LOCATION")
RESTORED_DISK_NAME = os.getenv("AZURE_RESTORED_DISK_NAME", "restored-vm-disk")

# Safety validation
if not SUBSCRIPTION_ID:
    raise ValueError("CRITICAL ERROR: 'AZURE_SUBSCRIPTION_ID' missing in .env file!")

def run_restore():
    try:
        logging.info("Initializing Azure Compute Client...")
        credential = DefaultAzureCredential()
        compute_client = ComputeManagementClient(credential, SUBSCRIPTION_ID)

        logging.info(f"Fetching existing snapshots in Resource Group '{RESOURCE_GROUP}'...")
        snapshots = list(compute_client.snapshots.list_by_resource_group(RESOURCE_GROUP))

        if not snapshots:
            logging.warning("No snapshots found in resource group. Restore aborted.")
            return

        latest_snapshot = snapshots[-1]
        logging.info(f"Selected latest snapshot for recovery: '{latest_snapshot.name}'")

        disk_parameters = Disk(
            location=LOCATION,
            creation_data=CreationData(
                create_option="Copy",
                source_resource_id=latest_snapshot.id
            ),
            sku={'name': 'Standard_LRS'}
        )

        logging.info(f"Initiating restoration to new Managed Disk '{RESTORED_DISK_NAME}'...")
        poller = compute_client.disks.begin_create_or_update(
            RESOURCE_GROUP,
            RESTORED_DISK_NAME,
            disk_parameters
        )

        restored_disk = poller.result()
        logging.info(f"SUCCESS: Disk restored successfully. ID: {restored_disk.id}")

    except AzureError as ae:
        logging.error(f"Azure API Error during restore: {ae.message}")
    except Exception as e:
        logging.error(f"Unexpected error during restore: {str(e)}")

if __name__ == "__main__":
    run_restore()