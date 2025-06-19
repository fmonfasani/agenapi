import jwt
import bcrypt
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from ..core.models import User, Permission

class SecurityManager:
    def __init__(self, secret_key: str = "your-secret-key-change-this"):
        self.secret_key = secret_key
        self.algorithm = "HS256"
        self.access_token_expire_minutes = 30
        self._users: Dict[str, User] = {}
        self._setup_default_users()

    def _setup_default_users(self):
        admin_user = User(
            id="admin",
            username="admin",
            permissions=[Permission.READ, Permission.WRITE, Permission.EXECUTE, Permission.ADMIN]
        )
        self._users["admin"] = admin_user

    def create_access_token(self, data: Dict[str, Any]) -> str:
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)

    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.PyJWTError:
            return None

    async def authenticate_user(self, username: str, password: str) -> Optional[User]:
        if username == "admin" and password == "admin":
            return self._users.get("admin")
        return None

    def check_permission(self, user: User, required_permission: Permission) -> bool:
        return required_permission in user.permissions or Permission.ADMIN in user.permissions

    def hash_password(self, password: str) -> str:
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def verify_password(self, password: str, hashed: str) -> bool:
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
