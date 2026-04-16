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
    
    if not check_valid_input(study, sleep, focus, sleep):
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
