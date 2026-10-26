from datetime import timedelta
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone
from .models import Assignment, Course, Enrollment, Lesson, Submission

User = get_user_model()


class CourseTestCase(TestCase):
    def setUp(self):
        self.lecturer = User.objects.create_user(
            username="testlecturer",
            password="test12345",
            role="LECTURER",
        )

    # TEST 1: Course berhasil dibuat
    def test_course_created(self):
        course = Course.objects.create(
            code="TEST01",
            title="Test Course",
            lecturer=self.lecturer,
        )
        self.assertEqual(course.code, "TEST01")

    # TEST 2: Code Course harus unik
    def test_course_code_unique(self):
        Course.objects.create(
            code="TEST01",
            title="Course Pertama",
            lecturer=self.lecturer,
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Course.objects.create(
                    code="TEST01",
                    title="Course Kedua",
                    lecturer=self.lecturer,
                )

    # TEST 3: Lesson berelasi dengan Course
    def test_lesson_relationship(self):
        course = Course.objects.create(
            code="TEST02",
            title="Course Django",
            lecturer=self.lecturer,
        )
        lesson = Lesson.objects.create(
            course=course,
            title="Pengenalan Django",
            order=1,
        )
        self.assertEqual(lesson.course, course)
        self.assertEqual(course.lessons.count(), 1)


class LMSModelTests(TestCase):
    def setUp(self):
        self.lecturer = User.objects.create_user(
            username="dosen_test",
            email="dosen@test.com",
            password="password123",
            role=User.Role.LECTURER,
        )
        self.student = User.objects.create_user(
            username="student_test",
            email="student@test.com",
            password="password123",
            role=User.Role.STUDENT,
        )
        self.course = Course.objects.create(
            code="TEST01",
            title="Pengujian Perangkat Lunak",
            description="Testing course",
            lecturer=self.lecturer,
        )

    def test_course_creation_and_traversal(self):
        """Test Course creation, string representation, and lecturer relationship."""
        self.assertEqual(str(self.course), "TEST01 - Pengujian Perangkat Lunak")
        self.assertEqual(self.course.lecturer.username, "dosen_test")
        self.assertIn(self.course, self.lecturer.courses_taught.all())

    def test_lesson_creation_and_ordering_constraint(self):
        """Test Lesson ordering, constraints, and reverse relationship traversal."""
        lesson1 = Lesson.objects.create(
            course=self.course,
            title="Pelajaran 1",
            content="Materi 1",
            order=1,
        )
        lesson2 = Lesson.objects.create(
            course=self.course,
            title="Pelajaran 2",
            content="Materi 2",
            order=2,
        )

        self.assertEqual(self.course.lessons.count(), 2)
        self.assertEqual(lesson1.course, self.course)
        self.assertEqual(str(lesson1), "TEST01 - Pelajaran 1")

        # Duplicate (course, order) must violate unique constraint
        with self.assertRaises(IntegrityError):
            Lesson.objects.create(
                course=self.course,
                title="Pelajaran Duplikat",
                content="Materi Duplikat",
                order=1,
            )

    def test_enrollment_unique_constraint(self):
        """Test Enrollment intermediate model and unique student-course constraint."""
        enrollment = Enrollment.objects.create(
            student=self.student,
            course=self.course,
        )
        self.assertEqual(str(enrollment), f"{self.student.username} -> {self.course.code}")
        self.assertIsNotNone(enrollment.enrolled_at)

        # Duplicate enrollment should raise IntegrityError
        with self.assertRaises(IntegrityError):
            Enrollment.objects.create(
                student=self.student,
                course=self.course,
            )

    def test_assignment_and_submission(self):
        """Test Assignment and Submission creation and traversal."""
        deadline = timezone.now() + timedelta(days=7)
        assignment = Assignment.objects.create(
            course=self.course,
            title="Tugas 1",
            description="Deskripsi tugas",
            deadline=deadline,
        )
        submission = Submission.objects.create(
            assignment=assignment,
            student=self.student,
            content="Jawaban tugas",
            grade=90.00,
        )

        self.assertEqual(assignment.course, self.course)
        self.assertEqual(submission.assignment, assignment)
        self.assertEqual(submission.student, self.student)
        self.assertEqual(assignment.submissions.count(), 1)
        self.assertEqual(self.student.submissions.first(), submission)

    def test_query_traversal_and_optimization(self):
        """Test QuerySet select_related and prefetch_related for relationship traversal."""
        Lesson.objects.create(course=self.course, title="Lesson A", content="A", order=1)
        Lesson.objects.create(course=self.course, title="Lesson B", content="B", order=2)

        # Traversal via select_related
        courses = Course.objects.select_related("lecturer").filter(code="TEST01")
        for c in courses:
            self.assertEqual(c.lecturer.username, "dosen_test")

        # Traversal via prefetch_related
        courses_with_lessons = Course.objects.prefetch_related("lessons").filter(code="TEST01")
        for c in courses_with_lessons:
            self.assertEqual(c.lessons.count(), 2)
