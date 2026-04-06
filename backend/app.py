import os
import logging
import tempfile
from flask import Flask, request, jsonify
from flask_cors import CORS
from services.extractor import get_chart_data

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'bmp', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy", "service": "DePlot Chart Backend"})

@app.route('/api/convert', methods=['POST'])
def process_chart():
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
        
    if not allowed_file(file.filename):
        return jsonify({"error": "Invalid file type"}), 400

    try:
        # Save temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp:
            file.save(tmp.name)
            tmp_path = tmp.name
            
        logger.info(f"Processing (DePlot): {tmp_path}")
        
        # Run DePlot Extraction
        result = get_chart_data(tmp_path)
        
        # Map DePlot output to Frontend format
        response = {
            "success": True,
            "data": result['data'],
            "columns": result['header'],
            "chart_type": "detected", 
            "method": "Google DePlot (SOTA)",
            "accuracy": {
                "score": result.get('confidence', 0.95) 
            },
            "metadata": {
                "title": "", 
                "full_text": result.get('raw_text', '')
            }
        }
        
        logger.info(f"Success. Rows: {len(result['data'])}")
        return jsonify(response)

    except Exception as e:
        logger.error(f"Processing failed: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500
        
    finally:
        if 'tmp_path' in locals() and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except:
                pass

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
