import os
import datetime
import sqlite3
from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, jsonify
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True


# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///wish.db")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Note: If status code 400, one solution is to run on different chrome user
@app.route("/")
@login_required
def index():
    # My thought: Just update the database, knows the importance of a well-designed database
    # My thought: First get user_id, then db.execute from the database of trade to show what the user did
    # Note: Fun fact: if we only get this line of code, website will be down to 502 bad request
    user_id = session["user_id"]
    # Note: SQL >> SELECT xxx AS yyy
    wishes = db.execute("SELECT date, type_id, id, content, wish_done FROM wishes WHERE user_id = ? ORDER BY date DESC", user_id)


    wish_unfinished = db.execute("SELECT wish_unfinished FROM users WHERE id = ?", user_id)
    unfinished_number = wish_unfinished[0]["wish_unfinished"]


    # Note: My personal touch >> One key sell ALL
    # Note: My reflection: Sadly, there is a flaw in this program that I only shows the cost but not the current price
    # Note: *** stock = stocks, stock is the name passed into HTML while stocks is the variable declared here
    return render_template("index.html", wish_number = unfinished_number, wishes = wishes)


@app.route("/wish", methods=["GET", "POST"])
@login_required
def wish():
    """Buy shares of stock"""
    # buy.html will be changed to make_a_wish.html
    if request.method == "GET":
        return render_template("wish.html")
    else:
        request.method == "POST"
        content = request.form.get("content")
        type_id = int(request.form.get("type"))
        if not content or not type_id:
            return apology("Both type and content are needed!")

        if type_id < 1 or type_id > 3:
            return apology("Please enter a valid type!")

        wish_type_db = db.execute("SELECT id, wish_type FROM wish_type")
        types = wish_type_db
        user_id = session["user_id"]

        # Note:  "?" can refer to things in SQL
        wish_unfinished = db.execute("SELECT wish_unfinished FROM users WHERE id = ?", user_id)
        unfinished_number = wish_unfinished[0]["wish_unfinished"]

        updated_wish = unfinished_number + 1

        # Note: to use datetime function, you need to import the library datetime
        date = datetime.datetime.now()
        # Note: Update cash after transaction
        db.execute("UPDATE users SET wish_unfinished = ? WHERE id = ?", updated_wish, user_id)
        db.execute("INSERT INTO wishes (user_id, date, type_id, content) VALUES (?, ?, ?, ?)", user_id, date, type_id, content)
        # print("Hello to the {} {}".format(var2,var1))
        flash("Made a wish on {}!! Good luck!".format(date))
        # {shares} share(s) of {symbol} on {date}!
        return redirect("/")

@app.route("/discover")
@login_required
def discover():
    # Randomly look at one of the wishese by other users
    user_id = session["user_id"]

    # Note: SQL >> SELECT xxx AS yyy

    # Note: **Solve the floating point issue coz 55 will be 55.00001 in HTML
    wish_db = db.execute("SELECT content FROM wishes WHERE user_id != ? LIMIT 1", user_id)
    wish = wish_db[0]["content"]

    return render_template("discover.html", wish = wish)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "GET":
        return render_template("register.html")
    else:
        request.method == "POST"
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")
        # Note: For CSS stuff: # >> id, . >> class
        # Note: if something does not exist we can just use if not xxx
        if not username or not password or not confirmation:
            return apology("Username, password and confirmation are ALL needed to create an account!")

        if password != confirmation:
            return apology("Passwords do not match!")

        hash_pw = generate_password_hash(password)

        # Note: INSERT INTO follows by TABLE name not database name
        # Note: Try / Except use in Python
        try:
            new_username = db.execute("INSERT INTO users (username, hash) VALUES (?, ?)", username, hash_pw)

        except:
            return apology("Username already used!")

        # Note: *** This is very important. You need this to let the computer remember the one logging in.
        session["user_id"] = new_username
        return redirect("/")



@app.route("/update", methods=["GET", "POST"])
@login_required
def update():
    # Note: Change to update.html later on
    if request.method == "GET":
        return render_template("update.html")
    else:
        request.method == "POST"
        update = request.form.get("update")
        wish_id = request.form.get("id")
        # yes = request.form.get("yes")
        if not update or not wish_id:
            return apology("Update information and wish_id are needed!")

        user_id = session["user_id"]


        wish_id_db = db.execute("SELECT id FROM wishes WHERE user_id = ?", user_id)

        # Note:  "?" can refer to things in SQL
        user_wishes = db.execute("SELECT content FROM wishes WHERE id = ?", wish_id)
        wishes = user_wishes[0]["content"]

        date = datetime.datetime.now()
        date_str = str(date)
        updated_wishes = "         " + wishes + " \n" + date_str + " UPDATE: " + "[" + update + "]"

        # Note: to use datetime function, you need to import the library datetime

        # Note: Update cash after transaction
        db.execute("UPDATE wishes SET content = ? WHERE id = ?", updated_wishes, wish_id)
        # print("Hello to the {} {}".format(var2,var1))
        flash("Updated wish(es) on {}!!".format(date))
        # {shares} share(s) of {symbol} on {date}!
        return redirect("/")
        #return jsonify(user_wish_id)



@app.route("/comment", methods=["GET", "POST"])
@login_required
def discussion():
    if request.method == "POST":
        # Todo: Create a ta
        date = datetime.datetime.now()
        title = request.form.get("title")
        content = request.form.get("content")
        contact = request.form.get("contact")
        db.execute("INSERT INTO comment (title, content, contact, date) VALUES (?, ?, ?, ?)", title, content, contact, date)
        return redirect("/comment")

    else:
        date = datetime.datetime.now()
        request.method == "GET"
        comments = db.execute("SELECT * from comment ORDER BY date")
        user_id = session["user_id"]
        date = datetime.datetime.now().date()
        user = db.execute("SELECT username from users WHERE id = ?", user_id)
        return render_template("comment.html", comments = comments, date = date, user = user)

@app.route("/done", methods=["GET", "POST"])
@login_required
def done():
    if request.method == "GET":
        return render_template("index.html")
    else:
        request.method == "POST"

        wish_id = request.form.get("id")

        if not wish_id:
            return apology("Wish_ID is needed!")

        user_id = session["user_id"]

        wish_id_db = db.execute("SELECT id FROM wishes WHERE user_id = ?", user_id)
        # so the wish_id_db will show [{id: 1}, {id: 2}] etc.


        unfinished_wish = db.execute("SELECT COUNT(wish_unfinished) AS FROM users WHERE id = ?", user_id)

        unfinished_wish_count = unfinished_wish[0]["wish_unfinished"]

        unfinished_wish_count -= 1

        yes = True

        db.execute("UPDATE users SET wish_unfinished = ? WHERE id = ?", unfinished_wish_count, user_id)

        db.execute("UPDATE wishes SET wish_done = ? WHERE id = ?", yes, wish_id)

        wishes = db.execute("SELECT date, type_id, id, content, wish_done FROM wishes WHERE user_id = ? ORDER BY date DESC", user_id)

        # Note: to use datetime function, you need to import the library datetime
        date = datetime.datetime.now()

        flash("One done! on {}! {} left! Keep going!".format(date, unfinished_wish_count))

        return render_template("index.html", wish_number = unfinished_wish_count, wishes = wishes)



