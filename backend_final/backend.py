import os
import io
import logging
import tempfile
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename
from PIL import Image
import pandas as pd

# Import core logic
try:
    import LLM_Final as extractor
    import accuracy_metrics as metrics
except ImportError:
    # Fallback for when running from parent directory or different context
    from . import LLM_Final as extractor
    from . import accuracy_metrics as metrics

# Configuration
app = Flask(__name__)

# CORS - Allow requests from frontend deployments
CORS(app, origins=[
    "https://*.pages.dev",  # Cloudflare Pages (wildcard for any subdomain)
    "https://*.up.railway.app",  # Railway frontends
    "http://localhost:5173",  # Local development
    "http://localhost:3000"   # Alternative local port
])

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database Configuration
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

# Use SQLite for local development if DATABASE_URL is not set
db_url = os.getenv('DATABASE_URL', 'sqlite:///local_extractions.db')
# Fix Railway MySQL URL format (mysql:// -> mysql+pymysql://)
if db_url.startswith('mysql://'):
    db_url = db_url.replace('mysql://', 'mysql+pymysql://', 1)
app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Database Model
class Extraction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    chart_type = db.Column(db.String(50))
    accuracy_score = db.Column(db.Float)
    extracted_data = db.Column(db.Text) # Stored as JSON string
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'filename': self.filename,
            'chart_type': self.chart_type,
            'accuracy_score': self.accuracy_score,
            'created_at': self.created_at.isoformat()
        }

# Create tables within app context
with app.app_context():
    db.create_all()

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy", "service": "LLM Chart Backend"})

@app.route('/api/convert', methods=['POST'])
def convert_chart():
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400
            
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400
            
        if not allowed_file(file.filename):
            return jsonify({"error": "Invalid file type"}), 400

        # Save to temp file because LLM_Final might expect a path or we want to keep it simple
        # Actually LLM_Final uses Image.open() which accepts streams, but let's be safe
        # and also we need the path for metrics evaluation if we want to reload it easily
        # (though metrics also takes path or stream if we adapted it, but let's just use temp file)
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp:
            file.save(tmp.name)
            tmp_path = tmp.name

        try:
            # 1. Extract Data
            logger.info(f"Processing file: {tmp_path}")
            result = extractor.process_chart_image(tmp_path, verbose=True)
            
            if not result['success']:
                return jsonify({"error": result.get('error', 'Extraction failed')}), 500
                
            df = result['df']
            chart_type = result.get('chart_type', 'bar chart')
            
            # 2. Calculate Accuracy (Error Metric)
            eval_result = metrics.evaluate_extraction(tmp_path, df, chart_type=chart_type)
            
            # 3. Prepare Response
            response_data = {
                "success": True,
                "data": df.to_dict(orient='records'),
                "columns": df.columns.tolist(),
                "chart_type": chart_type,
                "method": result.get('method', 'unknown'),
                "accuracy": {
                    "score": eval_result.get('accuracy_score', 0),
                    "ssim": eval_result.get('ssim', 0),
                    "note": "Accuracy is estimated using SSIM between original and re-rendered chart"
                }
            }
            
            # 4. Save to Database
            try:
                new_extraction = Extraction(
                    filename=file.filename,
                    chart_type=chart_type,
                    accuracy_score=eval_result.get('accuracy_score', 0),
                    extracted_data=json.dumps(response_data['data'])
                )
                db.session.add(new_extraction)
                db.session.commit()
                logger.info(f"Saved extraction to database: ID {new_extraction.id}")
            except Exception as db_err:
                logger.error(f"Failed to save to database: {db_err}")
                # Don't fail the request if DB save fails, just log it
            
            return jsonify(response_data)

        finally:
            # Cleanup temp file
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
                
    except Exception as e:
        logger.error(f"Error in convert_chart: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route('/api/convert/csv', methods=['POST'])
def convert_chart_csv():
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400
            
        file = request.files['file']
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp:
            file.save(tmp.name)
            tmp_path = tmp.name

        try:
            result = extractor.process_chart_image(tmp_path, verbose=True)
            
            if not result['success']:
                return jsonify({"error": result.get('error', 'Extraction failed')}), 500
                
            df = result['df']
            
            # Convert to CSV
            output = io.StringIO()
            df.to_csv(output, index=False)
            csv_data = output.getvalue()
            
            return send_file(
                io.BytesIO(csv_data.encode('utf-8')),
                mimetype='text/csv',
                as_attachment=True,
                download_name='extracted_data.csv'
            )

        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
                
    except Exception as e:
        logger.error(f"Error in convert_chart_csv: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    # Disable debug in production
    debug_mode = os.environ.get('FLASK_ENV') != 'production'
    app.run(host='0.0.0.0', port=port, debug=debug_mode)
