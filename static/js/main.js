
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
