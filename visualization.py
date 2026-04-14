import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
import base64

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