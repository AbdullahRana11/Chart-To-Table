# 🚀 Final Chart-to-Table Backend (LLM Powered)

This is the **final, high-accuracy backend** for the Chart-to-Table Converter.
It uses **Google Gemini Vision** (LLM) to extract data with near-perfect accuracy and includes an **error estimation system** using SSIM (Structural Similarity Index).

---

## 📦 Contents

- **`backend.py`**: The Flask API server.
- **`LLM_Final.py`**: The core extraction logic using Gemini.
- **`accuracy_metrics.py`**: Handles re-rendering charts and calculating accuracy scores.
- **`requirements.txt`**: Python dependencies.

---

## 🛠️ Setup & Run

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set API Key
You need a Google Gemini API key.
```bash
# Windows (PowerShell)
$env:GOOGLE_API_KEY="your_api_key_here"

# Linux/Mac
export GOOGLE_API_KEY="your_api_key_here"
```

### 3. Start Server
```bash
python backend.py
```
Server runs at `http://localhost:5000`

---

## 📡 API Endpoints

### 1. Convert Chart (JSON + Accuracy)
**POST** `/api/convert`
- **Body**: `form-data` with `file` (image)
- **Response**:
  ```json
  {
    "success": true,
    "data": [
      {"label": "A", "value": 10},
      {"label": "B", "value": 20}
    ],
    "chart_type": "bar chart",
    "accuracy": {
      "score": 95.5,   // 0-100% match score
      "ssim": 0.955    // Raw SSIM index
    }
  }
  ```

### 2. Download CSV
**POST** `/api/convert/csv`
- **Body**: `form-data` with `file` (image)
- **Response**: CSV file download.

---

## 📊 Accuracy Calculation
The backend automatically verifies the extraction accuracy:
1. Extracts data from the uploaded chart.
2. Re-renders the data into a new chart image using Matplotlib.
3. Compares the original image with the re-rendered image using **SSIM**.
4. Returns a confidence score (0-100%).

---

## 📝 Notes for Frontend Team
- Use the `/api/convert` endpoint to get both data and the accuracy score.
- Display the `accuracy.score` to the user to give them confidence in the result.
- If accuracy is low (<50%), you might want to show a warning.
