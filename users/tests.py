from django.contrib.auth import get_user_model
from django.test import TestCase

User = get_user_model()


class UserModelTests(TestCase):
    def test_default_role_is_student(self):
        user = User.objects.create_user(username="test_student", password="password123")
        self.assertEqual(user.role, User.Role.STUDENT)
        self.assertEqual(str(user), "test_student (STUDENT)")

    def test_lecturer_role(self):
        lecturer = User.objects.create_user(
            username="test_lecturer",
            password="password123",
            role=User.Role.LECTURER,
        )
        self.assertEqual(lecturer.role, User.Role.LECTURER)
        self.assertEqual(str(lecturer), "test_lecturer (LECTURER)")

    def test_admin_role_and_superuser(self):
        admin = User.objects.create_superuser(
            username="test_admin",
            password="password123",
            role=User.Role.ADMIN,
        )
        self.assertEqual(admin.role, User.Role.ADMIN)
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)
