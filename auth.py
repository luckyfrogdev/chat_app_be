
from fastapi import HTTPException,Form
from passlib.context import CryptContext
from datetime import datetime, timedelta
import jwt

from models import UserModel

from pymongo import MongoClient

# MongoDB connection settings
MONGODB_URL ="mongodb://root:root@localhost:27017/"
DATABASE_NAME = "chateo"
USER_COLLECTION = "users"


# JWT settings
SECRET_KEY = "50f1c5f3c8d8d5633ca20f62bff5214b433475528d8cbafddd6f102d36ce72b5"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

class AuthHandler:
    def __init__(self):
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.client = MongoClient(MONGODB_URL)
        self.db = self.client[DATABASE_NAME]
        self.collection = self.db[USER_COLLECTION]

    async def get_user_by_email(self, email: str):
        user = self.collection.find_one({"email": email})
        return user

    async def authenticate_user(self, email: str, password: str):
        user = await self.get_user_by_email(email)
        if not user:
            return False
        if not self.verify_password(password, user["password"]):
            return False
        return user

    def verify_password(self, plain_password, hashed_password):
        return self.pwd_context.verify(plain_password, hashed_password)

    def create_access_token(self, data: dict):
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    async def register_user(self, user: UserModel, password_confirmation: str = Form(...)):
        # Check if passwords match
        if user.password != password_confirmation:
             raise HTTPException(status_code=400, detail="Passwords do not match")
        
        hashed_password = self.hash_password(user.password)
        
        user_data = {
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "username": user.username,
            "password": hashed_password,
            "created_at": int(datetime.now().timestamp()),
            "updated_at": int(datetime.now().timestamp()),
            "is_active": False
        }
        
        res = self.collection.insert_one(user_data)
        if res is None:
            return False
        return res
        

    def hash_password(self, password):
        return self.pwd_context.hash(password)
