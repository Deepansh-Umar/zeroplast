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
            if user.username == "Admin":
                login_user(user)
                return redirect(url_for("admin.admin"))
            login_user(user)
            flash("Logged in successfully!", "success")
            return redirect(url_for("dashboard.dashboard"))
        else:
            flash("Invalid credentials", "danger")

    return render_template("login.html")



# User registration
@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.dashboard"))

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

# Vendor registration
@auth_bp.route("/register_vendor", methods=["GET", "POST"])
def register_vendor():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.dashboard"))

    if request.method == "POST":
        name = request.form.get("name")
        discount = request.form.get("discount", 0)
        description = request.form.get("description", "")

        if not name:
            flash("Vendor name is required!", "danger")
            return redirect(url_for("auth.register_vendor"))
        if models.Vendor.query.filter_by(name=name).first():
            flash("Vendor already exists!", "warning")
            return redirect(url_for("auth.register_vendor"))

        vendor = models.Vendor(name=name, discount=discount, description=description)
        db.session.add(vendor)
        db.session.commit()
        flash("Vendor registered successfully!", "success")
        return redirect(url_for("auth.login"))

    return render_template("register_vendor.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You’ve been logged out.", "info")
    return redirect(url_for("auth.login"))
