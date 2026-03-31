from azure.storage.blob import BlobServiceClient

conn_str = "your_connection_string"
container_name = "your-container"

# Pricing (example - adjust based on your tier & region)
PRICE_PER_GB = 0.02   # Hot tier approx (USD)

blob_service_client = BlobServiceClient.from_connection_string(conn_str)
container_client = blob_service_client.get_container_client(container_name)

total_size = 0

for blob in container_client.list_blobs():
    total_size += blob.size

# Convert to GB
total_size_gb = total_size / (1024**3)

# Estimate cost
estimated_cost = total_size_gb * PRICE_PER_GB

print(f"Total Size: {total_size_gb:.2f} GB")
print(f"Estimated Monthly Cost: ${estimated_cost:.2f}")
