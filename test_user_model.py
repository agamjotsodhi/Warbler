"""User model tests."""

import os
from unittest import TestCase
from models import db, User, Message, Follows
from app import app

# Set an environmental variable to use a different database for tests
os.environ['DATABASE_URL'] = "postgresql:///warbler-test"

# Create tables
db.create_all()

class UserModelTestCase(TestCase):
    """Test models for users."""

    def setUp(self):
        """Create test client, add sample data."""
        db.drop_all()
        db.create_all()

        u1 = User.signup("test1", "test1@test.com", "password", None)
        u1.id = 1111

        u2 = User.signup("test2", "test2@test.com", "password", None)
        u2.id = 2222

        db.session.commit()

        self.u1 = User.query.get(1111)
        self.u2 = User.query.get(2222)
        self.client = app.test_client()

    def tearDown(self):
        """Clean up any fouled transaction."""
        db.session.rollback()

    def test_user_model(self):
        """Does basic model work?"""
        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        db.session.add(u)
        db.session.commit()

        # User should have no messages & no followers
        self.assertEqual(len(u.messages), 0)
        self.assertEqual(len(u.followers), 0)

    def test_repr(self):
        """Does the repr method work as expected?"""
        self.assertEqual(repr(self.u1), f"<User #{self.u1.id}: test1, test1@test.com>")

    def test_is_following(self):
        """Does is_following successfully detect when user1 is following user2?"""
        self.u1.following.append(self.u2)
        db.session.commit()
        self.assertTrue(self.u1.is_following(self.u2))
        self.assertFalse(self.u2.is_following(self.u1))

    def test_is_followed_by(self):
        """Does is_followed_by successfully detect when user1 is followed by user2?"""
        self.u2.following.append(self.u1)
        db.session.commit()
        self.assertTrue(self.u1.is_followed_by(self.u2))
        self.assertFalse(self.u2.is_followed_by(self.u1))

    def test_signup(self):
        """Does User.signup successfully create a new user given valid credentials?"""
        u_test = User.signup("testtesttest", "testtest@test.com", "password", None)
        u_test.id = 99999
        db.session.commit()

        u_test = User.query.get(99999)
        self.assertIsNotNone(u_test)
        self.assertEqual(u_test.username, "testtesttest")
        self.assertEqual(u_test.email, "testtest@test.com")
        self.assertNotEqual(u_test.password, "password")
  

    
