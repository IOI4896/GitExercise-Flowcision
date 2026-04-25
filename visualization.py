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
#刚加的


def create_history_trend_chart(history_records):
    """
    生成历史趋势折线图
    history_records: 包含多次测试结果的列表
    """
    # 如果用户只测了一次或还没测过，画不出“趋势”，直接跳过
    if not history_records or len(history_records) < 2:
        return None

    # 提取每次测试的分数
    # 假设传进来的数据格式是字典的列表：[{'study': 5, 'sleep': 8, ...}, ...]
    x_labels = [f"Test {i+1}" for i in range(len(history_records))]
    study_scores = [record.get('study_hours', 0) for record in history_records]
    sleep_scores = [record.get('sleep_hours', 0) for record in history_records]
    focus_scores = [record.get('focus_level', 0) for record in history_records]
    stress_scores = [record.get('stress_level', 0) for record in history_records]

    # 清空之前的画布，防止和第一张图重叠
    plt.clf()
    
    # 设置画布大小
    plt.figure(figsize=(10, 5))
    
    # 画四条折线，加上不同形状的节点(marker)
    plt.plot(x_labels, study_scores, marker='o', label='Study Hours', color='blue')
    plt.plot(x_labels, sleep_scores, marker='s', label='Sleep Hours', color='green')
    plt.plot(x_labels, focus_scores, marker='^', label='Focus Level', color='orange')
    plt.plot(x_labels, stress_scores, marker='x', label='Stress Level', color='red')

    # 图表的美化
    plt.title('Your Simulation History Trend')
    plt.xlabel('Simulation Count')
    plt.ylabel('Scores')
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.7)

    # 转换成网页能显示的格式（和昨天一模一样）
    img = io.BytesIO()
    plt.savefig(img, format='png', bbox_inches='tight')
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode('utf8')
    plt.close()

    return plot_url