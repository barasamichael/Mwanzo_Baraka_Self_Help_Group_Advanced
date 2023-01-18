import unittest
from app.models import user

class UserModelTestCase(unittest.TestCase):
    def test_password_setter(self):
        """Ensures that a password hash is generated and not None value"""

        u = user(password = "john")
        self.assertTrue(u.password_hash is not None)


    def test_no_password_getter(self):
        """Ensures that password attribute is write-only"""

        u = user(password = "john")
        with self.assertRaises("AttributeError"):
            u.password


    def test_password_verification(self):
        """Ensures password verification works appropriately"""

        u = user(password = "john")
        self.assertTrue(u.verify_password('john'))
        self.assertFalse(u.verify_password('mark'))


    def test_password_salts_are_random(self):
        """Ensures password salts generated are random"""

        user_1 = user(password = "john")
        user_2 = user(password = "acts")
        self.assertTrue(user_1.password_hash != user_2.password_hash)
