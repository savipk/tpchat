import os
import uuid
import sys
from azure.identity import ClientSecretCredential
from azure.cosmos import CosmosClient, PartitionKey, exceptions

# === Configuration ===
TENANT_ID      = os.getenv("AZURE_TENANT_ID",      "<your-tenant-id>")
CLIENT_ID      = os.getenv("AZURE_CLIENT_ID",      "<your-client-id>")
CLIENT_SECRET  = os.getenv("AZURE_CLIENT_SECRET",  "<your-client-secret>")

COSMOS_ENDPOINT  = os.getenv("COSMOS_ENDPOINT",   "https://<your-account>.documents.azure.com:443/")
DATABASE_ID      = os.getenv("COSMOS_DATABASE",   "TestDatabase")
CONTAINER_ID     = os.getenv("COSMOS_CONTAINER",  "TestContainer")
PARTITION_KEY    = "/mypartitionkey"  # adapt as needed

# === Authenticate ===
try:
    credential = ClientSecretCredential(
        tenant_id=TENANT_ID,
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET
    )
    print("✅ Acquired AAD credential via service principal.")
except Exception as e:
    print("❌ Error acquiring credential:", e)
    sys.exit(1)

# === Create Cosmos client ===
try:
    client = CosmosClient(COSMOS_ENDPOINT, credential=credential)
    print("✅ CosmosClient created.")
except Exception as e:
    print("❌ Error creating CosmosClient:", e)
    sys.exit(1)

# === Create / get database & container ===
try:
    database = client.create_database_if_not_exists(id=DATABASE_ID)
    print(f"✅ Got or created database: {DATABASE_ID}")
except exceptions.CosmosHttpResponseError as e:
    print("❌ Database creation or retrieval failed:", e)
    sys.exit(1)

try:
    container = database.create_container_if_not_exists(
        id=CONTAINER_ID,
        partition_key=PartitionKey(path=PARTITION_KEY),
        offer_throughput=400
    )
    print(f"✅ Got or created container: {CONTAINER_ID}")
except exceptions.CosmosHttpResponseError as e:
    print("❌ Container creation or retrieval failed:", e)
    sys.exit(1)

# === Insert a test item ===
test_id = str(uuid.uuid4())
item_body = {
    "id": test_id,
    "mypartitionkey": "testPartition",
    "message": "Hello Cosmos!",
    "timestamp": str(os.times())
}

try:
    result = container.create_item(body=item_body)
    print(f"✅ Inserted item with id: {test_id}")
except exceptions.CosmosHttpResponseError as e:
    print("❌ Failed to insert item:", e)
    sys.exit(1)

# === Read back the item ===
try:
    read_item = container.read_item(item=test_id, partition_key="testPartition")
    print("✅ Read item back:", read_item)
except exceptions.CosmosHttpResponseError as e:
    print("❌ Failed to read item:", e)
    sys.exit(1)

# === Query items ===
try:
    query = "SELECT * FROM c WHERE c.mypartitionkey = @pk"
    items = list(container.query_items(
        query=query,
        parameters=[{"name":"@pk","value":"testPartition"}],
        enable_cross_partition_query=True
    ))
    print(f"✅ Query returned {len(items)} items. Sample:", items[:1])
except exceptions.CosmosHttpResponseError as e:
    print("❌ Query failed:", e)
    sys.exit(1)

print("🎉 Cosmos DB connectivity, write/read, and query succeeded.")
