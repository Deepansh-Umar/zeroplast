from datetime import datetime
from flask_login import UserMixin
from app_setup import db

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))
    email = db.Column(db.String(150), unique=True)

    logs = db.relationship('PlasticLog', backref='user')

class PlasticLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item = db.Column(db.String(150))
    quantity = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

class PointsLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    delta = db.Column(db.Integer, nullable=False)
    reason = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Vendor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    discount = db.Column(db.Integer, default=0)
    description = db.Column(db.String(300), default='')

class Reward(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    cost_points = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(300), default='')

class Redemption(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    reward_id = db.Column(db.Integer, db.ForeignKey('reward.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Team(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)

class TeamMembership(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Challenge(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.String(400), default='')
    start_date = db.Column(db.DateTime, nullable=True)
    end_date = db.Column(db.DateTime, nullable=True)
    points_bonus = db.Column(db.Integer, default=10)

class ChallengeParticipation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    challenge_id = db.Column(db.Integer, db.ForeignKey('challenge.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    completed = db.Column(db.Boolean, default=False)

from app_setup import db
from datetime import datetime

# Catalog of plastic item types for better analytics & alternatives
class ItemType(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(80), unique=True, nullable=False)  # e.g. 'bottle_500ml', 'bag'
    display_name = db.Column(db.String(120), nullable=False)
    default_weight_kg = db.Column(db.Float, default=0.02)        # fallback if log has no weight

# Optional: store actual weight if known (e.g., IoT bin read)
class ScanEvent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    item_type_id = db.Column(db.Integer, db.ForeignKey('item_type.id'), nullable=True)
    source = db.Column(db.String(50), default='qr') # qr | smart_bin | manual
    raw_code = db.Column(db.String(255), default='')
    quantity = db.Column(db.Integer, default=1)
    measured_weight_kg = db.Column(db.Float, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class SmartBin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    bin_code = db.Column(db.String(50), unique=True, nullable=False)  # e.g. BIN001
    location = db.Column(db.String(120), default='')
    item_type_id = db.Column(db.Integer, db.ForeignKey('item_type.id'), nullable=True)

# Alternatives & Vendor integration
class AlternativeItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    for_item_key = db.Column(db.String(80), nullable=False) # maps to ItemType.key
    name = db.Column(db.String(120), nullable=False)        # e.g. "Stainless steel bottle"
    description = db.Column(db.String(300), default='')
    vendor_id = db.Column(db.Integer, db.ForeignKey('vendor.id'), nullable=True)
    estimated_cost = db.Column(db.Integer, nullable=True)   # ₹
    co2_saving_kg = db.Column(db.Float, default=0.0)

# Admin policy recommendations (dynamic + manual)
class PolicyRecommendation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(300), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    active = db.Column(db.Boolean, default=True)
