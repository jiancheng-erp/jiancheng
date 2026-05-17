"""Tests for database models"""
import pytest
from models import User, Bom


class TestUserModel:
    """Test User model functionality"""
    
    def test_user_creation(self, db_session):
        """Test that a user can be created"""
        user = User(
            user_name='john_doe',
            user_passwd='hashedpassword123',
            staff_id=1
        )
        db_session.add(user)
        db_session.commit()
        
        assert user.user_id is not None
        assert user.user_name == 'john_doe'
    
    def test_user_query(self, db_session, sample_user):
        """Test that users can be queried"""
        queried_user = db_session.query(User).filter_by(user_name='testuser').first()
        
        assert queried_user is not None
        assert queried_user.user_name == 'testuser'
        assert queried_user.staff_id == 1
    
    def test_user_update(self, db_session, sample_user):
        """Test that user can be updated"""
        original_id = sample_user.user_id
        sample_user.staff_id = 5
        db_session.commit()
        
        updated_user = db_session.query(User).get(original_id)
        assert updated_user.staff_id == 5
    
    def test_user_repr(self, sample_user):
        """Test User string representation"""
        repr_str = repr(sample_user)
        assert 'User' in repr_str
        assert 'testuser' in repr_str


class TestBomModel:
    """Test BOM model functionality"""
    
    def test_bom_creation(self, db_session):
        """Test that a BOM can be created"""
        bom = Bom(
            bom_rid='BOM-2024-001',
            bom_type=1,
            order_shoe_type_id=123
        )
        db_session.add(bom)
        db_session.commit()
        
        assert bom.bom_id is not None
        assert bom.bom_rid == 'BOM-2024-001'
    
    def test_bom_query(self, db_session, sample_bom):
        """Test that BOMs can be queried"""
        queried_bom = db_session.query(Bom).filter_by(bom_rid='TEST-BOM-001').first()
        
        assert queried_bom is not None
        assert queried_bom.bom_rid == 'TEST-BOM-001'
    
    def test_bom_repr(self, sample_bom):
        """Test BOM string representation"""
        repr_str = repr(sample_bom)
        assert 'BomItem' not in repr_str  # Note: it's just Bom
        assert 'bom_id' in repr_str


class TestModelRelationships:
    """Test model relationships and constraints"""
    
    def test_multiple_users(self, db_session):
        """Test creating multiple users"""
        user1 = User(user_name='user1', user_passwd='pass1', staff_id=1)
        user2 = User(user_name='user2', user_passwd='pass2', staff_id=2)
        
        db_session.add(user1)
        db_session.add(user2)
        db_session.commit()
        
        users = db_session.query(User).all()
        assert len(users) >= 2
    
    def test_user_without_required_field(self, db_session):
        """Test that user without required field fails"""
        user = User(user_passwd='pass123', staff_id=1)  # Missing user_name
        db_session.add(user)
        
        # Should raise an error when committing
        with pytest.raises(Exception):
            db_session.commit()
