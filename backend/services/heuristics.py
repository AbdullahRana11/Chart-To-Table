import cv2
import pytesseract
import numpy as np
import re
import logging
from typing import Dict, Any, List, Optional
from PIL import Image

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure Tesseract path if necessary (Windows)
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def preprocess_image(image_path: str) -> np.ndarray:
    """
    Reads an image and applies preprocessing for OCR.
    """
    # Read image using cv2
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Could not read image at {image_path}")
    
    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Apply thresholding to binarize
    # Otsu's thresholding is generally good for text on charts
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    return thresh

def parse_y_axis_values(text_blocks: List[Dict[str, Any]], img_width: int, img_height: int) -> tuple[float, float, List[float]]:
    """
    Identifies numeric labels on the Y-axis (left side) and calculates range.
    """
    y_values = []
    
    # Define "left side" as the first 20% of the image width
    left_margin_threshold = img_width * 0.2
    
    for block in text_blocks:
        x, y, w, h = block['left'], block['top'], block['width'], block['height']
        text = block['text'].strip()
        
        # Check if block is roughly on the left
        if x < left_margin_threshold:
            # Clean text to finding numbers
            # Match number patterns: 10, 10.5, 1,000, $50
            clean_text = re.sub(r'[^\d.-]', '', text) 
            try:
                if clean_text:
                    val = float(clean_text)
                    y_values.append(val)
            except ValueError:
                continue
                
    if not y_values:
        return 0.0, 0.0, []
        
    return min(y_values), max(y_values), y_values

def identify_title(text_blocks: List[Dict[str, Any]], img_width: int, img_height: int) -> str:
    """
    Identifies the chart title based on position (top) and font size (height).
    """
    # Filter blocks in the top 20% of the image
    top_margin_threshold = img_height * 0.2
    candidates = []
    
    for block in text_blocks:
        y, h = block['top'], block['height']
        text = block['text'].strip()
        
        if y < top_margin_threshold and len(text) > 3: # Ignore tiny random headers
             candidates.append(block)
             
    if not candidates:
        return "Untitled Chart"
        
    # Heuristic: Title is often the largest text (tallest bounding box)
    candidates.sort(key=lambda b: b['height'], reverse=True)
    
    # Take the largest, or combine top few if they are close?
    # For now, take the largest valid text block
    if candidates:
        return candidates[0]['text'].strip()
        
    return "Untitled Chart"

def detect_units(text_blocks: List[Dict[str, Any]]) -> str:
    """
    Searches for units enclosed in parentheses, e.g., (kg), (%), ($).
    """
    unit_pattern = re.compile(r'\(([%$a-zA-Z0-9]+)\)')
    
    for block in text_blocks:
        text = block['text'].strip()
        match = unit_pattern.search(text)
        if match:
            return match.group(1) # Return the content inside parens
            
    return ""

def extract_metadata(image_path: str) -> Dict[str, Any]:
    """
    Main entry point to extract metadata from a chart image.
    """
    logger.info(f"Extracting metadata from {image_path}")
    
    try:
        # Preprocess
        processed_img = preprocess_image(image_path)
        
        # Run Tesseract to get data with bounding boxes
        # output_type=DICT returns: {'text': [], 'left': [], 'top': [], 'width': [], 'height': [], 'conf': []}
        data = pytesseract.image_to_data(processed_img, output_type=pytesseract.Output.DICT)
        
        img_h, img_w = processed_img.shape
        
        # Convert to list of dicts for easier handling
        text_blocks = []
        n_boxes = len(data['text'])
        for i in range(n_boxes):
            if int(data['conf'][i]) > 40: # Filter low confidence garbage
                text_blocks.append({
                    'text': data['text'][i],
                    'left': data['left'][i],
                    'top': data['top'][i],
                    'width': data['width'][i],
                    'height': data['height'][i],
                    'conf': data['conf'][i]
                })
        
        # Run Heuristics
        title = identify_title(text_blocks, img_w, img_h)
        units = detect_units(text_blocks)
        y_min, y_max, y_vals = parse_y_axis_values(text_blocks, img_w, img_h)
        
        return {
            'title': title,
            'y_min': y_min,
            'y_max': y_max,
            'units': units,
            'y_axis_values': y_vals # Debugging/Context
        }
        
    except Exception as e:
        logger.error(f"Heuristics extraction failed: {e}")
        # Return safe defaults
        return {
            'title': "Error extracting title",
            'y_min': 0.0,
            'y_max': 0.0,
            'units': "",
            'error': str(e)
        }
