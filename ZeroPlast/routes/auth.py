from flask import Blueprint, request, render_template, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
import models
from db_setup import db

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        user = models.User.query.filter_by(email=email).first()
        if user and user.password == password:  # TODO: hash check
            login_user(user)
            flash("Logged in successfully!", "success")
            return redirect(url_for("dashboard.dashboard"))
        else:
            flash("Invalid credentials", "danger")

    return render_template("login.html")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")

        if not all([name, email, password]):
            flash("All fields are required!", "danger")
            return redirect(url_for("auth.register"))

        if models.User.query.filter_by(email=email).first():
            flash("User already exists!", "warning")
            return redirect(url_for("auth.register"))
        if models.User.query.filter_by(username=name).first():
            flash("User already exists!", "warning")
            return redirect(url_for("auth.register"))

        new_user = models.User(username=name, email=email, password=password)
        db.session.add(new_user)
        db.session.commit()

        login_user(new_user)
        flash("Registration successful!", "success")
        return redirect(url_for("dashboard.dashboard"))

    return render_template("register.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You’ve been logged out.", "info")
    return redirect(url_for("auth.login"))
