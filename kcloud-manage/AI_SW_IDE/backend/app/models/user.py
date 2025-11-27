from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from app.db.session import Base


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, nullable=False, default="admin")
    name = Column(String, nullable=False)
    department = Column(String, nullable=False, default="openkcloud")
        
    servers = relationship("PodCreation", back_populates="user", cascade="all, delete-orphan")
    pvcs = relationship("PVC", back_populates="user", cascade="all, delete-orphan")
