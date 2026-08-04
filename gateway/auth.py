from jose import jwt
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()

JWT_SECRET = os.getenv("JWT_SECRET")

def create_token(user_id, role):
    token = jwt.encode({"user_id": user_id, "role": role, "exp": datetime.utcnow() + timedelta(hours=8)}, JWT_SECRET, algorithm="HS256")
    return token

def verify_token(token):
    payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    return payload