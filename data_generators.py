import random
import json
import os
from scipy.stats import truncnorm

# Load data files
try:
    path = os.path.join('data_crawler', 'data', 'title_index.json')
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
except FileNotFoundError:
    print(f"Warning: {path} not found. Some functions may not work correctly.")
    data = []

try:
    path_English = os.path.join('data_crawler', 'data', 'grammar_topics.json')
    with open(path_English, 'r', encoding='utf-8') as f:
        data_English = json.load(f)
        data_English = data_English.get('grammar_topics', [])
except FileNotFoundError:
    print(f"Warning: {path_English} not found. English topic generation may not work.")
    data_English = []

# Random float number between 1 and 10
def truncated_normal_points(mean=5, std=2.25, lower=0, upper=10, size=500000):
    """Generate truncated normal distribution points."""
    a, b = (lower - mean) / std, (upper - mean) / std
    return truncnorm.rvs(a, b, loc=mean, scale=std, size=size)

def generate_English_topic():
    """Generate a random English grammar topic."""
    if not data_English:
        return "Grammar basics"
    return random.choice(data_English)

def get_subject_topic(subject_title, grade_level):
    """Get a random topic for a given subject and grade level."""
    if subject_title == 'tiếng anh':
        return generate_English_topic()
    
    topic = None
    for ds in data:
        if ds['grade_level'] == str(grade_level):
            for subject in ds['subjects']:
                if subject_title in subject['subject_title'].lower():
                    lessons = subject.get('lessons', [])
                    if len(lessons) > 1:
                        # Filter out unwanted topics
                        valid_lessons = [
                            lesson for lesson in lessons[1:]
                            if 'tổng hợp' not in lesson.lower() 
                            and 'chương' not in lesson.lower() 
                            and 'chủ đề' not in lesson.lower()
                        ]
                        if valid_lessons:
                            topic = random.choice(valid_lessons).lower()
                            break
    
    if not topic:
        topic = "Khái niệm cơ bản"
    return topic
# Pre-generate samples for student level (lazy loading would be better, but kept for compatibility)
samples = truncated_normal_points()

def select_subject(SUBJECTS_DISTRIBUTION=None):
    """Selects a random subject based on configured distribution."""
    if SUBJECTS_DISTRIBUTION is None:
        from .config_education import GENERAL_CONFIG
        SUBJECTS_DISTRIBUTION = GENERAL_CONFIG["subjects"]
    
    if not SUBJECTS_DISTRIBUTION:
        raise ValueError("SUBJECTS_DISTRIBUTION cannot be empty")
    
    rand_val = random.random()
    cumulative_prob = 0.0
    total_weight = sum(SUBJECTS_DISTRIBUTION.values())
    
    if total_weight == 0:
        raise ValueError("Total weight in SUBJECTS_DISTRIBUTION cannot be zero")
    
    for subject, prob in SUBJECTS_DISTRIBUTION.items():
        cumulative_prob += prob / total_weight
        if rand_val < cumulative_prob:
            return subject
    
    # Fallback: return last subject if rounding errors occur
    return list(SUBJECTS_DISTRIBUTION.keys())[-1]

def generate_psychological_input_task5(config):
    """
    Generates random input for Task 5 (Psychological Support).
    Returns psychological topic and student profile.
    """
    topic = random.choice(config["psychological_topics"])
    profile = random.choice(config["student_profiles"])
    grade_level = random.choice(config["grade_levels"])
    return {
        "chủ_đề_tâm_lý": topic,
        "hồ_sơ_học_sinh": profile,
        "lớp": grade_level
    }

def re_choice(subject_title, grade_level):
    if grade_level == 1:
        return random.choice(["toán", "tiếng việt"])
    if subject_title in ["vật lí", "hóa", "sinh"]:
        if grade_level < 4:
            subject_title = "tự nhiên và xã hội"
        elif grade_level < 6:
            subject_title = "khoa học"
        elif grade_level < 10:
            subject_title = "khtn"
    if subject_title in ["sử", "địa"] and grade_level < 6:
        if grade_level > 3:
            subject_title = "lịch sử và địa lí"
        else: #học Toán trước nhé các mầm non tương lai :D
            subject_title = "toán"
    if subject_title in ["văn"] and grade_level < 6:
        subject_title = "tiếng việt"
    
    if subject_title == 'gdcd' and grade_level >= 10:
        subject_title = "ktpl"
    if subject_title == 'gdcd' and grade_level < 6:
        subject_title = "đạo đức"
    return subject_title

def generate_question_input_task3(config):
    """
    Generates random input parameters for Task 3 (Q&A).
    Returns grade level, subject, and topic suggestion.
    """
    grade_level = random.choice([1,2,3,4,5,6,7,8,9,10,11,12])
    subject_title = select_subject()
    
    subject_title = re_choice(subject_title, grade_level)
    
    # Use the shared function to get topic
    topic_suggestion = get_subject_topic(subject_title, grade_level)
    
    if subject_title == "khtn":
        subject_title = "KHTN(Khoa Học Tự Nhiên)"
    if subject_title == "ktpl":
        subject_title = "KTPL(Kinh Tế Pháp Luật)"
    
    return {
        "grade_level": grade_level,
        "subject": subject_title,
        "topic_suggestion": topic_suggestion
    }

