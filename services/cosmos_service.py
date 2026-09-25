import os
from datetime import datetime, timezone

from azure.cosmos import CosmosClient
from azure.cosmos.exceptions import CosmosResourceNotFoundError
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv


load_dotenv()


class CosmosService:

    def __init__(self):
        endpoint = os.getenv("COSMOS_ENDPOINT")
        database_name = os.getenv(
            "COSMOS_DATABASE",
            "rhet_db"
        )

        if not endpoint:
            raise ValueError(
                "COSMOS_ENDPOINT is missing from .env"
            )

        credential = DefaultAzureCredential()

        self.client = CosmosClient(
            endpoint,
            credential=credential
        )

        self.database = self.client.get_database_client(
            database_name
        )

        self.users = self.database.get_container_client(
            os.getenv(
                "COSMOS_USERS_CONTAINER",
                "users"
            )
        )

        self.conversations = self.database.get_container_client(
            os.getenv(
                "COSMOS_CONVERSATIONS_CONTAINER",
                "conversations"
            )
        )

        self.progress = self.database.get_container_client(
            os.getenv(
                "COSMOS_PROGRESS_CONTAINER",
                "progress"
            )
        )

    # ========================================================
    # USERS
    # ========================================================

    def save_user(self, user):
        return self.users.upsert_item(user)

    def get_user(self, user_id):
        try:
            return self.users.read_item(
                item=user_id,
                partition_key=user_id
            )
        except CosmosResourceNotFoundError:
            return None

    def get_user_by_email(self, email):
            query = """
            SELECT TOP 1 *
            FROM c
            WHERE LOWER(c.email) = @email
            """
    
            results = list(
                self.users.query_items(
                    query=query,
                    parameters=[
                        {
                            "name": "@email",
                            "value": email.strip().lower()
                        }
                    ],
                    enable_cross_partition_query=True
                )
            )
    
            return results[0] if results else None

    # ========================================================
    # CONVERSATIONS
    # ========================================================

    def save_conversation(self, conversation):
        conversation["updated_at"] = (
            datetime.now(timezone.utc).isoformat()
        )

        if "created_at" not in conversation:
            conversation["created_at"] = (
                datetime.now(timezone.utc).isoformat()
            )

        return self.conversations.upsert_item(
            conversation
        )

    def get_conversation(
        self,
        conversation_id,
        user_id
    ):
        try:
            return self.conversations.read_item(
                item=conversation_id,
                partition_key=user_id
            )
        except CosmosResourceNotFoundError:
            return None

    def get_user_conversations(self, user_id):
        query = """
        SELECT *
        FROM c
        WHERE c.user_id = @user_id
        ORDER BY c.updated_at DESC
        """

        return list(
            self.conversations.query_items(
                query=query,
                parameters=[
                    {
                        "name": "@user_id",
                        "value": user_id
                    }
                ],
                enable_cross_partition_query=True
            )
        )
    
    # ========================================================
    # PROGRESS
    # ========================================================

    def save_progress(self, progress):
        progress["updated_at"] = (
            datetime.now(timezone.utc).isoformat()
        )

        return self.progress.upsert_item(
            progress
        )

    def get_progress(self, user_id):
        try:
            return self.progress.read_item(
                item=f"progress_{user_id}",
                partition_key=user_id
            )
        except CosmosResourceNotFoundError:
            return None