#render_template = server to browser
#request = browser to server
from flask import Flask, render_template, request, redirect, session
import sqlite3
import os
from simulation import *
from visualization import get_performance_chart

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
        password TEXT
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
        score REAL
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
@app.route('/logout')
def logout():
    session.pop('user', None)

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
    c = conn.cursor()

    c.execute("SELECT study, sleep, focus, stress, score FROM history WHERE username=?", (session['user'],))
    data = c.fetchall()

    conn.close()

    # --- 这里是你新增的画图逻辑 ---
    # 1. 把数据库里拿到的原始数据，转换成我们图表能看懂的格式
    history_records = []
    for row in data:
        history_records.append({
            'study_hours': row[0],
            'sleep_hours': row[1],
            'focus_level': row[2],
            'stress_level': row[3]
        })
    
    # 2. 调用你刚才写的画图代码，生成折线图
    from visualization import create_history_trend_chart # 确保引入了你的模块
    trend_chart_url = create_history_trend_chart(history_records)
    # ------------------------------

    return render_template('history.html', data = data , trend_chart_url=trend_chart_url)

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

    #Save history if user had registered
    if 'user' in session:
        conn = sqlite3.connect("users.db")
        c = conn.cursor()

        c.execute("""
            INSERT INTO history (username, study, sleep, focus, stress, score) VALUES (?,?,?,?,?,?)
        """, (session['user'], study, sleep, focus, stress, score))

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
