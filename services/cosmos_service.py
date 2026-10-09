import os
from datetime import datetime, timezone

from azure.cosmos import CosmosClient
from azure.cosmos.exceptions import CosmosResourceNotFoundError
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv

from services.logger import rhet_log

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
        try:
            rhet_log.debug("CosmosService.save_user: user_id=%s", user.get("user_id") or user.get("id"))
            return self.users.upsert_item(user)
        except Exception as exc:
            rhet_log.error("CosmosService.save_user failed: %s", exc, exc_info=True)
            raise

    def get_user(self, user_id):
        try:
            return self.users.read_item(item=user_id, partition_key=user_id)
        except CosmosResourceNotFoundError:
            rhet_log.debug("CosmosService.get_user: not found user_id=%s", user_id)
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
                parameters=[{"name": "@email", "value": email.strip().lower()}],
                enable_cross_partition_query=True,
            )
        )

        if not results:
            rhet_log.debug("CosmosService.get_user_by_email: not found email=%s", email)
        return results[0] if results else None

    # ========================================================
    # CONVERSATIONS
    # ========================================================

    def save_conversation(self, conversation):
        conversation["updated_at"] = datetime.now(timezone.utc).isoformat()
        if "created_at" not in conversation:
            conversation["created_at"] = datetime.now(timezone.utc).isoformat()
        try:
            rhet_log.debug(
                "CosmosService.save_conversation: id=%s user_id=%s",
                conversation.get("id"), conversation.get("user_id"),
            )
            return self.conversations.upsert_item(conversation)
        except Exception as exc:
            rhet_log.error("CosmosService.save_conversation failed: %s", exc, exc_info=True)
            raise

    def get_conversation(self, conversation_id, user_id):
        try:
            return self.conversations.read_item(
                item=conversation_id,
                partition_key=user_id,
            )
        except CosmosResourceNotFoundError:
            rhet_log.debug(
                "CosmosService.get_conversation: not found id=%s user_id=%s",
                conversation_id, user_id
            )
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
        progress["updated_at"] = datetime.now(timezone.utc).isoformat()
        try:
            rhet_log.debug("CosmosService.save_progress: user_id=%s", progress.get("user_id"))
            return self.progress.upsert_item(progress)
        except Exception as exc:
            rhet_log.error("CosmosService.save_progress failed: %s", exc, exc_info=True)
            raise

    def get_progress(self, user_id):
        try:
            return self.progress.read_item(
                item=f"progress_{user_id}",
                partition_key=user_id,
            )
        except CosmosResourceNotFoundError:
            rhet_log.debug("CosmosService.get_progress: not found user_id=%s", user_id)
            return None

    # ========================================================
    # GOOGLE OAUTH IDENTITY LOOKUP
    # ========================================================

    def get_user_by_google_id(self, google_id: str):
        """
        Find a user whose ``google_id`` field matches *google_id*.

        Returns the user document or None.
        """
        query = """
        SELECT TOP 1 *
        FROM c
        WHERE c.google_id = @google_id
          AND (NOT IS_DEFINED(c.type) OR c.type != 'otp')
        """

        results = list(
            self.users.query_items(
                query=query,
                parameters=[{"name": "@google_id", "value": google_id}],
                enable_cross_partition_query=True,
            )
        )

        if not results:
            rhet_log.debug("CosmosService.get_user_by_google_id: not found google_id=%s", google_id)
        return results[0] if results else None
