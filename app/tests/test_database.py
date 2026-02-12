"""Unit tests for database models and operations."""
import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.backend.database import Base, User, Wardrobe, Item, Outfit, OutfitItem, ItemChange, get_db
from app.backend.security import hash_password


@pytest.fixture
def test_db():
    """Create an in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    db = TestingSessionLocal()
    yield db
    db.close()


class TestUserModel:
    """Test User model and operations."""
    
    def test_user_creation(self, test_db):
        """Test creating a user."""
        user = User(
            username="testuser",
            hashed_password=hash_password("password123")
        )
        test_db.add(user)
        test_db.commit()
        test_db.refresh(user)
        
        assert user.id is not None
        assert user.username == "testuser"
        assert user.created_at is not None
    
    def test_user_unique_username(self, test_db):
        """Test that usernames must be unique."""
        user1 = User(
            username="duplicate",
            hashed_password=hash_password("password1")
        )
        user2 = User(
            username="duplicate",
            hashed_password=hash_password("password2")
        )
        
        test_db.add(user1)
        test_db.commit()
        
        test_db.add(user2)
        with pytest.raises(Exception):  # IntegrityError
            test_db.commit()
    
    def test_user_query_by_username(self, test_db):
        """Test querying user by username."""
        user = User(
            username="john_doe",
            hashed_password=hash_password("password")
        )
        test_db.add(user)
        test_db.commit()
        
        queried_user = test_db.query(User).filter(User.username == "john_doe").first()
        
        assert queried_user is not None
        assert queried_user.username == "john_doe"
    
    def test_user_created_at_timestamp(self, test_db):
        """Test that created_at timestamp is set."""
        user = User(
            username="testuser",
            hashed_password=hash_password("password")
        )
        test_db.add(user)
        test_db.commit()
        test_db.refresh(user)
        
        assert user.created_at is not None
        assert isinstance(user.created_at, datetime)


class TestWardrobeModel:
    """Test Wardrobe model and operations."""
    
    def test_wardrobe_creation(self, test_db):
        """Test creating a wardrobe."""
        user = User(
            username="testuser",
            hashed_password=hash_password("password")
        )
        test_db.add(user)
        test_db.commit()
        test_db.refresh(user)
        
        wardrobe = Wardrobe(user_id=user.id)
        test_db.add(wardrobe)
        test_db.commit()
        test_db.refresh(wardrobe)
        
        assert wardrobe.id is not None
        assert wardrobe.user_id == user.id
        assert wardrobe.created_at is not None
    
    def test_wardrobe_unique_user(self, test_db):
        """Test that each user can have only one wardrobe."""
        user = User(
            username="testuser",
            hashed_password=hash_password("password")
        )
        test_db.add(user)
        test_db.commit()
        test_db.refresh(user)
        
        wardrobe1 = Wardrobe(user_id=user.id)
        wardrobe2 = Wardrobe(user_id=user.id)
        
        test_db.add(wardrobe1)
        test_db.commit()
        
        test_db.add(wardrobe2)
        with pytest.raises(Exception):  # IntegrityError
            test_db.commit()
    
    def test_wardrobe_user_relationship(self, test_db):
        """Test wardrobe-user relationship."""
        user = User(
            username="testuser",
            hashed_password=hash_password("password")
        )
        test_db.add(user)
        test_db.commit()
        test_db.refresh(user)
        
        wardrobe = Wardrobe(user_id=user.id)
        test_db.add(wardrobe)
        test_db.commit()
        test_db.refresh(wardrobe)
        
        assert wardrobe.user.username == "testuser"


class TestItemModel:
    """Test Item model and operations."""
    
    def test_item_creation(self, test_db):
        """Test creating an item."""
        user = User(
            username="testuser",
            hashed_password=hash_password("password")
        )
        test_db.add(user)
        test_db.commit()
        test_db.refresh(user)
        
        wardrobe = Wardrobe(user_id=user.id)
        test_db.add(wardrobe)
        test_db.commit()
        test_db.refresh(wardrobe)
        
        item = Item(
            user_id=user.id,
            wardrobe_id=wardrobe.id,
            node_id=1,
            image_path="/path/to/image.jpg",
            available=True
        )
        test_db.add(item)
        test_db.commit()
        test_db.refresh(item)
        
        assert item.id is not None
        assert item.user_id == user.id
        assert item.wardrobe_id == wardrobe.id
        assert item.available is True
    
    def test_item_with_embeddings(self, test_db):
        """Test creating an item with embeddings."""
        user = User(
            username="testuser",
            hashed_password=hash_password("password")
        )
        test_db.add(user)
        test_db.commit()
        test_db.refresh(user)
        
        wardrobe = Wardrobe(user_id=user.id)
        test_db.add(wardrobe)
        test_db.commit()
        test_db.refresh(wardrobe)
        
        # Create dummy embeddings (512-dim FashionCLIP)
        img_embedding = [0.1] * 512
        attr_embedding = [0.2] * 256
        
        item = Item(
            user_id=user.id,
            wardrobe_id=wardrobe.id,
            node_id=1,
            image_path="/path/to/image.jpg",
            img_embedding=img_embedding,
            attr_embedding=attr_embedding,
            available=True
        )
        test_db.add(item)
        test_db.commit()
        test_db.refresh(item)
        
        assert item.img_embedding == img_embedding
        assert item.attr_embedding == attr_embedding
    
    def test_item_with_attributes(self, test_db):
        """Test creating an item with category attributes."""
        user = User(
            username="testuser",
            hashed_password=hash_password("password")
        )
        test_db.add(user)
        test_db.commit()
        test_db.refresh(user)
        
        wardrobe = Wardrobe(user_id=user.id)
        test_db.add(wardrobe)
        test_db.commit()
        test_db.refresh(wardrobe)
        
        item = Item(
            user_id=user.id,
            wardrobe_id=wardrobe.id,
            node_id=1,
            image_path="/path/to/image.jpg",
            main_category_indices=[0],
            sub_category_indices=[5, 10],
            category_indices=[25],
            related_indices=[100, 200],
            available=True
        )
        test_db.add(item)
        test_db.commit()
        test_db.refresh(item)
        
        assert item.main_category_indices == [0]
        assert item.sub_category_indices == [5, 10]
        assert item.category_indices == [25]
        assert item.related_indices == [100, 200]


class TestOutfitModel:
    """Test Outfit and OutfitItem models."""
    
    def test_outfit_creation(self, test_db):
        """Test creating an outfit."""
        user = User(
            username="testuser",
            hashed_password=hash_password("password")
        )
        test_db.add(user)
        test_db.commit()
        test_db.refresh(user)
        
        wardrobe = Wardrobe(user_id=user.id)
        test_db.add(wardrobe)
        test_db.commit()
        test_db.refresh(wardrobe)
        
        outfit = Outfit(user_id=user.id, wardrobe_id=wardrobe.id)
        test_db.add(outfit)
        test_db.commit()
        test_db.refresh(outfit)
        
        assert outfit.id is not None
        assert outfit.user_id == user.id
        assert outfit.wardrobe_id == wardrobe.id
    
    def test_outfit_with_items(self, test_db):
        """Test outfit with multiple items."""
        user = User(
            username="testuser",
            hashed_password=hash_password("password")
        )
        test_db.add(user)
        test_db.commit()
        test_db.refresh(user)
        
        wardrobe = Wardrobe(user_id=user.id)
        test_db.add(wardrobe)
        test_db.commit()
        test_db.refresh(wardrobe)
        
        # Create items
        item1 = Item(
            user_id=user.id,
            wardrobe_id=wardrobe.id,
            node_id=1,
            image_path="/path/to/image1.jpg"
        )
        item2 = Item(
            user_id=user.id,
            wardrobe_id=wardrobe.id,
            node_id=2,
            image_path="/path/to/image2.jpg"
        )
        test_db.add_all([item1, item2])
        test_db.commit()
        test_db.refresh(item1)
        test_db.refresh(item2)
        
        # Create outfit with items
        outfit = Outfit(user_id=user.id, wardrobe_id=wardrobe.id)
        test_db.add(outfit)
        test_db.commit()
        test_db.refresh(outfit)
        
        outfit_item1 = OutfitItem(outfit_id=outfit.id, item_id=item1.id)
        outfit_item2 = OutfitItem(outfit_id=outfit.id, item_id=item2.id)
        test_db.add_all([outfit_item1, outfit_item2])
        test_db.commit()
        
        queried_outfit = test_db.query(Outfit).filter(Outfit.id == outfit.id).first()
        assert len(queried_outfit.items) == 2


class TestItemChangeModel:
    """Test ItemChange model for tracking item corrections."""
    
    def test_item_change_creation(self, test_db):
        """Test creating an item change record."""
        user = User(username="testuser", hashed_password=hash_password("pass"))
        wardrobe = Wardrobe(user_id=None)
        item = Item(node_id=1, user_id=None, wardrobe_id=None)
        
        test_db.add_all([user, wardrobe, item])
        test_db.flush()
        
        wardrobe.user_id = user.id
        item.user_id = user.id
        item.wardrobe_id = wardrobe.id
        test_db.commit()
        test_db.refresh(user)
        test_db.refresh(wardrobe)
        test_db.refresh(item)
        
        change = ItemChange(
            item_id=item.id,
            user_id=user.id,
            wardrobe_id=wardrobe.id,
            original_main_category_indices=[0, 1],
            corrected_main_category_indices=[0, 2],
            confidence_feedback=0.9
        )
        test_db.add(change)
        test_db.commit()
        test_db.refresh(change)
        
        assert change.id is not None
        assert change.confidence_feedback == 0.9
        assert change.created_at is not None
    
    def test_item_multiple_changes(self, test_db):
        """Test that an item can have multiple corrections."""
        user = User(username="testuser", hashed_password=hash_password("pass"))
        wardrobe = Wardrobe(user_id=None)
        item = Item(node_id=1, user_id=None, wardrobe_id=None)
        
        test_db.add_all([user, wardrobe, item])
        test_db.flush()
        test_db.refresh(user)
        test_db.refresh(wardrobe)
        test_db.refresh(item)
        
        for i in range(2):
            change = ItemChange(
                item_id=item.id,
                user_id=user.id,
                wardrobe_id=wardrobe.id,
                corrected_main_category_indices=[i + 1],
                confidence_feedback=0.8 + (i * 0.1)
            )
            test_db.add(change)
        test_db.commit()
        
        changes = test_db.query(ItemChange).filter(ItemChange.item_id == item.id).all()
        assert len(changes) == 2
    
    def test_filter_changes_by_confidence(self, test_db):
        """Test filtering changes by confidence level."""
        user = User(username="testuser", hashed_password=hash_password("pass"))
        wardrobe = Wardrobe(user_id=None)
        item = Item(node_id=1, user_id=None, wardrobe_id=None)
        
        test_db.add_all([user, wardrobe, item])
        test_db.flush()
        test_db.refresh(user)
        test_db.refresh(wardrobe)
        test_db.refresh(item)
        
        for confidence in [0.3, 0.5, 0.7, 0.9]:
            change = ItemChange(
                item_id=item.id,
                user_id=user.id,
                wardrobe_id=wardrobe.id,
                corrected_category_indices=[5],
                confidence_feedback=confidence
            )
            test_db.add(change)
        test_db.commit()
        
        high_conf = test_db.query(ItemChange).filter(
            ItemChange.confidence_feedback >= 0.7
        ).all()
        assert len(high_conf) == 2
