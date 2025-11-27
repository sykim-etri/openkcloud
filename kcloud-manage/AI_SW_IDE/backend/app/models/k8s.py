# app/models/pod_creation.py
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Table
from sqlalchemy.orm import relationship

from app.db.session import Base
from app.utils.common import now_kst


pvc_server_association = Table(
    "pvc_server_association",
    Base.metadata,
    Column("server_id", Integer, ForeignKey("servers.id"), primary_key=True),
    Column("pvc_id", Integer, ForeignKey("pvcs.id"), primary_key=True)
)

class PodCreation(Base):
    __tablename__ = "servers"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user = relationship("User", back_populates="servers")

    server_name = Column(String, nullable=False)
    pod_name = Column(String, nullable=False)
    cpu = Column(String, nullable=False)
    memory = Column(String, nullable=False)
    gpu = Column(String, nullable=False)

    description = Column(String, nullable=True)
    request_time = Column(DateTime(timezone=True), default=now_kst)
    internal_ip = Column(String, nullable=True)
    status = Column(String, nullable=False)
    tags = Column(String, nullable=True)

    pvcs = relationship("PVC", secondary=pvc_server_association, back_populates="servers")


class PVC(Base):
    __tablename__ = "pvcs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user = relationship("User", back_populates="pvcs")

    pvc_name = Column(String, nullable=False)
    pv = Column(String, nullable=True)
    path = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=now_kst)

    servers = relationship("PodCreation", secondary=pvc_server_association, back_populates="pvcs")
    
    