"""
Out-of-session storage for bulk vocabulary-recommender results.

Previously the full match set, vocabulary scores and ranking tables were stuffed
into ``request.session``. With the database session backend that serialises a
large blob into the DB on every request, which is slow and bloats the session
table. Instead we keep only a short ``job_id`` in the session and store the
heavy payload in Django's cache, keyed by that id.

Note: the default cache backend is per-process ``LocMemCache``. Run the app with
a single Gunicorn worker (and multiple threads) so writes and reads share the
same process memory, e.g. ``gunicorn config.wsgi --workers 1 --threads 4``.
Swap in a shared backend (Redis/Memcached/DatabaseCache) to scale out.
"""

import uuid

from django.core.cache import cache

SESSION_JOB_KEY = "job_id"
_CACHE_PREFIX = "recommender_job:"


def _cache_key(job_id: str) -> str:
    return f"{_CACHE_PREFIX}{job_id}"


def start_job(session) -> str:
    """Create a fresh job id for the current session and return it."""
    job_id = uuid.uuid4().hex
    session[SESSION_JOB_KEY] = job_id
    return job_id


def save_recommender_data(session, data: dict) -> str:
    """
    Merge ``data`` into the cached payload for this session's job.

    Creates a job id if one does not exist yet. Returns the job id.
    """
    job_id = session.get(SESSION_JOB_KEY) or start_job(session)

    payload = cache.get(_cache_key(job_id)) or {}
    payload.update(data)
    cache.set(_cache_key(job_id), payload)

    return job_id


def get_recommender_data(session) -> dict:
    """Return the cached payload for this session's job (empty dict if none)."""
    job_id = session.get(SESSION_JOB_KEY)
    if not job_id:
        return {}
    return cache.get(_cache_key(job_id)) or {}


def clear_job(session) -> None:
    """Drop the cached payload and the session pointer (e.g. on new upload)."""
    job_id = session.pop(SESSION_JOB_KEY, None)
    if job_id:
        cache.delete(_cache_key(job_id))
