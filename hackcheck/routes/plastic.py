from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from app_setup import db
import models
from utils import calculate_points

plastic_bp = Blueprint("plastic", __name__)

SMART_BIN_MAP = {
    'BIN001': ('Plastic Bottle', 1, 'bottle'),
    'BIN002': ('Plastic Bag', 1, 'bag'),
    'BIN003': ('Food Container', 1, 'container'),
}

@plastic_bp.route('/api/plastic/logs')
@login_required
def get_logs():
    logs = models.PlasticLog.query.filter_by(user_id=current_user.id).all()
    return jsonify({"logs":[{"id":l.id,"item":l.item,"quantity":l.quantity} for l in logs]})

@plastic_bp.route('/api/plastic/add', methods=['POST'])
@login_required
def add_log():
    data = request.get_json() or {}
    item = (data.get('item') or '').strip()
    qty = int(data.get('quantity',1))
    if not item: return jsonify({"ok": False, "error": "Item required"}), 400
    log = models.PlasticLog(item=item, quantity=qty, user_id=current_user.id)
    db.session.add(log)
    db.session.add(models.PointsLog(user_id=current_user.id, delta=qty, reason='plastic_log'))
    db.session.commit()
    return jsonify({"ok": True})

@plastic_bp.route('/api/scan', methods=['POST'])
@login_required
def api_scan():
    data = request.get_json() or {}
    code = (data.get('code') or '').strip()
    item = (data.get('item') or '').strip()
    qty = data.get('quantity'); quantity = None if qty is None else int(qty)

    if not item and code:
        if code.upper().startswith('BIN:'):
            bin_id = code.split(':',1)[1].strip().upper()
            mapped = SMART_BIN_MAP.get(bin_id)
            item, quantity = (mapped[0], mapped[1]) if mapped else (f"Smart Bin {bin_id}", 1)
        else:
            try:
                import json as _json
                payload = _json.loads(code)
                item = str(payload.get('item','')).strip()
                quantity = int(payload.get('quantity',1))
            except Exception:
                item = code; quantity = quantity or 1

    if not item: return jsonify({"ok": False, "error": "No item found in scan"}), 400
    if quantity is None: quantity = 1
    if quantity <= 0: return jsonify({"ok": False, "error": "Quantity must be positive"}), 400

    log = models.PlasticLog(user_id=current_user.id, item=item, quantity=quantity)
    db.session.add(log)
    db.session.add(models.PointsLog(user_id=current_user.id, delta=quantity, reason='qr_scan'))
    db.session.commit()
    return jsonify({"ok": True, "log": {"id": log.id, "item": log.item, "quantity": log.quantity},
                    "points": calculate_points(current_user.id)}), 201
