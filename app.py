import os
import cv2
from flask import Flask, render_template, request, jsonify
from ultralytics import YOLO  # Sử dụng YOLOv8
from deepface import DeepFace
from flask_cors import CORS
import json
from datetime import datetime, time


app = Flask(__name__)
CORS(app)  

# Load YOLOv8 model
yolo_model = YOLO("yolov8n.pt")  # Tự động tải weights nếu chưa có

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_image():
    try:
        today = datetime.today().date()
        start_time = datetime.now().time()

        print("\n===== New Request =====")
        print("Files received:", request.files)
        print("Form data:", request.form)

        if 'file' not in request.files:
            return jsonify({"error": "No file uploaded"}), 400
        
        file = request.files['file']
        task = request.form.get('task')
        
        # Tạo thư mục nếu chưa tồn tại
        os.makedirs("static/uploads", exist_ok=True)
        os.makedirs("static/results", exist_ok=True)
        
        img_path = f"static/uploads/{file.filename}"
        file.save(img_path)

        
        if task == "object_detection":
            # Lấy confidence từ kết quả YOLO
            result,output_path = yolo_detect(img_path)
            confidences = [box.conf.item() for box in result[0].boxes]
            avg_confidence = sum(confidences)/len(confidences) if confidences else 0
            end_time = datetime.now().time()
        
            dt1 = datetime.combine(today, start_time)
            dt2 = datetime.combine(today, end_time)
            processing_time = dt2 - dt1
            save_simple_log(
                task_type="object_detection",
                data={
                    "objects": [result[0].names[int(cls)] for cls in result[0].boxes.cls.unique()],
                    "avg_confidence": avg_confidence,
                    "processing_time": processing_time.total_seconds()
                }
            )
            return jsonify({"result_path": output_path})
        
        
        elif task == "face_analysis":
            analysis = analyze_face(img_path)
            end_time = datetime.now().time()
        
            dt1 = datetime.combine(today, start_time)
            dt2 = datetime.combine(today, end_time)
            processing_time = dt2 - dt1
            save_simple_log(
                task_type="face_analysis",
                data={
                    "age": analysis["age"],
                    "gender": analysis["gender"],
                    "emotion": analysis["emotion"],
                    "processing_time": processing_time.total_seconds()
                }
            )
            return jsonify({
                "age": analysis["age"],
                "gender": analysis["gender"],
                "emotion": analysis["emotion"]
            })
        
        return jsonify({"error": "Invalid task"}), 400
    
    except Exception as e:
        
        return jsonify({"error": str(e)}), 500

def yolo_detect(img_path):
    # Dự đoán và lưu kết quả
    results = yolo_model.predict(img_path)
    output_path = "static/results/yolo_output.jpg"
    results[0].save(output_path)
    return results,output_path

def analyze_face(img_path):
    results = DeepFace.analyze(
        img_path=img_path, 
        actions=['age', 'gender', 'emotion'],
        detector_backend='opencv',
        enforce_detection=False
    )
    
    # Lấy kết quả đầu tiên (nếu có nhiều khuôn mặt)
    analysis = results[0] if isinstance(results, list) else results
    
    # Trích xuất giới tính có xác suất cao nhất
    gender = max(analysis['gender'], key=analysis['gender'].get)
    
    return {
        "age": analysis["age"],
        "gender": gender,  # Trả về string ("Man" hoặc "Woman")
        "emotion": analysis["dominant_emotion"]
    }
def save_simple_log(task_type, data):
    log_dir = "simple_logs"
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "simple_logs.json")
    
    # Đọc log cũ hoặc tạo mới
    logs = []
    if os.path.exists(log_file):
        with open(log_file, "r") as f:
            try:
                logs = json.load(f)
            except json.JSONDecodeError:
                # Nếu file không hợp lệ, bạn có thể ghi đè bằng một danh sách rỗng
                logs = []
    
    # Thêm log mới
    logs.append({
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "task": task_type,
        "data": data  # Dữ liệu đơn giản
    })
    
    # Lưu file
    with open(log_file, "w") as f:
        json.dump(logs, f, indent=2)

if __name__ == '__main__':
    app.run(port=3000, debug=True)  