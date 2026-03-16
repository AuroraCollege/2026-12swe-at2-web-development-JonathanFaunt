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

    lb = db.execute(
    "SELECT * FROM leaderboards WHERE id = ?",
    (leaderboard_id,)
    ).fetchone()


    if lb["type"] == "time":
        entries = db.execute(
            "SELECT * FROM leaderboard_entries WHERE leaderboard_id = ? ORDER BY score ASC",
            (leaderboard_id,)
        ).fetchall()
    else:
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

        lb = db.execute(
            "SELECT type FROM leaderboards WHERE id = ?",
            (leaderboard_id,)
        ).fetchone()

        db.execute(
            "INSERT INTO leaderboard_entries (leaderboard_id, user_id, user, type, score) VALUES (?, ?, ?, ?, ?)",
            (leaderboard_id, session["user_id"], session["username"], lb["type"], score)
        )
        db.commit()

        return redirect(f"/leaderboard/{leaderboard_id}")

    leaderboards = db.execute("SELECT * FROM leaderboards").fetchall()
    return render_template("submit.html", leaderboards=leaderboards)

@app.route("/moderation",  methods=["GET", "POST"])
def moderation():
    db = get_db()
    return render_template("moderation.html")

@app.route("/moderation/new_leaderboard", methods=["GET", "POST"])
def new_leaderboard():
    if request.method == "POST":
        name = request.form["name"]
        description = request.form["description"]
        type = request.form["type"]

        db = get_db()
        db.execute(
            "INSERT INTO leaderboards (name, description, type) VALUES (?, ?, ?)",
            (name, description, type)
        )
        db.commit()

        return redirect("/moderation")

    return render_template("new_leaderboard.html")

@app.route("/moderation/submissions")
def manage_submissions():
    db = get_db()
    entries = db.execute("""
        SELECT leaderboard_entries.id, leaderboard_entries.score,
               users.username, leaderboards.name AS leaderboard_name
        FROM leaderboard_entries
        JOIN users ON users.id = leaderboard_entries.user_id
        JOIN leaderboards ON leaderboards.id = leaderboard_entries.leaderboard_id
        ORDER BY leaderboard_entries.id DESC
    """).fetchall()

    return render_template("manage_submissions.html", entries=entries)

@app.route("/moderation/delete_entry/<int:entry_id>")
def delete_entry(entry_id):
    db = get_db()
    db.execute("DELETE FROM leaderboard_entries WHERE id = ?", (entry_id,))
    db.commit()

    return redirect("/moderation/submissions")

@app.route("/moderation/users")
def manage_users():
    db = get_db()
    users = db.execute("SELECT id, username, role FROM users").fetchall()

    return render_template("manage_users.html", users=users)

@app.route("/moderation/delete_user/<int:user_id>")
def delete_user(user_id):
    db = get_db()
    db.execute("DELETE FROM users WHERE id = ?", (user_id,))
    db.commit()

    return redirect("/moderation/users")

@app.route("/account")
def account():
    db = get_db()

    submissions = db.execute("""
        SELECT leaderboard_entries.id,
               leaderboard_entries.score,
               leaderboard_entries.type,
               leaderboards.name AS leaderboard_name
        FROM leaderboard_entries
        JOIN leaderboards ON leaderboard_entries.leaderboard_id = leaderboards.id
        WHERE leaderboard_entries.user = ?
        ORDER BY leaderboard_entries.id DESC
    """, (session["username"],)).fetchall()

    return render_template("account.html", submissions=submissions)

@app.route("/delete/<int:entry_id>", methods=["POST"])
def delete_submission(entry_id):
    db = get_db()

    db.execute("""
        DELETE FROM leaderboard_entries
        WHERE id = ? AND user = ?
    """, (entry_id, session["username"]))

    db.commit()

    return redirect("/account")