def generate_grading_input_task7(config):
    """
    Generates random input for Task 7 (Essay Grading).
    Returns subject, grade level, topic, question type, student level, and number of questions.
    """
    subject_title = select_subject()
    if 'grade_levels' in config:
        grade_level = random.choice(config["grade_levels"])
    else:
        grade_level = random.choice([1,2,3,4,5,6,7,8,9,10,11,12])
    subject_title = re_choice(subject_title, grade_level)
    topic = get_subject_topic(subject_title, grade_level)
    
    # Determine question type
    only_choice = random.choice([0, 1, 2])
    if only_choice == 0:
        question_type = 'Trắc nghiệm'
    elif only_choice == 1:
        question_type = 'Tự luận'
    else:
        question_type = random.choice(config["question_types"])
    
    # Special handling for Văn (Literature)
    if subject_title == "văn":
        number_of_questions = random.randint(4, 7)
        question_type = 'Tự luận'  # Make Văn become tự luận
    elif question_type == 'Tự luận':
        number_of_questions = random.randint(1, 6)
    else:
        number_of_questions = random.randint(4, 30)

    
    if subject_title == "khtn":
        subject_title = "KHTN(Khoa Học Tự Nhiên)"
    if subject_title == "ktpl":
        subject_title = "KTPL(Kinh Tế Pháp Luật)"
    # Random float number between 1 and 10
    student_level = float(random.choice(samples))
    
    level_of_difficulty = random.choice(config["level_of_difficulty"])
    if level_of_difficulty == "Dễ":
        student_level = min(10, student_level + 2)
    elif level_of_difficulty == "Khó":
        student_level = max(0, student_level - 1)
    return {
        "subject": subject_title,
        "grade_level": grade_level,
        "topic": topic,
        "question_type": question_type,
        "student_level": student_level,
        "number_of_questions": number_of_questions,
        "level_of_difficulty": level_of_difficulty
    }

def generate_error_correction_input_task2(config):
    """
    Generates random input for Task 2 (Error Correction).
    Returns subject, grade level, topic, and student persona.
    """
    subject_title = select_subject()
    if 'grade_levels' in config:
        grade_level = random.choice(config["grade_levels"])
    else:
        grade_level = random.choice([1,2,3,4,5,6,7,8,9,10,11,12])
    subject_title = re_choice(subject_title, grade_level)
    topic = get_subject_topic(subject_title, grade_level)
    
    if subject_title == "khtn":
        subject_title = "KHTN(Khoa Học Tự Nhiên)"
    if subject_title == "ktpl":
        subject_title = "KTPL(Kinh Tế Pháp Luật)"

    
    return {
        "subject": subject_title,
        "grade_level": grade_level,
        "topic": topic
    }

def generate_grading_input_task8(config):
    """
    Generates random input for Task 8 (Lesson Planning).
    Returns subject, grade level, topic, question type, student level, and number of questions.
    """
    subject_title = select_subject()
    grade_level = random.choice(config["grade_levels"])
    topic = get_subject_topic(subject_title, grade_level)
    subject_title = re_choice(subject_title, grade_level)
    duration = random.choice([15,25,20,30,30,35,40,45,45,45,45,60,60])
    if subject_title == "khtn":
        subject_title = "KHTN(Khoa Học Tự Nhiên)"
    if subject_title == "ktpl":
        subject_title = "KTPL(Kinh Tế Pháp Luật)"
    return {
        "subject": subject_title,
        "grade_level": grade_level,
        "topic": topic,
        "duration": duration
    }

def generate_knowledge_question_input_task11(config):
    """
    Generates random input for Task 11 (Knowledge Question).
    Returns subject, grade level, topic, and question.
    """
    subject_title = select_subject()
    grade_level = random.choice(config["grade_levels"])
    topic = get_subject_topic(subject_title, grade_level)
    return {
        "subject": subject_title,
        "grade_level": grade_level,
        "topic": topic
    }

def generate_function_input_task12(all_functions):
    """
    Generates random input for Task 12 (Function Calling).
    Randomly selects 1 function from the provided list of functions.
    
    Args:
        all_functions: List of function dictionaries from education_functions.json
    
    Returns:
        dict: A randomly selected function dictionary
    """
    if not all_functions:
        raise ValueError("all_functions cannot be empty")
    
    return random.choice(all_functions)

if __name__ == "__main__":
    
    TASK7_CONFIG = {
    "total_samples": 2,
    "output_file": "output/task7_cham_diem_tu_luan_dataset.jsonl",
    
    # Danh sách cấp học
    "grade_levels": [1,2,3,4,5],

    
    # Question types
    "question_types": ["Viết đoạn văn", "Báo cáo dự án", "Điền đáp án vào chỗ trống", "Điền đúng / sai", "Trắc nghiệm + Tự luận",
    "Trắc nghiệm + Điền đáp án vào chỗ trống", "Trắc nghiệm + Điền đúng / sai", "Điền đúng / sai + Tự luận"],
    "level_of_difficulty": ["Dễ", "Trung bình", "Khó"],
    

}

    config = TASK7_CONFIG
    print(generate_grading_input_task7(config))
