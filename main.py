import cv2
import os
import numpy as np
import tensorflow as tf

# Load the TensorFlow model
MODEL_DIR = r"D:\haj\ssd_mobilenet_v2_320x320_coco17_tpu-8\saved_model"
model = tf.saved_model.load(str(MODEL_DIR))

# COCO dataset class names
COCO_CLASSES = [
    'person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus', 'train', 'truck', 'boat', 'traffic light',
    'fire hydrant', 'stop sign', 'parking meter', 'bench', 'bird', 'cat', 'dog', 'horse', 'sheep', 'cow',
    'elephant', 'bear', 'zebra', 'giraffe', 'backpack', 'umbrella', 'handbag', 'tie', 'suitcase', 'frisbee',
    'skis', 'snowboard', 'sports ball', 'kite', 'baseball bat', 'baseball glove', 'skateboard', 'surfboard',
    'tennis racket', 'bottle', 'wine glass', 'cup', 'fork', 'knife', 'spoon', 'bowl', 'banana', 'apple',
    'sandwich', 'orange', 'broccoli', 'carrot', 'hot dog', 'pizza', 'donut', 'cake', 'chair', 'couch',
    'potted plant', 'bed', 'dining table', 'toilet', 'TV', 'laptop', 'mouse', 'remote', 'keyboard', 'cell phone',
    'microwave', 'oven', 'toaster', 'sink', 'refrigerator', 'book', 'clock', 'vase', 'scissors', 'teddy bear',
    'hair drier', 'toothbrush'
]

def load_image_into_numpy_array(path):
    return np.array(cv2.imread(path))

def detect_objects(image_np):
    input_tensor = tf.convert_to_tensor(image_np)
    input_tensor = input_tensor[tf.newaxis, ...]
    detections = model(input_tensor)
    
    return detections

def process_image(filepath, operation, value, output_folder):
    image = cv2.imread(filepath)

    if operation == 'object_detection':
        image_np = load_image_into_numpy_array(filepath)
        detections = detect_objects(image_np)

        # Extract detection information
        detection_boxes = detections['detection_boxes'][0].numpy()
        detection_scores = detections['detection_scores'][0].numpy()
        detection_classes = detections['detection_classes'][0].numpy().astype(np.int32)

        height, width, _ = image.shape
        confidence_threshold = 0.5  # Set a confidence threshold

        for i in range(len(detection_scores)):
            if detection_scores[i] >= confidence_threshold:
                ymin, xmin, ymax, xmax = detection_boxes[i]
                (left, right, top, bottom) = (xmin * width, xmax * width, ymin * height, ymax * height)
                class_id = detection_classes[i]
                label = COCO_CLASSES[class_id - 1]  # Adjust for zero-indexing
                cv2.rectangle(image, (int(left), int(top)), (int(right), int(bottom)), (0, 255, 0), 2)
                cv2.putText(image, label, (int(left), int(top) - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

        processed_image = image

    elif operation == 'blur':
        ksize = int(value)
        if ksize % 2 == 0:  # Ensure the kernel size is odd
            ksize += 1
        processed_image = cv2.GaussianBlur(image, (ksize, ksize), 0)

    elif operation == 'contrast':
        alpha = float(value)
        beta = 1  # You can adjust this value if needed
        processed_image = cv2.convertScaleAbs(image, alpha=alpha, beta=beta)

    elif operation == 'sharpen':
        kernel_size = int(value)
        if kernel_size % 2 == 0:
            kernel_size += 1
        kernel = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]])  # Simple sharpen kernel
        processed_image = cv2.filter2D(image, -1, kernel)

    elif operation == 'invert':
        mask = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        _, mask = cv2.threshold(mask, 128, 255, cv2.THRESH_BINARY)
        processed_image = cv2.bitwise_not(mask)

    elif operation == 'detect_white':
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        processed_image = image.copy()
        cv2.drawContours(processed_image, contours, -1, (0, 0, 255), 2)

    elif operation == 'detect_color':
        # Convert selected color to BGR (OpenCV format)
        hex_color = value.lstrip('#')
        bgr_color = tuple(int(hex_color[i:i+2], 16) for i in (4, 2, 0))
        color_np = np.array([[bgr_color]], dtype=np.uint8)
        
        # Convert BGR to HSV for color detection
        hsv_color = cv2.cvtColor(color_np, cv2.COLOR_BGR2HSV)[0][0]
        lower_bound = np.array([hsv_color[0] - 10, 100, 100])
        upper_bound = np.array([hsv_color[0] + 10, 255, 255])
        
        # Convert image to HSV and create mask for the selected color
        hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv_image, lower_bound, upper_bound)
        
        # Find contours in the mask
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Draw contours on the processed image
        processed_image = image.copy()
        cv2.drawContours(processed_image, contours, -1, (0, 255, 0), 2)

    else:
        return None

    output_filename = f"{operation}_{os.path.basename(filepath)}"
    output_path = os.path.join(output_folder, output_filename)
    cv2.imwrite(output_path, processed_image)
    
    return output_filename
