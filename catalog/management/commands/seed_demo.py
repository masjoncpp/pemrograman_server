from datetime import timedelta
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone
from catalog.models import Assignment, Course, Enrollment, Lesson, Submission

User = get_user_model()


class Command(BaseCommand):
    help = "Seeds database with initial sample data idempotently as per Modul 4"

    def handle(self, *args, **options):
        self.stdout.write("Seeding sample data...")

        # 1. Superuser / Admin
        admin_user, created = User.objects.get_or_create(
            username="admin",
            defaults={
                "email": "admin@example.com",
                "role": User.Role.ADMIN,
                "is_staff": True,
                "is_superuser": True,
            },
        )
        if created:
            admin_user.set_password("admin123")
            admin_user.save()
        else:
            admin_user.role = User.Role.ADMIN
            admin_user.is_staff = True
            admin_user.is_superuser = True
            admin_user.save()
        self.stdout.write(f"- Admin user: {admin_user.username}")

        # 2. Lecturers
        lecturers_data = [
            ("suprayogi", "suprayogi@gmail.com", "12345"),
            ("agus", "agus@gmail.com", "123"),
            ("ayu", "ayu@gmail.com", "123"),
            ("bagus", "bagus@gmail.com", "123"),
            ("heru", "heru@gmail.com", "123"),
        ]
        lecturer_objects = {}
        for username, email, password in lecturers_data:
            user, u_created = User.objects.get_or_create(
                username=username,
                defaults={
                    "email": email,
                    "role": User.Role.LECTURER,
                },
            )
            if u_created:
                user.set_password(password)
                user.save()
            elif user.role != User.Role.LECTURER:
                user.role = User.Role.LECTURER
                user.save()
            lecturer_objects[username] = user
        self.stdout.write(f"- Lecturers created/verified: {len(lecturer_objects)}")

        # 3. Student (fauzan)
        student, s_created = User.objects.get_or_create(
            username="fauzan",
            defaults={
                "email": "fauzan@gmail.com",
                "role": User.Role.STUDENT,
            },
        )
        if s_created:
            student.set_password("12345")
            student.save()
        elif student.role != User.Role.STUDENT:
            student.role = User.Role.STUDENT
            student.save()
        self.stdout.write(f"- Student: {student.username}")

        # 4. Courses (PSS01 - PSS05)
        courses = [
            {
                "code": "PSS01",
                "title": "Pemrograman Sisi Server",
                "description": "Belajar backend development dengan Django.",
            },
            {
                "code": "PSS02",
                "title": "Django Framework",
                "description": "Mempelajari framework Django dan struktur project.",
            },
            {
                "code": "PSS03",
                "title": "Django ORM",
                "description": "Mempelajari database dan ORM menggunakan Django.",
            },
            {
                "code": "PSS04",
                "title": "REST API",
                "description": "Mempelajari pembuatan REST API dengan Django.",
            },
            {
                "code": "PSS05",
                "title": "Docker",
                "description": "Mempelajari containerisasi aplikasi Django.",
            },
        ]
        for data in courses:
            Course.objects.get_or_create(
                code=data["code"],
                defaults={
                    "title": data["title"],
                    "description": data["description"],
                    "lecturer": lecturer_objects["suprayogi"],
                },
            )
        course = Course.objects.get(code="PSS01")
        self.stdout.write(f"- Courses created/verified: {len(courses)}")

        # 5. Lessons
        lessons = [
            "Pengenalan Backend",
            "Pola Arsitektur Backend",
            "Containerisasi dengan Docker",
        ]
        for order, title in enumerate(lessons, start=1):
            Lesson.objects.get_or_create(
                course=course,
                order=order,
                defaults={
                    "title": title,
                },
            )
        self.stdout.write(f"- Lessons verified for {course.code}")

        # 6. Enrollment
        enrollment, _ = Enrollment.objects.get_or_create(
            student=student,
            course=course,
        )
        self.stdout.write(f"- Enrollment: {enrollment}")

        # 7. Assignments
        assignment1, _ = Assignment.objects.get_or_create(
            course=course,
            title="Tugas Django ORM",
            defaults={
                "description": "Implementasikan model dan relationship menggunakan Django ORM.",
                "deadline": timezone.now() + timedelta(days=7),
            },
        )
        assignment2, _ = Assignment.objects.get_or_create(
            course=course,
            title="Tugas REST API",
            defaults={
                "description": "Buat REST API sederhana menggunakan Django.",
                "deadline": timezone.now() + timedelta(days=14),
            },
        )
        self.stdout.write(f"- Assignments: {assignment1.title}, {assignment2.title}")

        # 8. Submissions
        Submission.objects.get_or_create(
            assignment=assignment1,
            student=student,
            defaults={
                "content": "Saya telah menyelesaikan implementasi Django ORM.",
                "grade": 87.5,
            },
        )
        Submission.objects.get_or_create(
            assignment=assignment2,
            student=student,
            defaults={
                "content": "Saya telah menyelesaikan REST API menggunakan Django.",
                "grade": 90.0,
            },
        )
        self.stdout.write(self.style.SUCCESS("Sample data berhasil dibuat."))
