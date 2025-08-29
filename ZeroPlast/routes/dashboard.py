from flask import Blueprint, render_template, request, url_for
from flask_login import login_required, current_user
from datetime import datetime, timedelta
import models
import os
from utils import calculate_points, save_graph_by_item, save_graph_by_day

dashboard_bp = Blueprint("dashboard", __name__)

@dashboard_bp.route('/dashboard')
@login_required
def dashboard():
    user_points = calculate_points(current_user.id)
    today = datetime.utcnow().date()
    week_ago = today - timedelta(days=6)
    logs = models.PlasticLog.query.filter_by(user_id=current_user.id).order_by(models.PlasticLog.created_at.desc()).all()
    plastic_usage_today = sum(l.quantity for l in logs if l.created_at.date() == today)
    plastic_usage_week = sum(l.quantity for l in logs if l.created_at.date() >= week_ago)
    last_10_logs = logs[:10]
    # Generate and save graphs
    items_graph = save_graph_by_item(logs, current_user.id)
    days_graph = save_graph_by_day(logs, current_user.id)
    message = request.args.get('message')
    error = request.args.get('error')
    return render_template('dashboard.html',
                           user_points=user_points,
                           plastic_usage_today=plastic_usage_today,
                           plastic_usage_week=plastic_usage_week,
                           last_10_logs=last_10_logs,
                           items_graph=items_graph,
                           days_graph=days_graph,
                           message=message,
                           error=error)


