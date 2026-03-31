from datetime import datetime, timezone
from azure.storage.blob import BlobServiceClient

def calculate_storage_cost_before_date(conn_str, container_name, cutoff_date):
    # Pricing for Standard GPv2 + RA-GRS (approx)
    PRICE_PER_GB = 0.045   # Hot tier estimate

    blob_service_client = BlobServiceClient.from_connection_string(conn_str)
    container_client = blob_service_client.get_container_client(container_name)

    total_size_bytes = 0

    for blob in container_client.list_blobs():
        if blob.last_modified < cutoff_date:
            total_size_bytes += blob.size

    total_size_gb = total_size_bytes / (1024**3)
    estimated_cost = total_size_gb * PRICE_PER_GB

    return {
        "size_gb": round(total_size_gb, 2),
        "estimated_monthly_cost_usd": round(estimated_cost, 2)
    }


# Example usage
cutoff = datetime(2026, 1, 1, tzinfo=timezone.utc)

result = calculate_storage_cost_before_date(
    conn_str="your_connection_string",
    container_name="your-container",
    cutoff_date=cutoff
)

print(result)
