from __future__ import annotations

from marshmallow import Schema, fields, validate
from models import PresenceStatus


class PresenceUpdateSchema(Schema):
    status = fields.Str(required=True, validate=validate.OneOf([s.value for s in PresenceStatus]))
    reason = fields.Str(allow_none=True)
    version = fields.Int(required=True)


class PresenceSnapshotSchema(Schema):
    grade = fields.Int(required=True)
    class_no = fields.Int(required=True)
    number = fields.Int(required=True)
    status = fields.Str(required=True)
    reason = fields.Str(allow_none=True)
    version = fields.Int(required=True)


class LogQuerySchema(Schema):
    since = fields.DateTime(required=False)
    limit = fields.Int(required=False, missing=100)


class CsrfSchema(Schema):
    csrf_token = fields.Str(required=True)
