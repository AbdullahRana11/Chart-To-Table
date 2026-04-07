# Chart-To-Table Converter (DePlot Edition)

A powerful full-stack application that uses **Google's DePlot (SOTA)** model to convert chart images into structured data tables.

## 🚀 Quick Start
**Use the One-Click Script (Windows)**
```powershell
.\run.ps1
```
This launches both the Backend (Flask) and Frontend (React/Vite) automatically.

## 🛠️ Manual Setup

### 1. Backend
The backend uses Python/Flask and Transformers.
```bash
cd backend
pip install -r ../requirements.txt
python app.py
```
*Note: The first run will download the `google/deplot` model (~1GB).*

### 2. Frontend
The frontend is built with React + Vite + Framer Motion.
```bash
cd frontend
npm install
npm run dev
```

## 🌟 Key Features
- **State-of-the-Art OCR**: Powered by `google/deplot`, specifically fine-tuned for charts.
- **Smart Parsing**: Automatically detects headers and data rows.
- **Heuristic Confidence**: Estimates accuracy based on table structure and numeric density.
- **Modern UI**: Drag-and-drop upload with "Glassmorphism" design.
- **History**: Saves previous extractions locally.

## 📂 Project Structure
- `backend/`: Flask API & Model Logic (`extractor.py`)
- `frontend/`: React Application
- `run.ps1`: Launch script
- `requirements.txt`: Python dependencies

## 📝 Notes
- Requires a GPU (CUDA) for optimal performance. CPU execution is supported but slower.
- The model runs locally on your machine.
