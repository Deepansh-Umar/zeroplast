from flask import Blueprint, jsonify, request, render_template
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

@plastic_bp.route('/plastic/add', methods=['GET', 'POST'])
@login_required
def add_log():
    if request.method == 'POST':
        item = (request.form.get('item') or '').strip()
        qty = int(request.form.get('quantity',1))
        if not item:
            return render_template('dashboard.html', error="Item required")
        log = models.PlasticLog(item=item, quantity=qty, user_id=current_user.id)
        db.session.add(log)
        db.session.add(models.PointsLog(user_id=current_user.id, delta=qty, reason='plastic_log'))
        db.session.commit()
        return render_template('dashboard.html', message="Plastic log added!")
    return render_template('add_plastic.html')

@plastic_bp.route('/scan', methods=['GET', 'POST'])
@login_required
def api_scan():
    if request.method == 'POST':
        code = (request.form.get('code') or '').strip()
        item = (request.form.get('item') or '').strip()
        qty = request.form.get('quantity'); quantity = None if qty is None else int(qty)

        if not item and code:
            if code.upper().startswith('BIN:'):
                bin_id = code.split(':',1)[1].strip().upper()
                mapped = SMART_BIN_MAP.get(bin_id)
                item, quantity = (mapped[0], mapped[1]) if mapped else (f"Smart Bin {bin_id}", 1)
            else:
                try:
                    import json as _json
                    payload = _json.loads(code)
                except Exception:
                    payload = None
                if payload:
                    item = payload.get('item', '')
                    quantity = payload.get('quantity', 1)
        # Save log if item is found
        if item:
            log = models.PlasticLog(item=item, quantity=quantity or 1, user_id=current_user.id)
            db.session.add(log)
            db.session.add(models.PointsLog(user_id=current_user.id, delta=quantity or 1, reason='scan'))
            db.session.commit()
            return render_template('dashboard.html', message="Scan log added!")
        return render_template('dashboard.html', error="No item found from scan.")
    return render_template('scan.html')
