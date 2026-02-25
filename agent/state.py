from typing import TypedDict, Optional
from langchain_core.messages import BaseMessage


class AgentState(TypedDict):
    # Conversation
    messages: list[BaseMessage]
    user_query: str
    query_type: str

    # Portfolio context (populated by portfolio_analysis tool)
    portfolio_snapshot: dict

    # Tool execution tracking
    tool_results: list[dict]

    # Verification layer
    pending_verifications: list[dict]
    confidence_score: float
    verification_outcome: str

    # Human-in-the-loop (read)
    awaiting_confirmation: bool
    confirmation_payload: Optional[dict]

    # Human-in-the-loop (write) — write intent waiting for user yes/no
    # pending_write holds the fully-built activity payload ready to POST.
    # confirmation_message is the plain-English summary shown to the user.
    # missing_fields lists what the agent still needs from the user before it
    # can build a payload (e.g. "quantity", "price").
    pending_write: Optional[dict]
    confirmation_message: Optional[str]
    missing_fields: list[str]

    # Per-request user auth — passed in from the Angular app.
    # When present, overrides GHOSTFOLIO_BEARER_TOKEN env var so the agent
    # operates on the logged-in user's own portfolio data.
    bearer_token: Optional[str]

    # Response
    final_response: Optional[str]
    citations: list[str]
    error: Optional[str]
