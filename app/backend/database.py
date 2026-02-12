"""Database configuration and session management."""
import os
from pathlib import Path
from sqlalchemy import Boolean, create_engine, Column, Integer, String, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime

# Create data directory inside backend app
DATA_DIR = Path(__file__).resolve().parents[1] / "data"
DATA_DIR.mkdir(exist_ok=True)

# Use SQLite database in data folder
DB_PATH = DATA_DIR / "wardrobes.db"
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ==================== Models ====================

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    # One-to-one relationship
    wardrobe = relationship("Wardrobe", back_populates="user", uselist=False, cascade="all, delete-orphan")
    items = relationship("Item", back_populates="user", cascade="all, delete-orphan")
    outfits = relationship("Outfit", back_populates="user", cascade="all, delete-orphan")



class Wardrobe(Base):
    __tablename__ = "wardrobes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)  # enforce one-to-one
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="wardrobe")
    items = relationship("Item", back_populates="wardrobe")
    outfits = relationship("Outfit", back_populates="wardrobe")


class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    node_id = Column(Integer, unique=True, index=True)  # dataset unique identifier

    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    wardrobe_id = Column(Integer, ForeignKey("wardrobes.id"), index=True)

    # Image storage
    image_path = Column(String, nullable=True)  # Path to stored image file

    # ML metadata
    related_indices = Column(JSON, nullable=True)
    category_indices = Column(JSON, nullable=True)
    main_category_indices = Column(JSON, nullable=True)
    sub_category_indices = Column(JSON, nullable=True)

    img_embedding = Column(JSON, nullable=True)   # image embedding vector
    attr_embedding = Column(JSON, nullable=True)  # attribute embedding vector

    # Availability
    available = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="items")
    wardrobe = relationship("Wardrobe", back_populates="items")
    outfit_items = relationship("OutfitItem", back_populates="item")



class Outfit(Base):
    __tablename__ = "outfits"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    wardrobe_id = Column(Integer, ForeignKey("wardrobes.id"), index=True)

    # Ratings
    user_rating = Column(Float, nullable=True)    # explicit user feedback
    system_rating = Column(Float, nullable=True)  # ML-driven score

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="outfits")
    wardrobe = relationship("Wardrobe", back_populates="outfits")
    items = relationship("OutfitItem", back_populates="outfit", cascade="all, delete-orphan")


class OutfitItem(Base):
    __tablename__ = "outfit_items"

    id = Column(Integer, primary_key=True, index=True)
    outfit_id = Column(Integer, ForeignKey("outfits.id"), index=True)
    item_id = Column(Integer, ForeignKey("items.id"), index=True)

    # Position in outfit (e.g., 0=top, 1=bottom, 2=shoes)
    position = Column(Integer, default=0)
    
    # Extra metadata
    score = Column(Float, nullable=True)   # compatibility / relevance score

    # Relationships
    outfit = relationship("Outfit", back_populates="items")
    item = relationship("Item", back_populates="outfit_items")


class ItemChange(Base):
    """Track item category changes for tagger improvement."""
    __tablename__ = "item_changes"

    id = Column(Integer, primary_key=True, index=True)
    
    item_id = Column(Integer, ForeignKey("items.id"), index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    wardrobe_id = Column(Integer, ForeignKey("wardrobes.id"), index=True)
    
    # Original ML predictions
    original_main_category_indices = Column(JSON, nullable=True)
    original_sub_category_indices = Column(JSON, nullable=True)
    original_category_indices = Column(JSON, nullable=True)
    original_related_indices = Column(JSON, nullable=True)
    
    # User corrections
    corrected_main_category_indices = Column(JSON, nullable=True)
    corrected_sub_category_indices = Column(JSON, nullable=True)
    corrected_category_indices = Column(JSON, nullable=True)
    corrected_related_indices = Column(JSON, nullable=True)
    
    # Change metadata
    confidence_feedback = Column(Float, nullable=True)  # User's confidence in correction (0-1)
    notes = Column(String, nullable=True)  # User notes on the change
    
    # Feedback source
    is_user_feedback = Column(Boolean, default=False)  # True if user-modified, False for other sources
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    item = relationship("Item", backref="changes")
    user = relationship("User", backref="item_changes")
    wardrobe = relationship("Wardrobe", backref="item_changes")
    





def init_db():
    """Create all tables."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Database session dependency for FastAPI."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
