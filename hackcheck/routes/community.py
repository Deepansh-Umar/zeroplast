from flask import Blueprint, jsonify, render_template
from flask_login import login_required, current_user
from sqlalchemy import func
from utils import nudge_for_items, estimate_impacts, nudge_for_user, community_impact_summary

community_bp = Blueprint("community", __name__)
@community_bp.route('/community')
@login_required
def community_page():
    nudge = nudge_for_user(current_user.id)
    community = community_impact_summary()
    return render_template('community.html', nudge=nudge, community=community)
import models


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
