from app.api.approvals import router as approvals_router
from app.api.auth import router as auth_router
from app.api.analysis import router as analysis_router
from app.api.knowledge import router as knowledge_router
from app.api.retrieval import router as retrieval_router
from app.api.tickets import router as tickets_router
from app.api.users import router as users_router

__all__ = ["analysis_router", "approvals_router", "auth_router", "knowledge_router", "retrieval_router", "tickets_router", "users_router"]
