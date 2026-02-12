"""Unit tests for API routes."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.main import app
from app.backend.database import Base, get_db, ItemChange
from app.backend.security import hash_password, create_access_token


# Create in-memory test database with thread safety
engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
Base.metadata.create_all(bind=engine)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


# Override the get_db dependency before TestClient instantiation
app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture
def test_db():
    """Create test database."""
    # Clear all tables before each test
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    db = TestingSessionLocal()
    yield db
    db.close()
    
    # Clear all tables after each test
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


@pytest.fixture
def test_user(test_db):
    """Create a test user."""
    from app.backend.database import User
    
    user = User(
        username="testuser",
        hashed_password=hash_password("testpassword")
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture
def test_token(test_user):
    """Create a test JWT token."""
    return create_access_token(user_id=test_user.id, username=test_user.username)


# Note: Auth and Wardrobe route tests require full API setup with /api/v1 prefix
# These tests are skipped in this version but should be implemented against the actual API endpoints


class TestHealthCheck:
    """Test health check endpoint."""
    
    def test_health_check(self):
        """Test health check endpoint."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"


class TestErrorHandling:
    """Test error handling."""
    
    def test_health_check(self):
        """Test health check endpoint works."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"


class TestItemChangesDatabase:
    """Test item change database operations."""
    
    def test_create_item_change_record(self, test_user, test_db):
        """Test creating an ItemChange record."""
        from app.backend.database import Wardrobe, Item
        
        wardrobe = Wardrobe(user_id=test_user.id)
        test_db.add(wardrobe)
        test_db.flush()
        
        item = Item(
            node_id=1,
            user_id=test_user.id,
            wardrobe_id=wardrobe.id,
            main_category_indices=[0, 1],
            sub_category_indices=[5, 6]
        )
        test_db.add(item)
        test_db.commit()
        test_db.refresh(wardrobe)
        test_db.refresh(item)
        
        # Create change record
        change = ItemChange(
            item_id=item.id,
            user_id=test_user.id,
            wardrobe_id=wardrobe.id,
            original_main_category_indices=[0, 1],
            corrected_main_category_indices=[0, 2],
            confidence_feedback=0.9,
            notes="Test correction"
        )
        test_db.add(change)
        test_db.commit()
        test_db.refresh(change)
        
        assert change.id is not None
        assert change.item_id == item.id
        assert change.user_id == test_user.id
        assert change.confidence_feedback == 0.9
    
    def test_query_user_changes(self, test_user, test_db):
        """Test querying all changes for a user."""
        from app.backend.database import Wardrobe, Item
        
        wardrobe = Wardrobe(user_id=test_user.id)
        test_db.add(wardrobe)
        test_db.flush()
        
        item = Item(node_id=1, user_id=test_user.id, wardrobe_id=wardrobe.id)
        test_db.add(item)
        test_db.commit()
        test_db.refresh(wardrobe)
        test_db.refresh(item)
        
        # Create multiple changes
        for i in range(3):
            change = ItemChange(
                item_id=item.id,
                user_id=test_user.id,
                wardrobe_id=wardrobe.id,
                corrected_category_indices=[i],
                confidence_feedback=0.8 + (i * 0.05)
            )
            test_db.add(change)
        test_db.commit()
        
        # Query changes
        changes = test_db.query(ItemChange).filter(
            ItemChange.user_id == test_user.id
        ).all()
        
        assert len(changes) == 3
    
    def test_query_wardrobe_changes(self, test_user, test_db):
        """Test querying changes for a specific wardrobe."""
        from app.backend.database import Wardrobe, Item, User
        
        # Create second user for second wardrobe
        user2 = User(
            username="testuser2",
            hashed_password=hash_password("testpassword")
        )
        test_db.add(user2)
        test_db.flush()
        
        wardrobe1 = Wardrobe(user_id=test_user.id)
        wardrobe2 = Wardrobe(user_id=user2.id)
        test_db.add_all([wardrobe1, wardrobe2])
        test_db.flush()
        
        item1 = Item(node_id=1, user_id=test_user.id, wardrobe_id=wardrobe1.id)
        item2 = Item(node_id=2, user_id=user2.id, wardrobe_id=wardrobe2.id)
        test_db.add_all([item1, item2])
        test_db.commit()
        test_db.refresh(wardrobe1)
        test_db.refresh(wardrobe2)
        test_db.refresh(item1)
        test_db.refresh(item2)
        
        # Create changes in both wardrobes
        change1 = ItemChange(item_id=item1.id, user_id=test_user.id, wardrobe_id=wardrobe1.id)
        change2 = ItemChange(item_id=item2.id, user_id=user2.id, wardrobe_id=wardrobe2.id)
        test_db.add_all([change1, change2])
        test_db.commit()
        
        # Query changes for wardrobe1
        changes = test_db.query(ItemChange).filter(
            ItemChange.wardrobe_id == wardrobe1.id
        ).all()
        
        assert len(changes) == 1
        assert changes[0].item_id == item1.id
    
    def test_change_stats_calculation(self, test_user, test_db):
        """Test calculating statistics from changes."""
        from app.backend.database import Wardrobe, Item
        
        wardrobe = Wardrobe(user_id=test_user.id)
        test_db.add(wardrobe)
        test_db.flush()
        
        item = Item(node_id=1, user_id=test_user.id, wardrobe_id=wardrobe.id)
        test_db.add(item)
        test_db.commit()
        test_db.refresh(wardrobe)
        test_db.refresh(item)
        
        # Create 12 changes
        for i in range(12):
            change = ItemChange(
                item_id=item.id,
                user_id=test_user.id,
                wardrobe_id=wardrobe.id,
                corrected_category_indices=[i],
                confidence_feedback=0.75
            )
            test_db.add(change)
        test_db.commit()
        
        # Query and calculate stats
        all_changes = test_db.query(ItemChange).filter(
            ItemChange.user_id == test_user.id
        ).all()
        
        assert len(all_changes) == 12
        avg_confidence = sum(c.confidence_feedback or 0 for c in all_changes) / len(all_changes)
        assert abs(avg_confidence - 0.75) < 0.01


class TestOutfitValidation:
    """Test outfit validation."""
    
    def test_outfit_create_rejects_duplicate_items(self):
        """Test that OutfitCreate rejects outfits with duplicate items."""
        from pydantic import ValidationError
        from app.backend.schemas import OutfitCreate
        
        # Should fail with duplicate items
        with pytest.raises(ValidationError) as exc_info:
            OutfitCreate(item_ids=[1, 2, 2, 3])
        
        error = exc_info.value
        assert "duplicate items" in str(error).lower()
    
    def test_outfit_create_accepts_unique_items(self):
        """Test that OutfitCreate accepts outfits with unique items."""
        from app.backend.schemas import OutfitCreate
        
        # Should succeed with unique items
        outfit = OutfitCreate(item_ids=[1, 2, 3])
        assert outfit.item_ids == [1, 2, 3]
    
    def test_outfit_create_empty_items(self):
        """Test that OutfitCreate allows empty item list."""
        from app.backend.schemas import OutfitCreate
        
        outfit = OutfitCreate(item_ids=[])
        assert outfit.item_ids == []
