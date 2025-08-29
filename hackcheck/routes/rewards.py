from flask import Blueprint, render_template, jsonify
from flask_login import login_required, current_user
from app_setup import db
import models
from utils import calculate_points

rewards_bp = Blueprint("rewards", __name__)

@rewards_bp.route('/rewards')
@login_required
def rewards_page():
    rewards = models.Reward.query.order_by(models.Reward.cost_points.asc()).all()
    return render_template('rewards.html', rewards=rewards, user_points=calculate_points(current_user.id))

@login_required
def redeem_reward(reward_id):
    reward = models.Reward.query.get(reward_id)
    if not reward: return jsonify({"ok": False, "error": "Reward not found"}), 404
    points = calculate_points(current_user.id)
    if points < reward.cost_points:
        return jsonify({"ok": False, "error": "Not enough points"}), 400
    db.session.add(models.Redemption(user_id=current_user.id, reward_id=reward.id))
    db.session.add(models.PointsLog(user_id=current_user.id, delta=-reward.cost_points, reason=f'redeem:{reward.name}'))
    db.session.commit()
    return jsonify({"ok": True})

@rewards_bp.route('/rewards/redeem/<int:reward_id>', methods=['POST'])
@login_required
def redeem_reward(reward_id):
    reward = models.Reward.query.get(reward_id)
    if not reward:
        return render_template('rewards.html', error="Reward not found")
    points = calculate_points(current_user.id)
    if points < reward.cost_points:
        return render_template('rewards.html', error="Not enough points")
    db.session.add(models.Redemption(user_id=current_user.id, reward_id=reward.id))
    db.session.add(models.PointsLog(user_id=current_user.id, delta=-reward.cost_points, reason=f'redeem:{reward.name}'))
    db.session.commit()
    return render_template('rewards.html', message="Reward redeemed!", rewards=models.Reward.query.order_by(models.Reward.cost_points.asc()).all(), user_points=calculate_points(current_user.id))
