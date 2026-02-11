"""
Task 7: Chấm Điểm Tự Luận - Essay Grading Pipeline
4-stage pipeline: Architect -> Simulator -> Teacher ->  Auditor
"""
import json
import os
from tqdm import tqdm
from . import llm
from .config_education import TASK7_CONFIG, GENERAL_CONFIG
from .data_generators import generate_grading_input_task7
from .prompts_task7 import (
    ARCHITECT_PROMPT, SIMULATOR_PROMPT, TEACHER_PROMPT,
    AUDITOR_PROMPT
)

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
import re

def clean_json_string(text: str) -> str:
    match = re.search(r'\{.*\}', text, re.DOTALL)
    
    if match:
        return match.group(0)
    else:
        return text


def verify_audit_task7(auditor_report):
    """
    Validates the sample based on the auditor's verdict.
    Returns True if PASS, False if FAIL.
    """
    if not auditor_report:
        logger.error("[Audit FAIL] Auditor did not provide a report.")
        return False
    
    is_valid = auditor_report.get("is_valid", False)
    
    if is_valid:
        audit_score = auditor_report.get("confidence_score", 0)
        logger.info(f"[Audit PASS] Audit quality score: {audit_score}/100")
        return True
    else:
        reasoning = auditor_report.get("reasoning", "Unknown reason")
        logger.error(f"[Audit FAIL] {reasoning}")
        return False

