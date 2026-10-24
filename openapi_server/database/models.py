import json
from decimal import Decimal

from sqlalchemy import Column, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.types import TypeDecorator, UserDefinedType


def _plain_numbers(value):
    """python-oracledb returns JSON numbers as Decimal; use int/float like asyncpg."""
    if isinstance(value, dict):
        return {k: _plain_numbers(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_plain_numbers(v) for v in value]
    if isinstance(value, Decimal):
        return int(value) if value == value.to_integral_value() else float(value)
    return value


class OracleJSON(UserDefinedType):
    """Oracle 21c+ native JSON column type (OSON binary storage)."""

    cache_ok = True

    def get_col_spec(self, **kw):
        return "JSON"


class JsonDocument(TypeDecorator):
    """JSON document column: JSONB on PostgreSQL, native JSON on Oracle."""

    impl = JSONB
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "oracle":
            return dialect.type_descriptor(OracleJSON())
        return dialect.type_descriptor(JSONB())

    def process_bind_param(self, value, dialect):
        if value is not None and dialect.name == "oracle":
            # Oracle converts JSON text implicitly when binding to a JSON column
            return json.dumps(value)
        return value

    def process_result_value(self, value, dialect):
        if isinstance(value, (str, bytes)):
            return json.loads(value)
        if dialect.name == "oracle":
            return _plain_numbers(value)
        return value


class Base(AsyncAttrs, DeclarativeBase):
    pass


class Service(Base):
    __tablename__ = "service"

    id = Column(Uuid, primary_key=True)  # uuid on PostgreSQL, CHAR(32) on Oracle
    payload = Column(JsonDocument, nullable=False)


class Hub(Base):
    """Event subscription (TMF630 hub): {"id", "href", "@type", "callback", "query"?}."""

    __tablename__ = "hub"

    id = Column(Uuid, primary_key=True)
    payload = Column(JsonDocument, nullable=False)
