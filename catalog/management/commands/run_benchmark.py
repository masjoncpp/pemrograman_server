import time
from django.core.management.base import BaseCommand
from django.db import connection
from django.db.models import Count
from django.test.utils import CaptureQueriesContext
from catalog.models import Course, Enrollment


class Command(BaseCommand):
    help = "Menjalankan seluruh skenario benchmark performa database sesuai Modul 5"

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("=== BENCHMARK PERFORMA DATABASE (MODUL 5) ==="))

        # Pastikan dataset tersedia
        total_courses = Course.objects.filter(code__startswith="PERF").count()
        if total_courses < 100:
            self.stderr.write(
                "Dataset belum lengkap. Jalankan generate_performance_data dan generate_relationship_data terlebih dahulu."
            )
            return

        self.stdout.write(f"Total Course PERF di database: {total_courses}\n")

        # -------------------------------------------------------------
        # 1. Course + Lecturer (select_related)
        # -------------------------------------------------------------
        self.stdout.write(self.style.SUCCESS("[1] Uji N+1 Course + Lecturer (100 Course)"))

        # BEFORE
        start = time.perf_counter()
        with CaptureQueriesContext(connection) as ctx_before_lec:
            courses = Course.objects.filter(code__startswith="PERF").order_by("code")[:100]
            result_before_lec = [(c.title, c.lecturer.username) for c in courses]
        time_before_lec = time.perf_counter() - start
        queries_before_lec = len(ctx_before_lec.captured_queries)

        # AFTER
        start = time.perf_counter()
        with CaptureQueriesContext(connection) as ctx_after_lec:
            courses = Course.objects.filter(code__startswith="PERF").order_by("code").select_related("lecturer")[:100]
            result_after_lec = [(c.title, c.lecturer.username) for c in courses]
        time_after_lec = time.perf_counter() - start
        queries_after_lec = len(ctx_after_lec.captured_queries)

        self.stdout.write(f"  BEFORE (Query biasa)     : {queries_before_lec} queries, {time_before_lec:.4f} detik")
        self.stdout.write(f"  AFTER  (select_related) : {queries_after_lec} queries, {time_after_lec:.4f} detik")
        improvement_lec = ((time_before_lec - time_after_lec) / time_before_lec * 100) if time_before_lec else 0
        self.stdout.write(f"  Query reduction: {queries_before_lec} -> {queries_after_lec} | Waktu improvement: {improvement_lec:.1f}%\n")

        # -------------------------------------------------------------
        # 2. Course + Lesson (prefetch_related)
        # -------------------------------------------------------------
        self.stdout.write(self.style.SUCCESS("[2] Uji N+1 Course + Lesson (50 Course)"))

        # BEFORE
        start = time.perf_counter()
        with CaptureQueriesContext(connection) as ctx_before_les:
            courses = Course.objects.filter(code__startswith="PERF").order_by("code")[:50]
            result_before_les = [[l.title for l in c.lessons.all()] for c in courses]
        time_before_les = time.perf_counter() - start
        queries_before_les = len(ctx_before_les.captured_queries)

        # AFTER
        start = time.perf_counter()
        with CaptureQueriesContext(connection) as ctx_after_les:
            courses = Course.objects.filter(code__startswith="PERF").order_by("code").prefetch_related("lessons")[:50]
            result_after_les = [[l.title for l in c.lessons.all()] for c in courses]
        time_after_les = time.perf_counter() - start
        queries_after_les = len(ctx_after_les.captured_queries)

        self.stdout.write(f"  BEFORE (Query biasa)      : {queries_before_les} queries, {time_before_les:.4f} detik")
        self.stdout.write(f"  AFTER  (prefetch_related) : {queries_after_les} queries, {time_after_les:.4f} detik")
        improvement_les = ((time_before_les - time_after_les) / time_before_les * 100) if time_before_les else 0
        self.stdout.write(f"  Query reduction: {queries_before_les} -> {queries_after_les} | Waktu improvement: {improvement_les:.1f}%\n")

        # -------------------------------------------------------------
        # 3. Teknik Optimasi Query Lain
        # -------------------------------------------------------------
        self.stdout.write(self.style.SUCCESS("[3] Teknik Optimasi Query Lain"))
        sample_course = Course.objects.get(code="PERF00001")
        has_enrollment = Enrollment.objects.filter(course=sample_course).exists()
        self.stdout.write(f"  exists()   : Ada mahasiswa terdaftar di PERF00001? {has_enrollment}")

        count_perf = Course.objects.filter(code__startswith="PERF").count()
        self.stdout.write(f"  count()    : Jumlah Course PERF: {count_perf}")

        values_sample = list(Course.objects.filter(code__startswith="PERF").values("code", "title")[:3])
        self.stdout.write(f"  values()   : {values_sample}")

        annotated_sample = list(
            Course.objects.filter(code__startswith="PERF")
            .annotate(jumlah_mahasiswa=Count("enrollments"))
            .order_by("code")
            .values("code", "jumlah_mahasiswa")[:3]
        )
        self.stdout.write(f"  annotate() : {annotated_sample}\n")

        # -------------------------------------------------------------
        # 4. Database Indexing & EXPLAIN
        # -------------------------------------------------------------
        self.stdout.write(self.style.SUCCESS("[4] Database Indexing & EXPLAIN"))
        qs_idx = Course.objects.filter(is_active=True, title="Performance Course 5000")
        
        start = time.perf_counter()
        _ = list(qs_idx)
        time_idx_query = time.perf_counter() - start
        
        explain_plan = qs_idx.explain()
        self.stdout.write(f"  Waktu eksekusi query filter: {time_idx_query:.6f} detik")
        self.stdout.write(f"  EXPLAIN Plan:\n{explain_plan}\n")

        # -------------------------------------------------------------
        # 5. Tabel Ringkasan untuk Laporan
        # -------------------------------------------------------------
        self.stdout.write(self.style.MIGRATE_HEADING("=== TABEL HASIL UNTUK LAPORAN ==="))
        self.stdout.write(f"| Percobaan         | Query BEFORE | Query AFTER | Waktu BEFORE | Waktu AFTER | Kesimpulan |")
        self.stdout.write(f"|-------------------|--------------|-------------|--------------|-------------|------------|")
        self.stdout.write(f"| Course + Lecturer | {queries_before_lec} queries   | {queries_after_lec} query    | {time_before_lec:.4f}s      | {time_after_lec:.4f}s     | N+1 terselesaikan via SQL JOIN |")
        self.stdout.write(f"| Course + Lesson   | {queries_before_les} queries   | {queries_after_les} queries   | {time_before_les:.4f}s      | {time_after_les:.4f}s     | N+1 terselesaikan via prefetch 2 queries |")
