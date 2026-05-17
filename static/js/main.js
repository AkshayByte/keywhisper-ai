
// Global Chart Instance
let chartContext = null;
let animationId = null;

// --- TOAST NOTIFICATION SYSTEM ---
// Replaces all browser alert() calls with non-blocking, auto-dismissing toasts.
// Usage: showToast('Your message here');          // green success toast
//        showToast('Something went wrong', 'error'); // red error toast
function showToast(message, type = 'success') {
    const colors = {
        success: 'background: linear-gradient(135deg, #059669, #10b981);',
        error:   'background: linear-gradient(135deg, #dc2626, #ef4444);',
        info:    'background: linear-gradient(135deg, #1d4ed8, #3b82f6);'
    };
    const toast = document.createElement('div');
    toast.style.cssText = `
        position: fixed; bottom: 24px; right: 24px; z-index: 9999;
        padding: 12px 20px; border-radius: 10px; color: #fff;
        font-family: 'Space Grotesk', sans-serif; font-size: 14px; font-weight: 500;
        box-shadow: 0 8px 24px rgba(0,0,0,0.4);
        ${colors[type] || colors.success}
        opacity: 0; transform: translateY(12px);
        transition: opacity 0.3s ease, transform 0.3s ease;
        max-width: 320px; word-break: break-word;
    `;
    toast.textContent = message;
    document.body.appendChild(toast);

    // Animate in
    requestAnimationFrame(() => {
        toast.style.opacity = '1';
        toast.style.transform = 'translateY(0)';
    });

    // Animate out and remove after 3.5s
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(12px)';
        setTimeout(() => toast.remove(), 300);
    }, 3500);
}

document.addEventListener('DOMContentLoaded', () => {
    // Determine page context by checking for landmark element IDs
    if(document.getElementById('spectrogram-canvas')) initDashboard();
    if(document.getElementById('upload-dropzone'))    initUpload();
    if(document.getElementById('btn-train-model'))    initTraining();
    if(document.getElementById('btn-export'))         initReports();
});

// --- DASHBOARD: Real-Time Spectrogram ---
function initDashboard() {
    const canvas = document.getElementById('spectrogram-canvas');
    const ctx = canvas.getContext('2d');
    const W = canvas.width;
    const H = canvas.height;
    
    // Gradient for heatmap: Green (low) → Yellow (mid) → Red (high)
    const gradient = ctx.createLinearGradient(0, H, 0, 0);
    gradient.addColorStop(0,   '#0f0'); // Low  (Green)
    gradient.addColorStop(0.5, '#ff0'); // Mid  (Yellow)
    gradient.addColorStop(1,   '#f00'); // High (Red)

    function fetchAndDraw() {
        fetch('/api/spectrogram')
            .then(r => r.json())
            .then(res => {
                const data = res.data; // Array of 100 floats (dBm values)
                const barWidth = W / data.length;
                
                // Fade effect — creates waterfall scroll simulation
                ctx.fillStyle = 'rgba(0, 0, 0, 0.1)';
                ctx.fillRect(0, 0, W, H);
                
                // Draw frequency bars
                data.forEach((db, i) => {
                    // Normalize range: -100 dBm (floor) to -20 dBm (ceiling) → 0 to 1
                    let h = (db + 100) / 80;
                    if (h < 0) h = 0;
                    if (h > 1) h = 1;
                    
                    const barHeight = h * H;
                    ctx.fillStyle = gradient;
                    ctx.fillRect(i * barWidth, H - barHeight, barWidth - 1, barHeight);
                });
                
                // Stochastically refresh stats (avoids hammering /api/stats every frame)
                if(Math.random() > 0.8) updateStats();
            })
            .catch(err => console.error('[Spectrogram] Fetch failed:', err));
        
        animationId = requestAnimationFrame(fetchAndDraw);
    }
    fetchAndDraw();
}

function updateStats() {
    fetch('/api/stats')
        .then(r => r.json())
        .then(d => {
            if(document.getElementById('stat-accuracy'))
                document.getElementById('stat-accuracy').innerText = d.accuracy + '%';
            if(document.getElementById('stat-threats'))
                document.getElementById('stat-threats').innerText = d.threats;
        })
        .catch(err => console.error('[Stats] Fetch failed:', err));
}

// --- DATA: File Upload ---
function initUpload() {
    const dropzone = document.getElementById('upload-dropzone');
    const input    = document.getElementById('file-upload-input');
    
    // Delegate click on the visual dropzone to the hidden file input
    dropzone.addEventListener('click', () => input.click());
    
    input.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if(!file) return;
        
        const fd = new FormData();
        fd.append('file', file);
        
        document.getElementById('upload-status').innerText = 'Uploading...';
        
        fetch('/api/upload', { method: 'POST', body: fd })
            .then(r => r.json())
            .then(res => {
                if(res.error) {
                    document.getElementById('upload-status').innerText = res.error;
                    showToast(res.error, 'error');
                    return;
                }
                document.getElementById('upload-status').innerText = res.msg;
                // ✅ Replaced: alert("Data Ingested Successfully!")
                showToast('Data ingested successfully! ✅');
            })
            .catch(err => {
                console.error('[Upload] Fetch failed:', err);
                showToast('Upload failed — check your connection.', 'error');
            });
    });
}

// --- ANALYTICS: Model Training ---
function initTraining() {
    document.getElementById('btn-train-model').addEventListener('click', () => {
        const epochs = document.getElementById('input-epochs').value;
        fetch('/api/train', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ epochs: epochs })
        })
        .then(r => r.json())
        .then(res => {
            if(res.error) {
                // ✅ Replaced: alert(res.error)
                showToast(res.error, 'error');
                return;
            }
            showToast(`Training started — ${epochs} epochs queued.`, 'info');
            monitorTraining();
        })
        .catch(err => {
            console.error('[Training] Fetch failed:', err);
            showToast('Could not start training — server unreachable.', 'error');
        });
    });
}

function monitorTraining() {
    const interval = setInterval(() => {
        fetch('/api/training-status')
            .then(r => r.json())
            .then(s => {
                const txt = document.getElementById('training-status-text');
                if(txt) txt.innerText = `${s.progress}% — ${s.log}`;
                
                if(!s.active && s.progress === 100) {
                    clearInterval(interval);
                    // ✅ Replaced: alert("Model Training Finished!")
                    showToast('Model training complete! 🎯');
                }
            })
            .catch(err => console.error('[Training Monitor] Fetch failed:', err));
    }, 500);
}

// --- REPORTS: Export ---
function initReports() {
    document.getElementById('btn-export').addEventListener('click', () => {
        window.location.href = '/api/export_report';
    });
}
