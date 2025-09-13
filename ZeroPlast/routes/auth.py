from flask import Blueprint, request, render_template, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
import models
from db_setup import db

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        if hasattr(current_user, 'role'):
            if current_user.role == 'admin':
                return redirect(url_for("admin.admin"))
            elif current_user.role == 'vendor':
                return redirect(url_for("admin.vendor_detail", user_id=current_user.id))
            return redirect(url_for("dashboard.dashboard"))
        return redirect(url_for("dashboard.dashboard"))

    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        user = models.User.query.filter_by(email=email).first()
        if user and user.password == password:  # TODO: hash check
            login_user(user)
            # Redirect by role
            if hasattr(user, 'role'):
                if user.role == 'admin':
                    return redirect(url_for("admin.admin"))
                elif user.role == 'vendor':
                    vendor = models.Vendor.query.filter_by(name=user.username).first()
                    if vendor:
                        return redirect(url_for("admin.vendor_detail", user_id=user.id))
                # default user
                flash("Logged in successfully!", "success")
                return redirect(url_for("dashboard.dashboard"))

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
        email = request.form.get("email")
        password = request.form.get("password")
        discount = request.form.get("discount", 0)
        description = request.form.get("description", "")

        if not all([name, email, password]):
            flash("All fields are required!", "danger")
            return redirect(url_for("auth.register_vendor"))
        if models.User.query.filter_by(email=email).first():
            flash("Email already registered!", "warning")
            return redirect(url_for("auth.register_vendor"))
        if models.User.query.filter_by(username=name).first():
            flash("Vendor name already registered as user!", "warning")
            return redirect(url_for("auth.register_vendor"))
        if models.Vendor.query.filter_by(name=name).first():
            flash("Vendor already exists!", "warning")
            return redirect(url_for("auth.register_vendor"))

        # Add to User table with role vendor
        new_vendor_user = models.User(username=name, email=email, password=password, role="vendor")
        db.session.add(new_vendor_user)
        
        # Add to Vendor table
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
