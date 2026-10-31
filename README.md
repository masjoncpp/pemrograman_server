# Simple LMS — Backend Development & Database Optimization
**Pemrograman Sisi Server (A11.64707) · Milestone 4 & Milestone 5 (UTS)**

Repositori ini berisi implementasi **Simple LMS** (Learning Management System) berbasis Django, PostgreSQL, Docker Compose, serta eksperimen optimasi performa database, penanganan *N+1 Query*, dan *Database Indexing*.

---

## 1. Domain Models & Relasi Database

Project ini mengimplementasikan model domain LMS secara lengkap:
- **`User` (Custom User)**: Menggunakan `AbstractUser` dengan atribut `role` (`ADMIN`, `LECTURER`, `STUDENT`).
- **`Course`**: Model mata kuliah yang diampu oleh `User` (role `LECTURER`). Memiliki indeks komposit pada `["is_active", "title"]` untuk optimasi pencarian data.
- **`Lesson`**: Materi pembelajaran pada course dengan relasi `ForeignKey(Course)` dan constraint unik `(course, order)`.
- **`Enrollment`**: Intermediate model pendaftaran mahasiswa (`Student`) ke `Course` dengan constraint unik `(student, course)`.
- **`Assignment`**: Tugas pada course dengan atribut `title`, `description`, dan `deadline`.
- **`Submission`**: Pengumpulan tugas oleh student yang mencatat konten jawaban, waktu pengumpulan (`submitted_at`), dan nilai (`grade`).

---

## 2. Struktur Project

```text
.
├── compose.yaml
├── Dockerfile
├── requirements.txt
├── .env
├── .gitignore
├── .dockerignore
├── manage.py
├── README.md
├── config/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── users/
│   ├── models.py
│   ├── admin.py
│   ├── tests.py
│   └── migrations/
│       └── 0001_initial.py
└── catalog/
    ├── models.py
    ├── admin.py
    ├── tests.py
    ├── management/
    │   └── commands/
    │       ├── seed_demo.py
    │       ├── generate_performance_data.py
    │       ├── generate_relationship_data.py
    │       └── run_benchmark.py
    └── migrations/
        ├── 0001_initial.py
        ├── 0002_lesson.py
        ├── 0003_assignment_submission_enrollment.py
        └── 0004_course_catalog_cou_is_acti_d7f8f8_idx.py
```

---

## 3. Langkah Menjalankan Project

### A. Build dan Jalankan Container Docker
Jalankan service container aplikasi Django dan database PostgreSQL:
```bash
docker compose up -d --build
```

Pastikan seluruh container berjalan normal:
```bash
docker compose ps
```

### B. Menjalankan Migrasi Database
Terapkan semua file migrasi ke PostgreSQL:
```bash
docker compose exec app python manage.py migrate
```

### C. Seed Initial Sample Data (Data Demo)
Jalankan command management untuk mengisi database dengan data demo awal:
```bash
docker compose exec app python manage.py seed_demo
```
*Data yang dibuat:* 1 Admin, 5 Dosen (`suprayogi`, `agus`, `ayu`, `bagus`, `heru`), 1 Mahasiswa (`fauzan`), 5 Course (`PSS01`–`PSS05`), Lesson, Enrollment, Assignment, dan Submission.

---

## 4. Dataset Performa (Milestone 5)

Untuk pengujian performa query dalam skala besar ($\ge 10.000$ records), jalankan generator dataset berikut:

### A. Generate 10.000 Course Performa
Command ini membuat 10.000 data Course berkode `PERF00000` s/d `PERF09999` secara efisien dan idempotent menggunakan `bulk_create(batch_size=500)`:
```bash
docker compose exec app python manage.py generate_performance_data
```

### B. Generate Data Relasi LMS
Command ini membuat dataset relasi yang mencakup 5 Dosen simulasi, 50 Mahasiswa simulasi, 1.000 Enrollment, 500 Lesson, 200 Assignment, dan 1.000 Submission:
```bash
docker compose exec app python manage.py generate_relationship_data
```

---

## 5. Menjalankan Benchmark & Pengujian Optimasi Query

### A. Cara Cepat: Automated Benchmark Command
Jalankan command berikut untuk mengeksekusi seluruh pengujian performa secara otomatis:
```bash
docker compose exec app python manage.py run_benchmark
```
Command ini akan menampilkan metrik sebelum vs sesudah optimasi, efisiensi query, dan query plan `EXPLAIN`.

---

### B. Cara Manual via Django Shell
Masuk ke Django Shell interaktif:
```bash
docker compose exec app python manage.py shell
```

#### 1. Optimasi N+1: Course + Lecturer (`select_related`)
```python
import time
from django.db import connection
from django.test.utils import CaptureQueriesContext
from catalog.models import Course

# BEFORE: Query biasa (menghasilkan 101 query)
with CaptureQueriesContext(connection) as ctx:
    courses = Course.objects.filter(code__startswith='PERF').order_by('code')[:100]
    result = [(c.title, c.lecturer.username) for c in courses]
print("Query BEFORE:", len(ctx.captured_queries))

# AFTER: Menggunakan select_related (menghasilkan 1 query via SQL JOIN)
with CaptureQueriesContext(connection) as ctx:
    courses = Course.objects.filter(code__startswith='PERF').order_by('code').select_related('lecturer')[:100]
    result = [(c.title, c.lecturer.username) for c in courses]
print("Query AFTER:", len(ctx.captured_queries))
```

#### 2. Optimasi N+1: Course + Lesson (`prefetch_related`)
```python
# BEFORE: Query biasa (menghasilkan 51 query)
with CaptureQueriesContext(connection) as ctx:
    titles = [[l.title for l in c.lessons.all()] for c in Course.objects.filter(code__startswith='PERF').order_by('code')[:50]]
print("Query BEFORE:", len(ctx.captured_queries))

# AFTER: Menggunakan prefetch_related (menghasilkan 2 query)
with CaptureQueriesContext(connection) as ctx:
    titles = [[l.title for l in c.lessons.all()] for c in Course.objects.filter(code__startswith='PERF').order_by('code').prefetch_related('lessons')[:50]]
print("Query AFTER:", len(ctx.captured_queries))
```

#### 3. Database Indexing & EXPLAIN Analysis
```python
qs = Course.objects.filter(is_active=True, title='Performance Course 5000')
print(qs.explain(analyze=True))
# Hasil: Index Scan menggunakan catalog_cou_is_acti_d7f8f8_idx
```

---

## 6. Ringkasan Hasil Benchmark (Before vs After)

| Percobaan | Metrik BEFORE | Metrik AFTER | Improvement | Kesimpulan |
|---|---|---|---|---|
| **Course + Lecturer** | 101 query (0.2306s) | 1 query (0.0164s) | **92.89%** | Masalah N+1 terselesaikan via SQL JOIN (`select_related`) |
| **Course + Lesson** | 51 query | 2 query | **96.08%** query reduction | Masalah N+1 terselesaikan via 2-query batching (`prefetch_related`) |
| **Database Index** | `Seq Scan` (1.738ms, cost 239.06) | `Index Scan` (0.079ms, cost 8.30) | **95.45%** waktu | Pemindaian berpindah ke struktur B-Tree index komposit |

---

## 7. Menjalankan Automated Unit Tests

Jalankan test suite untuk memastikan seluruh logika bisnis, validasi model, dan relasi tetap berfungsi dengan baik:
```bash
docker compose exec app python manage.py test
```
*Hasil:* 11 test lulus (**OK**) tanpa ada error/regression.
