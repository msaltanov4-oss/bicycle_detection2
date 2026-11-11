from ultralytics import YOLO

model = YOLO('yolov8n.pt')   # автоматически загрузит веса

def detect_bicycles(image_path):
    results = model(image_path)
    # фильтруем только класс 'bicycle' (индекс 1 в COCO)
    detections = []
    for box in results[0].boxes:
        cls = int(box.cls[0])
        if cls == 1:   # велосипед
            detections.append({
                'bbox': box.xyxy[0].tolist(),   # [x1,y1,x2,y2]
                'confidence': float(box.conf[0])
            })
    # сохраняем изображение с рамками
    img_with_boxes = results[0].plot()
    return img_with_boxes, len(detections)