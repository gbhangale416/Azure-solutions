import csv
import datetime
import time
from azure.identity import DefaultAzureCredential
from azure.mgmt.datafactory import DataFactoryManagementClient

# ===== CONFIGURATION =====
subscription_id = "<your-subscription-id>"
resource_group = "<your-resource-group>"
factory_name = "<your-adf-name>"
ir_name = "<your-integration-runtime-name>"
output_csv = "ir_monitoring.csv"
interval_seconds = 300  # 5 minutes

# Authenticate
credential = DefaultAzureCredential()
adf_client = DataFactoryManagementClient(credential, subscription_id)

def get_ir_status():
    ir_status = adf_client.integration_runtimes.get_status(
        resource_group_name=resource_group,
        factory_name=factory_name,
        integration_runtime_name=ir_name,
    )
    return ir_status

def log_ir_status():
    ir_status = get_ir_status()
    now = datetime.datetime.utcnow().isoformat()

    row = {
        "Timestamp": now,
        "IR_Name": ir_name,
        "State": ir_status.state,
        "Nodes": len(ir_status.nodes) if ir_status.nodes else 0,
        "CPU_Utilization": ir_status.nodes[0].cpu_utilization if ir_status.nodes else None,
        "AvailableMemoryInMB": ir_status.nodes[0].available_memory_in_mb if ir_status.nodes else None,
    }

    file_exists = False
    try:
        with open(output_csv, "r"):
            file_exists = True
    except FileNotFoundError:
        pass

    with open(output_csv, "a", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=row.keys())
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)

    print(f"[{now}] Logged IR status: {row}")

if __name__ == "__main__":
    print("Starting IR monitoring... Press Ctrl+C to stop.")
    while True:
        try:
            log_ir_status()
            time.sleep(interval_seconds)  # Wait 5 minutes
        except KeyboardInterrupt:
            print("Monitoring stopped by user.")
            break
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(interval_seconds)
