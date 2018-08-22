from django.test import TestCase
from django.contrib.auth.models import User
from peerinst.auth import authenticate_student
from peerinst.models import Student, Teacher
from peerinst.students import (
    get_student_username_and_password,
    get_old_lti_student_username_and_password,
)


class TestAuthenticateStudent(TestCase):
    def test_user_doesnt_exist(self):
        tests = [{"email": "test@localhost"}, {"email": "test2@email.com"}]

        for test in tests:
            user = authenticate_student(**test)
            self.assertIsInstance(user, User)
            self.assertTrue(User.objects.filter(email=test["email"]).exists())
            self.assertTrue(
                Student.objects.filter(student__email=test["email"]).exists()
            )

    def test_standalone_student_exists(self):
        tests = [{"email": "test@localhost"}, {"email": "test2@email.com"}]

        for test in tests:
            username, password = get_student_username_and_password(**test)
            Student.objects.create(
                student=User.objects.create_user(
                    username=username, email=test["email"], password=password
                )
            )

            user = authenticate_student(**test)
            self.assertIsInstance(user, User)

    def test_standalone_user_exists(self):
        tests = [{"email": "test@localhost"}, {"email": "test2@email.com"}]

        for test in tests:
            username, password = get_student_username_and_password(**test)
            User.objects.create_user(
                username=username, email=test["email"], password=password
            )

            user = authenticate_student(**test)
            self.assertIsInstance(user, User)
            self.assertTrue(
                Student.objects.filter(student__email=test["email"]).exists()
            )

    def test_lti_student_exists(self):
        tests = [{"email": "test@localhost"}, {"email": "test2@email.com"}]

        for test in tests:
            user_id = test["email"][:-10]
            username, password = get_old_lti_student_username_and_password(
                user_id
            )
            Student.objects.create(
                student=User.objects.create_user(
                    username=username, email=test["email"], password=password
                )
            )
            new_username, _ = get_student_username_and_password(test["email"])

            user = authenticate_student(**test)
            self.assertIsInstance(user, User)
            self.assertEqual(len(User.objects.filter(email=test["email"])), 1)
            self.assertEqual(
                len(Student.objects.filter(student__email=test["email"])), 1
            )
            self.assertFalse(
                User.objects.filter(username=new_username).exists()
            )
            self.assertFalse(
                Student.objects.filter(student__username=new_username).exists()
            )

    def test_lti_user_exists(self):
        tests = [{"email": "test@localhost"}, {"email": "test2@email.com"}]

        for test in tests:
            user_id = test["email"][:-10]
            username, password = get_old_lti_student_username_and_password(
                user_id
            )
            User.objects.create_user(
                username=username, email=test["email"], password=password
            )
            new_username, _ = get_student_username_and_password(test["email"])

            user = authenticate_student(**test)
            self.assertIsInstance(user, User)
            self.assertEqual(len(User.objects.filter(email=test["email"])), 1)
            self.assertTrue(
                Student.objects.filter(student__email=test["email"]).exists()
            )
            self.assertEqual(
                len(Student.objects.filter(student__email=test["email"])), 1
            )
            self.assertFalse(
                User.objects.filter(username=new_username).exists()
            )
            self.assertFalse(
                Student.objects.filter(student__username=new_username).exists()
            )

    def test_standalone_user_exists_is_teacher(self):
        tests = [{"email": "test@localhost"}, {"email": "test2@email.com"}]

        for test in tests:
            username, password = get_student_username_and_password(**test)
            Teacher.objects.create(
                user=User.objects.create_user(
                    username=username, email=test["email"], password=password
                )
            )

            user = authenticate_student(**test)
            self.assertIsInstance(user, User)
            self.assertFalse(
                Student.objects.filter(student__email=test["email"]).exists()
            )

    def test_lti_user_exists_is_teacher(self):
        tests = [{"email": "test@localhost"}, {"email": "test2@email.com"}]

        for test in tests:
            user_id = test["email"][:-10]
            username, password = get_old_lti_student_username_and_password(
                user_id
            )
            Teacher.objects.create(
                user=User.objects.create_user(
                    username=username, email=test["email"], password=password
                )
            )

            user = authenticate_student(**test)
            self.assertIsInstance(user, User)
            self.assertTrue(
                User.objects.filter(email=test["email"] + "-lti").exists()
            )
            self.assertFalse(
                Student.objects.filter(
                    student__email=test["email"] + "-lti"
                ).exists()
            )
            self.assertFalse(
                Student.objects.filter(student__email=test["email"]).exists()
            )
