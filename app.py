import os
import sqlite3
import apscheduler

from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime, timedelta
from apology import apology, login_required
from flask_apscheduler import APScheduler

# Configure application
app = Flask(__name__)
scheduler = APScheduler()


# Configure scheduler to reset all tasks at midnight
@scheduler.task('cron', id='reset_dailies', hour=0)
def perform_daily_action():
    # Connect database
    routine = sqlite3.connect('routine.db')
    db = routine.cursor()

    print("Commiting daily reset...")
    db.execute("UPDATE tasks SET done = ?", ("no", ))
    # Commit changes and close DB
    routine.commit()
    routine.close()

# Start the scheduler
scheduler.init_app(app)
scheduler.start()

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

@app.route("/leaderboards")
@login_required
def leaderboards():
    # Connect database
    routine = sqlite3.connect('routine.db')
    db = routine.cursor()  

    users = db.execute("SELECT * from users ORDER BY xp DESC")
    users_dict = []
    for user in users:
        user_dict = {
            "user": user[1],  
            "xp": user[4],  
        }
        users_dict.append(user_dict)

    routine.close()
    return render_template("leaderboards.html", users=users_dict)

@app.route("/routine")
@login_required
def routine():
    # SHOW TASKS

    # Connect database
    routine = sqlite3.connect('routine.db')
    db = routine.cursor()  

    tasks = db.execute("SELECT * from tasks WHERE user_id = ? ORDER BY substr(starting, 1, 2), substr(starting, 4, 2)", (session["user_id"],))
    tasks_dict = []
    for task in tasks:
        task_dict = {
            "id": task[0],  
            "name": task[1],  
            "diff": task[2],
            "starting": task[3],
            "ending": task[4],
            "done": task[5]
        }
        tasks_dict.append(task_dict)

    routine.close()
    return render_template("routine.html", tasks=tasks_dict)

@app.route("/perform_action", methods=["POST"])
@login_required
def perform_action():
    
    # Connect database
    routine = sqlite3.connect('routine.db')
    db = routine.cursor()  

    del_id = request.form.get('imageId')


    db.execute("DELETE FROM tasks WHERE id = ?", (del_id,))
    routine.commit()
    routine.close()
    return redirect("/routine")

@app.route("/complete_task", methods=["POST"])
@login_required
def complete_task():
    
    # Connect database
    routine = sqlite3.connect('routine.db')
    db = routine.cursor()  

    id = request.form.get('taskId')
    diff = int(request.form.get('taskDiff'))
    
    task_diff = db.execute("SELECT difficulty FROM tasks WHERE id = ?", (id,)).fetchone()
    task = db.execute("SELECT * from tasks WHERE id = ?", (id,)).fetchall()

    task_dict = {
            "id": task[0][0],  
            "name": task[0][1],  
            "diff": task[0][2],
            "starting": task[0][3],
            "ending": task[0][4],
            "done": task[0][5],
            "user_id": task[0][6]
        }

    if task_dict["user_id"] != session["user_id"]:
        return apology("Invalid task!", 402)
    elif task_dict["done"] == "yes":
        return apology("Task already completed!", 401)
    elif diff != int(task_diff[0]):
        return apology("Difficult don't match the server", 400)
    else:
        db.execute("UPDATE tasks SET done = ? WHERE id = ?", ("yes", id))
        routine.commit()
        db.execute("UPDATE users SET xp = xp + ? WHERE id = ?", (diff, session["user_id"]))
        routine.commit()
        routine.close()
        return redirect("/routine")





