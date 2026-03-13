from flask import Flask, render_template, redirect, request, session
import sqlite3

app = Flask(__name__)
app.secret_key = "secret_key"

def get_db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn

from flask import g

@app.before_request
def load_user():
    g.user = None
    if "user_id" in session:
        db = get_db()
        g.user = db.execute(
            "SELECT * FROM users WHERE id = ?",
            (session["user_id"],)
        ).fetchone()

@app.route("/")
def home():
    if "user_id" in session:
        return render_template('home.html', username = session["username"])
        print('at Homepage')
    else:
        return redirect('/login')
        print('going to Login')

@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        db = get_db()
        try:
            db.execute(
                "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                (username, password, 'User')
            )
            db.commit()
        except sqlite3.IntegrityError:
            return "That username is already taken."

        return redirect("/login")
    return render_template('register.html')

@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        db = get_db()
        user = db.execute(
            "SELECT * FROM users WHERE username = ? AND password = ?",
            (username, password)
        ).fetchone()

        if user is None:
            return "Incorrect username or password."

        session["user_id"] = user["id"]
        session["username"] = user["username"]

        return redirect("/")

    return render_template("login.html")

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')