from collections import Counter

#Score Converter
def study_score(study_hours):
    ideal = 4
    return max(0, 1 - abs(study_hours - ideal) / 10)

def sleep_score(sleep_hours):
    ideal = 8
    return max(0, 1 - abs(sleep_hours - ideal) / 8)

def focus_score(focus_level):
    if focus_level > 10:
        return 0
    return max(0, focus_level / 10)

def stress_score(stress_level):
    if stress_level > 10:
        return 0
    return max(0, 1 - (stress_level / 10))

#Score Penalty (Double penalty due to abnormal lifestyle and free riding)
def study_penalty(study_hours):
    if study_hours == 0:
        return 0
    return 1

def sleep_penalty(sleep_hours):
    if sleep_hours < 4 or sleep_hours > 12:
        return 0.5
    return 1

#Calculate Score
def calculate_score(study, sleep, focus ,stress):
    s1 = study_score(study)
    s2 = sleep_score(sleep)
    s3 = focus_score(focus)
    s4 = stress_score(stress)

    base = (s1 * 0.3) + (s2 * 0.3) + (s3 * 0.2) + (s4 * 0.2)
    penalty = study_penalty(study) * sleep_penalty(sleep)

    return round(base * penalty * 100, 2)

#Double check input
def check_valid_input(study, sleep, focus, stress):
    if study + sleep > 24 or focus > 10 or stress > 10:
        return False
    return True

#Analysis Data
def analyze_factors(study, sleep, focus, stress, study_count, academic_count, work_count, rest_count, pomodoro_streak):
    analysis = []
    recommendation = []
    strengths = []
    risks = []

    #Study
    if study <= 2:
        analysis.append("Your study time is low, this may lead to insufficient preparation or misunderstading.")
        recommendation.append("Increase daily study time, roman civilization was not achieved in a few days.")
    elif study >= 9:
        analysis.append("You may be overstudying.")
        recommendation.append("Avoid burnout by taking breaks and arrage learning paths reasonably, understanding is better than rote memorization.")
    
    #Sleep
    if sleep <= 5:
        analysis.append("Your sleep is below optimal level.")
        recommendation.append("Try to sleep atleast 7 hours, rest is for going further.")
        risks.append("Insufficient sleep may affect performance")
    elif sleep >= 10:
        analysis.append("You may be oversleeping.")
        recommendation.append("Maintain a consistent sleep schedule, having too much of anything is not good")
        risks.append("Excessive sleep may affect performance")
    else:
        strengths.append("Maintains a healthy sleep schedule.")
    
    #Focus
    if focus <= 4:
        analysis.append("Your focus level is low.")
        recommendation.append("Reduce distractions during study, focus is better than multitasking.")
        risks.append("Difficulty maintaining focus")
    elif focus >= 7:
        strengths.append("Demonstrates strong concentration ability.")

    #Stress
    if stress >= 7:
        analysis.append("Your stress level is too high.")
        recommendation.append("Consider relaxation or breaks, the world waits for no one, but you can wait for yourself.")
        risks.append("Elevated stress level detected.")

    #Planner
    if study_count != "None":
        if study_count + academic_count + work_count < rest_count * 3:
            strengths.append("Maintains a structured overall routine.")

    #Pomodoro
    if pomodoro_streak >= 5:
        strengths.append("Shows consistent focus discipline.")

    #Reasonable Daily Routine (No schedule issue and many potential)
    if analysis == [] and recommendation == [] and risks == [] and len(strengths) >= 3:
        analysis.append("You have a reasonable daily routine, keep it up!")
        recommendation.append("Try this kind of schedule to improve your grades.")

    elif analysis == [] and recommendation == []:
        analysis.append("You have a reasonable daily routine, but you still have room for improvement.")
        recommendation.append("Try out the accessibility features (Pomodoro, Planner, etc) we provided as your preference.")

    if risks == []:
        risks.append("No major concerns were identified based on the current data.")
    
    if strengths == []:
        strengths.append("Potential strengths become more accurate as additional simulations and activity records are collected.")

    return analysis, recommendation, strengths, risks

