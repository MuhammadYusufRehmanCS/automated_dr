import os
import logging
from datetime import datetime, timezone
from azure.identity import ManagedIdentityCredential
from azure.mgmt.compute import ComputeManagementClient

try:
    from automationassets import get_automation_variable
except ImportError:
    def get_automation_variable(name):
        return os.environ.get(name)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

RETENTION_DAYS = 30

def cleanup_snapshots():
    subscription_id = os.environ.get("AZURE_SUBSCRIPTION_ID")
    resource_group = get_automation_variable("AZURE_RESOURCE_GROUP")

    logging.info("Authenticating via Managed Identity...")
    credential = ManagedIdentityCredential()
    compute_client = ComputeManagementClient(credential, subscription_id)

    now = datetime.now(timezone.utc)
    snapshots = compute_client.snapshots.list_by_resource_group(resource_group)

    for snapshot in snapshots:
        # Check snapshot creation time against retention policy
        age_days = (now - snapshot.time_created).days
        if age_days > RETENTION_DAYS:
            logging.info(f"Deleting snapshot '{snapshot.name}' (Age: {age_days} days)...")
            poller = compute_client.snapshots.begin_delete(resource_group, snapshot.name)
            poller.result()
            logging.info(f"Deleted snapshot '{snapshot.name}'.")

if __name__ == "__main__":
    cleanup_snapshots()