#render_template = server to browser
#request = browser to server
from flask import Flask, render_template, request
from simulation import *
from visualization import get_performance_chart

app = Flask(__name__)

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/result', methods = ['POST'])
def result():
    try:
        study = int(request.form['study'])
        sleep = int(request.form['sleep'])
        focus = int(request.form['focus'])
        stress = int(request.form['stress'])
    except ValueError:
        return "Please enter valid numbers"
    except KeyError:
        return "Invalid input"
    
    #Double check input
    #24 hours invalid
    if study + sleep > 24:
        return "Nice try, more than 24 hours a day?"
    if focus > 10:
        return "May the force be with you :)"
    if stress > 10:
        return "I really envy your strong liver"

    analysis, recommendation = analyze_factors(study, sleep, focus, stress)
    score = calculate_score(study, sleep, focus, stress)

    if score >= 90:
        main_issue = "None"
    else:
        main_issue = get_main_issue(study, sleep, focus, stress)

    recs = get_recommendation(score, analysis, recommendation)

    #Calculation Graph
    plot_url = get_performance_chart(
        study_score(study) * study_penalty(study) * 100, 
        sleep_score(sleep) * sleep_penalty(sleep) * 100, 
        focus_score(focus) * 100, 
        stress_score(stress) * 100
    )
    
    return render_template(
        'result.html',
        score = score,
        analysis = analysis,
        recommendation = recommendation,
        main_issue = main_issue,
        recs = recs , 
        plot_url = plot_url
    )

if __name__ == "__main__":
    #Prevent Flask auto-reload that turn off socket
    app.run(debug = True, use_reloader = False)
