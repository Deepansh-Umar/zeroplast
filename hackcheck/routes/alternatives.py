from flask import Blueprint, jsonify, request
from flask_login import login_required
from utils import alternative_for

alts_bp = Blueprint("alternatives", __name__)

@alts_bp.route('/api/alternatives')
@login_required
def api_alternatives():
    item_key = (request.args.get('item_key') or '').strip().lower()
    if not item_key:
        return jsonify({"ok": False, "error": "item_key required"}), 400
    return jsonify({"ok": True, "alternatives": alternative_for(item_key)})