@app.route("/manage", methods=["GET", "POST"])
@login_required
def manage():

    # User tried to add task
    if request.method == "POST":
        if 'add' in request.form:

            # Connect database
            routine = sqlite3.connect('routine.db')
            db = routine.cursor()         

            # Get Values
            start_time = request.form.get("start-time")
            end_time = request.form.get("end-time")
            task = request.form.get("task")
            diff = request.form.get("diff")
            

            # Converting to datetime
            start_time_dt = datetime.strptime(start_time, '%H:%M')
            end_time_dt = datetime.strptime(end_time, '%H:%M')

            # Check if values are set
            if not diff or not task:
                return apology("Values not set")
            elif int(diff) < 1 or int(diff) > 3:
                return apology("Invalid Diffficulty")
            elif end_time_dt == start_time_dt:
                return apology("Starting and Ending time can't be the same")
            


            # Retrieve all existing tasks from the database
            all = db.execute("SELECT * FROM tasks WHERE user_id = ?", (session["user_id"],))
            for each in all:

                task_check = {
                    "starting": datetime.strptime(each[3], '%H:%M'),
                    "ending": datetime.strptime(each[4], '%H:%M')
                }

                if start_time_dt < end_time_dt:
                    # Normal case, no midnight crossing
                    if start_time_dt < task_check["ending"] and end_time_dt > task_check["starting"]:
                        return apology("Invalid hours!")
                else:
                    # Case where the time interval spans across midnight
                    if (start_time_dt < task_check["ending"] and task_check["ending"] < end_time_dt) \
                            or (start_time_dt < task_check["ending"] + timedelta(days=1) and end_time_dt > task_check["starting"]):
                        return apology("Invalid hours!")
                
            db.execute("INSERT INTO tasks (name, starting, ending, difficulty, user_id, done) values (?, ?, ?, ?, ?, ?)", (task, start_time, end_time, diff, session["user_id"], 'no'))
            
            # Commit changes and close DB
            routine.commit()
            routine.close()

            return render_template("manage.html")
        elif 'edit' in request.form:

            # Connect database
            routine = sqlite3.connect('routine.db')
            db = routine.cursor()

            # GET username data
            rows = db.execute("SELECT * FROM users WHERE id = ?", (session["user_id"],))
            rows = list(rows)

            # Check if old password is correct
            if check_password_hash(rows[0][2], request.form.get("old")):
                
                # Get Values
                new_username = request.form.get("username")
                new_password = request.form.get("password")
                repeat = request.form.get("repeat")
                hash = generate_password_hash(new_password, method='pbkdf2', salt_length=16)

                if new_username:
                    db.execute("UPDATE users SET username = ? WHERE id = ?", (new_username, session["user_id"]))
                    routine.commit()
                if new_password and new_password == repeat:
                    db.execute("UPDATE users SET hash = ? WHERE id = ?", (hash, session["user_id"]))
                    routine.commit()
                
                routine.close()
                return redirect("/manage")
            else:
                return apology("Invalid password")
        elif 'task' in request.form:
            
            # Connect database
            routine = sqlite3.connect('routine.db')
            db = routine.cursor()

            # Get Values
            old_task = request.form.get("old-task")
            start_time = request.form.get("edit-start")
            end_time = request.form.get("edit-end")
            task = request.form.get("edit-task")
            diff = request.form.get("edit-diff")

            # Check if values are set
            if not diff or not task or not old_task:
                return apology("Invalid values")
            elif int(diff) < 1 or int(diff) > 3:
                return apology("Invalid Diffficulty")
            else:
                db.execute("UPDATE tasks SET name = ?, difficulty = ?, starting = ?, ending = ? WHERE name = ? AND user_id = ?", (task, diff, start_time, end_time, old_task, session["user_id"]))
            
            routine.commit()
            routine.close()
            return redirect("/manage")
    else:

        # Connect database
        routine = sqlite3.connect('routine.db')
        db = routine.cursor() 
        
        user = db.execute("SELECT username FROM users where id = ?", (session["user_id"],))
        username = user.fetchone()
        name = username[0]

        tasks = db.execute("SELECT * from tasks WHERE user_id = ? AND done = ? ORDER BY substr(starting, 1, 2), substr(starting, 4, 2)", (session["user_id"], "no"))
        tasks_dict = []
        for task in tasks:
            task_dict = {
                "id": task[0],  
                "name": task[1],  
                "diff": task[2],
                "starting": task[3],
                "ending": task[4],
                "done": task[5]
            }   
            tasks_dict.append(task_dict)

        routine.close()
        return render_template("manage.html", name=name,tasks=tasks_dict)

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Connect database
    routine = sqlite3.connect('routine.db')
    db = routine.cursor()   
    
    # Forget any user_id
    session.clear()

    # User tried logging in
    if request.method == "POST":
        if not request.form.get("username"):
            return apology("Invalid username")
        elif not request.form.get("password"):
            return apology("Invalid password")
    
        # GET username data
        rows = db.execute( "SELECT * FROM users WHERE username = ?", (request.form.get("username"),))
        rows = list(rows)

        # Check if there is a username and password
        if len(rows) != 1 or not check_password_hash(
            rows[0][2], request.form.get("password")
        ):
            return apology("Username or password incorrect")
    
        # Remember which user has logged in
        session["user_id"] = rows[0][0]

        # Close DB
        routine.close()

        #redirect user to homepage
        return redirect("/routine")
    else:
        return render_template("login.html")
    
@app.route("/register", methods=["GET", "POST"])
def register():
    
    # Connect database
    routine = sqlite3.connect('routine.db')
    db = routine.cursor()

    # Get data
    username = request.form.get("username")
    password = request.form.get("password")
    repeat = request.form.get("repeat")

    # User tried register
    if request.method == "POST":
        if not username:
            return apology("Username can't be blank")
        if not password:
            return apology("Password can't be blank")
        if password != repeat:
            return apology("Passwords don't match")
    
        # Check if username already exists
        rows = db.execute("SELECT id FROM users WHERE username = ?", (username,))
        rows = list(rows)

        if len(rows) == 1:
            return apology("Username already taken")
        else:
            hash = generate_password_hash(password, method='pbkdf2', salt_length=16)
            db.execute("INSERT INTO users (username, hash, level, xp) values (?, ?, ?, ?)", (username, hash, 1, 0))

            # Commit changes and close DB
            routine.commit()
            routine.close()
            
            return redirect("/")
    else:
        return render_template("register.html")

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/logout")
@login_required
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

