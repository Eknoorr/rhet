import os
import json
import uuid
import time
from contextlib import contextmanager
from datetime import datetime

import streamlit as st
from streamlit_local_storage import LocalStorage

from services.foundry_agent import FoundryAgentClient
from services.orchestrator import MasterOrchestrator
from models.p3_schemas import LearnerTurnInput
from services.cosmos_service import CosmosService
# ============================================================
# PAGE SETUP
# ============================================================

st.set_page_config(
    page_title="parrhet.ai",
    page_icon="🦜",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# SESSION STATE
# ==========================
# ==================================

if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = str(uuid.uuid4())

if "messages" not in st.session_state:
    st.session_state.messages = []

if "orchestrator" not in st.session_state:
    st.session_state.orchestrator = MasterOrchestrator()

if "next_target" not in st.session_state:
    st.session_state.next_target = ""

if "pending_history_restore" not in st.session_state:
    st.session_state.pending_history_restore = None

if "page" not in st.session_state:
    st.session_state.page = "home"  # "home" | "chat" | "settings" | "profile" | "signup" | "signin"

if "navigation_loading" not in st.session_state:
    st.session_state.navigation_loading = False

if "chat_request_pending" not in st.session_state:
    st.session_state.chat_request_pending = False

if "cosmos" not in st.session_state:
    st.session_state.cosmos = CosmosService()

if "progress_session_counted" not in st.session_state:
    st.session_state.progress_session_counted = False

if "user_progress" not in st.session_state:
    st.session_state.user_progress = None


def navigate_to(page, pending_history=None):
    """Switch pages through the app's visual page-transition loader."""
    if pending_history is not None:
        st.session_state.pending_history_restore = pending_history
    st.session_state.page = page
    st.session_state.navigation_loading = True


def mark_chat_submission():
    """Prevent the page-transition overlay from appearing for chat submissions."""
    st.session_state.chat_request_pending = True
    st.session_state.navigation_loading = False


@contextmanager
def processing_loader(title, subtitle="Just a moment…"):
    """Show a compact in-chat loader while a chat request is running."""
    holder = st.empty()
    holder.markdown(
        f"""
        <div class="chat-processing-loader" aria-live="polite">
          <div class="chat-processing-card">
            <div class="chat-processing-spinner"></div>
            <div class="chat-processing-copy">
              <div class="chat-processing-title">{title}</div>
              <div class="chat-processing-sub">{subtitle}</div>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    try:
        yield
    finally:
        holder.empty()


def normalize_result_language_fields(result):
    """Give each Rhet response explicit learning/native text fields for the UI."""
    if not isinstance(result, dict):
        return result

    learning_text = (
        result.get("learning_language_text")
        or result.get("conversational_reply")
        or result.get("suggested_next_target")
        or ""
    )
    native_text = (
        result.get("native_language_text")
        or result.get("translation")
        or result.get("native_gloss")
        or ""
    )

    result["learning_language_text"] = str(learning_text or "").strip()
    result["native_language_text"] = str(native_text or "").strip()
    return result


def ensure_target_audio(result, language):
    """Regenerate missing practice-target audio when a saved session is reopened."""
    if not isinstance(result, dict):
        return None

    target = (
        result.get("suggested_next_target")
        or result.get("learning_language_text")
        or ""
    ).strip()
    if not target:
        return None

    current_path = result.get("target_audio_path")
    if current_path and os.path.exists(current_path):
        return current_path

    path = generate_pronunciation_audio(target, language)
    if path:
        result["target_audio_path"] = path
    return path

# ============================================================
# LOCAL STORAGE
# ============================================================

local_storage = LocalStorage()

HISTORY_KEY = "rhet_chat_history"

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "foundry_agent" not in st.session_state:
    st.session_state.foundry_agent = None

def get_foundry_agent():
    if st.session_state.foundry_agent is None:
        st.session_state.foundry_agent = FoundryAgentClient()

    return st.session_state.foundry_agent

def save_history_to_local_storage():
    """
    Save the current conversation list to browser localStorage.
    """
    try:
        local_storage.setItem(
            HISTORY_KEY,
            json.dumps(
                st.session_state.chat_history,
                ensure_ascii=False
            )
        )
    except Exception as e:
        st.warning(
            f"Could not save conversation history: {e}"
        )


def get_history_title(messages):
    """
    Use the first meaningful user message as the conversation title.
    """
    for message in messages:
        if message.get("role") == "user":
            content = message.get("content", "")

            if isinstance(content, str):
                title = content.strip()

                if title:
                    return (
                        title[:42] + "..."
                        if len(title) > 42
                        else title
                    )

    return "New conversation"


def get_language_flag(language):
    """
    Convert language name or language code into a flag.
    Supports both old and new history entries.
    """

    flags = {
        "Spanish": "🇪🇸",
        "English": "🇬🇧",
        "French": "🇫🇷",
        "German": "🇩🇪",
        "Japanese": "🇯🇵",
        "Hindi": "🇮🇳",

        # Old/localized language codes
        "es": "🇪🇸",
        "es-ES": "🇪🇸",

        "en": "🇬🇧",
        "en-US": "🇬🇧",

        "fr": "🇫🇷",
        "fr-FR": "🇫🇷",

        "de": "🇩🇪",
        "de-DE": "🇩🇪",

        "ja": "🇯🇵",
        "ja-JP": "🇯🇵",

        "hi": "🇮🇳",
        "hi-IN": "🇮🇳",
    }

    if not language:
        return "🌐"

    return flags.get(
        str(language).strip(),
        "🌐"
    )

def load_user_progress():
    """Load the current user's progress from Cosmos DB."""
    user_account = st.session_state.get("user_account") or {}
    user_id = user_account.get("user_id")

    if not user_id:
        return None

    try:
        progress = st.session_state.cosmos.get_progress(user_id)

        if progress:
            st.session_state.user_progress = progress

        return progress

    except Exception as e:
        st.warning(f"Could not load progress: {e}")
        return None

def update_user_progress():
    """
    Update the persistent learning progress for the current user.

    A session is counted only once per conversation.
    Messages are counted from the current conversation.
    """

    user_account = st.session_state.get("user_account") or {}
    user_id = user_account.get("user_id")

    if not user_id:
        return

    messages = st.session_state.get("messages", [])

    if not messages:
        return

    try:
        # --------------------------------------------------------
        # Get existing progress
        # --------------------------------------------------------
        progress = st.session_state.cosmos.get_progress(user_id)

        if not progress:
            progress = {
                "id": f"progress_{user_id}",
                "user_id": user_id,
                "total_sessions": 0,
                "total_messages": 0,
                "languages_practiced": [],
                "last_practice_date": None,
                "current_streak": 0,
                "longest_streak": 0
            }

        # --------------------------------------------------------
        # Count user messages
        # --------------------------------------------------------
        user_messages = [
            message
            for message in messages
            if message.get("role") == "user"
        ]

        progress["total_messages"] = len(user_messages)

        # --------------------------------------------------------
        # Count this conversation as ONE session
        # --------------------------------------------------------
        if not st.session_state.progress_session_counted:
            progress["total_sessions"] = (
                progress.get("total_sessions", 0) + 1
            )

            st.session_state.progress_session_counted = True

        # --------------------------------------------------------
        # Track language
        # --------------------------------------------------------
        target_language = st.session_state.get(
            "target_language",
            "Spanish"
        )

        languages = progress.get(
            "languages_practiced",
            []
        )

        if target_language and target_language not in languages:
            languages.append(target_language)

        progress["languages_practiced"] = languages

        # --------------------------------------------------------
        # Practice date
        # --------------------------------------------------------
        today = datetime.now().date().isoformat()

        last_practice = progress.get("last_practice_date")

        if last_practice != today:
            progress["last_practice_date"] = today

        # --------------------------------------------------------
        # Save to Cosmos
        # --------------------------------------------------------
        st.session_state.cosmos.save_progress(progress)

    except Exception as e:
        st.warning(
            f"Progress could not be saved to Cosmos DB: {e}"
        )

def load_user_conversations():
    """Load the current user's conversations from Cosmos DB."""

    user_account = st.session_state.get("user_account") or {}
    user_id = user_account.get("user_id")

    if not user_id:
        return []

    try:
        conversations = (
            st.session_state.cosmos
            .get_user_conversations(user_id)
        )

        conversations = list(conversations or [])

        # Newest first
        conversations.sort(
            key=lambda item: item.get("updated_at", ""),
            reverse=True
        )

        # Keep the same UI limit
        conversations = conversations[:20]

        st.session_state.chat_history = conversations

        return conversations

    except Exception as e:
        st.warning(
            f"Could not load conversations from Cosmos DB: {e}"
        )
        return []

def save_current_conversation():
    """
    Save the current chat to:
    1. Streamlit session state
    2. Cosmos DB
    3. Browser localStorage as a temporary fallback
    """

    messages = st.session_state.messages

    # Don't save empty conversations.
    if not messages:
        return

    user_account = st.session_state.get("user_account") or {}
    user_id = user_account.get("user_id")

    # We need a stable user ID before writing to Cosmos.
    if not user_id:
        st.warning(
            "No user ID found. Conversation could not be saved to Cosmos DB."
        )
        return

    conversation_id = st.session_state.get("conversation_id")

    if not conversation_id:
        conversation_id = str(uuid.uuid4())
        st.session_state.conversation_id = conversation_id

    now = datetime.now().isoformat()

    history_entry = {
        "id": conversation_id,
        "user_id": user_id,

        "title": get_history_title(messages),

        "flag": get_language_flag(
            st.session_state.get(
                "target_language",
                "Spanish"
            )
        ),

        "created_at": now,
        "updated_at": now,

        # Store a copy of the complete chat.
        "messages": json.loads(
            json.dumps(messages)
        ),

        "native_language": st.session_state.get(
            "native_language",
            "English"
        ),

        "target_language": st.session_state.get(
            "target_language",
            "Spanish"
        ),

        "level": st.session_state.get(
            "proficiency_level",
            "A1"
        ),
    }

    # ========================================================
    # UPDATE LOCAL SESSION STATE
    # ========================================================

    history = st.session_state.chat_history

    # Replace existing version of this conversation.
    history = [
        item
        for item in history
        if item.get("id") != conversation_id
    ]

    # Newest first.
    history.insert(0, history_entry)

    # Keep maximum 20 conversations in the UI.
    history = history[:20]

    st.session_state.chat_history = history

    # ========================================================
    # SAVE TO COSMOS DB
    # ========================================================

    try:
        st.session_state.cosmos.save_conversation(
            history_entry
        )

    except Exception as e:
        st.warning(
            f"Conversation saved locally, but Cosmos DB save failed: {e}"
        )

    # ========================================================
    # UPDATE LEARNING PROGRESS
    # ========================================================

    update_user_progress()

    # ========================================================
    # TEMPORARY LOCALSTORAGE FALLBACK
    # ========================================================

    save_history_to_local_storage()


def generate_pronunciation_audio(text, language):
    """
    Generate playable pronunciation audio using Azure Speech TTS.
    """

    if not text or not text.strip():
        return None

    # Convert language name to Azure Speech locale.
    speech_language_codes = {
        "Spanish": "es-ES",
        "English": "en-US",
        "French": "fr-FR",
        "German": "de-DE",
        "Japanese": "ja-JP",
        "Hindi": "hi-IN",
    }

    speech_language = speech_language_codes.get(
        language,
        "en-US"
    )

    import tempfile

    temp_fd, temp_path = tempfile.mkstemp(
        suffix=".wav"
    )
    os.close(temp_fd)

    try:
        st.session_state.orchestrator.pipeline_p4.speak_tutor_response(
            text=text.strip(),
            language=speech_language,
            output_audio_path=temp_path,
        )

        if os.path.exists(temp_path):
            return temp_path

    except Exception as e:
        st.warning(
            f"Could not generate pronunciation audio: {e}"
        )

    return None

# ============================================================
# ACCOUNT / SETTINGS STORAGE — ADDITIVE FUNCTIONALITY
# ============================================================

ACCOUNT_KEY = "rhet_user_account"
SETTINGS_KEY = "rhet_user_settings"

if "user_account" not in st.session_state:
    st.session_state.user_account = None

if "account_storage_record" not in st.session_state:
    st.session_state.account_storage_record = None

# LocalStorage's getItem component can need a second render before it
# exposes an existing browser value. Retry exactly once so a refresh does
# not incorrectly send an existing user to Sign up.
if "account_loaded" not in st.session_state or "settings_loaded" not in st.session_state or "history_loaded" not in st.session_state:
    # Read browser localStorage once per Streamlit session. Multiple getItem()
    # components in the same render can collide on the frontend component key.
    saved_storage = None
    try:
        saved_storage = local_storage.getAll()
    except Exception:
        saved_storage = None

    parsed_storage = {}

    if isinstance(saved_storage, dict):
        parsed_storage = saved_storage
    elif isinstance(saved_storage, str):
        try:
            loaded = json.loads(saved_storage)
            if isinstance(loaded, dict):
                parsed_storage = loaded
        except (json.JSONDecodeError, TypeError):
            parsed_storage = {}
    elif isinstance(saved_storage, list):
        for item in saved_storage:
            if isinstance(item, dict):
                item_key = item.get("key")
                if item_key and "value" in item:
                    parsed_storage[item_key] = item.get("value")
                elif item_key and "toStore" in item:
                    parsed_storage[item_key] = item.get("toStore")

    # getAll() can be empty/None on its first browser render. Retry once so an
    # existing local account is not mistaken for a new user.
    if saved_storage is None and not st.session_state.get("storage_load_retried", False):
        st.session_state.storage_load_retried = True
        st.rerun()

    if "history_loaded" not in st.session_state:
        saved_history = parsed_storage.get(HISTORY_KEY)

        if saved_history:
            try:
                if isinstance(saved_history, str):
                    loaded_history = json.loads(saved_history)

                    if isinstance(loaded_history, list):
                        st.session_state.chat_history = loaded_history

                elif isinstance(saved_history, list):
                    st.session_state.chat_history = saved_history

            except (json.JSONDecodeError, TypeError):
                st.session_state.chat_history = []

        st.session_state.history_loaded = True
        
    if "account_loaded" not in st.session_state:
        saved_account = parsed_storage.get(ACCOUNT_KEY)
        parsed_account = None
        if saved_account:
            try:
                if isinstance(saved_account, str):
                    parsed_account = json.loads(saved_account)
                elif isinstance(saved_account, dict):
                    parsed_account = saved_account
            except (json.JSONDecodeError, TypeError):
                parsed_account = None

        st.session_state.account_storage_record = (
            parsed_account
            if isinstance(parsed_account, dict) and parsed_account.get("email")
            else None
        )

        stored_account = st.session_state.account_storage_record
        if stored_account and not stored_account.get("user_id"):
            stored_account["user_id"] = (
                stored_account.get("id")
                or str(uuid.uuid4())
            )

            st.session_state.account_storage_record = stored_account

            try:
                local_storage.setItem(
                    ACCOUNT_KEY,
                    json.dumps(
                        stored_account,
                        ensure_ascii=False
                    )
                )
            except Exception:
                pass
        if stored_account:
            # Accounts created before the sign-in flow did not have an
            # authenticated flag; treat those as signed in for compatibility.
            authenticated = stored_account.get("authenticated", True)
            st.session_state.user_account = stored_account if authenticated else None

        st.session_state.account_loaded = True

    # ============================================================
    # LOAD PERSISTENT COSMOS DATA FOR SIGNED-IN USER
    # ============================================================

    if (
        st.session_state.get("user_account")
        and "cosmos_user_data_loaded" not in st.session_state
    ):

        user_id = (
            st.session_state.user_account
            .get("user_id")
        )

        if user_id:

            # ----------------------------------------------------
            # LOAD USER PROFILE + SETTINGS
            # ----------------------------------------------------

            try:
                cosmos_user = (
                    st.session_state.cosmos
                    .get_user(user_id)
                )

                if cosmos_user:

                    # Update account information
                    st.session_state.user_account.update({
                        "user_id": cosmos_user.get(
                            "user_id",
                            user_id
                        ),
                        "name": cosmos_user.get(
                            "name",
                            st.session_state.user_account.get(
                                "name",
                                ""
                            )
                        ),
                        "email": cosmos_user.get(
                            "email",
                            st.session_state.user_account.get(
                                "email",
                                ""
                            )
                        )
                    })

                    # Load learning settings
                    for key in (
                        "native_language",
                        "target_language",
                        "proficiency_level",
                        "daily_goal",
                        "session_length",
                        "correction_style",
                        "show_translations",
                        "pronunciation_feedback",
                        "auto_play_audio",
                    ):
                        if key in cosmos_user:
                            st.session_state[key] = (
                                cosmos_user[key]
                            )

            except Exception as e:
                st.warning(
                    f"Could not load user profile from Cosmos DB: {e}"
                )

            # ----------------------------------------------------
            # LOAD CONVERSATIONS
            # ----------------------------------------------------

            load_user_conversations()

            # ----------------------------------------------------
            # LOAD PROGRESS
            # ----------------------------------------------------

            try:
                progress = (
                    st.session_state.cosmos
                    .get_progress(user_id)
                )

                st.session_state.user_progress = (
                    progress
                    if progress
                    else None
                )

            except Exception as e:
                st.warning(
                    f"Could not load progress from Cosmos DB: {e}"
                )

        st.session_state.cosmos_user_data_loaded = True

    if "settings_loaded" not in st.session_state:
        saved_settings = parsed_storage.get(SETTINGS_KEY)
        if saved_settings:
            try:
                if isinstance(saved_settings, str):
                    saved_settings = json.loads(saved_settings)
                if isinstance(saved_settings, dict):
                    for key in (
                        "native_language", "target_language", "proficiency_level",
                        "daily_goal", "session_length", "correction_style",
                        "show_translations", "pronunciation_feedback", "auto_play_audio"
                    ):
                        if key in saved_settings:
                            st.session_state[key] = saved_settings[key]
            except (json.JSONDecodeError, TypeError):
                pass
        st.session_state.settings_loaded = True

def save_user_account(account):
    """Save the local account and persist signed-in state in one localStorage item."""
    record = dict(account)

    # Give every account one stable ID.
    if not record.get("user_id"):
        record["user_id"] = record.get("id") or str(uuid.uuid4())

    record["authenticated"] = True
    st.session_state.user_account = record
    st.session_state.account_storage_record = record

    # ========================================================
    # SAVE USER PROFILE TO COSMOS
    # ========================================================

    try:
        user_document = {
            "id": record["user_id"],
            "user_id": record["user_id"],
            "name": record.get("name", ""),
            "email": record.get("email", ""),
            "created_at": record.get(
                "created_at",
                datetime.now().isoformat()
            ),

            "native_language": st.session_state.get(
                "native_language",
                "English"
            ),
            "target_language": st.session_state.get(
                "target_language",
                "Spanish"
            ),
            "proficiency_level": st.session_state.get(
                "proficiency_level",
                "A1"
            ),
            "daily_goal": st.session_state.get(
                "daily_goal",
                10
            ),
            "session_length": st.session_state.get(
                "session_length",
                "10 minutes"
            ),
            "correction_style": st.session_state.get(
                "correction_style",
                "Balanced"
            ),
            "show_translations": st.session_state.get(
                "show_translations",
                True
            ),
            "pronunciation_feedback": st.session_state.get(
                "pronunciation_feedback",
                True
            ),
            "auto_play_audio": st.session_state.get(
                "auto_play_audio",
                True
            )
        }

        st.session_state.cosmos.save_user(user_document)

    except Exception as e:
        st.warning(
            f"Account created locally, but Cosmos user save failed: {e}"
        )

    # ========================================================
    # SAVE LOCAL ACCOUNT
    # ========================================================

    try:
        local_storage.setItem(
            ACCOUNT_KEY,
            json.dumps(record, ensure_ascii=False)
        )
        time.sleep(0.45)
        return True

    except Exception as e:
        st.warning(f"Could not save account information: {e}")
        return False

def sign_in_user(email):
    """Authenticate against the single locally stored demo account."""
    stored = st.session_state.get("account_storage_record") or {}
    stored_email = str(stored.get("email", "")).strip().lower()

    if not stored_email:
        return False, "No local account exists in this browser yet. Please create an account first."

    if email.strip().lower() != stored_email:
        return False, "That email does not match the local account saved in this browser."

    record = dict(stored)
    record["authenticated"] = True

    try:
        local_storage.setItem(
            ACCOUNT_KEY,
            json.dumps(record, ensure_ascii=False)
        )
        time.sleep(0.45)
    except Exception as e:
        return False, f"Could not save sign-in state: {e}"

    st.session_state.account_storage_record = record
    st.session_state.user_account = record
    return True, ""


def sign_out_user():
    """Sign out without deleting the locally stored account."""
    stored = st.session_state.get("account_storage_record") or {}
    if stored:
        record = dict(stored)
        record["authenticated"] = False
        try:
            local_storage.setItem(
                ACCOUNT_KEY,
                json.dumps(record, ensure_ascii=False)
            )
            time.sleep(0.3)
            st.session_state.account_storage_record = record
        except Exception as e:
            st.warning(f"Could not save sign-out state: {e}")
    st.session_state.user_account = None


def clear_user_account():
    """Delete the locally stored account completely."""
    st.session_state.user_account = None
    st.session_state.account_storage_record = None
    try:
        local_storage.removeItem(ACCOUNT_KEY)
    except Exception:
        try:
            local_storage.setItem(ACCOUNT_KEY, json.dumps({}))
        except Exception as e:
            st.warning(f"Could not clear account information: {e}")


def get_user_display_name():
    account = st.session_state.get("user_account") or {}
    return account.get("name") or "Learner"


def get_user_email():
    account = st.session_state.get("user_account") or {}
    return account.get("email") or ""

# ============================================================
# FONTS & STYLESHEET — CREAM + OLIVE EDITORIAL
# ============================================================

st.markdown("""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
""", unsafe_allow_html=True)

st.markdown("""
<style>
/* =========================================================
   DESIGN TOKENS — WARM CREAM + OLIVE
   ========================================================= */

:root {
    --bg:          #EDE6D6;
    --bg-sidebar:  #E2DAC9;
    --surface:     #FDFAF5;
    --surface-2:   #F5F0E8;
    --border:      rgba(90,80,55,0.18);
    --border-hi:   rgba(90,80,55,0.36);
    --olive:       #6B7A46;
    --olive-hi:    #4A5920;
    --olive-lo:    #8A9A62;
    --olive-pale:  #C8D4A8;
    --olive-card:  #7B8C52;
    --coral:       #C45030;
    --coral-pale:  #F2C5B0;
    --text:        #1A1710;
    --text-muted:  #7A7260;
    --radius:      10px;
    --radius-lg:   14px;
    /* Instrument Serif for display, Inter for UI */
    --font-display: 'Instrument Serif', Georgia, serif;
    --font:         'Inter', system-ui, sans-serif;
    --mono:         'JetBrains Mono', 'Courier New', monospace;
    --ease:         cubic-bezier(0.22, 1, 0.36, 1);
}

*, *::before, *::after { box-sizing: border-box; }

html, body, [data-testid="stAppViewContainer"] {
    background-color: var(--bg) !important;
    color: var(--text) !important;
    font-family: var(--font) !important;
    font-size: 15px;
    line-height: 1.6;
    -webkit-font-smoothing: antialiased !important;
    text-rendering: optimizeLegibility !important;
}

[data-testid="stHeader"],
[data-testid="stDecoration"],
#MainMenu, footer {
    display: none !important;
    visibility: hidden !important;
}

[data-testid="stBottomBlockContainer"] {
    background: var(--bg) !important;
    border-top: 1px solid var(--border) !important;
}

.block-container {
    padding-top: 0 !important;
    padding-bottom: 7.5rem !important;
    max-width: 100% !important;
}

/* =========================================================
   SIDEBAR
   ========================================================= */

[data-testid="stSidebar"] {
    background: var(--bg-sidebar) !important;
    border-right: 1.5px solid var(--border) !important;
}
[data-testid="stSidebar"] > div:first-child {
    padding: 24px 14px 24px;
}

/* Logo */
.sb-logo {
    font-family: var(--font-display);
    font-size: 22px;
    font-weight: 400;
    font-style: italic;
    background: linear-gradient(135deg, var(--text) 0%, var(--olive-hi) 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    letter-spacing: -0.4px;
    margin-bottom: 20px;
    line-height: 1;
}
.sb-logo-accent {
    background: linear-gradient(135deg, var(--coral) 0%, #E07040 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    font-style: normal;
    font-weight: 500;
}

/* Section labels */
.sb-label {
    font-family: var(--font);
    font-size: 9px;
    font-weight: 700;
    letter-spacing: 1.8px;
    text-transform: uppercase;
    color: var(--text-muted);
    margin: 20px 0 7px;
    padding-left: 1px;
    opacity: 0.65;
}

/* History card (empty state) */
.sb-card {
    padding: 8px 10px;
    border-radius: var(--radius);
    border: 1px solid var(--border);
    background: rgba(255,255,255,0.3);
    margin-bottom: 4px;
}
.sb-card-title {
    font-size: 12px;
    font-weight: 500;
    color: var(--text-muted);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.sb-card-meta {
    font-size: 10.5px;
    color: var(--text-muted);
    opacity: 0.65;
    margin-top: 2px;
}

/* ── ALL BUTTONS: base rule (outlined by default) ── */
[data-testid="stSidebar"] .stButton > button,
div.nb [data-testid="stButton"] > button,
div.nav-btn [data-testid="stButton"] > button,
div.nav-btn-active [data-testid="stButton"] > button {
    font-family: var(--font) !important;
    font-size: 12.5px !important;
    font-weight: 500 !important;
    width: 100% !important;
    min-height: 36px !important;
    border-radius: var(--radius) !important;
    text-align: left !important;
    transition: all 0.2s var(--ease) !important;
    padding: 6px 11px !important;
    outline: none !important;
}

/* Nav buttons — outlined, muted */
div.nav-btn [data-testid="stButton"] > button {
    background: transparent !important;
    color: var(--text-muted) !important;
    border: 1.5px solid var(--border) !important;
}
div.nav-btn [data-testid="stButton"] > button:hover {
    background: rgba(255,255,255,0.5) !important;
    border-color: var(--border-hi) !important;
    color: var(--text) !important;
    transform: translateX(2px) !important;
}

/* Active nav button — olive outlined */
div.nav-btn-active [data-testid="stButton"] > button {
    background: rgba(107,122,70,0.1) !important;
    color: var(--olive-hi) !important;
    border: 1.5px solid var(--olive-lo) !important;
    font-weight: 600 !important;
    cursor: default !important;
}

/* New conversation button — coral-outlined */
div.nb [data-testid="stButton"] > button {
    background: var(--surface) !important;
    color: var(--olive-hi) !important;
    border: 1.5px solid var(--border-hi) !important;
    font-weight: 600 !important;
    font-size: 13px !important;
    min-height: 40px !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06) !important;
}
div.nb [data-testid="stButton"] > button:hover {
    background: #FFFFFF !important;
    border-color: var(--olive) !important;
    color: var(--coral) !important;
    box-shadow: 0 3px 12px rgba(0,0,0,0.1) !important;
    transform: translateY(-1px) !important;
}

/* History + account buttons — outlined */
[data-testid="stSidebar"] .stButton > button {
    background: transparent !important;
    color: var(--text-muted) !important;
    border: 1px solid var(--border) !important;
    margin-bottom: 3px !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background: rgba(255,255,255,0.45) !important;
    border-color: var(--border-hi) !important;
    color: var(--text) !important;
    transform: translateX(2px) !important;
}

/* Sidebar selectboxes */
[data-testid="stSidebar"] [data-testid="stSelectbox"] label {
    color: var(--text-muted) !important;
    font-family: var(--font) !important;
    font-size: 9px !important;
    font-weight: 700 !important;
    letter-spacing: 1.5px !important;
    text-transform: uppercase !important;
    opacity: 0.65 !important;
}
[data-testid="stSidebar"] [data-testid="stSelectbox"] > div > div {
    background: var(--surface) !important;
    border: 1.5px solid var(--border) !important;
    border-radius: var(--radius) !important;
    color: var(--text) !important;
    font-family: var(--font) !important;
    font-size: 13px !important;
    font-weight: 500 !important;
}
[data-testid="stSidebar"] [data-testid="stSelectbox"] > div > div:hover {
    border-color: var(--olive-lo) !important;
}

/* =========================================================
   TOPBAR
   ========================================================= */

.topbar {
    height: 58px;
    border-bottom: 1.5px solid var(--border);
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 36px;
    background: rgba(237,230,214,0.92);
    backdrop-filter: blur(24px);
    -webkit-backdrop-filter: blur(24px);
    position: sticky;
    top: 0;
    z-index: 100;
    box-shadow: 0 1px 0 var(--border), 0 4px 16px rgba(0,0,0,0.04);
}
.topbar-left { display: flex; align-items: baseline; gap: 12px; }
.topbar-title {
    font-family: var(--font-display);
    font-size: 21px;
    font-weight: 400;
    font-style: italic;
    background: linear-gradient(135deg, var(--text) 40%, var(--coral) 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    letter-spacing: -0.4px;
    line-height: 1;
}
.topbar-divider {
    width: 1.5px;
    height: 16px;
    background: var(--border-hi);
    display: inline-block;
    border-radius: 2px;
}
.topbar-sub {
    font-family: var(--font);
    font-size: 11.5px;
    color: var(--text-muted);
    font-weight: 500;
    line-height: 1;
    letter-spacing: 0.02em;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    font-size: 9.5px;
}
.topbar-pill {
    display: inline-flex;
    align-items: center;
    gap: 7px;
    background: transparent;
    border: 1.5px solid rgba(107,122,70,0.35);
    border-radius: 100px;
    padding: 5px 14px;
    font-family: var(--font);
    font-size: 11px;
    font-weight: 600;
    color: var(--olive-hi);
    letter-spacing: 0.03em;
    transition: all 0.2s var(--ease);
}
.topbar-pill:hover {
    background: rgba(107,122,70,0.08);
    border-color: var(--olive);
}
.blink {
    width: 5px; height: 5px;
    border-radius: 50%;
    background: var(--olive);
    animation: blink 2.2s ease-in-out infinite;
}
@keyframes blink {
    0%,100% { opacity: 1; transform: scale(1); }
    50%      { opacity: 0.15; transform: scale(0.65); }
}

/* =========================================================
   CHAT WRAP
   ========================================================= */

.chat-wrap {
    max-width: 720px;
    margin: 0 auto;
    padding: 28px 12px 140px;
}

/* Quick-start section (on chat page) */
.qs-wrap {
    text-align: center;
    padding: 68px 0 36px;
}
.qs-title {
    font-family: var(--font-display);
    font-size: 38px;
    font-weight: 400;
    font-style: italic;
    color: var(--text);
    letter-spacing: -0.8px;
    line-height: 1.15;
    margin-bottom: 10px;
}
.qs-title em { color: var(--coral); font-style: normal; }
.qs-sub {
    font-family: var(--font);
    font-size: 15px;
    color: var(--text-muted);
    font-weight: 400;
    max-width: 400px;
    margin: 0 auto 32px;
    line-height: 1.75;
}
.qs-row {
    display: flex;
    flex-wrap: wrap;
    gap: 9px;
    justify-content: center;
}
.qchip {
    background: var(--surface);
    border: 1.5px solid var(--border);
    border-radius: 100px;
    padding: 8px 18px;
    font-family: var(--font);
    font-size: 13px;
    font-weight: 500;
    color: var(--text);
    cursor: default;
    transition: all 0.22s var(--ease);
    letter-spacing: -0.1px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}
.qchip:hover {
    background: var(--olive-hi);
    border-color: var(--olive-hi);
    color: #F5F0E6;
    transform: translateY(-3px);
    box-shadow: 0 8px 20px rgba(74,89,32,0.25);
}
.qchip.coral {
    border-color: rgba(196,64,40,0.35);
    color: var(--coral);
    background: rgba(196,64,40,0.04);
}
.qchip.coral:hover {
    background: var(--coral);
    border-color: var(--coral);
    color: #FFF5F0;
    transform: translateY(-3px);
    box-shadow: 0 8px 20px rgba(196,64,40,0.3);
}

/* =========================================================
   DASHBOARD
   ========================================================= */

.dash-wrap {
    max-width: 720px;
    margin: 0 auto;
    padding: 32px 12px 60px;
}

/* Olive hero band */
.olive-band {
    background: linear-gradient(130deg, #5C6E35 0%, #7B8C52 55%, #8FA068 100%);
    border-radius: var(--radius-lg);
    padding: 30px 32px;
    margin-bottom: 20px;
    position: relative;
    overflow: hidden;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 16px;
    border: 1.5px solid rgba(255,255,255,0.18);
    box-shadow: 0 4px 24px rgba(74,89,32,0.25);
}
.olive-band::before {
    content: '';
    position: absolute;
    top: -50px; right: -50px;
    width: 180px; height: 180px;
    border-radius: 50%;
    background: rgba(255,255,255,0.08);
}
.olive-band::after {
    content: '';
    position: absolute;
    bottom: -30px; left: 30%;
    width: 100px; height: 100px;
    border-radius: 50%;
    background: rgba(255,255,255,0.05);
}
.olive-band-text { color: #E8F0D8; position: relative; z-index: 1; }
.olive-band-title {
    font-family: var(--font-display);
    font-size: 26px;
    font-weight: 400;
    font-style: italic;
    letter-spacing: -0.5px;
    margin-bottom: 8px;
    line-height: 1.2;
    text-shadow: 0 1px 3px rgba(0,0,0,0.1);
}
.olive-band-sub {
    font-family: var(--font);
    font-size: 14px;
    opacity: 0.78;
    font-weight: 400;
    line-height: 1.55;
}
.olive-band-lang {
    font-family: var(--font);
    font-size: 32px;
    font-weight: 800;
    color: rgba(255,255,255,0.92);
    letter-spacing: -1.5px;
    line-height: 1;
    position: relative;
    z-index: 1;
    text-shadow: 0 2px 8px rgba(0,0,0,0.15);
}

/* Stats row */
.stats-row {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 10px;
    margin-bottom: 24px;
}
.stat-card {
    background: var(--surface);
    border: 1.5px solid var(--border);
    border-radius: var(--radius-lg);
    padding: 20px 16px;
    transition: all 0.22s var(--ease);
    cursor: default;
    position: relative;
    overflow: hidden;
}
.stat-card::after {
    content: '';
    position: absolute;
    left: 0; top: 0;
    width: 3px; height: 100%;
    background: var(--olive-pale);
    border-radius: 2px 0 0 2px;
    opacity: 0;
    transition: opacity 0.22s;
}
.stat-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 10px 28px rgba(0,0,0,0.1);
    border-color: var(--olive-lo);
    background: #FFFFFF;
}
.stat-card:hover::after { opacity: 1; }
.stat-card.accent {
    background: rgba(107,122,70,0.08);
    border-color: rgba(107,122,70,0.3);
}
.stat-card.accent::after { background: var(--olive); opacity: 1; }
.stat-card.accent:hover {
    background: rgba(107,122,70,0.14);
    border-color: var(--olive);
    box-shadow: 0 10px 28px rgba(74,89,32,0.15);
}
.stat-value {
    font-family: var(--font);
    font-size: 38px;
    font-weight: 800;
    color: var(--olive-hi);
    letter-spacing: -2px;
    line-height: 1;
    margin-bottom: 6px;
}
.stat-card.accent .stat-value { color: var(--olive); }
.stat-label {
    font-family: var(--font);
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 1.3px;
    text-transform: uppercase;
    color: var(--text-muted);
    opacity: 0.8;
}

/* Section title */
.dash-section-title {
    font-family: var(--font);
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    color: var(--text-muted);
    margin-bottom: 10px;
    opacity: 0.65;
}

/* Recent sessions grid */
.recents-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 8px;
    margin-bottom: 24px;
}
.recent-item {
    background: var(--surface);
    border: 1.5px solid var(--border);
    border-radius: var(--radius);
    padding: 14px 16px;
    transition: all 0.2s var(--ease);
    cursor: pointer;
    display: flex;
    align-items: flex-start;
    gap: 12px;
}
.recent-item:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(0,0,0,0.09);
    border-color: var(--olive-lo);
    background: #FFFFFF;
}
.recent-lang {
    font-family: var(--font);
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.5px;
    color: var(--olive-lo);
    background: rgba(107,122,70,0.1);
    border: 1px solid rgba(107,122,70,0.2);
    border-radius: 5px;
    padding: 2px 6px;
    margin-top: 1px;
    white-space: nowrap;
    flex-shrink: 0;
}
.recent-info { flex: 1; min-width: 0; }
.recent-title-text {
    font-family: var(--font);
    font-size: 12.5px;
    font-weight: 500;
    color: var(--text);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    line-height: 1.35;
    margin-bottom: 2px;
}
.recent-meta-text {
    font-family: var(--font);
    font-size: 11px;
    color: var(--text-muted);
}

/* =========================================================
   MESSAGES
   ========================================================= */

[data-testid="stChatMessage"] {
    max-width: 720px;
    margin: 0 auto 8px !important;
    font-family: var(--font) !important;
    background: var(--surface) !important;
    border: 1.5px solid var(--border) !important;
    border-radius: var(--radius-lg) !important;
    padding: 16px 20px !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.04) !important;
    color: var(--text) !important;
    transition: box-shadow 0.22s var(--ease), border-color 0.22s var(--ease), transform 0.22s var(--ease) !important;
}
[data-testid="stChatMessage"]:hover {
    box-shadow: 0 6px 20px rgba(0,0,0,0.08) !important;
    border-color: var(--border-hi) !important;
    transform: translateY(-1px) !important;
}
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
    background: var(--surface-2) !important;
    border-color: var(--border) !important;
    box-shadow: none !important;
}
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]):hover {
    transform: none !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.04) !important;
}

[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"],
[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] p,
[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] div,
[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] span,
[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] li {
    color: #22200A !important;
    font-family: var(--font) !important;
    font-size: 15px !important;
    line-height: 1.8 !important;
}
[data-testid="stChatMessage"] h1,[data-testid="stChatMessage"] h2,
[data-testid="stChatMessage"] h3,[data-testid="stChatMessage"] h4 {
    font-family: var(--font-display) !important;
    color: var(--text) !important;
    font-weight: 400 !important;
    font-style: italic !important;
    font-size: 22px !important;
    letter-spacing: -0.4px !important;
    margin-top: 14px !important;
    margin-bottom: 6px !important;
}
[data-testid="stChatMessage"] strong, [data-testid="stChatMessage"] b {
    font-weight: 700 !important;
    color: var(--olive-hi) !important;
}
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) [data-testid="stMarkdownContainer"] p {
    color: #30291A !important;
    font-size: 15px !important;
}

/* Rhet label */
.rhet-label {
    font-family: var(--font);
    font-size: 9.5px;
    font-weight: 700;
    letter-spacing: 2.5px;
    text-transform: uppercase;
    color: var(--coral);
    margin-bottom: 10px;
    display: flex;
    align-items: center;
    gap: 10px;
}
.rhet-label::before {
    content: '';
    width: 18px;
    height: 2px;
    background: var(--coral);
    border-radius: 2px;
    flex-shrink: 0;
}
.rhet-label::after {
    content: '';
    flex: 1;
    height: 1px;
    background: var(--border);
}
.rhet-response {
    font-family: var(--font);
    font-size: 15px;
    line-height: 1.82;
    color: #22200A;
    font-weight: 400;
}

/* Score badges */
.score-row {
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
    margin: 14px 0 6px;
}
.score-badge {
    background: linear-gradient(145deg, rgba(123,140,82,0.12) 0%, rgba(107,122,70,0.06) 100%);
    border: 1.5px solid rgba(123,140,82,0.3);
    border-radius: var(--radius);
    padding: 10px 14px;
    font-family: var(--font);
    font-size: 22px;
    font-weight: 800;
    color: var(--olive-hi);
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 4px;
    min-width: 80px;
    letter-spacing: -1px;
    transition: all 0.22s var(--ease);
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}
.score-badge:hover {
    background: linear-gradient(145deg, rgba(123,140,82,0.22) 0%, rgba(107,122,70,0.12) 100%);
    border-color: var(--olive);
    transform: translateY(-3px);
    box-shadow: 0 6px 16px rgba(74,89,32,0.18);
}
.score-badge span {
    font-family: var(--font);
    font-size: 9.5px;
    color: var(--olive-lo);
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1.2px;
}

/* Page + request loading overlays */
.page-loading-overlay {
    position: fixed;
    inset: 0;
    z-index: 999999;
    display: flex;
    align-items: center;
    justify-content: center;
    background: rgba(246, 235, 222, 0.38);
    backdrop-filter: blur(7px);
    -webkit-backdrop-filter: blur(7px);
    pointer-events: none;
    animation: rhet-page-loader-out 0.62s ease 0.12s forwards;
}
.page-loading-card {
    width: min(290px, calc(100vw - 48px));
    padding: 18px 22px;
    border: 1px solid rgba(107,122,70,0.28);
    border-radius: 15px;
    background: rgba(255,255,255,0.94);
    box-shadow: 0 14px 38px rgba(74,89,32,0.16);
    text-align: center;
}
.page-loading-spinner {
    width: 28px;
    height: 28px;
    margin: 0 auto 10px;
    border: 3px solid rgba(107,122,70,0.18);
    border-top-color: var(--olive);
    border-radius: 50%;
    animation: rhet-spin 0.8s linear infinite;
}
.page-loading-title {
    font-family: var(--font);
    font-size: 14px;
    font-weight: 800;
    color: var(--olive-hi);
}
.page-loading-sub {
    margin-top: 4px;
    font-family: var(--font);
    font-size: 11.5px;
    color: var(--text-muted);
}

/* Chat request loader: stays inside the conversation area. */
.chat-processing-loader {
    display: flex;
    justify-content: flex-start;
    margin: 8px 0 12px 0;
    pointer-events: none;
}
.chat-processing-card {
    display: inline-flex;
    align-items: center;
    gap: 10px;
    max-width: min(360px, 90%);
    padding: 10px 14px;
    border: 1px solid rgba(107,122,70,0.20);
    border-radius: 14px;
    background: rgba(255,255,255,0.94);
    box-shadow: 0 7px 18px rgba(74,89,32,0.10);
}
.chat-processing-spinner {
    width: 18px;
    height: 18px;
    flex: 0 0 18px;
    border: 2px solid rgba(107,122,70,0.18);
    border-top-color: var(--olive);
    border-radius: 50%;
    animation: rhet-spin 0.72s linear infinite;
}
.chat-processing-title {
    font-family: var(--font);
    font-size: 12.5px;
    font-weight: 800;
    color: var(--olive-hi);
}
.chat-processing-sub {
    margin-top: 2px;
    font-family: var(--font);
    font-size: 10.5px;
    color: var(--text-muted);
}
@keyframes rhet-spin {
    to { transform: rotate(360deg); }
}
@keyframes rhet-page-loader-out {
    0% { opacity: 1; visibility: visible; }
    100% { opacity: 0; visibility: hidden; }
}

/* Translation */
.translation-text {
    font-family: var(--font);
    font-size: 14px;
    color: var(--text-muted);
    line-height: 1.7;
    padding: 11px 0 5px;
    border-top: 1.5px solid var(--border);
    margin-top: 12px;
    font-style: italic;
}

/* Feedback */
.feedback-box {
    background: linear-gradient(135deg, rgba(123,140,82,0.1) 0%, rgba(107,122,70,0.05) 100%);
    border: 1.5px solid rgba(123,140,82,0.28);
    border-left: 3px solid var(--olive);
    border-radius: var(--radius);
    padding: 12px 16px;
    font-family: var(--font);
    font-size: 14px;
    color: var(--olive-hi);
    line-height: 1.7;
    margin: 12px 0 4px;
    transition: all 0.2s var(--ease);
}
.feedback-box:hover {
    border-left-color: var(--olive-card);
    background: linear-gradient(135deg, rgba(123,140,82,0.15) 0%, rgba(107,122,70,0.08) 100%);
}

/* Try saying */
.next-target {
    display: inline-flex;
    align-items: center;
    gap: 12px;
    background: rgba(196,64,40,0.06);
    border: 1.5px solid rgba(196,64,40,0.25);
    border-left: 3px solid var(--coral);
    border-radius: var(--radius);
    padding: 10px 16px;
    margin-top: 14px;
    font-family: var(--mono);
    font-size: 14px;
    color: var(--coral);
    transition: all 0.22s var(--ease);
    box-shadow: 0 1px 4px rgba(196,64,40,0.08);
}
.next-target:hover {
    background: rgba(196,64,40,0.1);
    border-color: var(--coral);
    border-left-color: var(--coral);
    transform: translateX(4px);
    box-shadow: 0 4px 12px rgba(196,64,40,0.15);
}
.next-target-label {
    font-family: var(--font);
    font-size: 9.5px;
    font-weight: 700;
    letter-spacing: 1.6px;
    text-transform: uppercase;
    color: rgba(196,64,40,0.6);
    white-space: nowrap;
}

/* Captions */
[data-testid="stChatMessage"] [data-testid="stCaptionContainer"],
[data-testid="stChatMessage"] [data-testid="stCaptionContainer"] p {
    color: var(--text-muted) !important;
    font-family: var(--font) !important;
    font-size: 11.5px !important;
}
[data-testid="stChatMessage"] [data-testid="stAlert"] {
    background: rgba(123,140,82,0.07) !important;
    border: 1.5px solid rgba(123,140,82,0.2) !important;
    border-radius: var(--radius) !important;
}
[data-testid="stChatMessage"] [data-testid="stAlert"] p,
[data-testid="stChatMessage"] [data-testid="stAlert"] div {
    color: var(--olive-hi) !important;
    font-family: var(--font) !important;
    font-size: 13px !important;
}
[data-testid="stChatMessage"] [data-testid="stMetricLabel"] { color: var(--text-muted) !important; }
[data-testid="stChatMessage"] [data-testid="stMetricValue"] { color: var(--olive-hi) !important; font-weight: 700 !important; }
[data-testid="stChatMessage"] code {
    font-family: var(--mono) !important;
    color: var(--coral) !important;
    background: rgba(196,80,48,0.07) !important;
    border: 1px solid rgba(196,80,48,0.18) !important;
    border-radius: 5px !important;
    padding: 1px 7px !important;
    font-size: 12.5px !important;
}
[data-testid="stChatMessage"] audio {
    width: 100% !important;
    height: 34px !important;
    border-radius: 7px;
    margin-top: 8px;
    opacity: 0.8;
    transition: opacity 0.2s;
}
[data-testid="stChatMessage"] audio:hover { opacity: 1; }

/* =========================================================
   CHAT INPUT
   ========================================================= */

[data-testid="stChatInput"] {
    width: 100% !important;
    max-width: 640px !important;
    margin: 0 auto !important;
    bottom: 18px !important;
    padding: 0 !important;
}

/* Keep the chat/search bar fixed to the viewport on desktop.
   Streamlit can otherwise let the widget move with the scrollable main body. */
@media (min-width: 681px) {
    [data-testid="stBottom"] {
        position: fixed !important;
        left: 0 !important;
        right: 0 !important;
        bottom: 0 !important;
        width: 100% !important;
        z-index: 10000 !important;
        pointer-events: none !important;
        background: transparent !important;
    }

    [data-testid="stBottom"] [data-testid="stChatInput"] {
        position: fixed !important;
        left: calc(50% + 168px) !important;
        transform: translateX(-50%) !important;
        bottom: 18px !important;
        width: min(640px, calc(100vw - 380px)) !important;
        max-width: 640px !important;
        margin: 0 !important;
        z-index: 10001 !important;
        pointer-events: auto !important;
    }

    /* Keep enough scroll clearance so the fixed input never obscures the
       final chat message. */
    [data-testid="stMainBlockContainer"] {
        padding-bottom: 110px !important;
    }
}
[data-testid="stChatInput"] > div {
    border-radius: var(--radius-lg) !important;
    border: 1.5px solid var(--border-hi) !important;
    background: #FFFFFF !important;
    box-shadow: 0 4px 20px rgba(0,0,0,0.09) !important;
    transition: border-color 0.22s, box-shadow 0.22s !important;
    padding: 3px 5px !important;
}
[data-testid="stChatInput"] > div:focus-within {
    border-color: var(--olive) !important;
    box-shadow: 0 4px 20px rgba(0,0,0,0.09), 0 0 0 3px rgba(107,122,70,0.12) !important;
}
[data-testid="stChatInput"] textarea {
    font-family: var(--font) !important;
    font-size: 14px !important;
    color: var(--text) !important;
    background: transparent !important;
    padding-left: 8px !important;
}
[data-testid="stChatInput"] textarea::placeholder {
    color: #B8B0A0 !important;
    font-style: italic !important;
}
[data-testid="stChatInput"] button {
    background: transparent !important;
    color: var(--olive) !important;
    border: 1.5px solid rgba(107,122,70,0.28) !important;
    border-radius: 8px !important;
    width: 34px !important;
    height: 34px !important;
    transition: all 0.18s var(--ease) !important;
}
[data-testid="stChatInput"] button:hover {
    background: rgba(107,122,70,0.1) !important;
    border-color: var(--olive) !important;
    color: var(--olive-hi) !important;
    transform: scale(1.06) !important;
}
[data-testid="stChatInput"] button:disabled {
    background: transparent !important;
    color: #C0B8A8 !important;
    border-color: var(--border) !important;
}
[data-testid="stChatInput"] button svg { color: currentColor !important; stroke: currentColor !important; }

/* =========================================================
   MOBILE
   ========================================================= */
@media (max-width: 680px) {
    .topbar { padding: 0 16px; }
    .chat-wrap, .dash-wrap { padding-left: 10px; padding-right: 10px; }
    .stats-row { grid-template-columns: repeat(2, 1fr); }
    .recents-grid { grid-template-columns: 1fr; }
    [data-testid="stChatInput"] { max-width: 94% !important; }
}
/* =========================================================
   BACKGROUND DECORATIVE DOTS
   ========================================================= */

.bg-dots {
    position: fixed;
    inset: 0;
    pointer-events: none;
    z-index: 0;
    overflow: hidden;
}

/* Base dot style */
.dot {
    position: absolute;
    border-radius: 50%;
    background: radial-gradient(
        circle,
        rgba(107,122,70,0.38) 0%,
        rgba(107,122,70,0.18) 50%,
        transparent 100%
    );
    box-shadow:
        inset 0 0 0 1.5px rgba(107,122,70,0.5),
        0 0 0 12px rgba(107,122,70,0.1),
        0 0 0 30px rgba(107,122,70,0.04),
        0 0 0 60px rgba(107,122,70,0.015);
}

/* Dot 1 — large, top-left, mostly offscreen */
.dot-1 {
    width: 380px; height: 380px;
    top: -120px; left: -100px;
    background: radial-gradient(circle, rgba(91,110,50,0.45) 0%, rgba(107,122,70,0.22) 55%, transparent 100%);
    box-shadow:
        inset 0 0 0 1.5px rgba(107,122,70,0.55),
        0 0 0 18px rgba(107,122,70,0.12),
        0 0 0 50px rgba(107,122,70,0.05),
        0 0 0 90px rgba(107,122,70,0.018);
}

/* Dot 2 — medium, top-right */
.dot-2 {
    width: 240px; height: 240px;
    top: -50px; right: 80px;
    background: radial-gradient(circle, rgba(91,110,53,0.4) 0%, rgba(91,110,53,0.18) 55%, transparent 100%);
    box-shadow:
        inset 0 0 0 1.5px rgba(91,110,53,0.5),
        0 0 0 14px rgba(91,110,53,0.1),
        0 0 0 38px rgba(91,110,53,0.035);
}

/* Dot 3 — large, right-center */
.dot-3 {
    width: 320px; height: 320px;
    top: 38%; right: -100px;
    background: radial-gradient(circle, rgba(123,140,82,0.38) 0%, rgba(123,140,82,0.16) 55%, transparent 100%);
    box-shadow:
        inset 0 0 0 1.5px rgba(123,140,82,0.48),
        0 0 0 20px rgba(123,140,82,0.09),
        0 0 0 55px rgba(123,140,82,0.03);
}

/* Dot 4 — medium, bottom-left */
.dot-4 {
    width: 280px; height: 280px;
    bottom: 60px; left: -60px;
    background: radial-gradient(circle, rgba(107,122,70,0.42) 0%, rgba(107,122,70,0.2) 55%, transparent 100%);
    box-shadow:
        inset 0 0 0 1.5px rgba(107,122,70,0.52),
        0 0 0 16px rgba(107,122,70,0.1),
        0 0 0 45px rgba(107,122,70,0.035);
}

/* Dot 5 — small, left-center */
.dot-5 {
    width: 160px; height: 160px;
    top: 52%; left: 14%;
    background: radial-gradient(circle, rgba(107,122,70,0.35) 0%, rgba(107,122,70,0.14) 60%, transparent 100%);
    box-shadow:
        inset 0 0 0 1.5px rgba(107,122,70,0.45),
        0 0 0 10px rgba(107,122,70,0.08),
        0 0 0 28px rgba(107,122,70,0.025);
}

/* Dot 6 — medium, bottom-right */
.dot-6 {
    width: 220px; height: 220px;
    bottom: -50px; right: 12%;
    background: radial-gradient(circle, rgba(91,110,53,0.38) 0%, rgba(91,110,53,0.16) 55%, transparent 100%);
    box-shadow:
        inset 0 0 0 1.5px rgba(91,110,53,0.48),
        0 0 0 12px rgba(91,110,53,0.09),
        0 0 0 34px rgba(91,110,53,0.03);
}

/* Dot 7 — tiny, upper-center */
.dot-7 {
    width: 110px; height: 110px;
    top: 22%; left: 42%;
    background: radial-gradient(circle, rgba(107,122,70,0.32) 0%, rgba(107,122,70,0.12) 60%, transparent 100%);
    box-shadow:
        inset 0 0 0 1px rgba(107,122,70,0.42),
        0 0 0 8px rgba(107,122,70,0.07),
        0 0 0 22px rgba(107,122,70,0.02);
}

/* Ensure all content sits above dot layer */
[data-testid="stSidebar"],
[data-testid="stMain"],
[data-testid="stBottom"] {
    position: relative;
    z-index: 1;
}
</style>
""", unsafe_allow_html=True)

# Inject fixed background dot layer
st.markdown("""
<div class="bg-dots" aria-hidden="true">
  <span class="dot dot-1"></span>
  <span class="dot dot-2"></span>
  <span class="dot dot-3"></span>
  <span class="dot dot-4"></span>
  <span class="dot dot-5"></span>
  <span class="dot dot-6"></span>
  <span class="dot dot-7"></span>
</div>
""", unsafe_allow_html=True)

# ============================================================
# PAGE TRANSITION LOADER
# ============================================================
if (
    st.session_state.get("navigation_loading")
    and not st.session_state.get("chat_request_pending")
):
    st.markdown(
        """
        <div class="page-loading-overlay" aria-live="polite">
          <div class="page-loading-card">
            <div class="page-loading-spinner"></div>
            <div class="page-loading-title">Loading Rhet…</div>
            <div class="page-loading-sub">Opening your page</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    # Do not sleep or wait for another Streamlit rerun. The CSS animation
    # dismisses the overlay in the browser while the new page is already rendered.
    st.session_state.navigation_loading = False

# ============================================================
# RESTORE PENDING HISTORY
# MUST HAPPEN BEFORE SIDEBAR WIDGETS
# ============================================================

if st.session_state.pending_history_restore is not None:

    item = st.session_state.pending_history_restore

    # Restore complete chat
    st.session_state.messages = json.loads(
        json.dumps(
            item.get("messages", [])
        )
    )

    # Restore conversation ID
    st.session_state.conversation_id = item.get(
        "id",
        str(uuid.uuid4())
    )
    st.session_state.progress_session_counted = True

    # Restore learner settings BEFORE widgets exist
    st.session_state.native_language = item.get(
        "native_language",
        "English"
    )

    st.session_state.target_language = item.get(
        "target_language",
        "Spanish"
    )

    st.session_state.proficiency_level = item.get(
        "level",
        "A1"
    )

    # Reset temporary target
    st.session_state.next_target = ""

    # Fresh orchestrator
    st.session_state.orchestrator = MasterOrchestrator()

    # Consume the pending restore
    st.session_state.pending_history_restore = None


# ============================================================
# AUTHENTICATION GATE — CHAT REQUIRES A LOCAL ACCOUNT
# ============================================================
if st.session_state.page == "chat" and not st.session_state.user_account:
    st.session_state.page = (
        "signin" if st.session_state.get("account_storage_record") else "signup"
    )

# ============================================================
# SIDEBAR (EXISTING FRONTEND + FUNCTIONAL ACCOUNT NAVIGATION)
# ============================================================

with st.sidebar:
    st.markdown('<div class="sb-logo">parrhet<span class="sb-logo-accent">.ai</span></div>', unsafe_allow_html=True)

    # ── Navigation ────────────────────────────────────────────────────────
    st.markdown('<div class="sb-label">Navigate</div>', unsafe_allow_html=True)

    home_cls = "nav-btn-active" if st.session_state.page == "home" else "nav-btn"
    chat_cls = "nav-btn-active" if st.session_state.page == "chat" else "nav-btn"

    st.markdown(f'<div class="{home_cls}">', unsafe_allow_html=True)
    if st.button("Home", use_container_width=True, key="nav_home"):
        navigate_to("home")
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown(f'<div class="{chat_cls}">', unsafe_allow_html=True)
    if st.button("Chat", use_container_width=True, key="nav_chat"):
        if st.session_state.user_account:
            navigate_to("chat")
        else:
            navigate_to("signup")
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    # ── New conversation button ───────────────────────────────────────────
    st.markdown('<div class="sb-label">Session</div>', unsafe_allow_html=True)
    st.markdown('<div class="nb">', unsafe_allow_html=True)
    if st.button("+ New conversation", use_container_width=True, key="new_conversation"):
        if not st.session_state.user_account:
            navigate_to("signup")
        else:
            save_current_conversation()

            st.session_state.messages = []
            st.session_state.orchestrator = MasterOrchestrator()
            st.session_state.next_target = ""
            st.session_state.conversation_id = str(uuid.uuid4())

            # New conversation = allow one new progress session count
            st.session_state.progress_session_counted = False

            navigate_to("chat")
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Existing learner settings ─────────────────────────────────────────
    st.markdown('<div class="sb-label">Settings</div>', unsafe_allow_html=True)

    native_language = st.selectbox(
        "Native language",
        ["English", "Hindi", "French", "Spanish", "German"],
        index=0,
        key="native_language"
    )

    target_language = st.selectbox(
        "Learning",
        ["Spanish", "English", "French", "German", "Japanese", "Hindi"],
        index=0,
        key="target_language"
    )

    proficiency_level = st.selectbox(
        "Level",
        ["A1", "A2", "B1", "B2", "C1", "C2"],
        index=0,
        key="proficiency_level"
    )

    # ── Recent ────────────────────────────────────────────────────────────
    st.markdown('<div class="sb-label">Recent</div>', unsafe_allow_html=True)

    if not st.session_state.chat_history:
        st.markdown(
            '<div class="sb-card"><div class="sb-card-title">No conversations yet</div>'
            '<div class="sb-card-meta">Start chatting to build your history</div></div>',
            unsafe_allow_html=True
        )
    else:
        for item in st.session_state.chat_history[:8]:
            conversation_id = item.get("id", str(uuid.uuid4()))
            title = item.get("title", "Conversation")
            if st.button(
                title,
                key=f"history_{conversation_id}",
                use_container_width=True
            ):
                if not st.session_state.user_account:
                    navigate_to("signup")
                else:
                    navigate_to("chat", pending_history=item)
                st.rerun()

    # ── Account ───────────────────────────────────────────────────────────
    st.markdown('<div class="sb-label">Account</div>', unsafe_allow_html=True)

    if st.session_state.user_account:
        if st.button("Profile", use_container_width=True, key="account_profile"):
            navigate_to("profile")
            st.rerun()
    else:
        if st.session_state.get("account_storage_record"):
            if st.button("Sign in", use_container_width=True, key="account_signin"):
                navigate_to("signin")
                st.rerun()
            if st.button("Sign up", use_container_width=True, key="account_signup"):
                navigate_to("signup")
                st.rerun()
        else:
            if st.button("Sign up", use_container_width=True, key="account_signup"):
                navigate_to("signup")
                st.rerun()

    if st.button("Settings", use_container_width=True, key="account_settings"):
        navigate_to("settings")
        st.rerun()

# ============================================================
# TOPBAR
# ============================================================

_page_labels = {
    "home": "Dashboard",
    "chat": "Conversation",
    "settings": "Settings",
    "profile": "Profile",
    "signup": "Sign up",
    "signin": "Sign in",
}
_page_label = _page_labels.get(st.session_state.page, "Dashboard")
st.markdown(f"""
<div class="topbar">
  <div class="topbar-left">
    <span class="topbar-title">parrhet.ai</span>
    <span class="topbar-divider"></span>
    <span class="topbar-sub">{_page_label}</span>
  </div>
  <div class="topbar-pill"><span class="blink"></span>Ready</div>
</div>
""", unsafe_allow_html=True)

# ============================================================
# PAGE ROUTER
# ============================================================

if st.session_state.page == "home":

    # ── DASHBOARD ────────────────────────────────────────────────────────
    st.markdown('<div class="dash-wrap">', unsafe_allow_html=True)

    tl = st.session_state.get("target_language", "Spanish")
    lvl = st.session_state.get("proficiency_level", "A1")
    flag = get_language_flag(tl)
    progress = load_user_progress() or {}

    total_sessions = progress.get(
        "total_sessions",
        0
    )

    langs_tried = len(
        progress.get("languages_practiced", [])
    ) or 1

    current_streak = progress.get(
        "current_streak",
        0
    )

    # Olive hero band
    st.markdown(f"""
    <div class="olive-band">
      <div class="olive-band-text">
        <div class="olive-band-title">Ready to practise, linguist?</div>
        <div class="olive-band-sub">
          Youre studying {tl} at level {lvl}.<br>
          Jump into a conversation and Rhet will guide you.
        </div>
      </div>
      <div class="olive-band-lang">{flag}</div>
    </div>
    """, unsafe_allow_html=True)

    # Stats row
    st.markdown(f"""
    <div class="stats-row">
      <div class="stat-card">
        <div class="stat-value">{total_sessions}</div>
        <div class="stat-label">Sessions</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{langs_tried}</div>
        <div class="stat-label">Languages</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{lvl}</div>
        <div class="stat-label">Current Level</div>
      </div>
      <div class="stat-card accent">
        <div class="stat-value" style="font-size:20px;letter-spacing:0">
            {current_streak}
        </div>
        <div class="stat-label">Keep It Up</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # Recent sessions
    if st.session_state.chat_history:
        recent = st.session_state.chat_history[:4]
        st.markdown('<div class="dash-section-title">Recent Sessions</div>', unsafe_allow_html=True)
        st.markdown('<div class="recents-grid">', unsafe_allow_html=True)
        for idx, item in enumerate(recent):
            rlang = item.get("target_language", "Spanish")
            rlvl = item.get("level", "")
            rtitle = item.get("title", "Conversation")[:38]
            conversation_id = item.get("id", str(uuid.uuid4()))
            if st.button(
                f"{get_language_flag(rlang)}  {rtitle}  ·  {rlang} {rlvl}",
                key=f"dashboard_history_{conversation_id}_{idx}",
                use_container_width=True
            ):
                if not st.session_state.user_account:
                    navigate_to("signup")
                else:
                    navigate_to("chat", pending_history=item)
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)


    st.markdown('</div>', unsafe_allow_html=True)

elif st.session_state.page == "settings":

    # ── SETTINGS PAGE ───────────────────────────────────────────────────
    st.markdown('<div class="dash-wrap">', unsafe_allow_html=True)
    st.markdown('<div class="dash-section-title">Settings & learning preferences</div>', unsafe_allow_html=True)

    st.markdown(
        """<div class="olive-band">
          <div class="olive-band-text">
            <div class="olive-band-title">Make Rhet fit your learning.</div>
            <div class="olive-band-sub">Control what you practise, how long you practise, and how Rhet coaches you. Everything is saved locally in this browser.</div>
          </div>
          <div class="olive-band-lang">⚙️</div>
        </div>""", unsafe_allow_html=True
    )

    languages_native = ["English", "Hindi", "French", "Spanish", "German"]
    languages_target = ["Spanish", "English", "French", "German", "Japanese", "Hindi"]
    levels = ["A1", "A2", "B1", "B2", "C1", "C2"]

    st.markdown("### Language")
    settings_native = st.selectbox(
        "Native language", languages_native,
        index=languages_native.index(st.session_state.get("native_language", "English")),
        key="settings_native_language"
    )
    settings_target = st.selectbox(
        "Learning language", languages_target,
        index=languages_target.index(st.session_state.get("target_language", "Spanish")),
        key="settings_target_language"
    )
    settings_level = st.selectbox(
        "Proficiency level", levels,
        index=levels.index(st.session_state.get("proficiency_level", "A1")),
        key="settings_proficiency_level"
    )

    st.markdown("### Practice")
    settings_daily_goal = st.select_slider(
        "Daily practice goal (minutes)", options=[5, 10, 15, 20, 30, 45, 60],
        value=st.session_state.get("daily_goal", 10), key="settings_daily_goal"
    )
    settings_session_length = st.selectbox(
        "Preferred session length", ["5 minutes", "10 minutes", "15 minutes", "20 minutes", "30 minutes"],
        index=["5 minutes", "10 minutes", "15 minutes", "20 minutes", "30 minutes"].index(
            st.session_state.get("session_length", "10 minutes")
        ), key="settings_session_length"
    )

    st.markdown("### Coaching")
    settings_correction = st.radio(
        "Correction style", ["Gentle", "Balanced", "Detailed"], horizontal=True,
        index=["Gentle", "Balanced", "Detailed"].index(
            st.session_state.get("correction_style", "Balanced")
        ), key="settings_correction_style"
    )
    settings_translation = st.toggle(
        "Show native-language translations",
        value=st.session_state.get("show_translations", True),
        key="settings_show_translations"
    )
    settings_pronunciation = st.toggle(
        "Show pronunciation feedback",
        value=st.session_state.get("pronunciation_feedback", True),
        key="settings_pronunciation_feedback"
    )
    settings_autoplay = st.toggle(
        "Auto-play Rhet audio when available",
        value=st.session_state.get("auto_play_audio", True),
        key="settings_auto_play_audio"
    )

    if st.button("Save settings", use_container_width=True, key="save_settings_page"):
        st.session_state.native_language = settings_native
        st.session_state.target_language = settings_target
        st.session_state.proficiency_level = settings_level
        st.session_state.daily_goal = settings_daily_goal
        st.session_state.session_length = settings_session_length
        st.session_state.correction_style = settings_correction
        st.session_state.show_translations = settings_translation
        st.session_state.pronunciation_feedback = settings_pronunciation
        st.session_state.auto_play_audio = settings_autoplay
        save_user_settings()
        st.success("Settings saved locally.")

    if st.button("Back to home", use_container_width=True, key="settings_home"):
        navigate_to("home")
        st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

elif st.session_state.page == "signin":

    # ── SIGN IN PAGE ───────────────────────────────────────────────────
    st.markdown('<div class="dash-wrap">', unsafe_allow_html=True)
    st.markdown('<div class="dash-section-title">Welcome back</div>', unsafe_allow_html=True)

    st.markdown(
        """<div class="olive-band">
          <div class="olive-band-text">
            <div class="olive-band-title">Sign back in to parrhet.ai.</div>
            <div class="olive-band-sub">Your local account is stored in this browser. Sign in with the same email you used when creating it.</div>
          </div>
          <div class="olive-band-lang">🦜</div>
        </div>""",
        unsafe_allow_html=True
    )

    with st.form("signin_form", clear_on_submit=False):
        signin_email = st.text_input(
            "Email",
            value="",
            placeholder="you@example.com"
        )
        signin_submit = st.form_submit_button(
            "Sign in",
            use_container_width=True
        )

    if signin_submit:
        clean_email = signin_email.strip()
        if not clean_email or "@" not in clean_email:
            st.error("Please enter the email used for this local account.")
        else:
            ok, message = sign_in_user(clean_email)
            if ok:
                navigate_to("home")
                st.rerun()
            else:
                st.error(message)

    if st.session_state.get("account_storage_record"):
        if st.button("Create a different local account", use_container_width=True, key="signin_signup"):
            clear_user_account()
            navigate_to("signup")
            st.rerun()
    else:
        if st.button("Create account", use_container_width=True, key="signin_create"):
            navigate_to("signup")
            st.rerun()

    if st.button("Back to home", use_container_width=True, key="signin_home"):
        navigate_to("home")
        st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

elif st.session_state.page == "signup":

    # ── SIGNUP PAGE ─────────────────────────────────────────────────────
    st.markdown('<div class="dash-wrap">', unsafe_allow_html=True)
    st.markdown('<div class="dash-section-title">Create your local account</div>', unsafe_allow_html=True)

    st.markdown(
        """<div class="olive-band">
          <div class="olive-band-text">
            <div class="olive-band-title">Welcome to parrhet.ai.</div>
            <div class="olive-band-sub">Create your learner profile. For now, the information stays in this browser's local storage.</div>
          </div>
          <div class="olive-band-lang">🦜</div>
        </div>""",
        unsafe_allow_html=True
    )

    with st.form("signup_form", clear_on_submit=False):
        signup_name = st.text_input("Full name", value="", placeholder="Your name")
        signup_email = st.text_input("Email", value="", placeholder="you@example.com")
        st.caption("You can choose your languages and learning preferences later in Settings.")
        signup_submit = st.form_submit_button("Create account", use_container_width=True)

    if signup_submit:
        clean_name = signup_name.strip()
        clean_email = signup_email.strip()

        if not clean_name:
            st.error("Please enter your name.")
        elif not clean_email or "@" not in clean_email:
            st.error("Please enter a valid email address.")
        else:
            account = {
                "id": str(uuid.uuid4()),
                "name": clean_name,
                "email": clean_email,
                "created_at": datetime.now().isoformat(),
            }

            if save_user_account(account):
                navigate_to("profile")
                st.rerun()

    if st.session_state.get("account_storage_record"):
        st.info("A local account already exists in this browser. Sign in instead, or create a different local account from the Sign in page.")
        if st.button("Go to sign in", use_container_width=True, key="signup_to_signin"):
            navigate_to("signin")
            st.rerun()

    if st.button("Back to home", use_container_width=True, key="signup_home"):
        navigate_to("home")
        st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

elif st.session_state.page == "profile":

    # ── PROFILE PAGE ────────────────────────────────────────────────────
    account = st.session_state.get("user_account") or {}

    if not account:
        st.session_state.page = "signup"
        st.rerun()

    st.markdown('<div class="dash-wrap">', unsafe_allow_html=True)
    st.markdown('<div class="dash-section-title">Your learner profile</div>', unsafe_allow_html=True)

    st.markdown(
        f"""<div class="olive-band">
          <div class="olive-band-text">
            <div class="olive-band-title">Hello, {account.get('name', 'Learner')}.</div>
            <div class="olive-band-sub">{account.get('email', '')}<br>Your learning preferences are managed in Settings.</div>
          </div>
          <div class="olive-band-lang">🦜</div>
        </div>""",
        unsafe_allow_html=True
    )

    st.markdown(f"**Name:** {account.get('name', '')}")
    st.markdown(f"**Email:** {account.get('email', '')}")
    st.markdown("**Learning preferences:** Configure your native language, learning language, level, and practice preferences in Settings.")

    if st.button("Sign out", use_container_width=True, key="profile_signout"):
        sign_out_user()
        navigate_to("home")
        st.rerun()

    if st.button("Go to settings", use_container_width=True, key="profile_settings"):
        navigate_to("settings")
        st.rerun()

    if st.button("Back to home", use_container_width=True, key="profile_home"):
        navigate_to("home")
        st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

else:

    # ── CHAT PAGE ────────────────────────────────────────────────────────
    st.markdown('<div class="chat-wrap">', unsafe_allow_html=True)

    # ── Quick start (shown when no messages) ────────────────────────────
    if len(st.session_state.messages) == 0:
        tl_qs = st.session_state.get("target_language", "Spanish")
        st.markdown(f"""
        <div class="qs-wrap">
          <div class="qs-title">Start a conversation</div>
          <div class="qs-sub">Type or speak in any language. Rhet will respond, coach your pronunciation, and guide the lesson.</div>
          <div class="qs-row">
            <span class="qchip">Practice {tl_qs} basics</span>
            <span class="qchip">Order food in Paris</span>
            <span class="qchip">Hiragana and Katakana</span>
            <span class="qchip coral">Explain past tense</span>
            <span class="qchip coral">Check my pronunciation</span>
          </div>
        </div>
        """, unsafe_allow_html=True)

    # Display messages
    for message in st.session_state.messages:

        with st.chat_message(message["role"]):

            # ------------------------------------------------
            # USER MESSAGE
            # ------------------------------------------------
            if message["role"] == "user":
                st.write(message["content"])
                continue

            # ------------------------------------------------
            # STRUCTURED RHET RESPONSE
            # ------------------------------------------------
            result = message["content"]

            result = normalize_result_language_fields(result)

            # ── Learning-language text
            learning_text = result.get("learning_language_text", "")
            if learning_text:
                st.markdown(
                    f'<div class="rhet-label">Rhet · {target_language}</div>'
                    f'<div class="rhet-response">{learning_text}</div>',
                    unsafe_allow_html=True
                )

            # ── Native-language translation
            native_text = result.get("native_language_text", "")
            if native_text:
                st.markdown(
                    f'<div class="translation-text">↳ {native_language}: {native_text}</div>',
                    unsafe_allow_html=True
                )

            # ── Transcript / speech-to-text result
            transcript = result.get("transcript", "")

            if transcript:
                st.caption(f"🎙️ You said: {transcript}")

            # ── Pronunciation scores
            scores = result.get("pronunciation_scores")

            if scores:
                pron = scores.get("pronunciation_score", 0)
                acc = scores.get("accuracy_score", 0)
                flu = scores.get("fluency_score", 0)
                comp = scores.get("completeness_score", 0)

                st.markdown(
                    f"""
                    <div class="score-row">
                      <div class="score-badge">{pron:.0f}<span>Pronunciation</span></div>
                      <div class="score-badge">{acc:.0f}<span>Accuracy</span></div>
                      <div class="score-badge">{flu:.0f}<span>Fluency</span></div>
                      <div class="score-badge">{comp:.0f}<span>Complete</span></div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            # ── Pronunciation guide
            pronunciation = result.get("pronunciation", "")

            if pronunciation:
                st.markdown(
                    f'<div class="translation-text">🔊 {pronunciation}</div>',
                    unsafe_allow_html=True
                )

            # ── Pronunciation audio
            pronunciation_audio_path = result.get(
                "pronunciation_audio_path"
            )

            if (
                pronunciation_audio_path
                and os.path.exists(pronunciation_audio_path)
            ):
                st.caption("🔊 Listen to Rhet")
                st.audio(
                    pronunciation_audio_path,
                    format="audio/wav"
                )

            # ── Pedagogical feedback
            feedback = result.get("pedagogical_feedback", "")

            if feedback:
                st.markdown(
                    f'<div class="feedback-box">{feedback}</div>',
                    unsafe_allow_html=True
                )

            # ── Practice target
            next_target = result.get(
                "suggested_next_target",
                ""
            ) or ""

            if next_target:
                st.markdown(
                    f'<div class="next-target">'
                    f'<span class="next-target-label">Try&nbsp;saying</span>'
                    f'{next_target}</div>',
                    unsafe_allow_html=True
                )

            # ── Target audio / Listen to it
            target_audio_path = ensure_target_audio(result, target_language)

            if target_audio_path and os.path.exists(target_audio_path):
                st.caption("🔊 Listen to it")
                st.audio(
                    target_audio_path,
                    format="audio/wav"
                )

    st.markdown('</div>', unsafe_allow_html=True)

    # ============================================================
    # CHAT INPUT — TEXT + VOICE
    # ============================================================

    submission = st.chat_input(
        "Speak or message in any language...",
        key="chat_input",
        accept_audio=True,
        audio_sample_rate=16000,
        on_submit=mark_chat_submission,
    )

    # ============================================================
    # HANDLE TEXT + VOICE SUBMISSION
    # ============================================================

    if submission is not None:

        # The request itself owns the loader now; never show the full-page
        # navigation overlay during text or voice processing.
        st.session_state.navigation_loading = False

        # --------------------------------------------------------
        # GET TEXT + AUDIO FROM THE SAME CHAT INPUT
        # --------------------------------------------------------
        text_input = (
            submission.text.strip()
            if submission.text
            else ""
        )

        audio_input = submission.audio

        # Keep the user's existing page behavior:
        # any actual input means we are in the conversation page.
        st.session_state.page = "chat"

        # --------------------------------------------------------
        # DO NOT ACCEPT TEXT + AUDIO IN THE SAME TURN
        # --------------------------------------------------------
        if text_input and audio_input is not None:

            st.warning(
                "Please use either text or voice for one turn."
            )
            st.session_state.chat_request_pending = False
            st.stop()

        # ========================================================
        # TEXT MODE
        # ========================================================

        elif text_input:

            # Store learner message
            st.session_state.messages.append({
                "role": "user",
                "content": text_input
            })

            try:
                # Existing Foundry agent functionality
                agent = get_foundry_agent()

                learner_signal = {
                    "transcript": text_input,
                    "detected_language": native_language,
                    "target_language": target_language,
                    "native_language": native_language,
                    "proficiency_level": proficiency_level,
                    "pronunciation_scores": None,
                    "language_analysis": {},
                }

                with processing_loader("Rhet is thinking…", "Generating your lesson response"):
                    result = agent.generate_tutor_turn(
                        learner_signal
                    )

                # Rhet's suggested next target becomes the
                # reference sentence for the next voice turn.
                st.session_state.next_target = (
                    result.get(
                        "suggested_next_target",
                        ""
                    ) or ""
                )

                next_target = result.get(
                    "suggested_next_target",
                    ""
                ) or ""

                # Existing Azure Speech TTS functionality:
                # audio for the suggested practice target.
                with processing_loader("Preparing pronunciation audio…", "Creating your practice clip"):
                    target_audio = generate_pronunciation_audio(
                        next_target,
                        target_language
                    )

                result["target_audio_path"] = target_audio

                # Existing Azure Speech TTS functionality:
                # audio for Rhet's conversational response.
                target_text = result.get(
                    "conversational_reply",
                    ""
                )

                with processing_loader("Preparing Rhet audio…", "Getting Rhet's voice ready"):
                    pronunciation_audio = generate_pronunciation_audio(
                        target_text,
                        target_language
                    )

                result["pronunciation_audio_path"] = (
                    pronunciation_audio
                )

                # Store complete structured response
                normalize_result_language_fields(result)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": result
                })

                # Persist the complete conversation
                save_current_conversation()

            except Exception as e:

                error_result = {
                    "conversational_reply":
                        "Sorry, I couldn't process that message.",
                    "translation": "",
                    "pedagogical_feedback": "",
                    "explanation": "",
                    "suggested_next_target": "",
                    "error": str(e),
                }

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error_result
                })

                save_current_conversation()

        # ========================================================
        # VOICE MODE
        # ========================================================

        elif audio_input is not None:

            import tempfile

            temp_fd, temp_path = tempfile.mkstemp(
                suffix=".wav"
            )
            os.close(temp_fd)

            try:

                # ------------------------------------------------
                # SAVE THE BROWSER RECORDING
                # ------------------------------------------------
                with open(temp_path, "wb") as f:
                    f.write(audio_input.getvalue())

                # ------------------------------------------------
                # UI LANGUAGE → AZURE SPEECH LOCALE
                # ------------------------------------------------
                speech_language_codes = {
                    "Spanish": "es-ES",
                    "English": "en-US",
                    "French": "fr-FR",
                    "German": "de-DE",
                    "Japanese": "ja-JP",
                    "Hindi": "hi-IN",
                }

                speech_language = (
                    speech_language_codes.get(
                        target_language,
                        "en-US"
                    )
                )

                # ------------------------------------------------
                # PREVIOUS RHET SUGGESTION =
                # REFERENCE SENTENCE FOR PRONUNCIATION
                # ------------------------------------------------
                reference_text = (
                    st.session_state.next_target.strip()
                    if st.session_state.next_target
                    else None
                )

                # ------------------------------------------------
                # BUILD EXISTING BACKEND INPUT
                # ------------------------------------------------
                turn_input = LearnerTurnInput(
                    user_id="user_123",
                    target_language=speech_language,
                    target_sentence=reference_text,
                    audio_path=temp_path,
                    target_gloss_language="en",
                )

                # ------------------------------------------------
                # SEND THE SAME WAV TO THE EXISTING ORCHESTRATOR
                # ------------------------------------------------
                with processing_loader("Rhet is analyzing your speech…", "Checking your pronunciation and response"):
                    response = (
                        st.session_state
                        .orchestrator
                        .process_turn(turn_input)
                    )

                # ------------------------------------------------
                # READ BACKEND RESPONSE
                # ------------------------------------------------
                transcript = getattr(
                    response,
                    "transcript",
                    ""
                )

                pronunciation_scores = getattr(
                    response,
                    "pronunciation_scores",
                    None
                )

                feedback = getattr(
                    response,
                    "feedback",
                    ""
                )

                native_gloss = getattr(
                    response,
                    "native_gloss",
                    ""
                )

                next_prompt = getattr(
                    response,
                    "next_prompt",
                    ""
                )

                tutor_audio_path = getattr(
                    response,
                    "tutor_audio_path",
                    None
                )

                learning_response_text = (next_prompt or "").strip()
                native_response_text = (native_gloss or "").strip()

                # Every voice response gets a playable practice-target clip.
                if learning_response_text:
                    with processing_loader("Preparing your pronunciation example…", "Creating the sentence for you to repeat"):
                        target_audio_path = generate_pronunciation_audio(
                            learning_response_text,
                            target_language
                        )
                else:
                    target_audio_path = None

                # ------------------------------------------------
                # STORE LEARNER'S SPOKEN MESSAGE
                # ------------------------------------------------
                if transcript:

                    st.session_state.messages.append({
                        "role": "user",
                        "content": f"🎙️ {transcript}"
                    })

                # ------------------------------------------------
                # STORE STRUCTURED RHET RESPONSE
                # ------------------------------------------------
                assistant_result = {
                    "transcript": transcript,
                    "pronunciation_scores":
                        pronunciation_scores,
                    "pedagogical_feedback":
                        feedback,
                    "translation":
                        native_gloss,
                    "native_gloss":
                        native_gloss,
                    "learning_language_text":
                        learning_response_text,
                    "native_language_text":
                        native_response_text,
                    "conversational_reply":
                        next_prompt,
                    "suggested_next_target":
                        next_prompt,
                    "tutor_audio_path":
                        tutor_audio_path,
                    "target_audio_path":
                        target_audio_path,
                }

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": assistant_result
                })

                # ------------------------------------------------
                # NEW TARGET FOR THE NEXT VOICE TURN
                # ------------------------------------------------
                st.session_state.next_target = (
                    next_prompt or ""
                )

                save_current_conversation()

            except Exception as e:

                st.error(
                    f"Voice processing failed: {e}"
                )

            finally:

                if os.path.exists(temp_path):
                    os.remove(temp_path)

        # Re-render exactly once after processing the turn.
        st.session_state.chat_request_pending = False
        st.rerun()
