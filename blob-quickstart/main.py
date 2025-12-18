import os

from azure.identity import AzureCliCredential
from azure.storage.blob import BlobServiceClient

# Azure Storage Info
account_url = "https://treeexbspstorage.blob.core.windows.net"
container_name = "images"

# Authenticate using Azure CLI (requires `az login`)
credential = AzureCliCredential()

# Connect to Blob Service
blob_service_client = BlobServiceClient(account_url, credential=credential)

# List containers
print("Listing containers:")
for container in blob_service_client.list_containers():
    print(container["name"])

# List blobs inside the target container
container_client = blob_service_client.get_container_client(container_name)
print("\nListing blobs in container:", container_name)
for b in container_client.list_blobs():
    print(b.name)

# Download file
local_path = "./downloads"
os.makedirs(local_path, exist_ok=True)

blob_name = "TESH Query.png"  # exact blob name
download_file_path = os.path.join(
    local_path,
    os.path.splitext(blob_name)[0] + "_DOWNLOAD" + os.path.splitext(blob_name)[1],
)

print("\nDownloading blob to:", download_file_path)

with open(download_file_path, "wb") as f:
    f.write(container_client.download_blob(blob_name).readall())

print("Download complete.")

# BREAK LEASE (correct way)
blob_client = container_client.get_blob_client(blob_name)
print("\nBreaking lease if any...")
try:
    blob_client.break_lease(0)  # break immediately
    print("Lease broken successfully.")
except Exception as e:
    print("No active lease or failed to break:", e)

# Delete blob
print("\nDeleting blob:", blob_name)
try:
    container_client.delete_blob(blob_name)
    print("Blob deleted successfully.")
except Exception as e:
    print("Blob not found or can't be deleted:", e)

# Upload blob back
print("\nUploading blob:", blob_name)

upload_path = "./downloads/TESH Query_DOWNLOAD.png"

try:
    with open(upload_path, "rb") as data:
        container_client.upload_blob(
            name="TESH Query_UPLOAD.png", data=data, overwrite=True
        )
    print("Blob uploaded successfully.")
except Exception as e:
    print("Upload failed:", e)