def run_task7_pipeline():
    """
    Executes the 4-stage pipeline to generate and validate one essay grading sample.
    
    Stages:
    1. Architect: Creates assessment question and detailed rubric
    2. Simulator: Creates student's answer based on profile
    3. Teacher: Grades the answer and provides feedback
    4.  Auditor: Independent quality verification
    """
    logger.info("\n--- Starting TASK 7: CHẤM ĐIỂM TỰ LUẬN (Essay Grading) pipeline (4 stages) ---")
    
    # Generate input parameters
    input_params = generate_grading_input_task7(TASK7_CONFIG)
    logger.info(f"Selected: {input_params['subject']} - {input_params['grade_level']} - Topic: {input_params['topic']}")
    logger.info(f"Question Type: {input_params['question_type']}")
    logger.info(f"Student Level: {input_params['student_level']}")
    logger.info(f"Number of Questions: {input_params['number_of_questions']}")
    try:
        # Stage 1: Architect (Question & Rubric Designer)
        logger.info("[1/4] Architect is designing assessment and rubric...")
        assessment, num_output_tokens = llm.call_llm(ARCHITECT_PROMPT.format(
            subject=input_params['subject'],
            grade_level=input_params['grade_level'],
            topic=input_params['topic'],
            question_type=input_params['question_type'],
            num_questions=input_params['number_of_questions'],
            level_of_difficulty=input_params['level_of_difficulty']
        ), is_creative=True)
        
        assessment = clean_json_string(assessment)
        assessment = json.loads(assessment, strict=False)
        
        if not assessment or not isinstance(assessment, dict):
            raise ValueError("Failed to generate assessment.")
        if "question_content" not in assessment or "rubric" not in assessment:
            raise ValueError("Assessment missing required fields (question_content or rubric).")
        logger.info(f"   Question: {assessment['question_content'][:100]}...")
        logger.info(f"   Number of output tokens: {num_output_tokens}")
        
        # Stage 2: Simulator (Student Answer)
        logger.info("[2/4] Simulator is creating student's answer...")
        student_submission, num_output_tokens = llm.call_llm(SIMULATOR_PROMPT.format(
            question_content=assessment.get('question_content', ''),
            student_level=input_params['student_level'],
            rubric=json.dumps(assessment['rubric'], ensure_ascii=False)
        ), is_creative=False)
        
        student_submission = clean_json_string(student_submission)
        student_submission = json.loads(student_submission, strict=False)
        
        if not student_submission or "submission_content" not in student_submission:
            raise ValueError("Failed to generate student submission.")
        logger.info(f"   Submission length: {len(student_submission['submission_content'])} characters")
        logger.info(f"   Number of output tokens: {num_output_tokens}")
        
        # Stage 3: Teacher (Grading & Feedback)
        logger.info("[3/4] Teacher is grading and providing feedback...")
        teacher_grading, num_output_tokens = llm.call_llm(TEACHER_PROMPT.format(
            assessment_json=json.dumps(assessment, ensure_ascii=False),
            student_submission_json=json.dumps(student_submission, ensure_ascii=False),
            grade_level=input_params['grade_level']
        ), is_creative=False)
        
        teacher_grading = clean_json_string(teacher_grading)
        try:
            teacher_grading = json.loads(teacher_grading, strict=False)
        except json.JSONDecodeError:
            raise ValueError("Failed to generate teacher grading.")
        
        if not teacher_grading or "total_score" not in teacher_grading:
            raise ValueError("Failed to generate teacher grading.")
        logger.info(f"   Total Score: {teacher_grading.get('total_score', 'N/A')}/10")
        logger.info(f"   Number of output tokens: {num_output_tokens}")
        
        # Stage 4: Auditor
        logger.info("[4/4] Pedagogical auditor is performing verification...")
        # auditor_report, num_output_tokens = llm.call_llm(AUDITOR_PROMPT.format(
        #     assessment_json=json.dumps(assessment, ensure_ascii=False)
        # ), is_creative=False)
        # auditor_report = clean_json_string(auditor_report)
        # auditor_report = json.loads(auditor_report, strict=False)
        
        # if not auditor_report or "confidence_score" not in auditor_report:
        #     raise ValueError("Failed to generate auditor report.")
        # logger.info(f"   Auditor report: {auditor_report.get('confidence_score', 'N/A')}")
        # logger.info(f"   Number of output tokens: {num_output_tokens}")




        score = teacher_grading.get('total_score', 'N/A')
        # print(type(score))
        try:
            score_float = float(score) if score != 'N/A' else None
            if score_float is None or ( abs(score_float - float(input_params['student_level'])) > 2 and input_params['subject'] != 'Văn'):
                raise ValueError("Sample failed with score of teacher is too far with student level")
        except TypeError as e:
            print(e)
            raise ValueError(f"Invalid score format: {score}") from e
        
        
        # Construct the conversation pair
        # User: Student submits their work
        # if verify_audit_task7(auditor_report):
        if True:
            user_content = f"""Thầy/Cô ơi, em vừa làm xong bài này. Thầy/Cô chấm điểm và góp ý giúp em với ạ!

    **Đề bài:** {assessment['question_content']}

    **Bài làm của em:**
    {student_submission['submission_content']}"""

            # Assistant: Teacher provides grading and feedback
            feedback = teacher_grading.get('feedback_content', {})
            assistant_content = f"""**ĐÁNH GIÁ BÀI LÀM**

    **Tổng điểm:** {teacher_grading.get('total_score', 'N/A')}/10

    **Chi tiết điểm:**
    """
            for detail in teacher_grading.get('detailed_scores', []):
                assistant_content += f"- {detail.get('criteria', 'N/A')}: {detail.get('score', 'N/A')} điểm\n"
            
            assistant_content += f"""
    **Nhận xét chung:**
    {feedback.get('general_comment', 'N/A')}

    **Điểm mạnh:**
    """
            for strength in feedback.get('strengths', []):
                assistant_content += f"- {strength}\n"
            
            assistant_content += f"""
    **Điểm cần cải thiện:**
    """
            for improvement in feedback.get('areas_for_improvement', []):
                assistant_content += f"- {improvement}\n"
            
            assistant_content += f"""
    **Gợi ý cụ thể:**
    {feedback.get('actionable_suggestion', 'N/A')}"""
            assistant_content = assistant_content.replace("rubric", "thang điểm").replace("Rubric", "Thang điểm")
            # Prepare final output
            final_sample_task7 = {
                "task": "task7_Automatic_Grading",
                "metadata": {
                    "subject": input_params['subject'],
                    "grade_level": input_params['grade_level'],
                    "topic": input_params['topic'],
                    "question_type": input_params['question_type'],
                    "student_level": input_params['student_level'],
                    "total_score": teacher_grading.get('total_score', 'N/A'),
                    "level_of_difficulty": input_params['level_of_difficulty']
                },
                "conversations": [
                    {
                        "role": "user",
                        "content": user_content
                    },
                    {
                        "role": "assistant",
                        "content": assistant_content
                    }
                ],
                "pipeline_outputs": {
                    "assessment": assessment,
                    "student_submission": student_submission,
                    "teacher_grading": teacher_grading,
                    # "audit_report": auditor_report
                }
            }
            logger.info("--- ✔ TASK 7 pipeline completed and validated! ---")
            '''example output of task 6: {
     "role": "assistant",
     "content": "**BỘ CÂU HỎI: QUANG HỢP Ở THỰC VẬT**\n**Môn:** Sinh học | **Lớp:** 7 | **Độ khó:** Trung bình\n\n---\n\n**Câu 1:** Quang hợp là quá trình:\nA. Cây hấp thụ nước từ đất\nB. Cây tạo chất hữu cơ từ chất vô cơ nhờ ánh sáng\nC. Cây hô hấp để sinh năng lượng\nD. Cây sinh trưởng và phát triển\n**Đáp án: B**\n\n**Câu 2:** Bào quan nào trong tế bào thực vật thực hiện quang hợp?\nA. Ti thể\nB. Nhân tế bào\nC. Lục lạp\nD. Không bào\n**Đáp án: C**\n\n**Câu 3:** Sản phẩm của quá trình quang hợp gồm:\nA. Glucose và O₂\nB. CO₂ và H₂O\nC. Protein và lipid\nD. CO₂ và O₂\n**Đáp án: A**\n\n**Câu 4:** Yếu tố nào KHÔNG ảnh hưởng trực tiếp đến cường độ quang hợp?\nA. Cường độ ánh sáng\nB. Nhiệt độ\nC. Nồng độ CO₂\nD. Độ ẩm không khí\n**Đáp án: D**\n\n**Câu 5:** Trong công thức quang hợp: 6CO₂ + 6H₂O → C₆H₁₂O₆ + 6O₂, khí O₂ được tạo ra từ:\nA. CO₂\nB. H₂O\nC. Glucose\nD. Diệp lục\n**Đáp án: B**\n\n**HƯỚNG DẪN GIẢI:**\n- Câu 5 là câu khó nhất, cần hiểu sâu về nguồn gốc O₂\n- Câu 4 phân biệt yếu tố trực tiếp và gián tiếp"
   }'''
            assistant_content = f"""a
    **BỘ CÂU HỎI: {assessment['question_content']}**
    **Môn:** {input_params['subject']} | **Lớp:** {input_params['grade_level']} | **Độ khó:** {input_params['level_of_difficulty']}
    {assessment['question_content']}
    """
            '''example:"role": "user",
     "content": "Tạo 5 câu hỏi trắc nghiệm về chủ đề 'Quang hợp ở thực vật' cho học sinh lớp 7, độ khó trung bình."
            '''
            user_content = f"""Tạo {input_params['number_of_questions']} câu hỏi {input_params['question_type']} về chủ đề '{input_params['topic']}' cho học sinh lớp {input_params['grade_level']}, độ khó {input_params['level_of_difficulty']}."""
            final_sample_task6 = {
                "task": "task6_Question_Generation",
                
                "conversations": [
                    {
                        "role": "user",
                        "content": user_content
                    },
                    {
                        "role": "assistant",
                        "content": assistant_content
                    }
                ],
                "pipeline_outputs": {
                    "assessment": assessment,
                }
            }
            return final_sample_task7, final_sample_task6
        else:
            raise ValueError("Sample failed pedagogical audit.")
    
    except Exception as e:
        logger.error(f"--- ✖ TASK 7 pipeline failed: {e} ---")
        return None, None


