# Database

parrhet.ai uses **Azure Cosmos DB for NoSQL** as its cloud persistence layer.

---

## Important distinction: authentication ≠ database

Cosmos DB stores **application data** — profiles, conversations, progress.
It does not handle authentication.

Authentication is handled by:
- Streamlit's built-in OAuth (`st.login` / `st.user`) for Google sign-in
- Email OTP (code generated in Python, sent by SendGrid/SMTP, verified in-session)

The Cosmos `users` container stores the **learner profile** after
authentication succeeds. It is not queried to verify identity — it is
queried to load settings and history.

---

## Database structure

```
Azure Cosmos DB account
└── rhet_db (database)
    ├── users          (partition key: /user_id)
    ├── conversations  (partition key: /user_id)
    └── progress       (partition key: /user_id)
```

All three containers use `/user_id` as the partition key. This means
every read, write, and delete for a given learner is scoped to a
single logical partition — efficient and secure by design.

---

## `users` container

**Purpose:** Stores learner profiles and learning preferences.
One document per user.

**Partition key:** `/user_id`

**Schema:**

```json
{
  "id": "3f7a1c2e-...",
  "user_id": "3f7a1c2e-...",
  "name": "Priya Sharma",
  "email": "priya@example.com",
  "google_id": "108234567890",
  "email_verified": true,
  "created_at": "2025-10-08T14:23:00.000Z",
  "native_language": "English",
  "target_language": "Spanish",
  "proficiency_level": "A1",
  "daily_goal": 10,
  "session_length": "10 minutes",
  "correction_style": "Balanced",
  "show_translations": true,
  "pronunciation_feedback": true,
  "auto_play_audio": true
}
```

**Notes:**
- `id` and `user_id` hold the same UUID value. Cosmos requires `id`; the
  application uses `user_id` as the logical key.
- `google_id` is present only for accounts created via Google OAuth.
  It is backfilled on first Google sign-in for existing email accounts.
- `email_verified` is set `true` after OTP verification or Google sign-in.
- Older accounts created before `user_id` was standardised may have
  `id` but not `user_id`. `_complete_email_signin()` handles this with
  `cosmos_user.get("user_id") or cosmos_user["id"]`.

**CRUD:**

| Operation | Method | Called from |
|---|---|---|
| Create / update | `CosmosService.save_user()` | `save_user_account()`, `sign_in_with_google_user()`, `save_user_settings()` |
| Read by ID | `CosmosService.get_user()` | Cosmos data load on sign-in |
| Read by email | `CosmosService.get_user_by_email()` | `request_signin_otp()`, sign-up duplicate check |
| Read by Google ID | `CosmosService.get_user_by_google_id()` | `sign_in_with_google_user()` |

---

## `conversations` container

**Purpose:** Stores complete conversation histories per user.
One document per conversation.

**Partition key:** `/user_id`

**Schema:**

```json
{
  "id": "conv-8a2b4c...",
  "user_id": "3f7a1c2e-...",
  "title": "Spanish practice at the market",
  "flag": "🇪🇸",
  "native_language": "English",
  "target_language": "Spanish",
  "level": "A1",
  "created_at": "2025-10-08T14:25:00.000Z",
  "updated_at": "2025-10-08T14:52:00.000Z",
  "messages": [
    {
      "role": "user",
      "content": "Quiero comprar manzanas."
    },
    {
      "role": "assistant",
      "content": {
        "conversational_reply": "¡Buena elección!",
        "translation": "Good choice!",
        "pedagogical_feedback": "Good sentence structure.",
        "suggested_next_target": "¿Cuánto cuestan las manzanas?",
        "pronunciation_scores": { "accuracy_score": 87.3, "fluency_score": 82.1, "completeness_score": 100.0, "pronunciation_score": 85.0, "prosody_score": 78.4 },
        "target_audio_path": null,
        "tutor_audio_path": null
      }
    }
  ]
}
```

**Notes:**
- `messages` stores the full conversation as a list of `{role, content}` dicts,
  mirroring Streamlit's `st.chat_message` structure.
- `updated_at` is set on every `upsert_item` call.
- Audio file paths (`target_audio_path`, `tutor_audio_path`) are temp file
  paths valid only during the session — they are stored in the document
  but will be `null` or stale after the session ends.
- The UI caps history at **20 conversations** per user.

**CRUD:**

| Operation | Method | Called from |
|---|---|---|
| Create / update | `CosmosService.save_conversation()` | `save_current_conversation()` |
| Read one | `CosmosService.get_conversation()` | `load_conversation_from_cosmos()` |
| Read all for user | `CosmosService.get_user_conversations()` | `load_user_conversations()` |

---

## `progress` container

**Purpose:** Tracks aggregate learning statistics per user.
One document per user.

**Partition key:** `/user_id`

**Document ID format:** `progress_{user_id}`

**Schema:**

```json
{
  "id": "progress_3f7a1c2e-...",
  "user_id": "3f7a1c2e-...",
  "total_sessions": 12,
  "total_messages": 48,
  "languages_practiced": ["Spanish", "French"],
  "last_practice_date": "2025-10-08",
  "current_streak": 3,
  "longest_streak": 7,
  "updated_at": "2025-10-08T14:52:00.000Z"
}
```

**Notes:**
- `total_sessions` increments once per conversation (guarded by
  `progress_session_counted` session state flag).
- `total_messages` is the count of user-role messages in the current
  conversation — it reflects the current session, not a cumulative total.
- `current_streak` and `longest_streak` are tracked but the streak
  increment logic is not yet implemented. *(🟡 in progress)*

**CRUD:**

| Operation | Method | Called from |
|---|---|---|
| Create / update | `CosmosService.save_progress()` | `update_user_progress()` |
| Read | `CosmosService.get_progress()` | `load_user_progress()` |

---

## Current state vs planned

| Capability | Status |
|---|---|
| User profile creation and retrieval | ✅ |
| Conversation save and load | ✅ |
| Progress tracking (sessions, messages, languages) | ✅ |
| Streak tracking | 🟡 Tracked, not yet incremented |
| Cross-device sync (Cosmos as source of truth) | ✅ |
| localStorage offline fallback | ✅ |
| Google ID backfill on first OAuth login | ✅ |
| Knowledge base content (Azure AI Search) | 🔮 Planned |

---

## Authentication architecture note

The current system uses email OTP and Google OAuth for identity
verification. The Cosmos `users` container stores the profile **after**
authentication succeeds — it does not store passwords, OTP codes, or
session tokens.

OTP codes are stored **in Streamlit session state only** (not Cosmos)
for the duration of the verification flow, then discarded.

For a production multi-tenant deployment, consider replacing the current
email-based identity with **Azure Entra ID** (formerly Azure AD) or
another managed identity provider. The `user_id` field in all three
containers would then be the identity provider's stable subject ID.
