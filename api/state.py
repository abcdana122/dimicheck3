# api/state.py
from datetime import datetime, timezone
from functools import wraps

from flask import Blueprint, request, jsonify, session
from extensions import db
from models import SavedBlob  # 위에서 추가한 모델

blueprint = Blueprint("state", __name__, url_prefix="/api/state")

def api_error(status, code, message):
    resp = jsonify({"error": {"code": code, "message": message}})
    resp.status_code = status
    return resp

def require_login(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("user"):
            return api_error(401, "unauthorized", "로그인이 필요합니다.")
        return fn(*args, **kwargs)
    return wrapper

def current_user_id():
    u = session.get("user") or {}
    return u.get("id") or u.get("user_id")

# ===== magnets =====
@blueprint.route("/magnets", methods=["GET"])
@require_login
def get_magnets():
    scope_key = request.args.get("scope_key", "default")
    owner_id = current_user_id()
    row = SavedBlob.query.filter_by(owner_id=owner_id, blob_type="magnets", key=scope_key).first()
    if not row:
        # 비어있는 상태를 그대로 반환하면 프런트가 그냥 무시
        return jsonify({"v": 1, "magnets": {}, "updated_at": None, "exists": False})
    return jsonify({
        "v": row.version,
        "magnets": row.data.get("magnets", {}),
        "updated_at": row.updated_at.astimezone(timezone.utc).isoformat(),
        "exists": True
    })

@blueprint.route("/magnets", methods=["PUT", "POST"])
@require_login
def upsert_magnets():
    payload = request.get_json(silent=True) or {}
    magnets = payload.get("magnets")
    if not isinstance(magnets, dict):
        return api_error(400, "invalid_payload", "magnets 필드는 객체여야 합니다.")
    scope_key = payload.get("scope_key", "default")
    version = int(payload.get("v") or 1)
    owner_id = current_user_id()

    now = datetime.now(timezone.utc)
    row = SavedBlob.query.filter_by(owner_id=owner_id, blob_type="magnets", key=scope_key).first()
    if row:
        row.version = version
        row.data = {"magnets": magnets}
        row.updated_at = now
    else:
        row = SavedBlob(owner_id=owner_id, blob_type="magnets", key=scope_key,
                        version=version, data={"magnets": magnets}, updated_at=now)
        db.session.add(row)
    db.session.commit()
    return jsonify({"ok": True, "updated_at": now.isoformat()})

@blueprint.route("/magnets", methods=["DELETE"])
@require_login
def delete_magnets():
    scope_key = request.args.get("scope_key", "default")
    owner_id = current_user_id()
    row = SavedBlob.query.filter_by(owner_id=owner_id, blob_type="magnets", key=scope_key).first()
    if not row:
        return api_error(404, "not_found", "삭제할 데이터가 없습니다.")
    db.session.delete(row)
    db.session.commit()
    return jsonify({"ok": True})

# ===== timetable =====
@blueprint.route("/timetable/<string:key>", methods=["GET"])
@require_login
def get_timetable(key):
    owner_id = current_user_id()
    row = SavedBlob.query.filter_by(owner_id=owner_id, blob_type="timetable", key=key).first()
    if not row:
        return api_error(404, "not_found", "데이터가 없습니다.")
    return jsonify({
        "data": row.data,
        "updated_at": row.updated_at.astimezone(timezone.utc).isoformat(),
    })

@blueprint.route("/timetable/<string:key>", methods=["PUT", "POST"])
@require_login
def upsert_timetable(key):
    payload = request.get_json(silent=True) or {}
    if "data" not in payload:
        return api_error(400, "invalid_payload", "data 필드가 필요합니다.")
    owner_id = current_user_id()
    now = datetime.now(timezone.utc)

    row = SavedBlob.query.filter_by(owner_id=owner_id, blob_type="timetable", key=key).first()
    if row:
        row.data = payload["data"]
        row.updated_at = now
    else:
        row = SavedBlob(owner_id=owner_id, blob_type="timetable", key=key,
                        version=1, data=payload["data"], updated_at=now)
        db.session.add(row)
    db.session.commit()
    return jsonify({"ok": True, "updated_at": now.isoformat()})

@blueprint.route("/timetable/<string:key>", methods=["DELETE"])
@require_login
def delete_timetable(key):
    owner_id = current_user_id()
    row = SavedBlob.query.filter_by(owner_id=owner_id, blob_type="timetable", key=key).first()
    if not row:
        return api_error(404, "not_found", "삭제할 데이터가 없습니다.")
    db.session.delete(row)
    db.session.commit()
    return jsonify({"ok": True})
