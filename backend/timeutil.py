"""UTC time helpers.

``datetime.datetime.utcnow()`` is deprecated since Python 3.12. The codebase
stores naive UTC timestamps (SQLite/PostgreSQL ``DateTime`` columns without
timezone), so this helper keeps that exact contract: it returns a *naive*
datetime representing the current UTC time, without the deprecation warning.
"""
import datetime


def utcnow() -> datetime.datetime:
    """Return the current UTC time as a naive datetime (drop-in for utcnow())."""
    return datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
