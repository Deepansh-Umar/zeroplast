from flask import Flask, render_template, redirect, url_for, flash, request
from flask_login import LoginManager, login_required, current_user
from datetime import datetime, timedelta
from utils import calculate_points
import models
from app_setup import create_app
from routes.auth import auth_bp
from routes.plastic import plastic_bp
from routes.alternatives import alts_bp
from routes.rewards import rewards_bp
from routes.community import community_bp
from routes.dashboard import dashboard_bp
from routes.admin import admin_bp
from routes.challenge import challenge_bp
from routes.teams import teams_bp




app = create_app()
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "auth.login"  # Redirect here if @login_required fails





@login_manager.user_loader
def load_user(user_id):
    return models.User.query.get(int(user_id))


# PUBLIC LANDING PAGE
@app.route('/')
def home():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.dashboard"))  # send logged-in users to dashboard
    return render_template('index.html',
                           total_donations=0,
                           total_users=0,
                           total_points=0,
                           logs=[])


# Register Blueprints
app.register_blueprint(auth_bp, url_prefix="/auth")
app.register_blueprint(plastic_bp, url_prefix="/plastic")
app.register_blueprint(alts_bp, url_prefix="/alternatives")
app.register_blueprint(rewards_bp, url_prefix="/rewards")
app.register_blueprint(community_bp, url_prefix="/community")
app.register_blueprint(admin_bp, url_prefix="/admin")

app.register_blueprint(challenge_bp)

app.register_blueprint(teams_bp)
app.register_blueprint(dashboard_bp)

if __name__ == "__main__":
    app.run(debug=True)
