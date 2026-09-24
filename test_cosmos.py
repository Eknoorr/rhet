import os
from dotenv import load_dotenv

from azure.cosmos import CosmosClient
from azure.identity import DefaultAzureCredential

load_dotenv()

endpoint = os.getenv("COSMOS_ENDPOINT")

if not endpoint:
    raise ValueError("COSMOS_ENDPOINT is missing")

print("Endpoint:", endpoint)

credential = DefaultAzureCredential()

client = CosmosClient(
    endpoint,
    credential=credential
)

database = client.get_database_client("rhet_db")
users = database.get_container_client("users")

test_user = {
    "id": "cosmos_test_user",
    "user_id": "cosmos_test_user",
    "type": "user",
    "display_name": "Cosmos Test",
    "native_language": "en",
    "target_language": "es",
    "proficiency_level": "A1"
}

print("Writing test document...")

users.upsert_item(test_user)

print("Reading test document...")

result = users.read_item(
    item="cosmos_test_user",
    partition_key="cosmos_test_user"
)

print("SUCCESS!")
print(result)