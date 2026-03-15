from flask import Flask, render_template, redirect, request, session, g
import sqlite3

app = Flask(__name__)
app.secret_key = "secret_key"

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect("database.db")
        g.db.row_factory = sqlite3.Row
    return g.db

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
        db = get_db()
        leaderboards = db.execute("SELECT * FROM leaderboards").fetchall()
        print("DEBUG leaderboards:", leaderboards)
        return render_template("home.html", leaderboards=leaderboards, username = session["username"])
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

@app.route("/leaderboard/<int:leaderboard_id>")
def show_leaderboard(leaderboard_id):
    db = get_db()
    leaderboard = db.execute(
        "SELECT * FROM leaderboards WHERE id = ?", (leaderboard_id,)
    ).fetchone()

    entries = db.execute(
        "SELECT * FROM leaderboard_entries WHERE leaderboard_id = ? ORDER BY score DESC",
        (leaderboard_id,)
    ).fetchall()

    return render_template("leaderboard.html", leaderboard=leaderboard, entries=entries)

@app.route("/submit", methods=["GET", "POST"])
def submit():
    db = get_db()

    if request.method == "POST":
        leaderboard_id = request.form["leaderboard_id"]
        score = request.form["score"]

        db.execute(
            "INSERT INTO leaderboard_entries (leaderboard_id, user_id, score) VALUES (?, ?, ?)",
            (leaderboard_id, session["user_id"], score)
        )
        db.commit()

        return redirect(f"/leaderboard/{leaderboard_id}")

    leaderboards = db.execute("SELECT * FROM leaderboards").fetchall()
    return render_template("submit.html", leaderboards=leaderboards)

@app.route("/moderation",  methods=["GET", "POST"])
def moderation():
    db = get_db()
    if g.user["role"] != "Moderator":
        return "Access denied"
    return render_template("moderation.html")