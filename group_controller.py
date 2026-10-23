from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from database import get_connection
from models import Member, Admin

group_bp = Blueprint('groups', __name__, url_prefix='/groups')

@group_bp.route('/')
def list_groups():
    if 'user_id' not in session:
        return redirect(url_for('auth.landing'))

    user_id = session['user_id']
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT g.group_id, g.group_name, g.created_by, u.username as creator_name
        FROM expense_groups g
        JOIN group_members gm ON g.group_id = gm.group_id
        JOIN users u ON g.created_by = u.user_id
        WHERE gm.user_id = ?
    """, (user_id,))
    groups = cursor.fetchall()

    group_data = []
    for g in groups:
        gid = g['group_id']
        cursor.execute("""
            SELECT u.username 
            FROM users u 
            JOIN group_members gm ON u.user_id = gm.user_id 
            WHERE gm.group_id = ?
        """, (gid,))
        members = [row['username'] for row in cursor.fetchall()]

        group_data.append({
            'group_id': gid,
            'group_name': g['group_name'],
            'created_by': g['created_by'],
            'is_admin': (g['created_by'] == user_id),
            'member_count': len(members),
            'members': members
        })

    conn.close()
    return render_template('groups_view.html', groups=group_data)

@group_bp.route('/create', methods=['POST'])
def create_group():
    if 'user_id' not in session:
        return redirect(url_for('auth.landing'))

    user_id = session['user_id']
    group_name = request.form.get('group_name', '').strip()
    additional_members_str = request.form.get('additional_members', '').strip()

    if not group_name:
        flash("Group name cannot be empty.", "error")
        return redirect(url_for('groups.list_groups'))

    conn = get_connection()
    cursor = conn.cursor()

    # Create Group
    cursor.execute("INSERT INTO expense_groups (group_name, created_by) VALUES (?, ?)", (group_name, user_id))
    group_id = cursor.lastrowid

    # Creator is Admin Member
    cursor.execute("INSERT INTO group_members (group_id, user_id) VALUES (?, ?)", (group_id, user_id))

    # Process additional members
    if additional_members_str:
        raw_names = [name.strip() for name in additional_members_str.split(',') if name.strip()]
        for name in raw_names:
            cursor.execute("SELECT user_id FROM users WHERE username = ?", (name,))
            user_row = cursor.fetchone()
            if user_row:
                add_id = user_row['user_id']
                if add_id != user_id:
                    cursor.execute("INSERT OR IGNORE INTO group_members (group_id, user_id) VALUES (?, ?)", (group_id, add_id))
            else:
                flash(f"User '{name}' not found. Added group with existing users.", "error")

    conn.commit()
    conn.close()
    flash(f"Group '{group_name}' created successfully!", "success")
    return redirect(url_for('groups.list_groups'))

@group_bp.route('/<int:group_id>/manage', methods=['GET', 'POST'])
def manage_group(group_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.landing'))

    user_id = session['user_id']
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM expense_groups WHERE group_id = ?", (group_id,))
    group = cursor.fetchone()

    if not group:
        conn.close()
        flash("Group not found.", "error")
        return redirect(url_for('groups.list_groups'))

    # Check Admin authorization
    is_admin = (group['created_by'] == user_id)

    if request.method == 'POST' and is_admin:
        action = request.form.get('action')

        if action == 'add_member':
            username = request.form.get('username', '').strip()
            cursor.execute("SELECT user_id FROM users WHERE username = ?", (username,))
            user_to_add = cursor.fetchone()

            if not user_to_add:
                flash(f"No user with that username: '{username}'", "error")
            else:
                add_id = user_to_add['user_id']
                cursor.execute("SELECT * FROM group_members WHERE group_id = ? AND user_id = ?", (group_id, add_id))
                if cursor.fetchone():
                    flash("User is already in this group.", "error")
                else:
                    cursor.execute("INSERT INTO group_members (group_id, user_id) VALUES (?, ?)", (group_id, add_id))
                    conn.commit()
                    flash(f"Added {username} to group.", "success")

        elif action == 'remove_member':
            remove_id = int(request.form.get('user_id'))
            if remove_id == group['created_by']:
                flash("Admin cannot be removed from the group.", "error")
            else:
                cursor.execute("DELETE FROM group_members WHERE group_id = ? AND user_id = ?", (group_id, remove_id))
                conn.commit()
                flash("Member removed.", "success")

        elif action == 'update_group_name':
            new_name = request.form.get('group_name', '').strip()
            if new_name:
                cursor.execute("UPDATE expense_groups SET group_name = ? WHERE group_id = ?", (new_name, group_id))
                conn.commit()
                flash("Group name updated.", "success")

        return redirect(url_for('groups.manage_group', group_id=group_id))

    cursor.execute("""
        SELECT u.user_id, u.username, u.email 
        FROM users u 
        JOIN group_members gm ON u.user_id = gm.user_id 
        WHERE gm.group_id = ?
    """, (group_id,))
    member_rows = cursor.fetchall()
    conn.close()

    # Polymorphic role assignment
    members_list = []
    for m in member_rows:
        if m['user_id'] == group['created_by']:
            obj = Admin(m['user_id'], m['username'], m['email'])
        else:
            obj = Member(m['user_id'], m['username'], m['email'])
        members_list.append(obj)

    return render_template('manage_group_view.html', group=group, members=members_list, is_admin=is_admin)

@group_bp.route('/<int:group_id>/delete', methods=['GET', 'POST'])
def delete_group(group_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.landing'))

    user_id = session['user_id']
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM expense_groups WHERE group_id = ?", (group_id,))
    group = cursor.fetchone()

    if not group or group['created_by'] != user_id:
        conn.close()
        flash("Unauthorized deletion request.", "error")
        return redirect(url_for('groups.list_groups'))

    if request.method == 'POST':
        cursor.execute("DELETE FROM expense_groups WHERE group_id = ?", (group_id,))
        conn.commit()
        conn.close()
        flash("Group deleted successfully.", "success")
        return redirect(url_for('groups.list_groups'))

    conn.close()
    return render_template('confirm_delete.html', item_type='Group', item_name=group['group_name'])