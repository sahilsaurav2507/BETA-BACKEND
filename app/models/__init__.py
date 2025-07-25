# Import all models to ensure they are registered with SQLAlchemy
from .user import User
from .share import ShareEvent

# Import feedback model if it exists
try:
    from .feedback import Feedback
    feedback_available = True
except ImportError:
    feedback_available = False

# Import email queue model
try:
    from .email_queue import EmailQueue, EmailType, EmailStatus
    email_queue_available = True
except ImportError:
    email_queue_available = False

# Build __all__ list dynamically
__all__ = ["User", "ShareEvent"]

if feedback_available:
    from .feedback import Feedback
    __all__.append("Feedback")

if email_queue_available:
    from .email_queue import EmailQueue, EmailType, EmailStatus
    __all__.extend(["EmailQueue", "EmailType", "EmailStatus"])