from azure.identity import DefaultAzureCredential
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.compute.models import Disk, CreationData

credential = DefaultAzureCredential()

SUBSCRIPTION_ID = "f2f06d27-7191-42c1-9a96-6f221f8d46e1"
RESOURCE_GROUP = "rg-disaster-recovery"
LOCATION = "eastus"
RESTORED_DISK_NAME = "restored-vm-disk"

compute_client = ComputeManagementClient(credential, SUBSCRIPTION_ID)

# 1. Fetch existing snapshots from Azure
print("Fetching existing snapshots...")
snapshots = list(compute_client.snapshots.list_by_resource_group(RESOURCE_GROUP))

if not snapshots:
    print("No snapshots found!")
    exit()

# Pick the newest snapshot from the list
latest_snapshot = snapshots[-1]
print(f"Found latest snapshot: {latest_snapshot.name}")

# 2. Build the Disk object using CreationData class
disk_parameters = Disk(
    location=LOCATION,
    creation_data=CreationData(
        create_option="Copy",
        source_resource_id=latest_snapshot.id
    ),
    sku={'name': 'Standard_LRS'}
)

# 3. Create a brand-new Managed Disk from that snapshot
print(f"Restoring snapshot to new disk '{RESTORED_DISK_NAME}'...")
poller = compute_client.disks.begin_create_or_update(
    RESOURCE_GROUP,
    RESTORED_DISK_NAME,
    disk_parameters
)

restored_disk = poller.result()

print("=" * 50)
print(f"SUCCESS! Brand new disk created from snapshot!")
print(f"Restored Disk Name: {restored_disk.name}")
print(f"Restored Disk ID:   {restored_disk.id}")
print("=" * 50)