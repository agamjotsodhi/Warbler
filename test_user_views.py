"""User view tests."""

import os
from unittest import TestCase
from models import db, User, Message
from app import app, CURR_USER_KEY

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"
app.config['WTF_CSRF_ENABLED'] = False

db.create_all()

class UserViewTestCase(TestCase):
    """Test views for users."""

    def setUp(self):
        """Create test client, add sample data."""
        db.drop_all()
        db.create_all()

        self.client = app.test_client()

        self.testuser = User.signup(username="testuser", email="test@test.com", password="testuser", image_url=None)
        self.testuser.id = 1111
        db.session.commit()

    def tearDown(self):
        """Clean up any fouled transaction."""
        db.session.rollback()

    def test_user_show(self):
        """Can we see a user's profile?"""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.get(f"/users/{self.testuser.id}")
            self.assertEqual(resp.status_code, 200)
            self.assertIn(b"testuser", resp.data)

    def test_user_following(self):
        """Can we see who a user is following?"""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.get(f"/users/{self.testuser.id}/following")
            self.assertEqual(resp.status_code, 200)
            self.assertIn(b"Following", resp.data)

    def test_user_followers(self):
        """Can we see who is following a user?"""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.get(f"/users/{self.testuser.id}/followers")
            self.assertEqual(resp.status_code, 200)
            self.assertIn(b"Followers", resp.data)
