
import os
import time
import threading
import random
import math
from flask import Flask, render_template, jsonify, request, send_file
from werkzeug.utils import secure_filename
from jinja2 import TemplateNotFound

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# --- EMC Data Simulation ---
class EMCSimulator:
    def __init__(self):
        self.base_freq = 2400 # MHz
        self.time_step = 0
        
    def get_spectrum_frame(self):
        """Generates a realistic frequency domain frame (FFT slice)."""
        self.time_step += 0.1
        # Create 100 frequency bins
        data = []
        for i in range(100):
            # Noise floor around -90dBm
            noise = -90 + random.uniform(-2, 2)
            
            # Simulated Carrier Signal at bin 40 (2440 MHz)
            signal = 0
            if i > 35 and i < 45:
                # Modulate signal amplitude over time
                amp = -40 + 10 * math.sin(self.time_step) 
                # Gaussian shape
                signal = amp * math.exp(-0.5 * ((i - 40) / 2)**2)
                
            # Random Interference Spikes
            interference = 0
            if random.random() > 0.98:
                interference = random.uniform(0, 30)
                
            # Combine (logarithmic addition approximation for visualization)
            val = max(noise, signal + noise if signal != 0 else noise) + interference
            data.append(val)
        return data

emc_sim = EMCSimulator()
training_state = {'active': False, 'progress': 0, 'log': 'Ready'}

@app.route('/')
def index(): return render_template('index.html')

@app.route('/<page>')
def pages(page):
    try:
        return render_template(f'{page}')
    except TemplateNotFound:
        return jsonify({'error': f'Page "{page}" not found'}), 404

@app.route('/api/spectrogram')
def api_spectrogram():
    """Returns a single frame of spectrum data [dBm values]."""
    return jsonify({
        'data': emc_sim.get_spectrum_frame(),
        'timestamp': time.time()
    })

@app.route('/api/stats')
def api_stats():
    return jsonify({
        'accuracy': random.randint(84, 88),
        'threats': random.randint(10, 15),
        'snr': round(-12 + random.uniform(-0.5, 0.5), 1)
    })

@app.route('/api/train', methods=['POST'])
def api_train():
    if training_state['active']: return jsonify({'error': 'Busy'}), 400
    
    def train_task():
        training_state['active'] = True
        training_state['progress'] = 0
        epochs = int(request.json.get('epochs', 50))
        
        for i in range(epochs):
            time.sleep(0.1) # Simulate work
            training_state['progress'] = int((i / epochs) * 100)
            training_state['log'] = f"Epoch {i+1}/{epochs} - Loss: {round(random.random(), 4)}"
            
        training_state['active'] = False
        training_state['progress'] = 100
        training_state['log'] = "Training Complete"
        
    threading.Thread(target=train_task).start()
    return jsonify({'status': 'started'})

@app.route('/api/training-status')
def api_training_status():
    return jsonify(training_state)

@app.route('/api/upload', methods=['POST'])
def api_upload():
    # Validate that a file field exists and is not empty
    if 'file' not in request.files or request.files['file'].filename == '':
        return jsonify({'error': 'No file selected. Please attach a file to the request.'}), 400
    f = request.files['file']
    filename = secure_filename(f.filename)
    if not filename:
        return jsonify({'error': 'Invalid filename after sanitization.'}), 400
    f.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    return jsonify({'msg': f'File "{filename}" ingested for analysis'})

@app.route('/api/export_report')
def export_report():
    # In real app, generate PDF here. We just return a dummy text file.
    return "Report ID: 4092\nSeverity: High\nDetected: 52 Keystrokes", 200, {
        'Content-Disposition': 'attachment; filename=emc_report_4092.txt'
    }

if __name__ == '__main__':
    app.run(debug=True, port=5000)
