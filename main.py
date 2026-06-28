#For tester only whoever missing any environments
def check_dependencies():
    try:
        import flask
        import matplotlib
        import zoneinfo
        import flask_limiter
    except ImportError as e:
        print("Missing dependency: ", e)
        print("Run: pip install -r requirements.txt")
        exit()

check_dependencies()

#render_template = server to browser
#request = browser to server
from flask import Flask, Response, render_template, request, redirect, session, send_from_directory, flash
import sqlite3
import os
from simulation import *
from visualization import get_performance_chart
from visualization import create_history_trend_chart
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import hashlib
import csv
import io
import json
import logging

app = Flask(__name__)
app.secret_key = "secret123"

# Initialize Security Audit Logging
log_format = '%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
logging.basicConfig(
    level=logging.INFO,
    format=log_format,
    handlers=[
        logging.FileHandler("server_audit.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("FlowcisionLogger")
logger.info("System Boot: Security Audit Logging initialized.")

app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax'
)

#Initialize the rate limiter (default global limit is 200 requests per day and 5)
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"]
)

print("DB PATH: ", os.path.abspath("users.db"))

#Database
def get_db():
    return sqlite3.connect("users.db", timeout = 5)

def init_db():
    print("DB Maintenance Check: INIT DB START")

    conn = get_db()
    c = conn.cursor()

    try:
        c.execute("ALTER TABLE users ADD COLUMN points INTEGER DEFAULT 0")
    except:
        pass

    try:
        c.execute("""
            ALTER TABLE users ADD COLUMN simulation_hotkey TEXT DEFAULT 'i'
        """)
    except:
        pass

    try:
        c.execute("""
            ALTER TABLE users ADD COLUMN pomodoro_hotkey TEXT DEFAULT 'p'
        """)
    except:
        pass

    try:
        c.execute("""
            ALTER TABLE users ADD COLUMN history_hotkey TEXT DEFAULT 'h'
        """)
    except:
        pass

    try:
        c.execute("""
            ALTER TABLE users ADD COLUMN dashboard_hotkey TEXT DEFAULT 'd'
        """)
    except:
        pass

    try:
        c.execute("""
            ALTER TABLE users ADD COLUMN planner_hotkey TEXT DEFAULT 'l'
        """)
    except:
        pass

    try:
        c.execute("""
            ALTER TABLE users ADD COLUMN settings_hotkey TEXT DEFAULT 's'
        """)
    except:
        pass

    try:
        c.execute("""
            ALTER TABLE users ADD COLUMN back_hotkey TEXT DEFAULT 'z'
        """)
    except:
        pass

    try:
        #User Database
        c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            tutorial_completed INTEGER DEFAULT 0,
            timezone TEXT DEFAULT 'AUTO',
            points INTEGER DEFAULT 0,
            planner_notification INTEGER DEFAULT 1,
            pomodoro_notification INTEGER DEFAULT 1,
            desktop_notification INTEGER DEFAULT 0,
            simulation_hotkey TEXT DEFAULT 'i',
            pomodoro_hotkey TEXT DEFAULT 'p',
            history_hotkey TEXT DEFAULT 'h',
            dashboard_hotkey TEXT DEFAULT 'd',
            planner_hotkey TEXT DEFAULT 'l',
            settings_hotkey TEXT DEFAULT 's',
            back_hotkey TEXT DEFAULT 'z',
            music_enabled INTEGER DEFAULT 1,
            music_volume INTEGER DEFAULT 50,
            music_theme TEXT DEFAULT 'none'
        )
        """)

        #History Database
        c.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            study INTEGER,
            sleep INTEGER,
            focus INTEGER,
            stress INTEGER,
            score REAL,
            timestamp_utc TEXT
        )
        """)

        #Pomodoro Database
        c.execute("""
        CREATE TABLE IF NOT EXISTS pomodoro (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            duration INTEGER,
            completed INTEGER,
            timestamp_utc TEXT
        )
        """)

        #Planner Database
        c.execute("""
        CREATE TABLE IF NOT EXISTS planner (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            day TEXT,
            hour INTEGER,
            task TEXT,
            UNIQUE(username, day, hour)
        )
        """)

        #Planner Preset Database
        c.execute("""
        CREATE TABLE IF NOT EXISTS planner_presets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            task TEXT
        )
        """)

        conn.commit()

    finally:
        conn.close()

    print("DB Maintenance Check: INIT DB DONE")

