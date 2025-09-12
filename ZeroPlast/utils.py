import models
from sqlalchemy import func, distinct
from app_setup import db
from collections import Counter
import os
import matplotlib
matplotlib.use('Agg')  # Use non-GUI backend for thread/process safety
import matplotlib.pyplot as plt
import io
import base64


# -----------------------------
# Awareness & Education Helpers
# -----------------------------
def estimate_impacts_from_counts(counts: dict) -> dict:
    """
    Estimate environmental impacts from item counts.
    Returns dict with plastic_kg, co2_kg, landfill_l, marine_lives_saved.
    """
    factors = {
        "bottle": {"plastic_kg": 0.02, "co2_kg": 0.054, "landfill_l": 0.05},
        "bag":    {"plastic_kg": 0.01, "co2_kg": 0.027, "landfill_l": 0.02},
        "cup":    {"plastic_kg": 0.015, "co2_kg": 0.04,  "landfill_l": 0.03},
        "straw":  {"plastic_kg": 0.005, "co2_kg": 0.01,  "landfill_l": 0.005},
    }
    total = {"plastic_kg": 0.0, "co2_kg": 0.0, "landfill_l": 0.0}
    total_items = 0
    for item, count in counts.items():
        f = factors.get(item.lower(), {"plastic_kg": 0, "co2_kg": 0, "landfill_l": 0})
        total["plastic_kg"] += f["plastic_kg"] * count
        total["co2_kg"] += f["co2_kg"] * count
        total["landfill_l"] += f["landfill_l"] * count
        total_items += count
    total["plastic_kg"] = round(total["plastic_kg"], 3)
    total["co2_kg"] = round(total["co2_kg"], 3)
    total["landfill_l"] = round(total["landfill_l"], 3)
    total["marine_lives_saved"] = max(0, round(total_items * 0.005, 2))
    return total

def nudge_for_user(user_id: int) -> dict:
    """
    Generate a friendly nudge for the user based on their plastic log history.
    Returns dict with message, details, items_count.
    """
    from models import PlasticLog
    counts = {}
    total_items = 0
    # Group by item and sum quantity
    rows = db.session.query(PlasticLog.item, func.sum(PlasticLog.quantity)) \
        .filter(PlasticLog.user_id == user_id) \
        .group_by(PlasticLog.item).all()
    for item, count in rows:
        counts[item] = int(count)
        total_items += int(count)
    details = estimate_impacts_from_counts(counts)
    if total_items >= 50:
        msg = f"Amazing — you’ve avoided ~{details['plastic_kg']} kg plastic and ~{details['co2_kg']} kg CO₂e. Keep leading!"
    elif total_items >= 10:
        msg = f"Great progress — {total_items} items logged, approx {details['plastic_kg']} kg plastic avoided. Keep going!"
    else:
        msg = "Tip: Scan via QR for quicker logging. Try refill stations to cut more plastic."
    return {"message": msg, "details": details, "items_count": total_items, "by_item": counts}

def community_impact_summary() -> dict:
    """
    Aggregate community impact and stats.
    Returns dict with total_items, unique_users, total_points, impact, by_item.
    """
    from models import PlasticLog, User, PointsLog
    # By item
    by_item = {}
    total_items = 0
    rows = db.session.query(PlasticLog.item, func.sum(PlasticLog.quantity)) \
        .group_by(PlasticLog.item).all()
    for item, count in rows:
        by_item[item] = int(count)
        total_items += int(count)
    # Unique users
    unique_users = db.session.query(func.count(distinct(PlasticLog.user_id))).scalar() or 0
    # Total points
    total_points = db.session.query(func.sum(PointsLog.delta)).scalar() or 0
    # Impact
    impact = estimate_impacts_from_counts(by_item)
    return {
        "total_items": total_items,
        "unique_users": unique_users,
        "total_points": total_points,
        "impact": impact,
        "by_item": by_item
    }

def save_graph_by_item(logs, user_id):
    item_counts = Counter()
    for l in logs:
        item_counts[l.item] += l.quantity
    top_items = item_counts.most_common(3)
    items, counts = zip(*top_items) if top_items else ([],[])
    fig, ax = plt.subplots()
    ax.bar(items, counts, color=['#16a34a', '#22c55e', '#a3e635'])
    ax.set_ylabel('Total Logged')
    ax.set_title('Top 3 Items by Total Logged')
    plt.tight_layout()
    graph_path = os.path.join('static', 'graphs', f'items_{user_id}.png')
    plt.savefig(graph_path)
    plt.close(fig)
    return graph_path

def save_graph_by_day(logs, user_id):
    day_counts = Counter()
    for l in logs:
        day = l.created_at.strftime('%Y-%m-%d')
        day_counts[day] += l.quantity
    top_days = day_counts.most_common(3)
    days, counts = zip(*top_days) if top_days else ([],[])
    fig, ax = plt.subplots()
    ax.bar(days, counts, color=['#16a34a', '#22c55e', '#a3e635'])
    ax.set_ylabel('Total Logged')
    ax.set_title('Top 3 Days by Total Logged')
    plt.tight_layout()
    graph_path = os.path.join('static', 'graphs', f'days_{user_id}.png')
    plt.savefig(graph_path)
    plt.close(fig)
    return graph_path


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


def generate_trend_graph(labels, values):
    """Generate a trend graph and return it as a base64 string."""
    fig, ax = plt.subplots(figsize=(8, 4))

    ax.plot(labels, values, marker='o', linestyle='-', color='b')
    ax.set(xlabel='Date', ylabel='Items Processed', title='Daily Plastic Log Trend')

    # Rotate the x-axis labels for readability
    plt.xticks(rotation=45, ha='right')

    # Save the plot to a BytesIO buffer
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)

    # Convert image to base64 for rendering in HTML
    img_str = base64.b64encode(buf.read()).decode('utf-8')
    buf.close()

    return img_str