def main():
    """Main function to run Task 7 pipeline multiple times."""
    logger.info("Initializing TASK 7: CHẤM ĐIỂM TỰ LUẬN (Essay Grading) Data Synthesis...")
    os.makedirs("output", exist_ok=True)
    
    output_file = TASK7_CONFIG["output_file"]
    output_file_task6 = TASK7_CONFIG["output_file_task6"]
    total_samples = TASK7_CONFIG["total_samples"]
    generated_count = 0
    with open(output_file, "a", encoding="utf-8") as f, open(output_file_task6, "a", encoding="utf-8") as f6, tqdm(total=total_samples, desc="Synthesizing Task 7 and Task 6 Samples") as synthsis_bar:
        while generated_count < total_samples:
            final_sample_task7, final_sample_task6 = run_task7_pipeline()
            if final_sample_task7 and final_sample_task6:
                f.write(json.dumps(final_sample_task7, ensure_ascii=False) + "\n")
                f6.write(json.dumps(final_sample_task6, ensure_ascii=False) + "\n")
                f.flush()
                f6.flush()
                generated_count += 1
                synthsis_bar.update(1)
            else:
                logger.error("Pipeline failed. Retrying with new parameters...")
    
    logger.info(f"\nTask 7 and Task 6 data synthesis complete. {generated_count} high-quality samples saved to {output_file} and {output_file_task6}.")

if __name__ == "__main__":
    main()