def get_main_issue(score, study, sleep, focus, stress):
    scores = {
        "Study" : study_score(study),
        "Sleep" : sleep_score(sleep) * sleep_penalty(sleep),
        "Focus" : focus_score(focus),
        "Stress" : stress_score(stress)
    }

    main_issue = min(scores, key = scores.get)

    if score < 90:
        return issue_message(main_issue)
    
    return "None"

#Explain result to user
def issue_message(issue):
    messages = {
        "Study" : "Your study time is insufficient.",
        "Sleep" : "Your sleep pattern needs improvement.",
        "Focus" : "Your focus level is too low.",
        "Stress" : "Your stress level is too high"
    }

    return messages.get(issue, "")

def apply_scenario_context(student_type, recommendation):
    context_recs = []

    if student_type == "foundation":
        context_recs.append("As a foundation student, focus on building strong fundamentals as they will impact future subjects.")
    
    elif student_type == "diploma":
        context_recs.append("As a diploma student, balancing coursework and practical skills is important for consistent performance.")
    
    elif student_type == "degree":
        context_recs.append("As a degree student, deeper understanding and independent learning are critical for success.")

    return context_recs + recommendation

def get_recommendation(score):
    if score < 40:
        return "The user may benefit from improving study habits and recovery routines."
    elif score < 70:
        return "The user shows moderate productivity with room for improvement."
    
    return "The user demostrates strong productivity potential."

#Calculate Graph
def s_study(study):
    return study_score(study) * study_penalty(study) * 100

def s_sleep(sleep):
    return sleep_score(sleep) * sleep_penalty(sleep) * 100

def s_focus(focus):
    return focus_score(focus) * 100

def s_stress(stress):
    return stress_score(stress) * 100

#Calculate Pomodoro (25 min = 10 points)
def calculate_pomodoro_points(duration):
    if duration >= 50:
        return 25
    
    elif duration >= 25:
        return 10
    
    elif duration == 5:
        return 10
    
    return 0

def apply_pomodoro_effects(base_focus, base_stress, pomodoro_count):
    bonus = min(pomodoro_count, 5)

    focus = min(10, base_focus + round(bonus / 2))
    stress = max(0, base_stress - round(bonus / 2))

    return focus, stress

#Predict System
def predict_base_state(history_records, pomodoro_count):
    if not history_records:
        return None, None
    
    avg_focus = sum(r['focus_level'] for r in history_records) / len(history_records)
    avg_stress = sum(r['stress_level'] for r in history_records) / len(history_records)

    predicted_focus = avg_focus + round(min(5, pomodoro_count) / 2)
    predicted_stress = avg_stress - round(min(5, pomodoro_count) / 2)

    predicted_focus = max(0, min(10, round(predicted_focus)))
    predicted_stress = max(0, min(10, round(predicted_stress)))
    
    return predicted_focus, predicted_stress

def study_pattern(sleep, morning_category, afternoon_category, night_category):
    planned_study = 0
    study_slots = 0

    if morning_category == "study":
        planned_study += 7
        study_slots += 1

    if afternoon_category == "study":
        planned_study += 6
        study_slots += 1

    if night_category == "study":
        planned_study += (11 - sleep)
        study_slots += 1
    
    return round(planned_study), study_slots

#Pet Progression
def pet_progression(points):
    if points >= 250:
        return "🌳 Focus Tree"
    elif points >= 100:
        return "🌿 Growing Plant"
    elif points >= 50:
        return "🌱 Sprout"
    else:
        return "🫘 Seed"
    
#Statistics
def pomodoro_hours(total_minutes):
    return round(total_minutes / 60, 1)

def task_count(categories):
    counts = Counter(categories)

    study_count = max(counts["study"], 0)
    academic_count = max(counts["academic"], 0)
    rest_count = max(counts["rest"], 0)
    exercise_count = max(counts["exercise"], 0)
    work_count = max(counts["work"], 0)
    other_count = max(counts["other"], 0)

    return study_count, academic_count, rest_count, exercise_count, work_count, other_count

def most_common_tasks(categories):
    counts = Counter(categories)
    most_common_task = "No Data"

    if counts:
        most_common_task = counts.most_common(1)[0][0]
    return most_common_task

