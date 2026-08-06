import os
import random
from azure.identity import DefaultAzureCrendential
from azure.compute import ComputeManagementClient

credential = DefaultAzureCredential()

SUBSCRIPTION_ID = "f2f06d27-7191-42c1-9a96-6f221f8d46e1"
RESOURCE_GROUP = "rg-disaster-recovery"
LOCATION = "eastus"
DISK_NAME = "test-vm-disk"

compute_client = ComputeManagementClient(credentials, SUBSCRIPTION_ID)
disk = compute_client.disks.get(RESOURCE_GROUP, DISK_NAME)

# creating a snapshot
timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
snapshot_name = f"snapshot-{DISK_NAME}-{timestamp}"
print(f"Creating snapshot '{snapshot_name}' for disk '{DISK_NAME}'...")

poller = compute.client.snapshots.begin_create_or_update(
    RESOURCE_GROUP,
    snapshot_name,
    {
        'location' : LOCATION,
        'creation_date' : {
            'create_option' : 'Copy',
            'source_resource_id' : disk.id
        },
        'tags' : {'CreatedBy' : 'PythonScript'}
    }
)

# Optional just outputs the results in the cli 
result = poller.result()

print(f"Done! Snapshot ID: {result.id}")