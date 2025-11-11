import os
from azure.identity import ClientSecretCredential
from azure.cosmos import CosmosClient, exceptions

# Config
COSMOS_ENDPOINT = os.getenv("COSMOS_ENDPOINT", "https://<account>.documents.azure.com:443/")
DATABASE_ID     = os.getenv("COSMOS_DATABASE", "standard-reference-data")
CONTAINER_ID    = os.getenv("COSMOS_CONTAINER", "talent-profile")

TENANT_ID     = os.getenv("AZURE_TENANT_ID", "<tenant-id>")
CLIENT_ID     = os.getenv("AZURE_CLIENT_ID", "<client-id>")
CLIENT_SECRET = os.getenv("AZURE_CLIENT_SECRET", "<client-secret>")

# Auth
credential = ClientSecretCredential(tenant_id=TENANT_ID, client_id=CLIENT_ID, client_secret=CLIENT_SECRET)

# Cosmos client using AAD
client = CosmosClient(COSMOS_ENDPOINT, credential=credential)

# Database and container clients
db = client.get_database_client(DATABASE_ID)
container = db.get_container_client(CONTAINER_ID)

# Try a simple read (no partition key needed for a cross-partition query)
try:
    items = list(container.query_items(
        query="SELECT TOP 1 * FROM c",
        enable_cross_partition_query=True
    ))
    if items:
        print("Read OK. Sample document:", items[0])
    else:
        print("Read OK. Container is empty.")
except exceptions.CosmosHttpResponseError as e:
    print("Read failed:", e)
    raise
