# Import all models to ensure they are registered with SQLAlchemy
from .user import User
from .share import ShareEvent

# Import feedback model if it exists
try:
    from .feedback import Feedback
    __all__ = ["User", "ShareEvent", "Feedback"]
except ImportError:
    __all__ = ["User", "ShareEvent"]