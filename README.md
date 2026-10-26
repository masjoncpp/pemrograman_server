# Modul Praktikum 4 — Django Framework & ORM
## Docker Development Environment + Core LMS Models

Praktikum Pemrograman Sisi Server (A11.64707) yang mengimplementasikan Core LMS Models menggunakan Django Framework, Django ORM, PostgreSQL, dan Docker Compose.

---

## 1. Domain LMS Models

Project ini mengimplementasikan model domain Simple LMS:
- **`User` (Custom User)**: Menggunakan `AbstractUser` dengan atribut `role` (`ADMIN`, `LECTURER`, `STUDENT`). Ditentukan sebelum initial migration auth.
- **`Course`**: Model mata kuliah/kelas yang diampu oleh seorang `User` dengan role `LECTURER`. Memiliki foreign key `lecturer` dengan `on_delete=PROTECT` dan `limit_choices_to={"role": "LECTURER"}`.
- **`Lesson`**: Materi di dalam course. Berelasi `ForeignKey(Course, on_delete=CASCADE, related_name="lessons")` dengan constraint unik `(course, order)`.
- **`Enrollment`**: Model intermediate yang menghubungkan `Student` (`role="STUDENT"`) dengan `Course`, mencatat tanggal pendaftaran (`enrolled_at`), serta mencegah duplikasi dengan constraint unik `(student, course)`.
- **`Assignment`**: Tugas pada sebuah course dengan field `deadline` dan `description`.
- **`Submission`**: Pengumpulan tugas oleh student yang berelasi ke `Assignment` dan `User` (student), mencatat waktu pengumpulan (`submitted_at`) dan nilai (`grade`).

---

## 2. Struktur Project

```text
week4/
├── compose.yaml
├── Dockerfile
├── requirements.txt
├── .env
├── .gitignore
├── .dockerignore
├── manage.py
├── config/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── users/
│   ├── __init__.py
│   ├── admin.py
│   ├── models.py
│   ├── tests.py
│   └── migrations/
│       ├── __init__.py
│       └── 0001_initial.py
└── catalog/
    ├── __init__.py
    ├── admin.py
    ├── models.py
    ├── tests.py
    ├── management/
    │   └── commands/
    │       └── seed_demo.py
    └── migrations/
        ├── __init__.py
        ├── 0001_initial.py
        ├── 0002_lesson.py
        └── 0003_assignment_submission_enrollment.py
```

---

## 3. Langkah Menjalankan Project

### A. Build dan Jalankan Container
Jalankan service container aplikasi Django dan database PostgreSQL:
```bash
docker compose up -d --build
```

Pastikan container berjalan:
```bash
docker compose ps
```

### B. Menjalankan Migrasi Database
Terapkan semua migration ke database PostgreSQL:
```bash
docker compose exec app python manage.py migrate
```

### C. Seed Sample Data (Idempotent)
Jalankan command management untuk mengisi database dengan data awal sesuai modul:
```bash
docker compose exec app python manage.py seed_demo
```

Data yang dibuat:
- **Admin**: `admin` (Role: ADMIN, is_staff=True, is_superuser=True)
- **Dosen / Lecturers**: `suprayogi`, `agus`, `ayu`, `bagus`, `heru` (Role: LECTURER)
- **Student**: `fauzan` (Role: STUDENT)
- **Courses**: `PSS01` s/d `PSS05` (*Pemrograman Sisi Server*, *Django Framework*, *Django ORM*, *REST API*, *Docker*)
- **Lessons**: 3 materi pelajaran terurut pada `PSS01`
- **Enrollment**: `fauzan` terdaftar pada `PSS01`
- **Assignments**: *Tugas Django ORM* dan *Tugas REST API* pada `PSS01`
- **Submissions**: Jawaban dari student `fauzan` dengan nilai `87.50` dan `90.00`

### D. Mengakses Django Admin
Buka browser pada URL:
[http://localhost:8000/admin/](http://localhost:8000/admin/)

Login menggunakan kredensial:
- **Username**: `admin`
- **Password**: `admin123`

### E. Menjalankan Unit Tests
Jalankan pengujian unit test model dan relasi domain:
```bash
docker compose exec app python manage.py test
```

Semua pengujian mencakup:
1. Validasi Custom User model dan role default `STUDENT`.
2. Validasi Course model, relasi Dosen, dan string representation.
3. Validasi Lesson ordering, unique constraint `(course, order)`, dan reverse relationship.
4. Validasi Intermediate model Enrollment dan unique constraint `(student, course)`.
5. Validasi Assignment dan Submission beserta foreign key relasinya.
6. Validasi optimasi query traversal (`select_related` dan `prefetch_related`).

---

## 4. Query Traversal & Optimasi Query (Django Shell)

Untuk mencoba penelusuran relasi dan optimasi query N+1:
```bash
docker compose exec app python manage.py shell
```

```python
from catalog.models import Course
from django.db import connection, reset_queries

# Optimasi 1: One-to-One / ForeignKey traversal menggunakan select_related
reset_queries()
for course in Course.objects.select_related("lecturer"):
    print(course.code, "Dosen:", course.lecturer.username)
print("Query count:", len(connection.queries))  # Menghasilkan 1 query

# Optimasi 2: Reverse ForeignKey / One-to-Many traversal menggunakan prefetch_related
reset_queries()
for course in Course.objects.prefetch_related("lessons"):
    print(course.code)
    for lesson in course.lessons.all():
        print(" -", lesson.title)
print("Query count:", len(connection.queries))  # Menghasilkan 2 query
```