def workload_stats(categories):
    study_count, academic_count, rest_count, exercise_count, work_count, other_count = task_count(categories)

    workload = study_count + academic_count + work_count
    recovery = rest_count + exercise_count

    if workload == 0:
        return "No Data"
    elif recovery == 0 or workload > recovery * 3:
        return "Heavy"
    return "Balanced"

def classify_task(task):
    task_categories = {
        "study": [
            "study",
            "revision",
            "research",
            "coding",
            "code",
            "practice",
            "assignment",
            "project",
            "homework"
        ],

        "academic": [
            "lecture",
            "class",
            "tutorial",
            "lab",
            "quiz",
            "test",
            "exam",
            "examination",
            "presentation",
        ],

        "rest": [
            "sleep",
            "rest",
            "break",
            "breakfast",
            "lunch",
            "dinner",
            "nap"
        ],

        "exercise": [
            "gym",
            "gymnasium",
            "exercise",
            "workout",
            "football",
            "basketball"
        ],

        "work": [
            "job",
            "meeting",
            "internship",
            "intern"
        ]
    }

    if not task:
        return "other"
    
    task = task.lower()
    for category, keywords in task_categories.items():
        for keyword in keywords:
            if keyword in task:
                return category
    
    return "other"

#Smart Planner Suggestion
def generate_planner_suggestion(categories):
    suggestions = []

    study_count, academic_count, rest_count, exercise_count, work_count, other_count = task_count(categories)

    recognized_count = study_count + academic_count + rest_count + exercise_count + work_count
    total_count = recognized_count + other_count

    #Prevent divided by 0
    if total_count == 0:
        recognition_rate = 0
    else:
        recognition_rate = round((recognized_count / total_count) * 100)

    analysis_confidence = "High"
    if recognition_rate < 50:
        analysis_confidence = "Low"
    elif recognition_rate < 80:
        analysis_confidence = "Medium"

    if recognized_count == 0:
        if other_count > 0:
            suggestions.append("Add recognizable tasks such as Study, Lecture, Assignment, Rest, Exercise or any of default presets that we given for more accurate recommendations.")
        suggestions.append("Create your weekly schedule to receive smart suggestions.")

        return recognition_rate, analysis_confidence, suggestions
    
    if rest_count == 0:
        suggestions.append("Your schedule contains no rest sessions.")

    if exercise_count == 0:
        suggestions.append("Consider adding exercise activities.")

    if study_count + academic_count + work_count > rest_count * 3:
        suggestions.append("Your workload may be too intensive")
    
    consecutive = 0
    for category in categories:
        if category in ["study", "academic"]:
            consecutive += 1
            if consecutive >= 4:
                suggestions.append("Too many consecutive academic sessions.")
                break
            else:
                consecutive = 0

    if not suggestions:
        suggestions.append("Your weekly schedule looks balanced.")
    
    return recognition_rate, analysis_confidence, suggestions

#User Behavior Analysis
def behavior_analysis(pomodoro_count, music_theme):
    behavior_msg = []

    behavior_msg.append(f"You completed {pomodoro_count} Pomodoro sessions today.")

    if music_theme == "rain":
        behavior_msg.append("Rain ambience may provide a calming environment for focused work.")

    if music_theme == "ocean":
        behavior_msg.append("Ocean sounds may promote relaxation and stress recovery.")

    if music_theme == "white_noise":
        behavior_msg.append("White noise can help reduce distractions during study sessions.")

    return behavior_msg

#Planner Feedback (Result)
def planner_feedback(study, sleep, morning_category, afternoon_category, night_category):
    planner_feedback = []
    planned_study, study_slots = study_pattern(sleep, morning_category, afternoon_category, night_category)
    
    if study_slots >= 2:
        planner_feedback.append("Your planner suggests a balanced day with significant study activities")
    
    elif study_slots == 1:
        planner_feedback.append("Today's planner contains a moderate study workload.")
    
    else:
        planner_feedback.append("Today's planner emphasizes recovery and non-study activities.")
    
    if study >= planned_study * 0.6:
        planner_feedback.append("Your study duration aligns well with today's planned workload.")

    else:
        planner_feedback.append("Your study is below the workload estimated from today's planner.")
    
    return planner_feedback
