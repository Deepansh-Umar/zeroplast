from flask import render_template, redirect, url_for, request, jsonify
from flask_login import login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import func
from datetime import datetime
from app_setup import create_app, db, login_manager
import models

app = create_app()

# -----------------------
# User Loader
# -----------------------
@login_manager.user_loader
def load_user(user_id):
    return models.User.query.get(int(user_id))


# -----------------------
# Routes
# -----------------------

@app.route('/')
@login_required
def dashboard():
    return render_template("dashboard.html")


# -------- AUTH ---------
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        if models.User.query.filter_by(username=username).first():
            return "Username already exists"
        new_user = models.User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('signup.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = models.User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        return "Invalid credentials"

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


# -------- Plastic Logs ---------
@app.route('/api/plastic/add', methods=['POST'])
@login_required
def add_plastic():
    data = request.json
    item = data.get('item')
    quantity = data.get('quantity')

    if not item or not quantity:
        return jsonify({"error": "Invalid input"}), 400

    log = models.PlasticLog(item=item, quantity=quantity, user_id=current_user.id)
    db.session.add(log)

    # Add equivalent points
    points = models.PointsLog(user_id=current_user.id, delta=quantity, reason="Plastic log")
    db.session.add(points)

    db.session.commit()
    return jsonify({"message": "Plastic logged", "points": quantity})


# -------- QR Code Scanning ---------
@app.route('/api/scan', methods=['POST'])
@login_required
def scan_qr():
    data = request.json
    item = data.get('item')
    quantity = data.get('quantity')

    if not item or not quantity:
        return jsonify({"error": "Invalid scan"}), 400

    log = models.PlasticLog(item=item, quantity=quantity, user_id=current_user.id)
    db.session.add(log)

    points = models.PointsLog(user_id=current_user.id, delta=quantity, reason="QR Scan")
    db.session.add(points)

    db.session.commit()
    return jsonify({"message": f"QR scan successful: {item} x{quantity}"})


# -------- Vendor Discounts ---------
@app.route('/vendors')
@login_required
def vendors():
    vendor_list = models.Vendor.query.all()
    return render_template("vendors.html", vendors=vendor_list)


# -------- Rewards ---------
@app.route('/rewards')
@login_required
def rewards():
    reward_list = models.Reward.query.all()
    return render_template("rewards.html", rewards=reward_list)


@app.route('/rewards/redeem/<int:reward_id>', methods=['POST'])
@login_required
def redeem_reward(reward_id):
    reward = models.Reward.query.get_or_404(reward_id)
    points = calculate_points(current_user.id)

    if points < reward.cost_points:
        return jsonify({"error": "Not enough points"}), 400

    redemption = models.Redemption(user_id=current_user.id, reward_id=reward_id)
    db.session.add(redemption)

    # Deduct points
    points_log = models.PointsLog(user_id=current_user.id, delta=-reward.cost_points, reason=f"Redeemed {reward.name}")
    db.session.add(points_log)

    db.session.commit()
    return jsonify({"message": f"Redeemed {reward.name}"})


# -------- Teams ---------
@app.route('/teams')
@login_required
def teams():
    team_list = models.Team.query.all()
    return render_template("teams.html", teams=team_list)


@app.route('/teams/join/<int:team_id>', methods=['POST'])
@login_required
def join_team(team_id):
    existing = models.TeamMembership.query.filter_by(user_id=current_user.id, team_id=team_id).first()
    if existing:
        return jsonify({"error": "Already in team"}), 400

    membership = models.TeamMembership(user_id=current_user.id, team_id=team_id)
    db.session.add(membership)
    db.session.commit()
    return jsonify({"message": f"Joined team {team_id}"})


# -------- Challenges ---------
@app.route('/challenges')
@login_required
def challenges():
    challenge_list = models.Challenge.query.all()
    return render_template("challenges.html", challenges=challenge_list)


@app.route('/challenges/join/<int:challenge_id>', methods=['POST'])
@login_required
def join_challenge(challenge_id):
    existing = models.ChallengeParticipation.query.filter_by(
        user_id=current_user.id, challenge_id=challenge_id
    ).first()

    if existing:
        return jsonify({"error": "Already joined"}), 400

    participation = models.ChallengeParticipation(user_id=current_user.id, challenge_id=challenge_id)
    db.session.add(participation)
    db.session.commit()
    return jsonify({"message": f"Joined challenge {challenge_id}"})


# -------- Community Stats ---------
@app.route('/community')
@login_required
def community():
    total_plastic = db.session.query(func.sum(models.PlasticLog.quantity)).scalar() or 0
    total_points = db.session.query(func.sum(models.PointsLog.delta)).scalar() or 0
    top_users = db.session.query(
        models.User.username, func.sum(models.PointsLog.delta).label("points")
    ).join(models.PointsLog, models.User.id == models.PointsLog.user_id).group_by(models.User.id).all()

    return render_template("community.html", total_plastic=total_plastic,
                           total_points=total_points, top_users=top_users)


# -------- Nudges ---------
@app.route('/nudge')
@login_required
def nudge():
    return jsonify({"message": "🌱 Remember to log your plastic today!"})


# -------- Admin Dashboard ---------
@app.route('/admin')
@login_required
def admin_dashboard():
    if current_user.username != "Admin":
        return "Unauthorized", 403
    return render_template("admin.html")


# -----------------------
# Helpers
# -----------------------
def calculate_points(user_id):
    total = db.session.query(func.sum(models.PointsLog.delta)).filter_by(user_id=user_id).scalar()
    return total or 0


# -----------------------
# Main Entry
# -----------------------
if __name__ == "__main__":
    app.run(debug=True)
