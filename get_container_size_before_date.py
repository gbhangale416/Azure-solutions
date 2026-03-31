from datetime import datetime, timezone
from azure.storage.blob import BlobServiceClient

conn_str = "your_connection_string"
container_name = "your-container"

cutoff_date = datetime(2026, 1, 1, tzinfo=timezone.utc)

PRICE_PER_GB = 0.02  # adjust

blob_service_client = BlobServiceClient.from_connection_string(conn_str)
container_client = blob_service_client.get_container_client(container_name)

total_size = 0

for blob in container_client.list_blobs():
    if blob.last_modified < cutoff_date:
        total_size += blob.size

total_size_gb = total_size / (1024**3)
estimated_cost = total_size_gb * PRICE_PER_GB

print(f"Size before 01-Jan-2026: {total_size_gb:.2f} GB")
print(f"Estimated Monthly Cost: ${estimated_cost:.2f}")
