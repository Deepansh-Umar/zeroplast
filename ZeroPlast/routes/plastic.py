from flask import Blueprint, jsonify, request, render_template,url_for,redirect
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
        return redirect(url_for('dashboard.dashboard'))
    return render_template('add_plastic.html')

