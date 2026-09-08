from django.http import JsonResponse
from django.db import connection


def health_check(request):
    """
    Quick end-to-end check: confirms Django is running AND can reach the
    configured MySQL database. Visit /api/health/ once your .env and MySQL
    server are set up -- see backend/README.md.
    """
    db_status = "unknown"
    db_error = None
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        db_status = "connected"
    except Exception as exc:
        db_status = "unreachable"
        db_error = str(exc)

    payload = {
        "service": "AFEWS backend",
        "status": "ok",
        "database": db_status,
    }
    if db_error:
        payload["database_error"] = db_error

    return JsonResponse(payload)
