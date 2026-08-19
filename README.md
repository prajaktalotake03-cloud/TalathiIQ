# TalathiIQ - Smart Preparation. Smarter Results.
### तलाठी भरतीची स्मार्ट तयारी

TalathiIQ is a modern, premium preparation platform for Maharashtra Talathi Bharti aspirants. Built with Python Flask on the backend and HTML5, CSS3, and Vanilla JavaScript on the frontend. It features practice quizzes, current affairs updates, real-time mock test simulations, smart revision tracking, and an AI-ready Study Mentor dashboard.

---

## Folder Structure

```text
TalathiIQ/
│
├── app.py                  # Flask Application & Routing
├── requirements.txt        # Backend dependencies
├── README.md               # Setup and execution guide
│
├── data/
│   └── questions.json      # 20 Seeded Practice Questions
│
├── templates/
│   ├── index.html          # Dashboard Landing page
│   ├── current-affairs.html# Categorized current affairs
│   ├── mcq.html            # Interactive MCQ Practice page
│   ├── mock-test.html      # 20-question Mock Test Portal
│   ├── result.html         # Test results summary report
│   ├── revision.html       # Adaptive mistakes revision tracker
│   ├── performance.html    # SVG progress dashboard
│   └── ai-assistant.html   # AI Mentor Chatbot UI
│
└── static/
    ├── css/
    │   └── style.css       # Custom Glassmorphic Dark-Theme Stylesheet
    └── js/
        ├── main.js         # Navigation and layout controllers
        ├── mcq.js          # Interactive MCQ solver and score manager
        ├── mock-test.js    # Simulated Mock Exam tracker and timer
        └── dashboard.js    # LocalStorage metrics sync and cards
```

---

## Setup & Running Instructions

Follow these simple steps to run the application locally on your computer:

### Step 1: Install Python
Ensure you have Python 3.8 or higher installed. You can check this by running in your terminal:
```bash
python --version
```
If Python is not installed, download and install it from the official site: [python.org](https://www.python.org/).

### Step 2: Create a Virtual Environment
Navigate to the project root directory in your command line and run the following command to create a virtual environment:

**On Windows:**
```bash
python -m venv venv
```

**On macOS / Linux:**
```bash
python3 -m venv venv
```

### Step 3: Activate the Virtual Environment
Activate the environment to isolate project dependencies:

**On Windows (Command Prompt):**
```cmd
venv\Scripts\activate.bat
```
**On Windows (PowerShell):**
```powershell
.\venv\Scripts\activate.ps1
```

**On macOS / Linux:**
```bash
source venv/bin/activate
```

### Step 4: Install Dependencies
Install all required libraries using the package manager `pip`:
```bash
pip install -r requirements.txt
```

### Step 5: Run the Flask Application
Start the development server with the following command:
```bash
python app.py
```

### Step 6: Open the Website in Your Browser
Once the server starts running, open your web browser and navigate to:
```text
http://127.0.0.1:5000/
```

---

## Features Implemented
* **Interactive AI MCQs Practice:** Practice 20 sample Talathi-oriented MCQs. Get live feedback, option highlighting (correct/wrong), score updates, accuracy rates, and detailed explanation text.
* **Simulated Mock Test:** Answer 20 questions under a 20-minute countdown timer. Supports flag-marking questions for review, a sidebar navigation grid indicating answer states, automatic submission on timeout, and redirects to a custom results screen.
* **Detailed Results Sheet:** Review score out of 40, accuracy rates, correct vs. incorrect answers count, and time taken.
* **Smart Revision:** Tracks wrong answers automatically via `localStorage` and lets you practice/clear them dynamically.
* **Performance Dashboard:** View overall statistics (solved count, streak, accuracy) and custom subject accuracy graphs without heavy third-party charting libraries.
* **AI Mentor Chat UI:** Modern floating dialog interface prepared for future LLM API integration.
