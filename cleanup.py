import os
import logging
from datetime import datetime, timezone, timedelta
from azure.identity import DefaultAzureCredential
from azure.mgmt.compute import ComputeManagementClient
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
RETENTION_DAYS = int(os.getenv("AZURE_RETENTION_DAYS", "7"))

# Safety validation
if not SUBSCRIPTION_ID:
    raise ValueError("CRITICAL ERROR: 'AZURE_SUBSCRIPTION_ID' missing in .env file!")

def run_cleanup():
    try:
        logging.info("Initializing Azure Compute Client...")
        credential = DefaultAzureCredential()
        compute_client = ComputeManagementClient(credential, SUBSCRIPTION_ID)

        logging.info(f"Scanning snapshots older than {RETENTION_DAYS} days in '{RESOURCE_GROUP}'...")
        snapshots = compute_client.snapshots.list_by_resource_group(RESOURCE_GROUP)

        now = datetime.now(timezone.utc)
        deleted_count = 0

        for snapshot in snapshots:
            created_time = snapshot.time_created
            age = now - created_time

            logging.info(f"Evaluating Snapshot: '{snapshot.name}' (Age: {age.days} days, {age.seconds // 3600} hours)")

            if age > timedelta(days=RETENTION_DAYS):
                logging.info(f"Snapshot '{snapshot.name}' exceeds retention limit! Deleting...")
                poller = compute_client.snapshots.begin_delete(RESOURCE_GROUP, snapshot.name)
                poller.result()
                logging.info(f"SUCCESS: Purged snapshot '{snapshot.name}'.")
                deleted_count += 1
            else:
                logging.info(f"Snapshot '{snapshot.name}' is within retention limit. Retaining.")

        logging.info("=" * 50)
        logging.info(f"Cleanup finished. Total snapshots purged: {deleted_count}")
        logging.info("=" * 50)

    except AzureError as ae:
        logging.error(f"Azure API Error during cleanup: {ae.message}")
    except Exception as e:
        logging.error(f"Unexpected error during cleanup: {str(e)}")

if __name__ == "__main__":
    run_cleanup()