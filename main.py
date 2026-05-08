#render_template = server to browser
#request = browser to server
from flask import Flask, render_template, request, redirect, session
import sqlite3
import os
from simulation import *
from visualization import get_performance_chart
from visualization import create_history_trend_chart
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

#For tester only whoever missing any environments
def check_dependencies():
    try:
        import flask
        import matplotlib
        import zoneinfo
    except ImportError as e:
        print("Missing dependency: ", e)
        print("Run: pip install -r requirements.txt")
        exit()

check_dependencies()
app = Flask(__name__)
app.secret_key = "secret123"

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
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            timezone TEXT DEFAULT 'Asia/Kuala_Lumpur',
            points INTEGER DEFAULT 0
        )
        """)

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

        c.execute("""
        CREATE TABLE IF NOT EXISTS pomodoro (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            duration INTEGER,
            completed INTEGER,
            timestamp_utc TEXT
        )
        """)
    
        conn.commit()

    finally:
        conn.close()

    print("DB Maintenance Check: INIT DB DONE")

init_db()

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

        conn = get_db()
        c = conn.cursor()

        try:
            c.execute("INSERT INTO users (username, password) VALUES (?,?)", (username, password))
            conn.commit()

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
    if 'user' in session:
        conn = get_db()
        c = conn.cursor()

        try:
            c.execute("SELECT points FROM users WHERE username=?", (session['user'],))
            result = c.fetchone()

            if result:
                points = result[0]
        
        finally:
            conn.close()
        
    return dict(user = session.get('user'), points = points)

#Login
@app.route('/login', methods = ['GET', 'POST'])
def login():
    if request.method == "POST":
        username = request.form.get('username')
        password = request.form.get('password')

        conn = get_db()
        c = conn.cursor()

        try:
            c.execute("SELECT * FROM users WHERE username=? and password=?", (username, password))
            user = c.fetchone()
        
        finally:
            conn.close()

        if user:
            session['user'] = username
            return redirect('/')
        else:
            return "Login Failed"
        
    return render_template('login.html')

#Logout
@app.route('/logout_confirm')
def logout_confirm():
    return render_template("logout_confirm.html")

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/')

#Simulation
@app.route('/index')
def index():
    if 'user' not in session:
        return render_template("index.html")
    
    conn = get_db()
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    try:
        c.execute("""
            SELECT focus, stress FROM history WHERE username=? ORDER BY timestamp_utc DESC LIMIT 5
        """, (session['user'],))

        history = c.fetchall()

        if not history:
            return render_template("index.html", predicted_focus = None, predicted_stress = None)
        
        history_record = [
            {
                "focus_level": h["focus"],
                "stress_level": h["stress"]
            }
            for h in history
        ]

        c.execute("""
            SELECT COUNT(*) FROM pomodoro WHERE username=? AND timestamp_utc >= datetime('now', '-1 day')
        """,(session['user'],))

        pomodoro_count = c.fetchone()[0]
    
    finally:
        conn.close()

    predicted_focus, predicted_stress = predict_base_state(history_record, pomodoro_count)

    return render_template("index.html", predicted_focus = predicted_focus, predicted_stress = predicted_stress)

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
        user_timezone = user['timezone'] if user else 'UTC'

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

#Pomodoro
@app.route('/pomodoro')
def pomodoro():
    if 'user' not in session:
        return redirect('/login')
    return render_template('pomodoro.html')

@app.route('/completed_pomodoro', methods = ['POST'])
def completed_pomodoro():
    if 'user' not in session:
        return redirect('/login')
    duration = int(request.form['duration']) #25 / 50 etc
    if duration not in [5, 25, 50]:
        return "Invalid duration"
    
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

#Market Research
@app.route('/market_research')
def market_research():
    return render_template("market_research.html")

#Result
@app.route('/result', methods = ['POST'])
def result():
    student_type = request.form['student_type']

    try:
        study = int(request.form['study'])
        sleep = int(request.form['sleep'])
        focus = int(request.form['focus'])
        stress = int(request.form['stress'])
    except ValueError:
        return "Please enter valid numbers"
    except KeyError:
        return "Invalid input"
    
    if not check_valid_input(study, sleep, focus, stress):
        return "Invalid input"
    
    #timestamp_utc = Change time record to UTC (EX: Malaysia is UTC +8)
    timestamp_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    
    behavior_msg = "Login any account and try our Pomodoro Technique for more accurate result"

    if 'user' in session:
        conn = get_db()
        c = conn.cursor()

        try:
            #Pomodoro count reset every 24 hours
            c.execute("SELECT COUNT(*) FROM pomodoro WHERE username=? AND timestamp_utc >= datetime('now', '-1 day')", (session['user'],))
            pomodoro_count = c.fetchone()[0]

        finally:
            conn.close()

        behavior_msg = f"You completed {pomodoro_count} Pomodoro sessions in the last 24 hours"
        focus, stress = apply_pomodoro_effects(focus, stress, pomodoro_count)

    analysis, recommendation = analyze_factors(study, sleep, focus, stress)
    recommendation = apply_scenario_context(student_type, recommendation)

    score = calculate_score(study, sleep, focus, stress)

    main_issue = get_main_issue(score, study, sleep, focus, stress)
    recs = get_recommendation(score, analysis, recommendation)

    plot_url = get_performance_chart(
        s_study(study),
        s_sleep(sleep),
        s_focus(focus),
        s_stress(stress)
    )

    #Save history if user had login
    if 'user' in session:
        conn = get_db()
        c = conn.cursor()

        try:
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
        main_issue = main_issue,
        recs = recs,
        behavior_msg = behavior_msg,
        plot_url = plot_url
    )

if __name__ == "__main__":
    #Prevent Flask auto-reload that turn off socket
    app.run(debug = True, use_reloader = False)
