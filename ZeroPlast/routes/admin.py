from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from collections import defaultdict
import models
from utils import estimate_impacts_from_counts,generate_trend_graph
import base64
from flask import send_file
from io import BytesIO

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
def admin():
    logs = models.PlasticLog.query.all()
    total_items = int(sum([l.quantity for l in logs]))
    by_item = {}
    for l in logs:
        by_item[l.item] = by_item.get(l.item, 0) + l.quantity
    totals = {
        "logs": len(logs),
        "users": models.User.query.count(),
        "points": sum(p.delta for p in models.PointsLog.query.all())
    }
    totals.update(estimate_impacts_from_counts(by_item))
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

    vendors = models.Vendor.query.all()
    users = models.User.query.all()
    return render_template('admin.html',
       trend_labels=dates, trend_values=values, recommendations=recs, tot_it=total_items,
        vendors=vendors, users=users, totals=totals)



# Vendors list page
@admin_bp.route('/admin/vendors')
@login_required
def vendors_page():
    logs = models.PlasticLog.query.all()
    total_items = int(sum([l.quantity for l in logs]))
    by_item = {}
    for l in logs:
        by_item[l.item] = by_item.get(l.item, 0) + l.quantity
    totals = {
        "logs": len(logs),
        "users": models.User.query.count(),
        "points": sum(p.delta for p in models.PointsLog.query.all())
    }
    totals.update(estimate_impacts_from_counts(by_item))
    recs = [
        'Ban single-use plastics at all campus events and canteens',
        'Install mandatory water refill stations in every building',
        'Vendor contracts must use reusable/compostable packaging',
        'Offer BYO discounts at partner vendors',
        'Run a “Plastic-Free Week” each semester',
    ]
    vendors = models.Vendor.query.all()
    users = models.User.query.all()
    return render_template('admin.html', vendors=vendors, users=users, totals=totals, recommendations=recs, tot_it=total_items, trend_labels=[], trend_values=[])

# Vendor detail page
@admin_bp.route('/admin/vendor/<int:vendor_id>')
@login_required
def vendor_detail(vendor_id):
    vendor = models.Vendor.query.get_or_404(vendor_id)
    alternatives = models.AlternativeItem.query.filter_by(vendor_id=vendor.id).all()
    return render_template('vendor.html', vendor=vendor, alternatives=alternatives)


# Users list page
@admin_bp.route('/admin/users')
@login_required
def users_page():
    logs = models.PlasticLog.query.all()
    total_items = int(sum([l.quantity for l in logs]))
    by_item = {}
    for l in logs:
        by_item[l.item] = by_item.get(l.item, 0) + l.quantity
    totals = {
        "logs": len(logs),
        "users": models.User.query.count(),
        "points": sum(p.delta for p in models.PointsLog.query.all())
    }
    totals.update(estimate_impacts_from_counts(by_item))
    recs = [
        'Ban single-use plastics at all campus events and canteens',
        'Install mandatory water refill stations in every building',
        'Vendor contracts must use reusable/compostable packaging',
        'Offer BYO discounts at partner vendors',
        'Run a “Plastic-Free Week” each semester',
    ]
    vendors = models.Vendor.query.all()
    users = models.User.query.all()
    return render_template('admin.html', users=users, vendors=vendors, totals=totals, recommendations=recs, tot_it=total_items, trend_labels=[], trend_values=[])

# User detail page
@admin_bp.route('/admin/user/<int:user_id>')
@login_required
def user_detail(user_id):
    user = models.User.query.get_or_404(user_id)
    # Calculate total points for user
    total_points = sum(p.delta for p in models.PointsLog.query.filter_by(user_id=user.id).all())
    user.total_points = total_points
    return render_template('user.html', user=user)

# Host a challenge (admin only)
@admin_bp.route('/admin/host-challenge', methods=['POST'])
@login_required
def host_challenge():
    if not hasattr(current_user, 'username') or current_user.username.lower() != 'admin':
        flash('Only admin can host challenges.', 'danger')
        return redirect(url_for('admin.admin'))
    name = request.form.get('name')
    description = request.form.get('description')
    start_date = request.form.get('start_date')
    end_date = request.form.get('end_date')
    points_bonus = request.form.get('points_bonus', 10)
    from datetime import datetime
    challenge = models.Challenge(
        name=name,
        description=description,
        start_date=datetime.strptime(start_date, '%Y-%m-%d'),
        end_date=datetime.strptime(end_date, '%Y-%m-%d'),
        points_bonus=points_bonus
    )
    import app_setup
    app_setup.db.session.add(challenge)
    app_setup.db.session.commit()
    flash('Challenge hosted successfully!', 'success')
    return redirect(url_for('admin.admin'))


# Challenges list page for admin
@admin_bp.route('/admin/challenges')
@login_required
def challenges_page():
    challenges = models.Challenge.query.order_by(models.Challenge.start_date.desc()).all()
    return render_template('challenges.html', challenges=challenges)