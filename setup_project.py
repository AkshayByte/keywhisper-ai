# setup_project.py
import os
import re

# 1. Create Directory Structure
os.makedirs('templates', exist_ok=True)
os.makedirs('static/js', exist_ok=True)
os.makedirs('uploads', exist_ok=True)

# 2. Define the Patcher Function
def patch_html(filename, content):
    """Injects IDs and scripts into the HTML so the backend can control it."""
    
    # Common Injections
    if '</body>' in content:
        content = content.replace('</body>', '<script src="/static/js/main.js"></script>\n</body>')

    # Specific Injections based on file content
    if 'reports.html' in filename:
        # Table ID
        content = re.sub(r'<table.*?>', '<table id="reports-table" class="w-full text-left">', content, 1)
        # Button IDs
        content = re.sub(r'download\s+Export Report', 'download Export Report', content) # Normalize
        content = re.sub(r'<button.*?Export Report.*?</button>', '<button id="btn-export" class="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors">\n<span class="material-symbols-outlined">download</span>Export Report\n</button>', content, flags=re.DOTALL)
        content = re.sub(r'<button.*?Analyze.*?</button>', '<button id="btn-refresh-reports" class="px-4 py-2 bg-primary/20 text-primary rounded-lg hover:bg-primary/30 transition-colors">Analyze</button>', content, flags=re.DOTALL)

    elif 'index.html' in filename:
        # Dashboard Stats
        content = re.sub(r'85%', '<span id="stat-accuracy">85%</span>', content)
        content = re.sub(r'12\s+<', '<span id="stat-threats">12</span> <', content)
        content = re.sub(r'-12dB', '<span id="stat-snr">-12dB</span>', content)
        
        # Spectrogram Chart Container - Finding the specific div for the chart
        # We look for "Real-Time EM Spectrogram" and target the empty div or image below it
        pattern = r'(Real-Time EM Spectrogram.*?T-Minus.*?</div>\s*<div.*?>)(.*?)(</div>)'
        # Replace the placeholder content with a Canvas
        replacement = r'\1anvas id="spectrogram-canvas" width="600" height="200" class="w-full h-full rounded bg-black"></canvas>\3'
        content = re.sub(pattern, replacement, content, flags=re.DOTALL)

    elif 'data.html' in filename:
        # File Upload
        content = re.sub(r'Drag and drop.*?files here', 'Drag and drop .WAV, .CSV, or .IQ files here<br><span id="upload-status" class="text-sm text-gray-400"></span>', content)
        # Find the upload container (the one with dashed border)
        content = re.sub(r'(<div.*?border-dashed.*?>)', r'\1<input type="file" id="file-upload-input" style="display:none">', content)
        # Add ID to the container itself (approximate matching)
        content = content.replace('border-dashed', 'border-dashed" id="upload-dropzone')

    elif 'analytics.html' in filename:
        # Training Controls
        content = re.sub(r'<button.*?Start Analysis.*?</button>', '<button id="btn-train-model" class="w-full py-3 bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg font-medium hover:opacity-90 transition-opacity flex items-center justify-center gap-2">Start Training</button>', content, flags=re.DOTALL)
        content = re.sub(r'1e-3', '<input type="text" id="input-lr" value="0.001" class="bg-transparent w-full text-center">', content)
        content = re.sub(r'50', '<input type="number" id="input-epochs" value="50" class="bg-transparent w-full text-center">', content)
        # Progress Bar
        content = re.sub(r'Hyperparameters', 'Hyperparameters <span id="training-status-text" class="text-xs text-blue-400 ml-2"></span>', content)

    return content

# 3. Process Files
files = ['reports.html', 'index.html', 'data.html', 'analytics.html']
for f in files:
    if os.path.exists(f):
        with open(f, 'r', encoding='utf-8') as file:
            raw = file.read()
        
        fixed = patch_html(f, raw)
        
        with open(os.path.join('templates', f), 'w', encoding='utf-8') as file:
            file.write(fixed)
        print(f"✅ Patched and moved {f} to /templates")
    else:
        print(f"❌ Could not find {f} in current directory.")

# 4. Generate Backend (app.py)
app_code = r'''
import os
import time
import threading
import random
import math
from flask import Flask, render_template, jsonify, request, send_file
from werkzeug.utils import secure_filename

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
    return render_template(f'{page}')

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
    f = request.files['file']
    f.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(f.filename)))
    return jsonify({'msg': 'File Ingested for Analysis'})

@app.route('/api/export_report')
def export_report():
    # In real app, generate PDF here. We just return a dummy text file.
    return "Report ID: 4092\nSeverity: High\nDetected: 52 Keystrokes", 200, {
        'Content-Disposition': 'attachment; filename=emc_report_4092.txt'
    }

if __name__ == '__main__':
    app.run(debug=True, port=5000)
'''

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(app_code)
print("✅ Generated app.py")

