import time
from ultralytics import YOLO
from multiprocessing import freeze_support
import os
from pathlib import Path
import torch
import gc


def train():
    if torch.cuda.is_available():
        # Get the default GPU device
        device = torch.device('cuda')

        # Get total memory
        total_memory = torch.cuda.get_device_properties(device).total_memory

        # Get allocated memory
        allocated_memory = torch.cuda.memory_allocated(device)

        # Get cached memory (memory reserved by PyTorch)
        reserved_memory = torch.cuda.memory_reserved(device)

        # Get free memory
        free_memory = total_memory - allocated_memory

        print(f"Total GPU memory: {total_memory / 1e9:.2f} GB")
        print(f"Allocated GPU memory: {allocated_memory / 1e9:.2f} GB")
        print(f"Free GPU memory: {free_memory / 1e9:.2f} GB")
        print(f"Reserved GPU memory: {reserved_memory / 1e9:.2f} GB")

        print("GPU is not available")

    gc.collect()

    torch.cuda.empty_cache()
    os.environ['PYTORCH_CUDA_ALLOC_CONF'] = 'expandable_segments:True'
    freeze_support()
    # Load the YOLOv8 model (you can choose different versions like yolov8n, yolov8s, yolov8m, yolov8l)
    model = YOLO('../runs/detect/yolov8_custom/weights/last.pt')
    # Train the model
    model.train(data='data.yaml', epochs=300, imgsz=128, batch=128, name='yolov8_custom', cache=False, resume=True)


def predict():
    model = YOLO('../runs/detect/yolov8_custom9/weights/best.pt')
    image_folder = 'bot data/opts/'
    # Make predictions
    a = time.time()
    results = model.predict(image_folder)
    characters = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    combinations = [a + b for a in characters for b in characters]
    combo_to_id = {combo: idx for idx, combo in enumerate(combinations)}
    combo_keys = list(combo_to_id.keys())
    # Display the results
    for result in results:
        boxes = result.boxes  # Bounding boxes
        print(f'boxes {len(boxes)} ')
        if len(boxes) > 0:
            box = boxes[0]
            id_class = combo_keys[int(box.cls[0])]
            confidence = box.conf
            if confidence > 0.5:
                print(f"Class: {id_class}, Confidence: {box.conf}, time: {time.time() - a}")


def convert_onnx():

    # Load the YOLOv8 model
    model = YOLO('../runs/detect/yolov8_custom/weights/best.pt')

    # Export the model to ONNX format
    model.export(format="onnx", imgsz=[128, 128], optimize=True)  # creates 'yolov8n.onnx'


def onnx_predict():
    characters = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    combinations = [a + b for a in characters for b in characters]
    combo_to_id = {combo: idx for idx, combo in enumerate(combinations)}
    combo_keys = list(combo_to_id.keys())
    image_folder = 'bot data/opts/'

    # Load the exported ONNX model
    onnx_model = YOLO("../runs/detect/yolov8_custom9/weights/best.onnx")
    a = time.time()
    # Get list of image files in the directory
    image_files = [file for file in Path(image_folder).glob('*') if file.suffix.lower() == '.png']
    for img_path in image_files:
        # Run inference
        try:
            results = onnx_model.predict(img_path, imgsz=(128, 128))

            # Extract boxes, class IDs, and confidence scores from results
            if len(results) > 0:
                boxes = results[0].boxes  # Access the first result's boxes

                if boxes is not None and len(boxes) > 0:
                    class_ids = boxes.cls.cpu().numpy()  # Get class IDs
                    confidences = boxes.conf.cpu().numpy()  # Get confidence scores

                    # Print class IDs and their corresponding confidence scores
                    for i, class_id in enumerate(class_ids):
                        first_class_id = combo_keys[int(class_id)]
                        confidence = confidences[i]
                        if confidence > 0.5:
                            print(f"Image: {img_path.name}, Class ID: {first_class_id}, Confidence: {confidence:.2f}")
                else:
                    print(f"No detections for image: {img_path.name}")
            else:
                print(f"No results returned for image: {img_path.name}")

        except Exception as e:
            print(f"Error during inference on image {img_path.name}: {e}")


if __name__ == "__main__":
    convert_onnx()