"""Modele SQLAlchemy.

Importujemy każdy model na poziomie pakietu, żeby Alembic/`flask db migrate`
widział je wszystkie podczas autogenerowania migracji.
"""

from .animal import Animal
from .conversation import Conversation
from .farm import Farm
from .favorite import Favorite
from .message import Message
from .notification import Notification
from .user import User

__all__ = [
    "Animal",
    "Conversation",
    "Farm",
    "Favorite",
    "Message",
    "Notification",
    "User",
]
