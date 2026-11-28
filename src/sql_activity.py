"""Capture SQL issued for one dashboard request on its own connection."""

from contextlib import contextmanager

from sqlalchemy import event


@contextmanager
def capture_sql(connection, queries):
    """Record SQL text and completion without logging parameter values."""
    if queries is None:
        yield
        return

    def before_execute(_connection, _cursor, statement, _parameters, _context, _many):
        queries.append({"sql": statement.strip(), "status": "failed"})

    def after_execute(_connection, _cursor, _statement, _parameters, _context, _many):
        queries[-1]["status"] = "completed"

    event.listen(connection, "before_cursor_execute", before_execute)
    event.listen(connection, "after_cursor_execute", after_execute)
    try:
        yield
    finally:
        event.remove(connection, "before_cursor_execute", before_execute)
        event.remove(connection, "after_cursor_execute", after_execute)
