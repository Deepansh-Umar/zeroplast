from flask import Blueprint, render_template
from flask_login import login_required, current_user
from collections import defaultdict
import models
from utils import estimate_impacts
admin_bp = Blueprint("admin", __name__)

def aggregate_daily_logs():
    daily = defaultdict(int)
    for l in models.PlasticLog.query.all():
        key = l.created_at.strftime('%Y-%m-%d')
        daily[key] += l.quantity
    dates = sorted(daily.keys())
    values = [daily[d] for d in dates]
    return dates, values

@admin_bp.route('/admin')
@login_required
def admin_dashboard():
    if getattr(current_user, "role", "user") != "admin":
        return "Unauthorized", 403
    logs = models.PlasticLog.query.all()
    total_items = sum(l.quantity for l in logs)
    totals = {
        "items": total_items,
        "logs": len(logs),
        "users": models.User.query.count(),
        "points": sum(p.delta for p in models.PointsLog.query.all())
    }
    totals.update(estimate_impacts(total_items))
    dates, values = aggregate_daily_logs()
    recs = [
        'Ban single-use plastics at all campus events and canteens',
        'Install mandatory water refill stations in every building',
        'Vendor contracts must use reusable/compostable packaging',
        'Offer BYO discounts at partner vendors',
        'Run a “Plastic-Free Week” each semester',
    ]
    if total_items > 500:
        recs.append('Set department-level reduction targets with monthly reporting')
    if totals["users"] > 50:
        recs.append('Launch inter-department eco-leaderboards with small grants')

    return render_template('admin.html',
        totals=totals, trend_labels=dates, trend_values=values, recommendations=recs)
