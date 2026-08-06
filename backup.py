from datetime import datetime
from azure.identity import DefaultAzureCredential
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.compute.models import Snapshot, CreationData

credential = DefaultAzureCredential()

SUBSCRIPTION_ID = "f2f06d27-7191-42c1-9a96-6f221f8d46e1"
RESOURCE_GROUP = "rg-disaster-recovery"
LOCATION = "eastus"
DISK_NAME = "test-vm-disk"

compute_client = ComputeManagementClient(credential, SUBSCRIPTION_ID)
disk = compute_client.disks.get(RESOURCE_GROUP, DISK_NAME)

# creating a snapshot
timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
snapshot_name = f"snapshot-{DISK_NAME}-{timestamp}"
print(f"Creating snapshot '{snapshot_name}' for disk '{DISK_NAME}'...")

snapshot_parameters = Snapshot(
    location=LOCATION,
    creation_data=CreationData(
        create_option="Copy",
        source_resource_id=disk.id
    ),
    tags={'CreatedBy': 'PythonScript'}
)

poller = compute_client.snapshots.begin_create_or_update(
    RESOURCE_GROUP,
    snapshot_name,
    snapshot_parameters
)

# Optional just outputs the results in the cli 
result = poller.result()

print(f"Done! Snapshot ID: {result.id}")