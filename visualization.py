import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
import base64
from simulation import *

def get_performance_chart(s_study, s_sleep, s_focus, s_stress):
    plt.figure(figsize=(8, 4))
    categories = ['Study', 'Sleep', 'Focus', 'Stress Control']
    values = [s_study, s_sleep, s_focus, s_stress]
    colors = ['#4CAF50', '#2196F3', '#FFC107', '#F44336']

    plt.barh(categories, values, color=colors)
    plt.xlim(0, 100)
    plt.xlabel('Score (%)')
    plt.title('Performance Analysis')
    plt.tight_layout()

    img = io.BytesIO()
    plt.savefig(img, format='png', transparent=True)
    img.seek(0)
    return base64.b64encode(img.getvalue()).decode('utf8')

def create_history_trend_chart(history_records):
    if not history_records or len(history_records) < 2:
        return None

    x_labels = [f"Test {i+1}" for i in range(len(history_records))]
    study_scores = [s_study(record['study_hours']) for record in history_records]
    sleep_scores = [s_sleep(record['sleep_hours']) for record in history_records]
    focus_scores = [s_focus(record['focus_level']) for record in history_records]
    stress_scores = [s_stress(record['stress_level']) for record in history_records]

    plt.clf()
    
    plt.figure(figsize=(10, 5))
    
    plt.plot(x_labels, study_scores, marker='o', label='Study Score', color='blue')
    plt.plot(x_labels, sleep_scores, marker='s', label='Sleep Score', color='green')
    plt.plot(x_labels, focus_scores, marker='^', label='Focus Score', color='orange')
    plt.plot(x_labels, stress_scores, marker='x', label='Stress Control Score', color='red')

    plt.title('Your Simulation History Trend')
    plt.xlabel('Simulation Count')
    plt.ylabel('Performance Scores (%)')
    plt.ylim(0, 100)
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.tight_layout()

    img = io.BytesIO()
    plt.savefig(img, format='png', bbox_inches='tight')
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode('utf8')
    plt.close()

    return plot_url
