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

app = Flask(__name__)
app.secret_key = "secret123"

print("DB PATH: ", os.path.abspath("users.db"))

#Database
def init_db():
    print("DB Maintenance Check: INIT DB START")

    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        password TEXT,
        timezone TEXT DEFAULT 'Asia/Kuala_Lumpur'
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

        conn = sqlite3.connect("users.db")
        c = conn.cursor()
        c.execute("INSERT INTO users (username, password) VALUES (?,?)", (username, password))
        conn.commit()
        conn.close()

        return redirect('/login')
    
    return render_template('register.html')

@app.route('/auth')
def auth():
    if 'user' in session:
        return redirect('/logout_confirm')
    return redirect('/login')

@app.context_processor
def inject_user():
    return dict(user = session.get('user'))

#Login
@app.route('/login', methods = ['GET', 'POST'])
def login():
    if request.method == "POST":
        username = request.form.get('username')
        password = request.form.get('password')

        conn = sqlite3.connect("users.db")
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=? and password=?", (username, password))
        user = c.fetchone()
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
    return render_template("index.html")

#History
@app.route('/history')
def history():
    if 'user' not in session:
        return redirect('/login')
    
    conn = sqlite3.connect("users.db")
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    c.execute('SELECT timezone FROM users WHERE username=?',(session['user'],))
    user = c.fetchone()
    user_timezone = user['timezone'] if user else 'UTC'

    c.execute("""
        SELECT study, sleep, focus, stress, score, timestamp_utc
        FROM history WHERE username=?
        ORDER BY timestamp_utc DESC
    """, (session['user'],))

    data = c.fetchall()
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

    #timestamp_utc = Change time record to UTC (EX: Malaysia is UTC +8)
    timestamp_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    #Save history if user had registered
    if 'user' in session:
        conn = sqlite3.connect("users.db")
        c = conn.cursor()

        c.execute("""
            INSERT INTO history (username, study, sleep, focus, stress, score, timestamp_utc) VALUES (?,?,?,?,?,?,?)
        """, (session['user'], study, sleep, focus, stress, score, timestamp_utc))

        conn.commit()
        conn.close()

    return render_template(
        'result.html',
        score = score,
        analysis = analysis,
        recommendation = recommendation,
        main_issue = main_issue,
        recs = recs,
        plot_url = plot_url
    )

if __name__ == "__main__":
    #Prevent Flask auto-reload that turn off socket
    app.run(debug = True, use_reloader = False)
