# EM-SEC: Side-Channel Attack on Keyboards

A full-stack research platform for demonstrating electromagnetic (EM) side-channel attacks on keyboards. This platform captures, visualizes, and classifies keyboard keystrokes by analyzing electromagnetic emissions without physical contact with the target device.

## Overview

This project is a proof-of-concept cybersecurity research platform demonstrating non-invasive side-channel attacks on physical keyboards. Every key pressed generates a unique electromagnetic signature. By capturing these signals with an SDR (Software Defined Radio) antenna and feeding the data through a neural network model, keystrokes can be reconstructed.

The platform provides an interactive dashboard to:
- Visualize EM frequency spectrums.
- Configure and train neural network architectures (LSTM, CNN, Transformer).
- Upload raw `.WAV`, `.CSV`, or `.IQ` capture files for analysis.
- Review keystroke classification reports with confidence scores.

## Features

- **Live Dashboard:** Real-time EM spectrogram rendered on HTML5 Canvas with an animated waterfall display and statistics polling.
- **Model Configuration:** Interactive neural network topology builder. Configure layers, dropout, batch size, epochs, and learning rate.
- **Data Ingestion:** File uploader for EM trace datasets.
- **Reports:** Per-keystroke classification results table with confidence bars and waveform previews.
- **API Backend:** RESTful Flask API serving live spectrum frames, model training control, file uploads, and report exports.
- **Real-time Training:** Background threaded model training with live progress polling.

## Architecture

```text
ai-based-side-channel-attack-on-keyboard/
├── app.py                  # Flask backend API, EMC simulator, training controller
├── templates/              # Jinja2 templates
│   ├── index.html          # Dashboard
│   ├── analytics.html      # Model configuration
│   ├── data.html           # Data ingestion
│   └── reports.html        # Classification reports
├── static/
│   └── js/
│       └── main.js         # Frontend JavaScript
└── uploads/                # Directory for uploaded EM trace files
```

## Tech Stack

- **Backend:** Python 3.9+, Flask, Werkzeug
- **Frontend:** HTML5, Vanilla JavaScript
- **Styling:** Tailwind CSS
- **Visualization:** HTML5 Canvas API
- **Concurrency:** Python threading for non-blocking operations

## Installation

### Prerequisites

- Python 3.9+
- Git

### Setup

1. Clone the repository:
```bash
git clone https://github.com/AkshayByte/keywhisper-ai.git
cd keywhisper-ai
```

2. Create a virtual environment:
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Launch the application:
```bash
python app.py
```

Navigate to `http://127.0.0.1:5000` in your browser.

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Serves the main dashboard |
| GET | `/<page>` | Dynamically serves template by name |
| GET | `/api/spectrogram` | Returns FFT spectrum frame |
| GET | `/api/stats` | Returns accuracy, threats, and SNR |
| POST | `/api/train` | Starts training |
| GET | `/api/training-status` | Returns training progress |
| POST | `/api/upload` | Accepts multipart file upload |
| GET | `/api/export_report` | Returns downloadable report file |
