"""Rozszerzenia Flaska w jednym miejscu.

Trzymamy je z dala od fabryki, żeby modele i inne moduły mogły je importować
bez ryzyka cyklicznych zależności.
"""

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_socketio import SocketIO
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()
# async_mode="gevent" zgodne z workerem gunicorna na AGH lab (Lab 8).
socketio = SocketIO(async_mode="gevent", cors_allowed_origins=[])
# Rate limiting — Lab 9. Domyślny limit chroni przed łatwymi DoS-ami.
limiter = Limiter(key_func=get_remote_address, default_limits=["1000 per day", "200 per hour"])
