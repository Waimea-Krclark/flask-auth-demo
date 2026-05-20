#===========================================================
# APP NAME HERE
# By YOUR NAME HERE
#===========================================================

from flask import Flask, request, session, render_template, flash, redirect, send_file, make_response
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
from os import getenv
from io import BytesIO
import html
from app.helpers import *


# Create the app
app = Flask(__name__)


#===========================================================
# App Routes Handlers
#===========================================================

#-----------------------------------------------------------
# Welcome page
#-----------------------------------------------------------
@app.get("/")
def show_welcome():
    return render_template("pages/welcome.jinja")

#-----------------------------------------------------------
# Signup page
#-----------------------------------------------------------
@app.get("/user/new")
def show_signup_form():
    return render_template("pages/user_form.jinja")

#-----------------------------------------------------------
# Sign In page
#-----------------------------------------------------------
@app.get("/user/login")
def show_login_form():
    return render_template("pages/user_login.jinja")

#-----------------------------------------------------------
# Handle User Signup
#-----------------------------------------------------------
@app.post("/user")
def process_new_user():
    forename = request.form.get('forename', '').strip()
    surname = request.form.get('surname', '').strip()
    username = request.form.get('username', '').strip().lower()
    password = request.form.get('password', '').strip()

    with connect_db() as db:
        sql = "SELECT id FROM users WHERE username=?"
        params = (username,)
        user = db.execute(sql, params).fetchone()

        if user:
            flash(f"Username '{username}' already exists", "error")
            return redirect("/user/new")

        pass_hash = generate_password_hash(password)

        sql = """
            INSERT INTO users (forename, surname, username, password_hash)
            VALUES (?, ?, ?, ?)
        """
        params = (forename, surname, username, pass_hash)
        db.execute(sql, params)

        flash("Account created. Please login", "success")
        return redirect("/login")

#-----------------------------------------------------------
# Handle User Sign in
#-----------------------------------------------------------
@app.post("/login")
def login_user():
    username = request.form.get('username', '').strip().lower()
    password = request.form.get('password', '').strip()

    with connect_db() as db:
        sql = """
            SELECT id, forename, surname, password_hash
            FROM users
            WHERE username=?
        """
        params = (username,)
        user = db.execute(sql, params).fetchone()

        if not user:
            flash(f"Unknown user", "error")
            return redirect("/user/login")

        if not check_password_hash(user["password_hash"], password):
            flash(f"Incorrect password", "error")
            return redirect("/user/login")

        session["logged_in"] = True
        session["user"] = {
            "user_id": user["id"],
            "username": username,
            "forename": user["forename"],
            "surname":  user["surname"],
        }

        flash("Login successful", "success")
        return redirect("/")

#-----------------------------------------------------------
# Handle User Log Out
#-----------------------------------------------------------
@app.get("/logout")
def logout_user():
    session.clear()
    flash(f"You have been logged out", "success")
    return redirect("/")

#-----------------------------------------------------------
# Creature list page - Show all the creatures
#-----------------------------------------------------------
@app.get("/creatures")
def show_all_creatures():
    with connect_db() as db:
        sql = """
            SELECT id, species, name
            FROM creatures
        """
        params = ()
        creatures = db.execute(sql, params).fetchall()

        return render_template("pages/creature_list.jinja", creatures=creatures)


#-----------------------------------------------------------
# Messages page - Show some help
#-----------------------------------------------------------
@app.get("/messages")
@login_required
def show_help():
    with connect_db() as db:
        sql = """
            SELECT messages.title, users.username, messages.body, messages.user_id, messages.id
            FROM messages
            INNER JOIN users ON messages.user_id = users.id
        """
        params = ()
        messages = db.execute(sql, params).fetchall()

        return render_template("pages/messages.jinja", messages=messages)

#-----------------------------------------------------------
# Create Message page - Show some help
#-----------------------------------------------------------
@app.get("/message/new")
@login_required
def show_message_form():
    return render_template("pages/message_form.jinja")

#-----------------------------------------------------------
# Message post Route - Show some help
#-----------------------------------------------------------
@app.post("/message")
def create_message():
    title = request.form.get('title', '').strip()
    body = request.form.get('body', '').strip()

    with connect_db() as db:
        sql = """
            INSERT INTO messages (user_id, title, body)
            VALUES (?, ?, ?)
        """
        params = (session.get("user")["user_id"], title, body)
        db.execute(sql, params)

    flash("Posted Message", "success")
    return redirect("/messages")

#-----------------------------------------------------------
# Delete messages route - Show some help
#-----------------------------------------------------------
@app.get("/message/delete/<int:id>")
@login_required
def delete_message(id):
    with connect_db() as db:
        sql = """
            DELETE FROM messages WHERE id = ?
        """
        params = (id,)
        db.execute(sql, params)

    flash("Deleted Message", "success")
    return redirect("/messages")

@app.get("/message/edit/<int:id>")
@login_required
def show_edit_message(id):
    with connect_db() as db:
        sql = """
            SELECT title, body
            FROM messages WHERE id = ?
        """
        params = (id,)
        message = db.execute(sql, params).fetchone()

    return render_template("pages/edit_message_form.jinja", message = message, id=id)

@app.post("/edit/<int:id>")
@login_required
def edit_message(id):
    title = request.form.get('title', '').strip()
    body = request.form.get('body', '').strip()
    with connect_db() as db:
        sql = """
            UPDATE messages SET title = ?, body = ? WHERE id = ?
        """
        params = (title, body, id)
        db.execute(sql, params)
    return redirect("/messages")
#===========================================================
# Configure the app
#===========================================================
load_dotenv()
app.config.from_prefixed_env()
init_logging(app)
init_text_filters(app)
init_date_filters(app)
init_error_handlers(app)
init_database()
register_commands(app)

