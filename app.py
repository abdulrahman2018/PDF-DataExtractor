from flask import Flask, render_template, request, jsonify, send_file
import os
from werkzeug.utils import secure_filename
from pdf_extractor import PDFExtractor
import shutil
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Create permanent upload and output directories
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'outputs')

# Ensure directories exist
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_DIR
app.config['OUTPUT_FOLDER'] = OUTPUT_DIR

logger.info(f"Upload directory: {UPLOAD_DIR}")
logger.info(f"Output directory: {OUTPUT_DIR}")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process_files():
    if 'files' not in request.files:
        return jsonify({'success': False, 'error': 'No files provided'}), 400

    files = request.files.getlist('files')
    if not files or files[0].filename == '':
        return jsonify({'success': False, 'error': 'No files selected'}), 400

    try:
        # Create a unique session directory for this upload
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        session_dir = os.path.join(app.config['UPLOAD_FOLDER'], f'session_{timestamp}')
        os.makedirs(session_dir, exist_ok=True)
        logger.info(f"Created session directory: {session_dir}")

        # Save uploaded files
        saved_files = []
        for file in files:
            if file and file.filename.endswith('.pdf'):
                filename = secure_filename(file.filename)
                filepath = os.path.join(session_dir, filename)
                
                # Save the file
                try:
                    file.save(filepath)
                    if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
                        saved_files.append(filepath)
                        logger.info(f"Successfully saved file: {filepath}")
                    else:
                        logger.error(f"File was not saved properly: {filepath}")
                        raise Exception(f"Failed to save file: {filename}")
                except Exception as e:
                    logger.error(f"Error saving file {filename}: {str(e)}")
                    raise

        if not saved_files:
            return jsonify({'success': False, 'error': 'No valid PDF files uploaded'}), 400

        # Process files
        extractor = PDFExtractor()
        output_file = os.path.join(app.config['OUTPUT_FOLDER'], f'extracted_data_{timestamp}.xlsx')
        
        # Verify files exist before processing
        for filepath in saved_files:
            if not os.path.exists(filepath):
                raise Exception(f"File not found: {filepath}")
        
        logger.info(f"Processing {len(saved_files)} files")
        # Process the directory
        extractor.process_directory(session_dir)
        # Save the results
        extractor.save_to_excel(output_file)

        # Store the output file path in the session
        app.config['LAST_OUTPUT_FILE'] = output_file

        return jsonify({'success': True})

    except Exception as e:
        logger.error(f"Error processing files: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/download')
def download_file():
    try:
        output_file = app.config.get('LAST_OUTPUT_FILE')
        if not output_file or not os.path.exists(output_file):
            logger.error(f"Output file not found: {output_file}")
            return jsonify({'success': False, 'error': 'No processed data available'}), 404

        logger.info(f"Sending file for download: {output_file}")
        return send_file(
            output_file,
            as_attachment=True,
            download_name='extracted_data.xlsx',
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    except Exception as e:
        logger.error(f"Error downloading file: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

# Optional: Add a cleanup route to remove old files
@app.route('/cleanup', methods=['POST'])
def cleanup():
    try:
        # Keep only the last 5 sessions
        sessions = sorted([d for d in os.listdir(app.config['UPLOAD_FOLDER']) 
                         if d.startswith('session_')])
        if len(sessions) > 5:
            for session in sessions[:-5]:
                shutil.rmtree(os.path.join(app.config['UPLOAD_FOLDER'], session))
                logger.info(f"Cleaned up old session: {session}")

        # Keep only the last 5 output files
        outputs = sorted([f for f in os.listdir(app.config['OUTPUT_FOLDER']) 
                        if f.startswith('extracted_data_')])
        if len(outputs) > 5:
            for output in outputs[:-5]:
                os.remove(os.path.join(app.config['OUTPUT_FOLDER'], output))
                logger.info(f"Cleaned up old output: {output}")

        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Error during cleanup: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True) 