from sqlalchemy import func
from app_setup import db
import models

# -----------------------------
# Plastic Tracking + Points
# -----------------------------
def log_plastic(user_id, item, quantity, reason="Plastic log"):
    """Log plastic usage and award points."""
    log = models.PlasticLog(item=item, quantity=quantity, user_id=user_id)
    points = models.PointsLog(user_id=user_id, delta=quantity, reason=reason)
    db.session.add(log)
    db.session.add(points)
    db.session.commit()
    return quantity


def calculate_points(user_id):
    """Calculate total points for a user."""
    total = db.session.query(func.sum(models.PointsLog.delta)) \
                      .filter_by(user_id=user_id).scalar()
    return total or 0


def user_points(user_id: int) -> int:
    """Alias for calculate_points (returns total points)."""
    return calculate_points(user_id)


# -----------------------------
# Alternatives
# -----------------------------
def alternative_for(item: str) -> list[str]:
    """Suggest eco-friendly alternatives for a given plastic item."""
    alternatives = {
        "bottle": ["Metal bottle", "Glass bottle", "Refill station"],
        "bag": ["Cloth bag", "Jute bag", "Paper bag"],
        "cup": ["Steel cup", "Biodegradable cup", "Bring-your-own mug"],
        "straw": ["Steel straw", "Paper straw", "Bamboo straw"],
    }
    return alternatives.get(item.lower(), ["No alternative found"])


def nudge_for_items(items: list[str]) -> dict:
    """Return friendly nudges / reminders for given plastic items."""
    nudges = {
        "bottle": "Try carrying a reusable water bottle 🚰",
        "bag": "Cloth bags last longer and save plastic 🌱",
        "cup": "A steel cup or your own mug reduces waste ☕",
        "straw": "Skip the straw or use a bamboo one 🌿",
    }
    return {item: nudges.get(item.lower(), "Be mindful of single-use plastics ♻️") for item in items}


def estimate_impacts(items: dict) -> dict:
    """
    Estimate environmental impacts of plastic usage.
    items = { "bottle": 3, "bag": 5 }
    Returns dict with CO2 saved, plastic saved, etc.
    """
    # rough example factors (made up for prototype!)
    impact_factors = {
        "bottle": {"plastic_g": 20, "co2_g": 50},
        "bag": {"plastic_g": 10, "co2_g": 20},
        "cup": {"plastic_g": 15, "co2_g": 40},
        "straw": {"plastic_g": 5, "co2_g": 10},
    }

    total = {"plastic_g": 0, "co2_g": 0}
    for item, qty in items.items():
        factor = impact_factors.get(item.lower())
        if factor:
            total["plastic_g"] += factor["plastic_g"] * qty
            total["co2_g"] += factor["co2_g"] * qty
    
    return total


# -----------------------------
# Rewards
# -----------------------------
def redeem_reward(user_id, reward_id):
    """Redeem a reward if enough points."""
    reward = models.Reward.query.get(reward_id)
    if not reward:
        return False, "Reward not found"
    
    points = calculate_points(user_id)
    if points < reward.cost_points:
        return False, "Not enough points"
    
    redemption = models.Redemption(user_id=user_id, reward_id=reward.id)
    log = models.PointsLog(user_id=user_id, delta=-reward.cost_points,
                           reason=f"Redeemed {reward.name}")
    db.session.add(redemption)
    db.session.add(log)
    db.session.commit()
    return True, f"Redeemed {reward.name}"


# -----------------------------
# Teams
# -----------------------------
def get_team_points(team_id):
    """Get total points for all users in a team."""
    users = models.User.query.filter_by(team_id=team_id).all()
    return sum(calculate_points(u.id) for u in users)


def get_leaderboard(top_n=10):
    """Get leaderboard of users by points."""
    users = models.User.query.all()
    leaderboard = [(u.username, calculate_points(u.id)) for u in users]
    leaderboard.sort(key=lambda x: x[1], reverse=True)
    return leaderboard[:top_n]


# -----------------------------
# Vendors
# -----------------------------
def add_vendor(name, description, qr_code=None):
    """Register a new eco-friendly vendor."""
    vendor = models.Vendor(name=name, description=description, qr_code=qr_code)
    db.session.add(vendor)
    db.session.commit()
    return vendor


def log_vendor_redemption(user_id, vendor_id, item, points_used):
    """Track redemption at a vendor (discounts, eco-products)."""
    vendor = models.Vendor.query.get(vendor_id)
    if not vendor:
        return False, "Vendor not found"
    
    points = calculate_points(user_id)
    if points < points_used:
        return False, "Not enough points"
    
    redemption = models.Redemption(user_id=user_id, reward_id=None,
                                   vendor_id=vendor_id)
    log = models.PointsLog(user_id=user_id, delta=-points_used,
                           reason=f"Vendor redemption: {item}")
    db.session.add(redemption)
    db.session.add(log)
    db.session.commit()
    return True, f"Redeemed {item} with {points_used} points"


# -----------------------------
# Admin utilities
# -----------------------------
def seed_admin():
    """Create admin if not exists."""
    existing_admin = models.User.query.filter_by(username="Admin").first()
    if not existing_admin:
        from werkzeug.security import generate_password_hash
        admin = models.User(
            username="Admin",
            email="admin@example.com",
            password=generate_password_hash("admin@iitm"),
            role="admin"
        )
        db.session.add(admin)
        db.session.commit()
        return True
    return False
