from datetime import datetime, timedelta
import jwt
from app.config import setting
def create_access_token(user_id: int) ->str :
    expire = datetime.now() + timedelta(setting.JWT_EXPIRE_HOURS)
    payload = {"user_id": user_id, "exp": expire}
    return jwt.encode(payload, setting.JWT_SECRET_KEY, algorithm=setting.JWT_ALGORITHM)

def decode_access_token(token: str):
    return jwt.decode(token, setting.JWT_SECRET_KEY, algorithms=setting.JWT_ALGORITHM)