"""Message model tests."""

# run these tests like:
#
#    python -m unittest test_message_model.py

import os
from unittest import TestCase
from models import db, User, Message
from app import app

# Set an environmental variable to use a different database for tests
os.environ['DATABASE_URL'] = "postgresql:///warbler-test"

# Create our tables
db.create_all()

class MessageModelTestCase(TestCase):
    """Test message model."""

    def setUp(self):
        """Create test client, add sample data."""
        db.drop_all()
        db.create_all()

        self.uid = 12345
        u = User.signup("testuser", "test@test.com", "password", None)
        u.id = self.uid
        db.session.commit()

        self.u = User.query.get(self.uid)

        self.client = app.test_client()

    def tearDown(self):
        """Clean up any fouled transaction."""
        db.session.rollback()

    def test_message_model(self):
        """Does basic model work?"""
        m = Message(
            text="A test message",
            user_id=self.uid
        )

        db.session.add(m)
        db.session.commit()

        # Message should have content and be linked to a user
        self.assertEqual(len(self.u.messages), 1)
        self.assertEqual(self.u.messages[0].text, "A test message")

    def test_repr(self):
        """Does the repr method work as expected?"""
        m = Message(
            text="A test message",
            user_id=self.uid
        )

        db.session.add(m)
        db.session.commit()

        self.assertEqual(repr(m), f"<Message #{m.id}: A test message, User #{m.user_id}>")

    def test_message_creation(self):
        """Does the Message model correctly create a new message with a valid input?"""
        m = Message(
            text="Another test message",
            user_id=self.uid
        )

        db.session.add(m)
        db.session.commit()

        self.assertEqual(m.text, "Another test message")
        self.assertEqual(m.user_id, self.uid)
