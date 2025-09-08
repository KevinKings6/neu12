from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime, timedelta
from bson import ObjectId
from jose import JWTError, jwt
from passlib.context import CryptContext


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Auth configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "emergency-sos-secret-key-2025")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")


# Auth Models
class User(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    username: str
    email: str
    full_name: str
    role: str = "user"  # user or admin
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        allow_population_by_field_name = True


class UserCreate(BaseModel):
    username: str
    email: str
    full_name: str
    password: str
    role: str = "user"


class UserLogin(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str
    user: User


# Existing Models
class EmergencyContact(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    user_id: str  # Link to user
    name: str
    phone: str
    relationship: str
    is_primary: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        allow_population_by_field_name = True


class EmergencyContactCreate(BaseModel):
    name: str
    phone: str
    relationship: str
    is_primary: bool = False


class EmergencyContactUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    relationship: Optional[str] = None
    is_primary: Optional[bool] = None


class UserProfile(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    user_id: str  # Link to user
    name: str
    phone: str
    medical_conditions: List[str] = []
    allergies: List[str] = []
    medications: List[str] = []
    blood_type: Optional[str] = None
    emergency_message: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        allow_population_by_field_name = True


class UserProfileCreate(BaseModel):
    name: str
    phone: str
    medical_conditions: List[str] = []
    allergies: List[str] = []
    medications: List[str] = []
    blood_type: Optional[str] = None
    emergency_message: Optional[str] = None


class SOSAlert(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    user_id: str
    location_lat: Optional[float] = None
    location_lng: Optional[float] = None
    location_address: Optional[str] = None
    alert_type: str = "emergency"  # emergency, medical, fire, police
    message: Optional[str] = None
    contacts_notified: List[str] = []
    status: str = "active"  # active, resolved, cancelled
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        allow_population_by_field_name = True


class SOSAlertCreate(BaseModel):
    location_lat: Optional[float] = None
    location_lng: Optional[float] = None
    location_address: Optional[str] = None
    alert_type: str = "emergency"
    message: Optional[str] = None


# News Models
class NewsArticle(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    title: str
    content: str
    author_id: str  # Admin who created it
    author_name: str
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        allow_population_by_field_name = True


class NewsArticleCreate(BaseModel):
    title: str
    content: str


class NewsArticleUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    is_active: Optional[bool] = None


# Chat Models
class ChatMessage(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    user_id: str
    username: str
    message: str
    chat_type: str = "admin"  # admin, voice
    group_id: Optional[str] = None  # For group messages
    is_voice_message: bool = False
    voice_data: Optional[str] = None  # base64 encoded voice data
    voice_duration: Optional[int] = None  # Duration in seconds
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        allow_population_by_field_name = True


class ChatMessageCreate(BaseModel):
    message: str
    chat_type: str = "admin"
    group_id: Optional[str] = None
    is_voice_message: bool = False
    voice_data: Optional[str] = None
    voice_duration: Optional[int] = None


# Group Models
class ChatGroup(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    name: str
    description: Optional[str] = None
    created_by: str  # Admin who created it
    members: List[str] = []  # List of user IDs
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True


class ChatGroupCreate(BaseModel):
    name: str
    description: Optional[str] = None
    members: List[str] = []


class ChatGroupUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    members: Optional[List[str]] = None
    is_active: Optional[bool] = None


# Auth utility functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = await db.users.find_one({"username": username})
    if user is None:
        raise credentials_exception
    
    user["_id"] = str(user["_id"])
    return User(**user)


async def get_current_admin_user(current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user


# Auth Routes
@api_router.post("/register", response_model=User)
async def register(user: UserCreate):
    # Check if user already exists
    existing_user = await db.users.find_one({"$or": [{"username": user.username}, {"email": user.email}]})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already registered"
        )
    
    # Hash password
    hashed_password = get_password_hash(user.password)
    
    # Create user
    user_dict = user.dict()
    del user_dict["password"]
    user_dict["hashed_password"] = hashed_password
    
    result = await db.users.insert_one(user_dict)
    created_user = await db.users.find_one({"_id": result.inserted_id})
    created_user["_id"] = str(created_user["_id"])
    
    return User(**created_user)


@api_router.post("/login", response_model=Token)
async def login(user_credentials: UserLogin):
    user = await db.users.find_one({"username": user_credentials.username})
    if not user or not verify_password(user_credentials.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user is active
    if not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account has been suspended. Please contact support.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"]}, expires_delta=access_token_expires
    )
    
    user["_id"] = str(user["_id"])
    user_obj = User(**user)
    
    return Token(access_token=access_token, token_type="bearer", user=user_obj)


@api_router.get("/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user


# Create admin user if not exists
@api_router.post("/create-admin")
async def create_admin():
    admin_exists = await db.users.find_one({"role": "admin"})
    if admin_exists:
        return {"message": "Admin user already exists"}
    
    admin_user = {
        "username": "admin",
        "email": "admin@emergency-sos.com",
        "full_name": "System Administrator",
        "role": "admin",
        "hashed_password": get_password_hash("admin123"),
        "is_active": True,
        "created_at": datetime.utcnow()
    }
    
    result = await db.users.insert_one(admin_user)
    return {"message": "Admin user created", "username": "admin", "password": "admin123"}


# Emergency Contacts Routes (User-specific)
@api_router.post("/emergency-contacts", response_model=EmergencyContact)
async def create_emergency_contact(contact: EmergencyContactCreate, current_user: User = Depends(get_current_user)):
    contact_dict = contact.dict()
    contact_dict["user_id"] = current_user.id
    result = await db.emergency_contacts.insert_one(contact_dict)
    created_contact = await db.emergency_contacts.find_one({"_id": result.inserted_id})
    created_contact["_id"] = str(created_contact["_id"])
    return EmergencyContact(**created_contact)


@api_router.get("/emergency-contacts", response_model=List[EmergencyContact])
async def get_emergency_contacts(current_user: User = Depends(get_current_user)):
    contacts = await db.emergency_contacts.find({"user_id": current_user.id}).to_list(1000)
    for contact in contacts:
        contact["_id"] = str(contact["_id"])
    return [EmergencyContact(**contact) for contact in contacts]


@api_router.put("/emergency-contacts/{contact_id}", response_model=EmergencyContact)
async def update_emergency_contact(contact_id: str, contact_update: EmergencyContactUpdate, current_user: User = Depends(get_current_user)):
    if not ObjectId.is_valid(contact_id):
        raise HTTPException(status_code=400, detail="Invalid contact ID")
    
    # Verify contact belongs to user
    existing_contact = await db.emergency_contacts.find_one({"_id": ObjectId(contact_id), "user_id": current_user.id})
    if not existing_contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    update_data = {k: v for k, v in contact_update.dict().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    result = await db.emergency_contacts.update_one(
        {"_id": ObjectId(contact_id), "user_id": current_user.id}, 
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    updated_contact = await db.emergency_contacts.find_one({"_id": ObjectId(contact_id)})
    updated_contact["_id"] = str(updated_contact["_id"])
    return EmergencyContact(**updated_contact)


@api_router.delete("/emergency-contacts/{contact_id}")
async def delete_emergency_contact(contact_id: str, current_user: User = Depends(get_current_user)):
    if not ObjectId.is_valid(contact_id):
        raise HTTPException(status_code=400, detail="Invalid contact ID")
    
    result = await db.emergency_contacts.delete_one({"_id": ObjectId(contact_id), "user_id": current_user.id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    return {"message": "Contact deleted successfully"}


# User Profile Routes (User-specific)
@api_router.post("/user-profile", response_model=UserProfile)
async def create_user_profile(profile: UserProfileCreate, current_user: User = Depends(get_current_user)):
    # Check if profile already exists for user
    existing_profile = await db.user_profiles.find_one({"user_id": current_user.id})
    if existing_profile:
        # Update existing profile
        update_data = profile.dict()
        update_data["updated_at"] = datetime.utcnow()
        await db.user_profiles.update_one(
            {"user_id": current_user.id}, 
            {"$set": update_data}
        )
        updated_profile = await db.user_profiles.find_one({"user_id": current_user.id})
        updated_profile["_id"] = str(updated_profile["_id"])
        return UserProfile(**updated_profile)
    else:
        # Create new profile
        profile_dict = profile.dict()
        profile_dict["user_id"] = current_user.id
        result = await db.user_profiles.insert_one(profile_dict)
        created_profile = await db.user_profiles.find_one({"_id": result.inserted_id})
        created_profile["_id"] = str(created_profile["_id"])
        return UserProfile(**created_profile)


@api_router.get("/user-profile", response_model=Optional[UserProfile])
async def get_user_profile(current_user: User = Depends(get_current_user)):
    profile = await db.user_profiles.find_one({"user_id": current_user.id})
    if profile:
        profile["_id"] = str(profile["_id"])
        return UserProfile(**profile)
    return None


# SOS Alert Routes (User-specific)
@api_router.post("/sos-alert", response_model=SOSAlert)
async def create_sos_alert(alert: SOSAlertCreate, current_user: User = Depends(get_current_user)):
    alert_dict = alert.dict()
    alert_dict["user_id"] = current_user.id
    result = await db.sos_alerts.insert_one(alert_dict)
    created_alert = await db.sos_alerts.find_one({"_id": result.inserted_id})
    created_alert["_id"] = str(created_alert["_id"])
    return SOSAlert(**created_alert)


@api_router.get("/sos-alerts", response_model=List[SOSAlert])
async def get_sos_alerts(current_user: User = Depends(get_current_user)):
    alerts = await db.sos_alerts.find({"user_id": current_user.id}).sort("created_at", -1).to_list(100)
    for alert in alerts:
        alert["_id"] = str(alert["_id"])
    return [SOSAlert(**alert) for alert in alerts]


@api_router.put("/sos-alerts/{alert_id}/status")
async def update_sos_alert_status(alert_id: str, status: str, current_user: User = Depends(get_current_user)):
    if not ObjectId.is_valid(alert_id):
        raise HTTPException(status_code=400, detail="Invalid alert ID")
    
    if status not in ["active", "resolved", "cancelled"]:
        raise HTTPException(status_code=400, detail="Invalid status")
    
    result = await db.sos_alerts.update_one(
        {"_id": ObjectId(alert_id), "user_id": current_user.id}, 
        {"$set": {"status": status}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    return {"message": f"Alert status updated to {status}"}


# Admin Routes
@api_router.get("/admin/users", response_model=List[User])
async def get_all_users(current_admin: User = Depends(get_current_admin_user)):
    users = await db.users.find().to_list(1000)
    for user in users:
        user["_id"] = str(user["_id"])
    return [User(**user) for user in users]


@api_router.get("/admin/sos-alerts", response_model=List[SOSAlert])
async def get_all_sos_alerts(current_admin: User = Depends(get_current_admin_user)):
    alerts = await db.sos_alerts.find().sort("created_at", -1).to_list(1000)
    for alert in alerts:
        alert["_id"] = str(alert["_id"])
    return [SOSAlert(**alert) for alert in alerts]


@api_router.get("/admin/emergency-contacts", response_model=List[EmergencyContact])
async def get_all_emergency_contacts(current_admin: User = Depends(get_current_admin_user)):
    contacts = await db.emergency_contacts.find().to_list(1000)
    for contact in contacts:
        contact["_id"] = str(contact["_id"])
        # Handle legacy data without user_id
        if "user_id" not in contact:
            contact["user_id"] = "legacy_user"
    return [EmergencyContact(**contact) for contact in contacts]


@api_router.put("/admin/sos-alerts/{alert_id}/status")
async def admin_update_sos_alert_status(alert_id: str, status: str, current_admin: User = Depends(get_current_admin_user)):
    if not ObjectId.is_valid(alert_id):
        raise HTTPException(status_code=400, detail="Invalid alert ID")
    
    if status not in ["active", "resolved", "cancelled", "admin_active"]:
        raise HTTPException(status_code=400, detail="Invalid status")
    
    result = await db.sos_alerts.update_one(
        {"_id": ObjectId(alert_id)}, 
        {"$set": {"status": status, "admin_handled_by": current_admin.id if status == "admin_active" else None}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    return {"message": f"Alert status updated to {status}"}


@api_router.delete("/admin/sos-alerts/{alert_id}")
async def delete_sos_alert(alert_id: str, current_admin: User = Depends(get_current_admin_user)):
    """Admin can completely delete SOS alerts"""
    if not ObjectId.is_valid(alert_id):
        raise HTTPException(status_code=400, detail="Invalid alert ID")
    
    result = await db.sos_alerts.delete_one({"_id": ObjectId(alert_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    return {"message": "SOS alert deleted successfully"}


@api_router.get("/admin/active-alerts", response_model=List[SOSAlert])
async def get_admin_active_alerts(current_admin: User = Depends(get_current_admin_user)):
    """Get only admin-active SOS alerts (status = admin_active)"""
    alerts = await db.sos_alerts.find({"status": "admin_active"}).sort("created_at", -1).to_list(1000)
    for alert in alerts:
        alert["_id"] = str(alert["_id"])
    return [SOSAlert(**alert) for alert in alerts]


@api_router.put("/admin/users/{user_id}/status")
async def update_user_status(user_id: str, is_active: bool, current_admin: User = Depends(get_current_admin_user)):
    """Admin can activate/deactivate users"""
    if not ObjectId.is_valid(user_id):
        raise HTTPException(status_code=400, detail="Invalid user ID")
    
    if user_id == current_admin.id:
        raise HTTPException(status_code=400, detail="Cannot deactivate yourself")
    
    result = await db.users.update_one(
        {"_id": ObjectId(user_id)}, 
        {"$set": {"is_active": is_active}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"message": f"User {'activated' if is_active else 'deactivated'} successfully"}


class UpdateUserRole(BaseModel):
    role: str


@api_router.put("/admin/users/{user_id}/role")
async def update_user_role(user_id: str, role_data: UpdateUserRole, current_admin: User = Depends(get_current_admin_user)):
    """Admin can change user roles via request body"""
    if not ObjectId.is_valid(user_id):
        raise HTTPException(status_code=400, detail="Invalid user ID")
    
    if role_data.role not in ["admin", "user", "team", "emergency"]:
        raise HTTPException(status_code=400, detail="Invalid role")
    
    # Convert current_admin.id to string for comparison
    current_admin_id_str = str(current_admin.id)
    if user_id == current_admin_id_str:
        raise HTTPException(status_code=400, detail="Cannot change your own role")
    
    result = await db.users.update_one(
        {"_id": ObjectId(user_id)}, 
        {"$set": {"role": role_data.role}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"message": f"User role updated to {role_data.role}"}


class UpdateUserGroups(BaseModel):
    group_ids: List[str]


@api_router.put("/admin/users/{user_id}/groups")
async def assign_user_to_groups(user_id: str, groups_data: UpdateUserGroups, current_admin: User = Depends(get_current_admin_user)):
    """Admin assigns user to chat groups"""
    if not ObjectId.is_valid(user_id):
        raise HTTPException(status_code=400, detail="Invalid user ID")
    
    # Validate all group IDs
    for group_id in groups_data.group_ids:
        if not ObjectId.is_valid(group_id):
            raise HTTPException(status_code=400, detail=f"Invalid group ID: {group_id}")
    
    # Add user to all specified groups
    for group_id in groups_data.group_ids:
        await db.chat_groups.update_one(
            {"_id": ObjectId(group_id)},
            {"$addToSet": {"members": user_id}}
        )
    
    # Remove user from groups not in the list
    await db.chat_groups.update_many(
        {"_id": {"$nin": [ObjectId(gid) for gid in groups_data.group_ids]}, "members": user_id},
        {"$pull": {"members": user_id}}
    )
    
    return {"message": "User group assignments updated successfully"}


# News Routes (Public read, Admin write)
@api_router.get("/news", response_model=List[NewsArticle])
async def get_news():
    """Get all active news articles for public viewing"""
    news = await db.news_articles.find({"is_active": True}).sort("created_at", -1).to_list(100)
    for article in news:
        article["_id"] = str(article["_id"])
    return [NewsArticle(**article) for article in news]


@api_router.post("/admin/news", response_model=NewsArticle)
async def create_news_article(article: NewsArticleCreate, current_admin: User = Depends(get_current_admin_user)):
    """Admin creates news article"""
    article_dict = article.dict()
    article_dict["author_id"] = current_admin.id
    article_dict["author_name"] = current_admin.full_name
    article_dict["is_active"] = True  # Explicitly set to True by default
    article_dict["created_at"] = datetime.utcnow()
    article_dict["updated_at"] = datetime.utcnow()
    
    result = await db.news_articles.insert_one(article_dict)
    created_article = await db.news_articles.find_one({"_id": result.inserted_id})
    created_article["_id"] = str(created_article["_id"])
    return NewsArticle(**created_article)


@api_router.get("/admin/news", response_model=List[NewsArticle])
async def get_all_news_articles(current_admin: User = Depends(get_current_admin_user)):
    """Admin gets all news articles including inactive ones"""
    news = await db.news_articles.find().sort("created_at", -1).to_list(1000)
    for article in news:
        article["_id"] = str(article["_id"])
    return [NewsArticle(**article) for article in news]


@api_router.put("/admin/news/{article_id}", response_model=NewsArticle)
async def update_news_article(article_id: str, article_update: NewsArticleUpdate, current_admin: User = Depends(get_current_admin_user)):
    """Admin updates news article"""
    if not ObjectId.is_valid(article_id):
        raise HTTPException(status_code=400, detail="Invalid article ID")
    
    update_data = {k: v for k, v in article_update.dict().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    update_data["updated_at"] = datetime.utcnow()
    
    result = await db.news_articles.update_one(
        {"_id": ObjectId(article_id)}, 
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Article not found")
    
    updated_article = await db.news_articles.find_one({"_id": ObjectId(article_id)})
    updated_article["_id"] = str(updated_article["_id"])
    return NewsArticle(**updated_article)


@api_router.delete("/admin/news/{article_id}")
async def delete_news_article(article_id: str, current_admin: User = Depends(get_current_admin_user)):
    """Admin deletes news article"""
    if not ObjectId.is_valid(article_id):
        raise HTTPException(status_code=400, detail="Invalid article ID")
    
    result = await db.news_articles.delete_one({"_id": ObjectId(article_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Article not found")
    
    return {"message": "Article deleted successfully"}


# Chat Group Routes (Admin only)
@api_router.post("/admin/chat/groups", response_model=ChatGroup)
async def create_chat_group(group: ChatGroupCreate, current_admin: User = Depends(get_current_admin_user)):
    """Admin creates chat group"""
    group_dict = group.dict()
    group_dict["created_by"] = current_admin.id
    
    result = await db.chat_groups.insert_one(group_dict)
    created_group = await db.chat_groups.find_one({"_id": result.inserted_id})
    created_group["_id"] = str(created_group["_id"])
    return ChatGroup(**created_group)


@api_router.get("/admin/chat/groups", response_model=List[ChatGroup])
async def get_chat_groups(current_admin: User = Depends(get_current_admin_user)):
    """Admin gets all chat groups"""
    groups = await db.chat_groups.find({"is_active": True}).to_list(1000)
    for group in groups:
        group["id"] = str(group["_id"])
        group["_id"] = str(group["_id"])
    return [ChatGroup(**group) for group in groups]


@api_router.put("/admin/chat/groups/{group_id}", response_model=ChatGroup)
async def update_chat_group(group_id: str, group_update: ChatGroupUpdate, current_admin: User = Depends(get_current_admin_user)):
    """Admin updates chat group"""
    if not ObjectId.is_valid(group_id):
        raise HTTPException(status_code=400, detail="Invalid group ID")
    
    update_data = {k: v for k, v in group_update.dict().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    result = await db.chat_groups.update_one(
        {"_id": ObjectId(group_id)}, 
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Group not found")
    
    updated_group = await db.chat_groups.find_one({"_id": ObjectId(group_id)})
    updated_group["_id"] = str(updated_group["_id"])
    return ChatGroup(**updated_group)


@api_router.delete("/admin/chat/groups/{group_id}")
async def delete_chat_group(group_id: str, current_admin: User = Depends(get_current_admin_user)):
    """Admin deletes chat group"""
    if not ObjectId.is_valid(group_id):
        raise HTTPException(status_code=400, detail="Invalid group ID")
    
    result = await db.chat_groups.delete_one({"_id": ObjectId(group_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Group not found")
    
    # Also delete all messages in this group
    await db.chat_messages.delete_many({"group_id": group_id})
    
    return {"message": "Group deleted successfully"}


# Chat Routes (Admin only) - Updated for groups
@api_router.post("/admin/chat", response_model=ChatMessage)
async def send_chat_message(message: ChatMessageCreate, current_admin: User = Depends(get_current_admin_user)):
    """Admin sends chat message"""
    message_dict = message.dict()
    message_dict["user_id"] = current_admin.id
    message_dict["username"] = current_admin.username
    
    result = await db.chat_messages.insert_one(message_dict)
    created_message = await db.chat_messages.find_one({"_id": result.inserted_id})
    created_message["_id"] = str(created_message["_id"])
    return ChatMessage(**created_message)


@api_router.get("/admin/chat", response_model=List[ChatMessage])
async def get_chat_messages(chat_type: str = "admin", group_id: Optional[str] = None, current_admin: User = Depends(get_current_admin_user)):
    """Admin gets chat messages"""
    query = {"chat_type": chat_type}
    if group_id:
        query["group_id"] = group_id
    
    messages = await db.chat_messages.find(query).sort("created_at", -1).limit(100).to_list(100)
    for message in messages:
        message["_id"] = str(message["_id"])
    return [ChatMessage(**message) for message in messages][::-1]  # Reverse to show oldest first


class UpdateAdminProfile(BaseModel):
    full_name: str


# Admin profile update route
@api_router.put("/admin/profile", response_model=User)
async def update_admin_profile(profile_data: UpdateAdminProfile, current_admin: User = Depends(get_current_admin_user)):
    """Admin updates their display name"""
    result = await db.users.update_one(
        {"_id": ObjectId(current_admin.id)}, 
        {"$set": {"full_name": profile_data.full_name}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    updated_user = await db.users.find_one({"_id": ObjectId(current_admin.id)})
    updated_user["_id"] = str(updated_user["_id"])
    return User(**updated_user)


# Test endpoint for creating test users with different roles
@api_router.post("/admin/test-user-role")
async def create_test_users_with_roles(current_admin: User = Depends(get_current_admin_user)):
    """Test endpoint to create test users with different roles"""
    try:
        # Create test users with different roles
        test_users = [
            {
                "username": "testuser1",
                "email": "user@test.com", 
                "full_name": "Test User",
                "role": "user",
                "is_active": True,
                "created_at": datetime.utcnow()
            },
            {
                "username": "testteam1", 
                "email": "team@test.com",
                "full_name": "Test Team Member",
                "role": "team",
                "is_active": True,
                "created_at": datetime.utcnow()
            }
        ]
        
        created_users = []
        for user_data in test_users:
            # Check if user already exists
            existing_user = await db.users.find_one({"email": user_data["email"]})
            if not existing_user:
                # Hash password
                user_data["hashed_password"] = get_password_hash("test123")
                result = await db.users.insert_one(user_data)
                created_users.append(user_data["username"])
        
        if created_users:
            return {"message": f"Test users created with different roles: {', '.join(created_users)}"}
        else:
            return {"message": "Test users already exist"}
    except Exception as e:
        print(f"Error creating test users: {e}")
        raise HTTPException(status_code=500, detail=f"Error creating test users: {str(e)}")


# Health check
@api_router.get("/")
async def root():
    return {"message": "Emergency SOS API with Authentication, News & Chat is running"}


@api_router.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow()}


# Chat message management endpoints
@api_router.put("/admin/chat/{message_id}")
async def update_chat_message(message_id: str, request: dict, current_admin: User = Depends(get_current_admin_user)):
    """Admin or message owner updates a chat message"""
    try:
        if not ObjectId.is_valid(message_id):
            raise HTTPException(status_code=400, detail="Invalid message ID")
        
        # Get the message
        message = await db.chat_messages.find_one({"_id": ObjectId(message_id)})
        if not message:
            raise HTTPException(status_code=404, detail="Message not found")
        
        # Check if user can edit (owner or admin)
        if message["user_id"] != current_admin.id and current_admin.role != "admin":
            raise HTTPException(status_code=403, detail="Not authorized to edit this message")
        
        # Update message
        new_message = request.get("message", "").strip()
        if not new_message:
            raise HTTPException(status_code=400, detail="Message cannot be empty")
        
        result = await db.chat_messages.update_one(
            {"_id": ObjectId(message_id)},
            {"$set": {"message": new_message, "updated_at": datetime.utcnow()}}
        )
        
        return {"message": "Chat message updated successfully"}
    except Exception as e:
        print(f"Error updating chat message: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@api_router.delete("/admin/chat/{message_id}")
async def delete_chat_message(message_id: str, current_admin: User = Depends(get_current_admin_user)):
    """Admin or message owner deletes a chat message"""
    try:
        if not ObjectId.is_valid(message_id):
            raise HTTPException(status_code=400, detail="Invalid message ID")
        
        # Get the message
        message = await db.chat_messages.find_one({"_id": ObjectId(message_id)})
        if not message:
            raise HTTPException(status_code=404, detail="Message not found")
        
        # Check if user can delete (owner or admin)
        if message["user_id"] != current_admin.id and current_admin.role != "admin":
            raise HTTPException(status_code=403, detail="Not authorized to delete this message")
        
        # Delete message
        await db.chat_messages.delete_one({"_id": ObjectId(message_id)})
        
        return {"message": "Chat message deleted successfully"}
    except Exception as e:
        print(f"Error deleting chat message: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Enhanced user management for Test Emergency User
@api_router.post("/admin/users/{user_id}/toggle-status")
async def toggle_user_status(user_id: str, current_admin: User = Depends(get_current_admin_user)):
    """Admin toggles user active/inactive status"""
    try:
        if not ObjectId.is_valid(user_id):
            raise HTTPException(status_code=400, detail="Invalid user ID")
        
        # Don't allow toggling own status
        if user_id == current_admin.id:
            raise HTTPException(status_code=400, detail="Cannot toggle own status")
        
        # Get current user status
        user = await db.users.find_one({"_id": ObjectId(user_id)})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        new_status = not user.get("is_active", True)
        
        # Update user status
        result = await db.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"is_active": new_status}}
        )
        
        status_text = "aktiviert" if new_status else "gesperrt"
        return {"message": f"Benutzer wurde {status_text}", "is_active": new_status}
    except Exception as e:
        print(f"Error toggling user status: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Test endpoint for creating emergency user role
@api_router.post("/admin/create-emergency-user")
async def create_emergency_user(current_admin: User = Depends(get_current_admin_user)):
    """Create a test emergency user"""
    try:
        emergency_user = {
            "username": "emergencyuser",
            "email": "emergency@test.com",
            "full_name": "Test Emergency User",
            "role": "emergency",
            "is_active": True,
            "hashed_password": get_password_hash("emergency123"),
            "created_at": datetime.utcnow()
        }
        
        # Check if user already exists
        existing_user = await db.users.find_one({"email": emergency_user["email"]})
        if existing_user:
            return {"message": "Test Emergency User already exists", "user_id": str(existing_user["_id"])}
        
        result = await db.users.insert_one(emergency_user)
        return {"message": "Test Emergency User created successfully", "user_id": str(result.inserted_id)}
    except Exception as e:
        print(f"Error creating emergency user: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# SOS Management endpoints
@api_router.put("/admin/sos/{sos_id}/activate")
async def activate_sos_alert(sos_id: str, current_admin: User = Depends(get_current_admin_user)):
    """Admin activates SOS alert (moves it to active state and removes from pending list)"""
    try:
        if not ObjectId.is_valid(sos_id):
            raise HTTPException(status_code=400, detail="Invalid SOS ID")
        
        # Update SOS status to active
        result = await db.sos_alerts.update_one(
            {"_id": ObjectId(sos_id)},
            {"$set": {"status": "active", "activated_by": current_admin.id, "activated_at": datetime.utcnow()}}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="SOS alert not found")
        
        return {"message": "SOS alert activated successfully", "status": "active"}
    except Exception as e:
        print(f"Error activating SOS alert: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Enhanced profile update for name changes
@api_router.put("/profile")
async def update_user_profile(request: dict, current_user: User = Depends(get_current_user)):
    """User updates their own profile (name changes)"""
    try:
        updates = {}
        
        # Allow updating full_name
        if "full_name" in request:
            full_name = request["full_name"].strip()
            if not full_name:
                raise HTTPException(status_code=400, detail="Name cannot be empty")
            updates["full_name"] = full_name
        
        # Allow updating other profile fields
        allowed_fields = ["full_name", "phone", "address", "emergency_contact"]
        for field in allowed_fields:
            if field in request and field != "full_name":
                updates[field] = request[field]
        
        if not updates:
            raise HTTPException(status_code=400, detail="No valid fields to update")
        
        # Update user profile
        result = await db.users.update_one(
            {"_id": ObjectId(current_user.id)},
            {"$set": updates}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="User not found")
        
        return {"message": "Profile updated successfully", "updated_fields": list(updates.keys())}
    except Exception as e:
        print(f"Error updating profile: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()


# Helper function for password hashing (if not already defined)
def hash_password(password: str) -> str:
    return pwd_context.hash(password)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
