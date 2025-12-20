# Chart-to-Table Frontend

This is the frontend application for the Chart-to-Table Extraction project.

## Prerequisites

- Node.js installed (version 18 or higher recommended)

## How to Run

### 1. Start the Backend Server
The frontend needs the backend to be running to extract data.

1.  Open a **new terminal**.
2.  Navigate to the project folder:
    ```bash
    cd "d:\3rd Semester\Software Engineering\Project"
    ```
3.  Install Python dependencies:
    ```bash
    pip install -r backend_final/requirements.txt
    ```
4.  Start the server:
    ```bash
    python backend_final/backend.py
    ```
    You should see "Running on http://0.0.0.0:5000".

### 2. Start the Frontend
1.  Open **another terminal**.
2.  Navigate to the frontend folder:
    ```bash
    cd frontend
    ```
3.  Start the React app:
    ```bash
    npm run dev
    ```
4.  Open the link shown (e.g., `http://localhost:5173`).

## Project Structure

- `src/pages/`: Contains the main pages (Home, Upload, Results).
- `src/components/`: Reusable components like the Layout.
- `src/index.css`: Global styles and theme variables.
