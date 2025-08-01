import os
import json
import logging
import datetime
import asyncio
import re # For regex to extract message_id and channel_name
from ultralytics import YOLO
from hashlib import md5 # For generating unique hash for processed images

# --- Configuration ---
RAW_IMAGES_DIR = 'data/raw/telegram_images'
PROCESSED_DATA_DIR = 'data/processed'
YOLO_DETECTIONS_FILE = os.path.join(PROCESSED_DATA_DIR, 'yolo_detections.jsonl')
PROCESSED_IMAGES_LOG = os.path.join(PROCESSED_DATA_DIR, 'processed_images.log') # To track processed images for idempotency

# Ensure processed data directory exists
os.makedirs(PROCESSED_DATA_DIR, exist_ok=True)

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.FileHandler('data/yolo_detector.log'),
                        logging.StreamHandler()
                    ])
logger = logging.getLogger(__name__)

def load_yolo_model():
    """Loads a pre-trained YOLOv8n model."""
    try:
        # 'yolov8n.pt' is the nano version, good for quick testing and balanced performance
        # It will download the weights the first time it's run.
        model = YOLO('yolov8n.pt')
        logger.info("YOLOv8n model loaded successfully.")
        return model
    except Exception as e:
        logger.error(f"Error loading YOLOv8 model: {e}", exc_info=True)
        raise

def get_image_hash(image_path):
    """Generates an MD5 hash of an image file for unique identification."""
    hasher = md5()
    try:
        with open(image_path, 'rb') as f:
            buf = f.read()
            hasher.update(buf)
        return hasher.hexdigest()
    except Exception as e:
        logger.warning(f"Could not hash image {image_path}: {e}")
        return None

def get_processed_image_hashes():
    """Reads the set of already processed image hashes from the log file."""
    processed_hashes = set()
    if os.path.exists(PROCESSED_IMAGES_LOG):
        try:
            with open(PROCESSED_IMAGES_LOG, 'r') as f:
                for line in f:
                    processed_hashes.add(line.strip())
        except Exception as e:
            logger.error(f"Error reading processed images log: {e}", exc_info=True)
    return processed_hashes

def log_processed_image_hash(image_hash):
    """Appends a new image hash to the processed images log file."""
    try:
        with open(PROCESSED_IMAGES_LOG, 'a') as f:
            f.write(f"{image_hash}\n")
    except Exception as e:
        logger.error(f"Error writing to processed images log: {e}", exc_info=True)

def extract_metadata_from_path(image_path):
    """
    Extracts scraped_date, channel_name, and message_id from the image file path.
    Assumes path format: data/raw/telegram_images/YYYY-MM-DD/channel_name/filename.jpg
    Filename format: channel_name_message_id_photo.jpg or channel_name_message_id_doc.ext
    """
    parts = image_path.split(os.sep)
    if len(parts) < 5 or parts[-4] != 'telegram_images': # e.g., week7/data/raw/telegram_images/YYYY-MM-DD/channel_name/filename.jpg
        logger.warning(f"Unexpected image path format: {image_path}")
        return None, None, None

    scraped_date_str = parts[-3] # YYYY-MM-DD
    channel_name = parts[-2]
    filename = parts[-1]

    # Extract message_id from filename (e.g., "CheMed123_12345_photo.jpg")
 # Updated regex to handle message_id followed directly by file extension
    match = re.match(r'.*_(\d+)\.(jpg|jpeg|png|gif|bmp)$', filename, re.IGNORECASE)
    message_id = int(match.group(1)) if match else None

    if not message_id:
        logger.warning(f"Could not extract message_id from filename: {filename}")

    return scraped_date_str, channel_name, message_id

async def run_yolo_detection():
    """
    Scans for new images, runs YOLOv8 detection, and logs results.
    """
    model = load_yolo_model()
    if not model:
        return

    processed_hashes = get_processed_image_hashes()
    new_detections_count = 0
    images_scanned_count = 0

    logger.info(f"Starting YOLO object detection. Scanning directory: {RAW_IMAGES_DIR}")

    # Iterate through the partitioned image directory structure
    for date_dir in os.listdir(RAW_IMAGES_DIR):
        full_date_dir_path = os.path.join(RAW_IMAGES_DIR, date_dir)
        if not os.path.isdir(full_date_dir_path):
            continue

        for channel_dir in os.listdir(full_date_dir_path):
            full_channel_dir_path = os.path.join(full_date_dir_path, channel_dir)
            if not os.path.isdir(full_channel_dir_path):
                continue

            for filename in os.listdir(full_channel_dir_path):
                if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
                    image_path = os.path.join(full_channel_dir_path, filename)
                    images_scanned_count += 1

                    image_hash = get_image_hash(image_path)
                    if image_hash in processed_hashes:
                        # logger.debug(f"Skipping already processed image: {image_path}")
                        continue

                    # Extract metadata from path
                    scraped_date_str, channel_name, message_id = extract_metadata_from_path(image_path)
                    if not message_id:
                        logger.warning(f"Skipping image {image_path} due to missing message_id.")
                        log_processed_image_hash(image_hash) # Log it as processed to avoid re-attempting
                        continue

                    try:
                        # Run inference on the image
                        results = model.predict(source=image_path, conf=0.25, iou=0.7, verbose=False) # conf: confidence threshold, iou: IoU threshold for NMS

                        # Process results
                        for r in results:
                            boxes = r.boxes # Bounding boxes, classes, scores
                            names = r.names # Class names mapping

                            for box in boxes:
                                class_id = int(box.cls[0])
                                confidence = float(box.conf[0])
                                object_class = names[class_id]

                                detection_record = {
                                    'message_id': message_id,
                                    'image_path': image_path, # Keep original path for traceability
                                    'scraped_date': scraped_date_str,
                                    'channel_name': channel_name,
                                    'detected_object_class': object_class,
                                    'confidence_score': confidence,
                                    'timestamp': datetime.datetime.now().isoformat()
                                }

                                # Append detection record to JSONL file
                                with open(YOLO_DETECTIONS_FILE, 'a', encoding='utf-8') as f:
                                    json.dump(detection_record, f, ensure_ascii=False)
                                    f.write('\n')
                                new_detections_count += 1
                        
                        # Log the image hash only after all its detections are processed
                        log_processed_image_hash(image_hash)

                    except Exception as e:
                        logger.error(f"Error processing image {image_path}: {e}", exc_info=True)
                        # Log the hash even on error to avoid re-attempting problematic images
                        log_processed_image_hash(image_hash)

    logger.info(f"YOLO detection complete. Scanned {images_scanned_count} images. Found {new_detections_count} new detections.")

if __name__ == '__main__':
    # YOLO model downloads weights on first run. This might take a moment.
    # Ensure you have internet access for the first run.
    asyncio.run(run_yolo_detection())