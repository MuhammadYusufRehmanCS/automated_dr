import os
import logging
from datetime import datetime
from azure.identity import DefaultAzureCredential
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.compute.models import Snapshot, CreationData
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
DISK_NAME = os.getenv("AZURE_DISK_NAME")

# Safety validation
if not SUBSCRIPTION_ID:
    raise ValueError("CRITICAL ERROR: 'AZURE_SUBSCRIPTION_ID' missing in .env file!")

def run_backup():
    try:
        logging.info("Initializing Azure Compute Client...")
        credential = DefaultAzureCredential()
        compute_client = ComputeManagementClient(credential, SUBSCRIPTION_ID)

        logging.info(f"Fetching target disk '{DISK_NAME}' from Resource Group '{RESOURCE_GROUP}'...")
        disk = compute_client.disks.get(RESOURCE_GROUP, DISK_NAME)

        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        snapshot_name = f"snapshot-{DISK_NAME}-{timestamp}"

        snapshot_parameters = Snapshot(
            location=LOCATION,
            creation_data=CreationData(
                create_option="Copy",
                source_resource_id=disk.id
            ),
            tags={'CreatedBy': 'PythonDRScript', 'Environment': 'Production'}
        )

        logging.info(f"Triggering snapshot creation: '{snapshot_name}'...")
        poller = compute_client.snapshots.begin_create_or_update(
            RESOURCE_GROUP,
            snapshot_name,
            snapshot_parameters
        )

        result = poller.result()
        logging.info(f"SUCCESS: Snapshot created. ID: {result.id}")

    except AzureError as ae:
        logging.error(f"Azure API Error during backup: {ae.message}")
    except Exception as e:
        logging.error(f"Unexpected error during backup: {str(e)}")

if __name__ == "__main__":
    run_backup()