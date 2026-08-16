"""Custom SQLAlchemy Types and Engine Compatibility Helpers."""

import json
from typing import Any, List, Optional
from sqlalchemy import TypeDecorator, Text
from sqlalchemy.dialects.postgresql import JSONB


class CompatibleVector(TypeDecorator):
    """
    Vector type decorator that seamlessly uses pgvector on PostgreSQL
    and falls back to JSON-serialized Text on SQLite / testing engines.
    """
    impl = Text
    cache_ok = True

    def __init__(self, dimension: int = 1536, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.dimension = dimension

    def load_dialect_impl(self, dialect: Any) -> Any:
        if dialect.name == "postgresql":
            try:
                from pgvector.sqlalchemy import Vector
                return dialect.type_descriptor(Vector(self.dimension))
            except ImportError:
                return dialect.type_descriptor(Text())
        return dialect.type_descriptor(Text())

    def process_bind_param(self, value: Optional[List[float]], dialect: Any) -> Optional[Any]:
        if value is None:
            return None
        if dialect.name == "postgresql":
            return value
        return json.dumps(value)

    def process_result_value(self, value: Optional[Any], dialect: Any) -> Optional[List[float]]:
        if value is None:
            return None
        if isinstance(value, list):
            return [float(x) for x in value]
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
                if isinstance(parsed, list):
                    return [float(x) for x in parsed]
            except Exception:
                pass
        return None


class CompatibleJSON(TypeDecorator):
    """
    JSON type decorator that uses PostgreSQL JSONB when available
    and falls back to standard Text/JSON on SQLite.
    """
    impl = Text
    cache_ok = True

    def load_dialect_impl(self, dialect: Any) -> Any:
        if dialect.name == "postgresql":
            return dialect.type_descriptor(JSONB())
        return dialect.type_descriptor(Text())

    def process_bind_param(self, value: Any, dialect: Any) -> Optional[str]:
        if value is None:
            return None
        if dialect.name == "postgresql":
            return value
        return json.dumps(value)

    def process_result_value(self, value: Any, dialect: Any) -> Any:
        if value is None:
            return None
        if isinstance(value, (dict, list)):
            return value
        if isinstance(value, str):
            try:
                return json.loads(value)
            except Exception:
                return value
        return value