init_db()

@app.route('/images/<filename>')
def get_images(filename):
    return send_from_directory('static/images', filename)

def get_user_timezone(username):
    conn = get_db()
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    try:
        c.execute("Select timezone FROM users WHERE username=?", (username,))

        user = c.fetchone()

        if not user:
            return "UTC"

        timezone_setting = user["timezone"]

        if timezone_setting == "AUTO":
            device_tz = session.get("device_timezone", "UTC")
            return device_tz
        
        return timezone_setting
    
    finally:
        conn.close()

@app.route('/save_timezone', methods = ["POST"])
def save_timezone():
    data = request.get_json()
    
    session["device_timezone"] = data["timezone"]
    return {"status": "ok"}

#Home
@app.route('/')
def home():
    return render_template("home.html")

#Register
@app.route('/register', methods = ['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        ip_address = request.remote_addr # 抓取访问者IP
        
        logger.info(f"Registration Attempt: User '{username}' from IP {ip_address}")

        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        conn = get_db()
        c = conn.cursor()

        try:
            c.execute("INSERT INTO users (username, password) VALUES (?,?)", (username, hashed_password))
            conn.commit()
            logger.info(f"SUCCESS: Account '{username}' successfully created.")

        except Exception as e:
            logger.warning(f"SECURITY ALERT: Failed registration for '{username}' from IP {ip_address}. Reason: Username exists.")
            flash("Username already exists")
            return redirect('/register')
        
        finally:
            conn.close()

        return redirect('/login')
    return render_template('register.html')

#Auto switch between login / logout button and also prevent error
@app.route('/auth')
def auth():
    if 'user' in session:
        return redirect('/logout_confirm')
    return redirect('/login')

#Able connect info to all HTML
@app.context_processor
def inject_user():
    points = 0
    desktop_notification = 0
    planner_notification = 0
    pomodoro_notification = 0

    simulation_hotkey = "i"
    pomodoro_hotkey = "p"
    history_hotkey = "h"
    dashboard_hotkey = "d"
    planner_hotkey = "l"
    settings_hotkey = "s"
    back_hotkey = "z"

    music_enabled = 1
    music_volume = 50
    music_theme = "none"

    tutorial_completed = 0

    if 'user' in session:
        conn = get_db()
        conn.row_factory = sqlite3.Row
        c = conn.cursor()

        try:
            c.execute("SELECT tutorial_completed, points, desktop_notification, planner_notification, pomodoro_notification, simulation_hotkey, pomodoro_hotkey, history_hotkey, dashboard_hotkey, planner_hotkey, settings_hotkey, back_hotkey, music_enabled, music_volume, music_theme FROM users WHERE username=?", (session['user'],))
            row = c.fetchone()

            if row:
                tutorial_completed = row["tutorial_completed"]
                points = row["points"]
                desktop_notification = row["desktop_notification"]
                planner_notification = row["planner_notification"]
                pomodoro_notification = row["pomodoro_notification"]

                simulation_hotkey = (row["simulation_hotkey"] or "i")
                pomodoro_hotkey = (row["pomodoro_hotkey"] or "p")
                history_hotkey = (row["history_hotkey"] or "h")
                dashboard_hotkey = (row["dashboard_hotkey"] or "d")
                planner_hotkey = (row["planner_hotkey"] or "l")
                settings_hotkey = (row["settings_hotkey"] or "s")
                back_hotkey = (row["back_hotkey"] or "z")

                music_enabled = row["music_enabled"]
                music_volume = row["music_volume"]
                music_theme = row["music_theme"]
        
        finally:
            conn.close()
        
    return dict(user = session.get('user'), 
                tutorial_completed = tutorial_completed,
                points = points, 
                desktop_notification = desktop_notification, 
                planner_notification = planner_notification, 
                pomodoro_notification = pomodoro_notification,
                simulation_hotkey = simulation_hotkey,
                pomodoro_hotkey = pomodoro_hotkey,
                history_hotkey = history_hotkey,
                dashboard_hotkey = dashboard_hotkey,
                planner_hotkey = planner_hotkey,
                settings_hotkey = settings_hotkey,
                back_hotkey = back_hotkey,
                music_enabled = music_enabled,
                music_volume = music_volume,
                music_theme = music_theme)

#Login
@app.route('/login/', methods = ['GET', 'POST'])
@limiter.limit("10 per minute")
def login():
    if request.method == "POST":
        username = request.form.get('username')
        password = request.form.get('password')
        ip_address = request.remote_addr  

        hashed_password = hashlib.sha256(password.encode()).hexdigest()

        conn = get_db()
        c = conn.cursor()

        try:
            c.execute("SELECT * FROM users WHERE username=? and password=?", (username, hashed_password))
            user = c.fetchone()
        
        finally:
            conn.close()

        if user:
            session['user'] = username
            logger.info(f"SUCCESS: User '{username}' logged in from IP {ip_address}.") 
            return redirect('/')
        else:
            logger.warning(f"FAILED LOGIN: Invalid credentials for '{username}' from IP {ip_address}.") 
            flash("Invalid Username or Password. Please try again.")
            return redirect('/login/')
        
    return render_template('login.html')

@app.errorhandler(429)
def ratelimit_handler(e):
    ip_address = request.remote_addr
    logger.warning(f"SECURITY ALERT: Rate limit exceeded by IP: {ip_address}! Blocked by Limiter.")
    return "Too Many Requests. You have been temporarily blocked.", 429

#Logout
@app.route('/logout_confirm')
def logout_confirm():
    return render_template("logout_confirm.html")

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/')

#Tutorial
@app.route('/complete_tutorial', methods = ["POST"])
def complete_tutorial():
    if 'user' not in session:
        return {"status": "not logged in"}, 401
    
    conn = get_db()
    c = conn.cursor()

    try:
        c.execute("""
            UPDATE users
            SET tutorial_completed=1
            WHERE username=?
        """, (session['user'],))

        conn.commit()
    
    finally:
        conn.close()
    
    return {"status": "ok"}

#Settings
@app.route('/settings', methods = ['GET', 'POST'])
def settings():
    if 'user' not in session:
        return redirect('/login')
    
    conn = get_db()
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    if request.method == 'POST':
        planner_notification = (1 if 'planner_notification' in request.form else 0)
        pomodoro_notification = (1 if 'pomodoro_notification' in request.form else 0)
        desktop_notification = (1 if 'desktop_notification' in request.form else 0)

        hotkeys = {
            "simulation": request.form.get("simulation_hotkey", "i"),
            "pomodoro": request.form.get("pomodoro_hotkey", "p"),
            "history": request.form.get("history_hotkey", "h"),
            "dashboard": request.form.get("dashboard_hotkey", "d"),
            "planner": request.form.get("planner_hotkey", "l"),
            "settings": request.form.get("settings_hotkey", "s"),
            "back": request.form.get("back_hotkey", "z")
        }

        music_enabled = 1 if 'music_enabled' in request.form else 0
        music_theme = request.form.get("music_theme", "none")
        music_volume = int(request.form.get("music_volume", 50))

        #Check duplicate
        values = list(hotkeys.values())
        if len(values) != len(set(values)):
            flash("Hotkeys cannot be duplicated")
            return redirect('/settings')
        
        #Only single key
        for k, v in hotkeys.items():
            if len(v) != 1:
                flash(f"{k} hotkey must be a single key")
                return redirect('/settings')
        
        timezone = request.form.get('timezone', 'UTC')
        
        try:
            c.execute("""
                UPDATE users
                SET
                    planner_notification=?,
                    pomodoro_notification=?,
                    desktop_notification=?,
                    timezone=?,
                    simulation_hotkey=?,
                    pomodoro_hotkey=?,
                    history_hotkey=?,
                    dashboard_hotkey=?,
                    planner_hotkey=?,
                    settings_hotkey=?,
                    back_hotkey=?,
                    music_enabled=?,
                    music_theme=?,
                    music_volume=?
                WHERE username=?
            """, (planner_notification, pomodoro_notification, desktop_notification, timezone, hotkeys["simulation"], hotkeys["pomodoro"], hotkeys["history"], hotkeys["dashboard"], hotkeys["planner"], hotkeys["settings"], hotkeys["back"], music_enabled, music_theme, music_volume, session['user'],))

            conn.commit()
        
        finally:
            conn.close()
        
        return redirect('/settings')
    
    try:
        c.execute("""
            SELECT * FROM users WHERE username=?
        """, (session['user'],))

        settings_data = c.fetchone()
    
    finally:
        conn.close()
    
    return render_template("settings.html", settings_data = settings_data)

#Performance Assessment Analyzer
@app.route('/index')
def index():
    if 'user' not in session:
        return redirect('/login')
    
    conn = get_db()
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    try:
        predicted_study = None
        predicted_sleep = None
        predicted_focus = None
        predicted_stress = None

        c.execute("""
            SELECT sleep FROM history WHERE username=? ORDER BY timestamp_utc DESC LIMIT 5
        """, (session['user'],))

        sleep_history = c.fetchall()

        today = datetime.now().strftime("%A")

        c.execute("""
            SELECT hour, task
            FROM planner WHERE username=? AND day=?
        """, (session['user'], today))

        planner_rows = c.fetchall()

        planner_tasks = [row["task"] for row in planner_rows if row["task"]]
        planner_categories = [classify_task(t) for t in planner_tasks]

        stress_adjustment = 0
        focus_adjustment = 0

        if planner_rows:
            predicted_study, _ = study_pattern(planner_categories)
        
            planned_sleep = calculate_planned_sleep(planner_rows)

            previous_sleep = [row["sleep"] for row in sleep_history if row["sleep"] is not None]
            predicted_sleep = predict_sleep(planned_sleep, previous_sleep)

            all_tasks = []
            for row in planner_rows:
                if row["task"]:
                    all_tasks.append(row["task"])
        
            categories = [classify_task(task) for task in all_tasks]
            stress_adjustment = planner_stress(categories)
            focus_adjustment = planner_focus(categories)

        c.execute("""
            SELECT COUNT(*) FROM pomodoro WHERE username=? AND timestamp_utc >= datetime('now', '-1 day')
        """,(session['user'],))

        pomodoro_count = c.fetchone()[0]

        if planner_tasks:
            predicted_focus, predicted_stress = predict_base_state(pomodoro_count, stress_adjustment, focus_adjustment)
        
        if not planner_rows:
            predicted_focus = None
            predicted_stress = None

    finally:
        conn.close()

    if any(x is None for x in [predicted_study, predicted_sleep, predicted_focus, predicted_stress]):
        return render_template("index.html",
            predicted_focus = None,
            predicted_stress = None,
            predicted_study = None,
            predicted_sleep = None)
    
    session["predicted_focus"] = predicted_focus
    session["predicted_stress"] = predicted_stress
    session["predicted_study"] = predicted_study
    session["predicted_sleep"] = predicted_sleep

    return render_template("index.html", 
        predicted_focus = round(predicted_focus), 
        predicted_stress = round(predicted_stress), 
        predicted_study = round(predicted_study), 
        predicted_sleep = round(predicted_sleep))

#Dashboard
@app.route('/dashboard')
def dashboard():
    if 'user'not in session:
        return redirect('/login')
    
    conn = get_db()
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    try:
        #User points
        c.execute("""
            SELECT points FROM users WHERE username=?
        """, (session['user'],))

        user_data = c.fetchone()
        
        #History Analytics
        c.execute("""
            SELECT
                COUNT(*) as total_simulations,
                AVG(score) as avg_score,
                MAX(score) as best_score
            FROM history WHERE username=?
        """, (session['user'],))

        history_stats = c.fetchone()
        total_simulations = history_stats["total_simulations"] or 0
        avg_score = round(history_stats["avg_score"] or 0, 2)
        best_score = round(history_stats["best_score"] or 0, 2)

        #Pomodoro Analytics
        c.execute("""
            SELECT
                COUNT(*) as total_pomodoro,
                SUM(duration) as total_minutes
            FROM pomodoro WHERE username=?
        """, (session['user'],))

        pomodoro_stats = c.fetchone()
        total_pomodoro = pomodoro_stats["total_pomodoro"] or 0
        total_minutes = pomodoro_stats["total_minutes"] or 0
        total_hours = pomodoro_hours(total_minutes)

        #Planner Analytics
        c.execute("""
            SELECT task
            FROM planner WHERE username=?
        """, (session['user'],))

        planner_rows = c.fetchall()

        all_tasks = []
        for row in planner_rows:
            if row["task"]:
                all_tasks.append(row["task"])
        
        categories = [classify_task(task) for task in all_tasks]
        study_count, academic_count, rest_count, exercise_count, work_count, other_count = task_count(categories)

        #Workload Status
        workload_status = workload_stats(categories)
        
        #Most Common Task
        all_tasks = [task for task in all_tasks if task and task.strip()]
        most_common_task = most_common_tasks(all_tasks)

    finally:
        conn.close()
    
    points = user_data['points'] if user_data else 0

    pet_stage = pet_progression(points)

    return render_template(
        "dashboard.html", points = points, 
        total_simulations = total_simulations, avg_score = avg_score, best_score = best_score,
        total_pomodoro = total_pomodoro, total_minutes = total_minutes, total_hours = total_hours,
        most_common_task = most_common_task, workload_status = workload_status,
        study_count = study_count, academic_count = academic_count, rest_count = rest_count, exercise_count = exercise_count, work_count = work_count, other_count = other_count,
        pet_stage = pet_stage
    )

#History
@app.route('/history')
def history():
    if 'user' not in session:
        return redirect('/login')
    
    conn = get_db()
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    try:
        c.execute('SELECT timezone FROM users WHERE username=?',(session['user'],))
        user = c.fetchone()
        user_timezone = get_user_timezone(session['user'])

        c.execute("""
            SELECT study, sleep, focus, stress, score, timestamp_utc
            FROM history WHERE username=?
            ORDER BY timestamp_utc DESC
        """, (session['user'],))

        data = c.fetchall()
    
    finally:
        conn.close()

    #trend chart record
    history_records = []

    #showcase table record
    history_data = []

    for record in data:
        utc_dt = datetime.strptime(record['timestamp_utc'], "%Y-%m-%d %H:%M:%S")
        utc_dt = utc_dt.replace(tzinfo = timezone.utc)

        local_dt = utc_dt.astimezone(ZoneInfo(user_timezone))

        history_records.append({
            'study_hours': record[0],
            'sleep_hours': record[1],
            'focus_level': record[2],
            'stress_level': record[3],
        })

        history_data.append({
            'study' : record['study'],
            'sleep' : record['sleep'],
            'focus' : record['focus'],
            'stress' : record['stress'],
            'score' : record['score'],
            'timestamp' : local_dt.strftime("%Y-%m-%d %H:%M:%S")
        })

    trend_chart_url = create_history_trend_chart(history_records)

    return render_template('history.html', data = history_data, trend_chart_url = trend_chart_url)

# Export data as a CSV report
@app.route('/export_csv')
def export_csv():
    if 'user' not in session:
        return redirect('/login')
    
    username = session['user']
    conn = get_db()
    c = conn.cursor()
    
    c.execute("SELECT study, sleep, focus, stress, score, timestamp_utc FROM history WHERE username=?", (username,))
    records = c.fetchall()
    conn.close()

    # Generate CSV table
    si = io.StringIO()
    cw = csv.writer(si)
    cw.writerow(['Study', 'Sleep', 'Focus', 'Stress', 'Score', 'Date & Time'])
    cw.writerows(records)
    
    return Response(
        si.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=Flowcision_History.csv"}
    )

#Planner
@app.route('/planner', methods = ['GET', 'POST'])
def planner():
    if 'user' not in session:
        return redirect('/login')

    conn = get_db()
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    default_presets = ["Lecture", "Self Study", "Rest", "Sleep", "Revision", "Assignment", "Examination"]

    try:
        if request.method == 'POST':
            for day in days:
                for hour in range(24):
                    task = request.form.get(f"{day}_h{hour}")

                    if task == "Custom":
                        custom_task = request.form.get(f"{day}_h{hour}_custom")
                        task = custom_task.strip() if task else ""
                    else:
                        task = task.strip() if task else ""
                    
                    if not task:
                        task = None

                    c.execute("""
                        INSERT INTO planner
                        (username, day, hour, task)
                        VALUES(?,?,?,?)
                        ON CONFLICT(username, day, hour)
                        DO UPDATE SET task=excluded.task
                    """, (session['user'], day, hour, task))

                    #Save Custom Preset
                    if task and task not in default_presets:
                        c.execute("""
                            SELECT * FROM planner_presets
                            WHERE username=? AND task=?
                        """, (session['user'], task))

                        if not c.fetchone():
                            c.execute("""
                                INSERT INTO planner_presets
                                (username, task)
                                VALUES (?,?)
                            """, (session['user'], task))

            conn.commit()

        #Load Preset Data
        c.execute("""
            SELECT day, hour, task FROM planner WHERE username=?
        """, (session['user'],))

        rows = c.fetchall()

        #Custom Preset
        planner_data = {}

        for row in rows:
            day = row["day"]
            hour = row["hour"]
            task = row["task"]

            if day not in planner_data:
                planner_data[day] = {}
            
            if task:
                planner_data[day][hour] = task

        c.execute("""
            SELECT task FROM planner_presets WHERE username=?
        """, (session['user'],))

        custom_rows = c.fetchall()

        custom_presets = [row['task'] for row in custom_rows]
        all_presets = default_presets + [p for p in custom_presets if p not in default_presets]

        all_tasks = []
        for day in planner_data.values():
            for task in day.values():
                if task and task != "Empty":
                    all_tasks.append(task)

        categories = [classify_task(task) for task in all_tasks]
        recognition_rate, analysis_confidence, planner_suggestion = generate_planner_suggestion(categories)

        day = datetime.now().strftime("%A")
        hour = datetime.now().hour

        c.execute("""
            SELECT task FROM planner
            WHERE username=? AND day=? AND hour=?
        """, (session['user'], day, hour))

        current_task_rows = c.fetchone()
        current_task = current_task_rows["task"]

        planner_json = json.dumps(planner_data)

    finally:
        conn.close()

    return render_template("planner.html", days = days, planner_data = planner_data, planner_json = planner_json, all_presets = all_presets, planner_suggestion = planner_suggestion, analysis_confidence = analysis_confidence, recognition_rate = recognition_rate, current_task = current_task)

#Pomodoro
@app.route('/pomodoro')
def pomodoro():
    if 'user' not in session:
        return redirect('/login')
    
    conn = get_db()
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    try:
        day = datetime.now().strftime("%A")
        hour = datetime.now().hour

        c.execute("""
            SELECT task FROM planner
            WHERE username=? AND day=? AND hour=?
        """, (session['user'], day, hour))

        current_task_rows = c.fetchone()
        current_task = current_task_rows["task"]
    
    finally:
        conn.close()

    return render_template('pomodoro.html', current_task = current_task)

@app.route('/completed_pomodoro', methods = ['POST'])
def completed_pomodoro():
    if 'user' not in session:
        return redirect('/login')
    duration = int(request.form['duration']) #25 / 50 etc
    
    points = calculate_pomodoro_points(duration)

    timestamp_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    conn = get_db()
    c = conn.cursor()

    try:
        c.execute("""
            INSERT INTO pomodoro (username, duration, completed, timestamp_utc) VALUES (?,?,?,?)
        """, (session['user'], duration, 1, timestamp_utc))

        c.execute("""
            UPDATE users SET points = points + ? WHERE username=?
        """, (points, session['user']))

        conn.commit()
    
    finally:
        conn.close()

    return redirect('/pomodoro_complete')

@app.route('/pomodoro_complete')
def pomodoro_complete():
    if 'user' not in session:
        return redirect('/login')
    
    conn = get_db()
    c = conn.cursor()

    try:
        c.execute("""
            SELECT points FROM users WHERE username=?
        """, (session['user'],))

        points = c.fetchone()[0]
    
    finally:
        conn.close()
    
    return render_template("pomodoro_complete.html", points = points)

#Easter Egg
@app.route('/backrooms')
def backrooms():
    if 'user' not in session:
        return redirect('/')
    
    conn = get_db()
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    try:
        c.execute("""
            SELECT points FROM users WHERE username=?
        """, (session['user'],))

        user_data = c.fetchone()

        points = user_data['points'] if user_data else 0
        user_timezone = get_user_timezone(session['user'])
    
    finally:
        conn.close()
    
    return render_template("backrooms.html", user = session['user'], points= points, timezone = user_timezone)

#Result
@app.route('/result', methods = ['POST'])
def result():
    study = session.get("predicted_study")
    sleep = session.get("predicted_sleep")
    focus = session.get("predicted_focus")
    stress = session.get("predicted_stress")
    
    if any(x is None for x in [study, sleep, focus, stress]):
        flash("Assessment data unavailable")
        return redirect("/index")
    
    #timestamp_utc = Change time record to UTC (EX: Malaysia is UTC +8)
    timestamp_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    if 'user' in session:
        conn = get_db()
        conn.row_factory = sqlite3.Row
        c = conn.cursor()

        try:
            #Pomodoro count reset every 24 hours
            c.execute("SELECT COUNT(*) FROM pomodoro WHERE username=? AND timestamp_utc >= datetime('now', '-1 day')", (session['user'],))
            pomodoro_count = c.fetchone()[0]

            c.execute("SELECT music_theme FROM users WHERE username=?", (session['user'],))
            music_theme = c.fetchone()

            today = datetime.now().strftime("%A")

            c.execute("""
                SELECT hour, task
                FROM planner WHERE username=? AND day=?
            """, (session['user'], today))

            planner_rows = c.fetchall()

            study_count = "None"
            academic_count = "None"
            rest_count = "None"
            work_count = "None"

            if planner_rows:
                categories = []
                for row in planner_rows:
                    if row["task"]:
                        categories.append(classify_task(row["task"]))

                study_count, academic_count, rest_count, e0, work_count, e1 = task_count(categories)
                planner_msg = planner_feedback(study, categories)

            else:
                planner_msg = ["Create your weekly schedule to receive smart planner suggestions."]

        finally:
            conn.close()

        behavior_msg = behavior_analysis(pomodoro_count, music_theme)

    analysis, recommendation, potential_strengths, potential_risks, interviewer_note = analyze_factors(study, sleep, focus, stress, study_count, academic_count, work_count, rest_count, pomodoro_count)

    score = calculate_score(study, sleep, focus, stress)

    main_issue = get_main_issue(score, study, sleep, focus, stress)
    recs = get_recommendation(score)

    plot_url = get_performance_chart(
        s_study(study),
        s_sleep(sleep),
        s_focus(focus),
        s_stress(stress)
    )

    if 'user' in session:
        conn = get_db()
        c = conn.cursor()

        try:
            #Save history
            c.execute("""
                INSERT INTO history (username, study, sleep, focus, stress, score, timestamp_utc) VALUES (?,?,?,?,?,?,?)
            """, (session['user'], study, sleep, focus, stress, score, timestamp_utc))

            conn.commit()
        
        finally:
            conn.close()

    return render_template(
        'result.html',
        score = score,
        analysis = analysis,
        recommendation = recommendation,
        potential_strengths = potential_strengths,
        potential_risks = potential_risks,
        interviewer_note = interviewer_note,
        main_issue = main_issue,
        recs = recs,
        behavior_msg = behavior_msg,
        planner_msg = planner_msg,
        plot_url = plot_url
    )

if __name__ == "__main__":
    #Prevent Flask auto-reload that turn off socket
    app.run(host = "0.0.0.0", debug = True, use_reloader = False)
