import os
import cv2
from flask import Flask, render_template, request, jsonify
from ultralytics import YOLO  # Sử dụng YOLOv8
from deepface import DeepFace
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  

# Load YOLOv8 model
yolo_model = YOLO("yolov8n.pt")  # Tự động tải weights nếu chưa có

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
@app.route('/upload', methods=['POST'])
def upload_image():
    try:
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
            output_path = yolo_detect(img_path)
            return jsonify({"result_path": output_path})
        
        elif task == "face_analysis":
            analysis = analyze_face(img_path)
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
    return output_path

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

if __name__ == '__main__':
    app.run(port=3000, debug=True)  