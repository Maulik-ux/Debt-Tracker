from flask import Blueprint, render_template, request, session, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from database import get_connection
from utils.validators import validate_password_strength, WeakPasswordError, EmptyFieldError

settings_bp = Blueprint('settings', __name__, url_prefix='/settings')

@settings_bp.route('/', methods=['GET', 'POST'])
def index():
    if 'user_id' not in session:
        return redirect(url_for('auth.landing'))

    user_id = session['user_id']
    conn = get_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'update_profile':
            username = request.form.get('username', '').strip()
            email = request.form.get('email', '').strip().lower()
            currency = request.form.get('currency', '$')

            try:
                if not username or not email:
                    raise EmptyFieldError("Username and email cannot be empty.")

                cursor.execute("""
                    UPDATE users SET username = ?, email = ?, currency = ? WHERE user_id = ?
                """, (username, email, currency, user_id))
                conn.commit()

                # Update active session settings
                session['username'] = username
                session['currency'] = currency
                flash("Settings updated successfully!", "success")

            except Exception as e:
                flash(str(e), "error")

        elif action == 'change_password':
            old_password = request.form.get('old_password', '')
            new_password = request.form.get('new_password', '')

            try:
                cursor.execute("SELECT password_hash FROM users WHERE user_id = ?", (user_id,))
                user_row = cursor.fetchone()

                if not check_password_hash(user_row['password_hash'], old_password):
                    raise ValueError("Current password is incorrect.")

                validate_password_strength(new_password)

                new_hash = generate_password_hash(new_password)
                cursor.execute("UPDATE users SET password_hash = ? WHERE user_id = ?", (new_hash, user_id))
                conn.commit()

                flash("Password updated successfully!", "success")

            except (WeakPasswordError, ValueError) as e:
                flash(str(e), "error")

    cursor.execute("SELECT user_id, username, email, currency FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()

    return render_template('settings_view.html', user=user, currency=session.get('currency', '$'))