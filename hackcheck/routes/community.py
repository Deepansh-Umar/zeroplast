from flask import Blueprint, jsonify
from flask_login import login_required, current_user
from sqlalchemy import func
from utils import nudge_for_items
from utils import estimate_impacts
import models

community_bp = Blueprint("community", __name__)

@community_bp.route('/api/community/stats')
@login_required
def api_community_stats():
    total_items = (models.db.session.query(func.sum(models.PlasticLog.quantity)).scalar() or 0)
    total_logs = models.PlasticLog.query.count()
    total_users = models.User.query.count()
    total_points = (models.db.session.query(func.sum(models.PointsLog.delta)).scalar() or 0)
    imp = estimate_impacts(total_items)
    return jsonify({"ok": True,
        "community": {"total_items": total_items, "total_logs": total_logs, "total_users": total_users, "total_points": total_points},
        "impact": imp
    })

@community_bp.route('/api/nudges')
@login_required
def api_nudges():
    my_items = sum(l.quantity for l in models.PlasticLog.query.filter_by(user_id=current_user.id).all())
    return jsonify({"ok": True, "nudge": {"message": nudge_for_items(my_items), "items": my_items}})
