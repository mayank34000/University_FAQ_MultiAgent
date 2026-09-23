from functools import wraps
import re

from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from db import create_user, get_user_by_email

auth_bp = Blueprint("auth", __name__)


def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("auth.login"))
        return view(*args, **kwargs)

    return wrapped_view


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not email or not password:
            flash("Email and password are required.")
            return render_template("login.html")

        user = get_user_by_email(email)

        if user is None or not check_password_hash(user["password_hash"], password):
            flash("Invalid email or password.")
            return render_template("login.html")

        session.clear()
        session["user_id"] = user["id"]
        session["user_name"] = user["name"]
        session["user_email"] = user["email"]

        return redirect(url_for("index"))

    return render_template("login.html")


@auth_bp.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        roll_number = request.form.get("roll_number", "").strip() or None
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not name or not email or not password:
            flash("Name, email and password are required.")
            return render_template("signup.html")

        if password != confirm_password:
            flash("Passwords do not match.")
            return render_template("signup.html")

        if len(password) < 8:
            flash("Password must be at least 8 characters.")
            return render_template("signup.html")

        if not re.search(r"[A-Z]", password):
            flash("Password must contain an uppercase letter.")
            return render_template("signup.html")

        if not re.search(r"[a-z]", password):
            flash("Password must contain a lowercase letter.")
            return render_template("signup.html")

        if not re.search(r"\d", password):
            flash("Password must contain a number.")
            return render_template("signup.html")

        if get_user_by_email(email):
            flash("An account with this email already exists.")
            return render_template("signup.html")

        try:
            create_user(
                name,
                email,
                roll_number,
                generate_password_hash(password)
            )
        except Exception:
            flash("Could not create account. Please check your details.")
            return render_template("signup.html")

        return redirect(url_for("auth.login"))

    return render_template("signup.html")


@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))
