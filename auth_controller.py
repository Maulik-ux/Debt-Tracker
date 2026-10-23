from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from database import get_connection
from utils.validators import validate_password_strength, WeakPasswordError, EmptyFieldError

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/')
def landing():
    if 'user_id' in session:
        return redirect(url_for('dashboard.index'))
    return render_template('auth_view.html', mode='login')

@auth_bp.route('/signup/step1', methods=['POST'])
def signup_step1():
    email = request.form.get('email', '').strip().lower()
    password = request.form.get('password', '')

    try:
        if not email or not password:
            raise EmptyFieldError("All fields are required.")

        validate_password_strength(password)

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM users WHERE email = ?", (email,))
        existing = cursor.fetchone()
        conn.close()

        if existing:
            flash("An account with this email already exists. Please log in.", "error")
            return render_template('auth_view.html', mode='login')

        # Store in session temporary signup buffer
        session['signup_email'] = email
        session['signup_password_hash'] = generate_password_hash(password)

        return render_template('auth_view.html', mode='signup_step2', email=email)

    except WeakPasswordError as e:
        flash(str(e), "error")
        return render_template('auth_view.html', mode='signup_step1', email=email)
    except EmptyFieldError as e:
        flash(str(e), "error")
        return render_template('auth_view.html', mode='signup_step1')

@auth_bp.route('/signup/step2', methods=['POST'])
def signup_step2():
    username = request.form.get('username', '').strip()
    email = session.get('signup_email')
    password_hash = session.get('signup_password_hash')

    if not email or not password_hash:
        flash("Session expired. Please start registration again.", "error")
        return render_template('auth_view.html', mode='signup_step1')

    if not username:
        flash("Username cannot be empty.", "error")
        return render_template('auth_view.html', mode='signup_step2', email=email)

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
            (username, email, password_hash)
        )
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()

        # Clear registration buffer and log in user
        session.pop('signup_email', None)
        session.pop('signup_password_hash', None)

        session['user_id'] = user_id
        session['username'] = username
        session['role'] = 'Member'

        flash("Account created successfully!", "success")
        return redirect(url_for('dashboard.index'))

    except Exception:
        conn.close()
        flash("Username is already taken. Please choose another.", "error")
        return render_template('auth_view.html', mode='signup_step2', email=email)

@auth_bp.route('/login', methods=['POST'])
def login():
    login_input = request.form.get('login_input', '').strip()
    password = request.form.get('password', '')

    if not login_input or not password:
        flash("Please enter all fields.", "error")
        return render_template('auth_view.html', mode='login')

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM users WHERE email = ? OR username = ?", 
        (login_input.lower(), login_input)
    )
    user = cursor.fetchone()
    conn.close()

    if not user:
        flash("No account found. Please sign up first.", "error")
        return render_template('auth_view.html', mode='login')

    if not check_password_hash(user['password_hash'], password):
        flash("Incorrect password.", "error")
        return render_template('auth_view.html', mode='login')

    session['user_id'] = user['user_id']
    session['username'] = user['username']
    session['role'] = user['role']

    return redirect(url_for('dashboard.index'))

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for('auth.landing'))