import os
from dotenv import load_dotenv

load_dotenv()

TOTAL_SAMPLES = 50
NUM_WORKERS = 20
LLM_PROVIDER = "openai"
LLM_MODELS = {
    "openai": "gemini-2.5-flash"
}

TASK8_CONFIG = {
    "total_samples": 2000,
    "output_file": "output/task8_teaching_material_generation2.jsonl",
    
    # Danh sách các chủ đề mẫu cho từng môn học
    "sample_topics": {
        "Toán": ["Phương trình bậc nhất", "Hình học không gian", "Đạo hàm", "Phân số"],
        "Văn": ["Thơ Tố Hữu", "Truyện Kiều", "Văn bản thuyết minh", "Nghị luận xã hội"],
        "Vật lí": ["Động học", "Nhiệt học", "Điện học", "Quang học"],
        "Hóa": ["Bảng tuần hoàn", "Phản ứng oxi hóa khử", "Hóa học hữu cơ", "Dung dịch"],
        "Sinh": ["Di truyền học", "Sinh thái học", "Cấu tạo tế bào", "Tiến hóa"],
        "Sử": ["Cách mạng tháng Tám", "Chiến tranh Việt Nam", "Văn minh cổ đại", "Lịch sử thế giới"],
        "Địa": ["Khí hậu Việt Nam", "Địa hình", "Dân cư và xã hội", "Tài nguyên thiên nhiên"],
        "Tiếng Anh": ["Present tenses", "Past tenses", "Vocabulary building", "Reading comprehension"]
    },
    
    # Cấp độ lớp
    "grade_levels": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
    
    # Thời lượng bài giảng (phút)
    "durations": [30, 45, 60, 90],
}

GENERAL_CONFIG = {
    "retry_limit": 3,  # Số lần thử lại khi pipeline thất bại
    "progress_checkpoint_interval": 10,
     "grade_levels": [1,2,3,4,5,6,7,8,9,10,11,12],
     "subjects": {"toán": 2, "vật lí": 2, "hóa": 2, "sinh": 2, "sử": 5, "địa": 4, "gdcd": 3, "công nghệ": 1, "tin học": 1,
     "văn": 4, "tiếng anh": 2},
}
