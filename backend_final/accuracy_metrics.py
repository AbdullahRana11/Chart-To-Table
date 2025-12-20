import io
import logging
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from PIL import Image
from skimage.metrics import structural_similarity as ssim

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def normalize_image(img, size=(512, 512)):
    """Convert image to grayscale and resize for comparison"""
    return np.array(img.convert("L").resize(size, Image.Resampling.BILINEAR))

def calculate_ssim(img1, img2):
    """Calculate Structural Similarity Index between two images"""
    # Ensure images are same size and grayscale
    i1 = normalize_image(img1)
    i2 = normalize_image(img2)
    
    # Calculate SSIM
    score, _ = ssim(i1, i2, full=True, data_range=255)
    return score

def render_chart(df, chart_type="bar chart", title=None, size=(800, 600)):
    """
    Render a dataframe back into a chart image for comparison.
    """
    try:
        plt.figure(figsize=(size[0]/100, size[1]/100), dpi=100)
        
        # Clean data
        # Assume first column is label, rest are values
        if df.empty:
            return None
            
        label_col = df.columns[0]
        value_cols = df.columns[1:]
        
        # Convert label column to string
        df[label_col] = df[label_col].astype(str)
        
        # Ensure value columns are numeric
        for col in value_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

        chart_type_lower = str(chart_type).lower()

        if "pie" in chart_type_lower:
            # Pie Chart
            # Use the first value column
            if len(value_cols) > 0:
                val_col = value_cols[0]
                plt.pie(df[val_col], labels=df[label_col], autopct='%1.1f%%')
        
        elif "line" in chart_type_lower:
            # Line Chart
            for col in value_cols:
                plt.plot(df[label_col], df[col], marker='o', label=col)
            if len(value_cols) > 1:
                plt.legend()
            plt.xticks(rotation=45)
            plt.grid(True)
            
        else:
            # Default to Bar Chart
            x = np.arange(len(df))
            width = 0.8 / len(value_cols) if len(value_cols) > 0 else 0.8
            
            for i, col in enumerate(value_cols):
                plt.bar(x + i*width, df[col], width, label=col)
                
            plt.xticks(x + width * (len(value_cols) - 1) / 2, df[label_col], rotation=45)
            if len(value_cols) > 1:
                plt.legend()
            plt.grid(axis='y')

        if title:
            plt.title(title)
            
        plt.tight_layout()
        
        # Save to buffer
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        plt.close()
        buf.seek(0)
        
        return Image.open(buf).convert("RGB")
        
    except Exception as e:
        logger.error(f"Error rendering chart: {e}")
        plt.close()
        return None

def evaluate_extraction(original_image_path, extracted_df, chart_type="bar chart"):
    """
    Evaluate the accuracy of extraction by re-rendering and comparing.
    Returns a dict with metrics.
    """
    try:
        original_img = Image.open(original_image_path).convert("RGB")
        
        # Render extracted data
        rendered_img = render_chart(extracted_df, chart_type=chart_type, size=original_img.size)
        
        if rendered_img is None:
            return {"error": "Failed to render comparison chart"}
            
        # Calculate metrics
        ssim_score = calculate_ssim(original_img, rendered_img)
        
        # Normalize score to 0-100%
        accuracy = max(0, min(100, ssim_score * 100))
        
        return {
            "ssim": float(ssim_score),
            "accuracy_score": float(accuracy),
            "rendered_image": rendered_img
        }
        
    except Exception as e:
        logger.error(f"Evaluation failed: {e}")
        return {"error": str(e)}