# 5. Generate Frontend (main.js)
js_code = r'''
// Global Chart Instance
let chartContext = null;
let animationId = null;

document.addEventListener('DOMContentLoaded', () => {
    // Determine page context
    if(document.getElementById('spectrogram-canvas')) initDashboard();
    if(document.getElementById('upload-dropzone')) initUpload();
    if(document.getElementById('btn-train-model')) initTraining();
    if(document.getElementById('btn-export')) initReports();
});

// --- DASHBOARD: Real-Time Spectrogram ---
function initDashboard() {
    const canvas = document.getElementById('spectrogram-canvas');
    const ctx = canvas.getContext('2d');
    const W = canvas.width;
    const H = canvas.height;
    
    // Gradient for heatmap
    const gradient = ctx.createLinearGradient(0, H, 0, 0);
    gradient.addColorStop(0, '#0f0');   // Low (Green)
    gradient.addColorStop(0.5, '#ff0'); // Mid (Yellow)
    gradient.addColorStop(1, '#f00');   // High (Red)

    function fetchAndDraw() {
        fetch('/api/spectrogram')
            .then(r => r.json())
            .then(res => {
                const data = res.data; // Array of 100 floats
                const barWidth = W / data.length;
                
                // Fade effect (waterfall simulation)
                ctx.fillStyle = 'rgba(0, 0, 0, 0.1)'; 
                ctx.fillRect(0, 0, W, H);
                
                // Draw Bars
                data.forEach((db, i) => {
                    // Normalize -100dB to -20dB range into 0-1 height
                    let h = (db + 100) / 80; 
                    if (h < 0) h = 0;
                    if (h > 1) h = 1;
                    
                    const barHeight = h * H;
                    ctx.fillStyle = gradient;
                    ctx.fillRect(i * barWidth, H - barHeight, barWidth - 1, barHeight);
                });
                
                // Also update stats occasionally
                if(Math.random() > 0.8) updateStats();
            });
        
        animationId = requestAnimationFrame(fetchAndDraw);
    }
    fetchAndDraw();
}

function updateStats() {
    fetch('/api/stats').then(r => r.json()).then(d => {
        if(document.getElementById('stat-accuracy')) 
            document.getElementById('stat-accuracy').innerText = d.accuracy + '%';
        if(document.getElementById('stat-threats')) 
            document.getElementById('stat-threats').innerText = d.threats;
    });
}

// --- DATA: Upload ---
function initUpload() {
    const dropzone = document.getElementById('upload-dropzone');
    const input = document.getElementById('file-upload-input');
    
    dropzone.addEventListener('click', () => input.click());
    
    input.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if(!file) return;
        
        const fd = new FormData();
        fd.append('file', file);
        
        document.getElementById('upload-status').innerText = "Uploading...";
        
        fetch('/api/upload', {method: 'POST', body: fd})
            .then(r => r.json())
            .then(res => {
                document.getElementById('upload-status').innerText = res.msg;
                alert("Data Ingested Successfully!");
            });
    });
}

// --- ANALYTICS: Training ---
function initTraining() {
    document.getElementById('btn-train-model').addEventListener('click', () => {
        const epochs = document.getElementById('input-epochs').value;
        fetch('/api/train', {
            method: 'POST', 
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({epochs: epochs})
        })
        .then(r => r.json())
        .then(res => {
            if(res.error) return alert(res.error);
            monitorTraining();
        });
    });
}

function monitorTraining() {
    const interval = setInterval(() => {
        fetch('/api/training-status').then(r => r.json()).then(s => {
            const txt = document.getElementById('training-status-text');
            if(txt) txt.innerText = `${s.progress}% - ${s.log}`;
            
            if(!s.active && s.progress === 100) {
                clearInterval(interval);
                alert("Model Training Finished!");
            }
        });
    }, 500);
}

// --- REPORTS: Export ---
function initReports() {
    document.getElementById('btn-export').addEventListener('click', () => {
        window.location.href = '/api/export_report';
    });
}
'''

with open('static/js/main.js', 'w', encoding='utf-8') as f:
    f.write(js_code)
print("✅ Generated static/js/main.js")
print("\n🎉 SETUP COMPLETE! Run 'python app.py' and go to http://127.0.0.1:5000")
