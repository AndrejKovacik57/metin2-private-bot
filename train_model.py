# from ultralytics import YOLO


# # Load the YOLOv8 model (you can choose different versions like yolov8n, yolov8s, yolov8m, yolov8l)
# model = YOLO('yolov8m.pt')
# # Train the model
# model.train(data='data.yaml', epochs=20, imgsz=100, batch=32, name='yolov8_custom')
import torch

# Check if CUDA is available
if torch.cuda.is_available():
    print(f"CUDA is available. Using GPU: {torch.cuda.get_device_name(0)}")
else:
    print("CUDA is not available. Please check your setup.")