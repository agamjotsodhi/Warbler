"""Message View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_message_views.py

import os
from unittest import TestCase

from models import db, connect_db, Message, User

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"

from app import app, CURR_USER_KEY

db.create_all()

app.config['WTF_CSRF_ENABLED'] = False

class MessageViewTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""
        db.drop_all()
        db.create_all()

        self.client = app.test_client()

        self.testuser1 = User.signup(username="testuser1",
                                     email="test1@test.com",
                                     password="testuser1",
                                     image_url=None)

        self.testuser2 = User.signup(username="testuser2",
                                     email="test2@test.com",
                                     password="testuser2",
                                     image_url=None)

        db.session.commit()

    def tearDown(self):
        """Clean up any fouled transaction."""
        db.session.rollback()

    def test_following_pages_logged_in(self):
        """Test if logged-in user can see following/follower pages."""
        with self.client as client:
            with client.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser1.id

            resp = client.get(f"/users/{self.testuser2.id}/following")
            self.assertEqual(resp.status_code, 200)

            resp = client.get(f"/users/{self.testuser2.id}/followers")
            self.assertEqual(resp.status_code, 200)

    def test_following_pages_logged_out(self):
        """Test if logged-out user cannot see following/follower pages."""
        with self.client as client:
            resp = client.get(f"/users/{self.testuser2.id}/following")
            self.assertEqual(resp.status_code, 302)
            self.assertIn('/login', resp.location)

            resp = client.get(f"/users/{self.testuser2.id}/followers")
            self.assertEqual(resp.status_code, 302)
            self.assertIn('/login', resp.location)

    def test_add_message_logged_in(self):
        """Test if logged-in user can add a message."""
        with self.client as client:
            with client.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser1.id

            resp = client.post("/messages/new", data={"text": "Hello"})
            self.assertEqual(resp.status_code, 302)

            msg = Message.query.one()
            self.assertEqual(msg.text, "Hello")

    def test_delete_message_logged_in(self):
        """Test if logged-in user can delete their own message."""
        msg = Message(text="test message", user_id=self.testuser1.id)
        db.session.add(msg)
        db.session.commit()

        with self.client as client:
            with client.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser1.id

            resp = client.post(f"/messages/{msg.id}/delete")
            self.assertEqual(resp.status_code, 302)

            msg = Message.query.get(msg.id)
            self.assertIsNone(msg)

  