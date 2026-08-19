import os
import json
import sqlite3
import io
from flask import Flask, render_template, jsonify, request, redirect, url_for, send_file, session
from werkzeug.security import generate_password_hash, check_password_hash
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

app = Flask(__name__)
app.secret_key = 'talathiiq_secret_key_12345'

DATABASE = os.path.join(app.root_path, 'data', 'talathiiq.db')

HAS_NIRMALA = False
try:
    font_path = r"C:\Windows\Fonts\Nirmala.ttf"
    if os.path.exists(font_path):
        pdfmetrics.registerFont(TTFont('Nirmala', font_path))
        HAS_NIRMALA = True
except Exception as e:
    print(f"Error registering Nirmala font: {e}")

PYQ_PAPERS = [
    {
        "id": "talathi_2023_s1",
        "title": "Talathi Bharti Question Paper 2023 (Shift 1)",
        "year": 2023,
        "questions_count": 50,
        "duration": 30,
        "slice_start": 0,
        "slice_end": 50
    },
    {
        "id": "talathi_2023_s2",
        "title": "Talathi Bharti Question Paper 2023 (Shift 2)",
        "year": 2023,
        "questions_count": 50,
        "duration": 30,
        "slice_start": 50,
        "slice_end": 100
    },
    {
        "id": "talathi_2022",
        "title": "Talathi Bharti Question Paper 2022",
        "year": 2022,
        "questions_count": 50,
        "duration": 30,
        "slice_start": 100,
        "slice_end": 150
    },
    {
        "id": "mpsc_combine",
        "title": "MPSC Combined Group B & C Exam PYQ Paper",
        "year": 2025,
        "questions_count": 50,
        "duration": 30,
        "slice_start": 150,
        "slice_end": 200
    },
    {
        "id": "talathi_2019_s1",
        "title": "Talathi Bharti Question Paper 2019 (Shift 1)",
        "year": 2019,
        "questions_count": 50,
        "duration": 30,
        "slice_start": 200,
        "slice_end": 250
    },
    {
        "id": "talathi_2019_s2",
        "title": "Talathi Bharti Question Paper 2019 (Shift 2)",
        "year": 2019,
        "questions_count": 27,
        "duration": 20,
        "slice_start": 250,
        "slice_end": 277
    }
]

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    os.makedirs(os.path.dirname(DATABASE), exist_ok=True)
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS study_materials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            subject TEXT NOT NULL,
            file_name TEXT NOT NULL,
            file_data BLOB NOT NULL,
            academy TEXT DEFAULT 'Standard Academy',
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    # Check if 'academy' column exists, otherwise alter table
    try:
        conn.execute('SELECT academy FROM study_materials LIMIT 1')
    except sqlite3.OperationalError:
        conn.execute('ALTER TABLE study_materials ADD COLUMN academy TEXT DEFAULT "Standard Academy"')
        conn.commit()

    conn.execute('''
        CREATE TABLE IF NOT EXISTS material_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            request_text TEXT NOT NULL,
            submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

# Initialize DB on startup
init_db()

# Helper to read questions database
def load_questions():
    questions_path = os.path.join(app.root_path, 'data', 'questions.json')
    try:
        with open(questions_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading questions: {e}")
        return []

def save_questions(questions):
    questions_path = os.path.join(app.root_path, 'data', 'questions.json')
    try:
        with open(questions_path, 'w', encoding='utf-8') as f:
            json.dump(questions, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"Error saving questions: {e}")
        return False

def parse_pdf_questions(file_stream):
    import pypdf
    import re
    
    try:
        reader = pypdf.PdfReader(file_stream)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
    except Exception as e:
        print(f"Failed to read PDF: {e}")
        return []
        
    lines = text.split('\n')
    questions = []
    
    current_q = None
    options_temp = []
    
    # Heuristics:
    # Match a line starting with a number e.g., "1. What is..." or "1) What is..." or "१. ..."
    q_re = re.compile(r'^\s*(\d+|[०-९]+)[\.\)]\s*(.*)')
    # Match options starting with A, B, C, D or numbers 1, 2, 3, 4
    opt_re = re.compile(r'^\s*([A-Da-d]|[१-४]|[1-4])[\.\)]\s*(.*)')
    # Answer line pattern e.g., "Answer: A" or "उत्तर: २"
    ans_re = re.compile(r'(?:Answer|उत्तर|Ans)\s*[:\-]?\s*([A-Da-d]|[१-४]|[1-4])', re.IGNORECASE)
    
    for line in lines:
        line_str = line.strip()
        if not line_str:
            continue
            
        q_match = q_re.match(line_str)
        if q_match:
            # Save previous question if complete
            if current_q and len(options_temp) >= 2:
                while len(options_temp) < 4:
                    options_temp.append("Option")
                current_q["options"] = options_temp[:4]
                questions.append(current_q)
                
            current_q = {
                "question": q_match.group(2),
                "options": [],
                "answer": 0, # Default to option A
                "explanation": "Previous Year Question (PYQ) extracted from PDF.",
                "subject": "General Knowledge", # Default fallback
                "topic": "PYQ Practice",
                "difficulty": "Hard",
                "source": "PYQ"
            }
            options_temp = []
            continue
            
        opt_match = opt_re.match(line_str)
        if opt_match and current_q:
            options_temp.append(opt_match.group(2))
            continue
            
        ans_match = ans_re.search(line_str)
        if ans_match and current_q:
            val = ans_match.group(1).upper()
            if val in ['A', '1', '१']:
                current_q["answer"] = 0
            elif val in ['B', '2', '२']:
                current_q["answer"] = 1
            elif val in ['C', '3', '३']:
                current_q["answer"] = 2
            elif val in ['D', '4', '४']:
                current_q["answer"] = 3
            continue
            
        # Append text to current question text if no options match yet
        if current_q and not options_temp:
            current_q["question"] += " " + line_str
            
    # Save the last question
    if current_q and len(options_temp) >= 2:
        while len(options_temp) < 4:
            options_temp.append("Option")
        current_q["options"] = options_temp[:4]
        questions.append(current_q)
        
    return questions

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/current-affairs')
def current_affairs():
    return render_template('current-affairs.html')

@app.route('/mcq')
def mcq():
    return render_template('mcq.html')

@app.route('/mock-test')
def mock_test():
    return render_template('mock-test.html')

@app.route('/result')
def result():
    return render_template('result.html')

@app.route('/revision')
def revision():
    return render_template('revision.html')

@app.route('/performance')
def performance():
    return render_template('performance.html')

@app.route('/ai-assistant')
def ai_assistant():
    return render_template('ai-assistant.html')

@app.route('/syllabus')
def syllabus():
    return render_template('syllabus.html')


@app.route('/api/questions')
def api_questions():
    paper = request.args.get('paper')
    if paper:
        paper_obj = next((p for p in PYQ_PAPERS if p['id'] == paper), None)
        if not paper_obj:
            return jsonify([])
        questions = load_questions()
        pyq_questions = [q for q in questions if q.get('source') == 'PYQ']
        return jsonify(pyq_questions[paper_obj['slice_start']:paper_obj['slice_end']])
        
    difficulty = request.args.get('difficulty')
    source = request.args.get('source')
    limit = request.args.get('limit', type=int)
    subject = request.args.get('subject')
    stage = request.args.get('stage')
    
    questions = load_questions()
    
    # Filter by stage
    if stage:
        questions = [q for q in questions if q.get('stage', '').lower() == stage.lower()]
    
    # Filter by source
    if source:
        questions = [q for q in questions if q.get('source', 'Standard').lower() == source.lower()]
    else:
        questions = [q for q in questions if q.get('source', 'Standard').lower() == 'standard']
        
    # Filter by difficulty
    if difficulty:
        diff_val = 'Hard' if difficulty.lower() == 'hardest' else difficulty.capitalize()
        questions = [q for q in questions if q.get('difficulty', 'Medium').capitalize() == diff_val]
        
    # Filter by subject
    if subject and subject.lower() != 'all':
        subj_lower = subject.lower()
        if 'geography' in subj_lower or 'भूगोल' in subj_lower:
            questions = [q for q in questions if q.get('subject', '').lower() == 'geography' or 'geography' in q.get('topic', '').lower() or 'भूगोल' in q.get('topic', '').lower()]
        elif 'history' in subj_lower or 'polity' in subj_lower:
            questions = [q for q in questions if q.get('subject', '').lower() in ['history', 'polity'] or 'history' in q.get('topic', '').lower() or 'polity' in q.get('topic', '').lower() or 'इतिहास' in q.get('topic', '').lower() or 'राज्यशास्त्र' in q.get('topic', '').lower()]
        elif 'science' in subj_lower or 'विज्ञान' in subj_lower:
            questions = [q for q in questions if q.get('subject', '').lower() in ['science', 'general science'] or 'science' in q.get('topic', '').lower() or 'विज्ञान' in q.get('topic', '').lower()]
        elif 'math' in subj_lower or 'गणित' in subj_lower:
            questions = [q for q in questions if q.get('subject', '').lower() in ['mathematics', 'math'] or 'math' in q.get('topic', '').lower() or 'गणित' in q.get('topic', '').lower()]
        elif 'reasoning' in subj_lower or 'बुद्धिमत्ता' in subj_lower:
            questions = [q for q in questions if q.get('subject', '').lower() == 'reasoning' or 'reasoning' in q.get('topic', '').lower() or 'बुद्धिमत्ता' in q.get('topic', '').lower()]
        else:
            questions = [q for q in questions if q.get('subject', '').lower() == subj_lower]
        
    if limit:
        questions = questions[:limit]
        
    return jsonify(questions)


@app.route('/admin/upload-pyq', methods=['POST'])
def upload_pyq():
    file = request.files.get('file')
    if not file or file.filename == '':
        return "Bad Request: No file provided", 400
        
    if not file.filename.lower().endswith('.pdf'):
        return "Bad Request: Only PDF files are allowed", 400
        
    try:
        new_questions = parse_pdf_questions(io.BytesIO(file.read()))
        if not new_questions:
            return "No questions could be parsed from the PDF.", 400
            
        existing_questions = load_questions()
        
        # Ensure unique IDs
        max_id = max([q.get('id', 0) for q in existing_questions]) if existing_questions else 0
        for i, q in enumerate(new_questions):
            q["id"] = max_id + 1 + i
            # Assign subjects based on simple heuristics in question text
            text = q["question"].lower()
            if "marathi" in text or "मराठी" in text:
                q["subject"] = "Marathi"
            elif "english" in text or "english" in text:
                q["subject"] = "English"
            elif "math" in text or "गणित" in text:
                q["subject"] = "Mathematics"
            elif "reasoning" in text or "बुद्धिमत्ता" in text:
                q["subject"] = "Reasoning"
            else:
                q["subject"] = "General Knowledge"
                
            existing_questions.append(q)
            
        save_questions(existing_questions)
        return jsonify({
            "status": "success",
            "message": f"Successfully parsed and loaded {len(new_questions)} questions from PDF.",
            "questions_added": len(new_questions)
        })
    except Exception as e:
        print(f"Error parsing PYQ PDF: {e}")
        return f"Internal Server Error: {e}", 500


@app.route('/study-materials')
def study_materials():
    conn = get_db_connection()
    materials = conn.execute(
        'SELECT id, title, subject, file_name, uploaded_at, academy FROM study_materials ORDER BY uploaded_at DESC'
    ).fetchall()
    requests_list = conn.execute(
        'SELECT name, request_text, submitted_at FROM material_requests ORDER BY submitted_at DESC'
    ).fetchall()
    conn.close()
    
    # Split into Prajakta Lotake Notes and Other Notes
    prajakta_subjects = ['Geography', 'Economics', 'History', 'Polity']
    prajakta_notes = {}
    other_notes = {}
    
    for item in materials:
        subject = item['subject']
        if subject in prajakta_subjects:
            if subject not in prajakta_notes:
                prajakta_notes[subject] = []
            prajakta_notes[subject].append(item)
        else:
            if subject not in other_notes:
                other_notes[subject] = []
            other_notes[subject].append(item)
            
    return render_template(
        'study-materials.html', 
        prajakta_notes=prajakta_notes, 
        other_notes=other_notes, 
        requests_list=requests_list
    )


@app.route('/submit-request', methods=['POST'])
def submit_request():
    name = request.form.get('name')
    request_text = request.form.get('request_text')
    
    if not name or not request_text:
        return "Bad Request: Missing fields", 400
        
    conn = get_db_connection()
    conn.execute(
        'INSERT INTO material_requests (name, request_text) VALUES (?, ?)',
        (name, request_text)
    )
    conn.commit()
    conn.close()
    
    return redirect(url_for('study_materials'))


@app.route('/admin/upload-pdf', methods=['POST'])
def upload_pdf():
    passcode = request.form.get('passcode')
    if passcode != 'admin123':
        return "Unauthorized: Invalid Passcode", 401
        
    title = request.form.get('title')
    subject = request.form.get('subject')
    academy = request.form.get('academy') or 'Standard Academy'
    file = request.files.get('file')
    
    if not title or not subject or not file or file.filename == '':
        return "Bad Request: Missing fields or file", 400
        
    if not file.filename.lower().endswith('.pdf'):
        return "Bad Request: Only PDF files are allowed", 400
        
    file_name = file.filename
    file_data = file.read()
    
    conn = get_db_connection()
    conn.execute(
        'INSERT INTO study_materials (title, subject, file_name, file_data, academy) VALUES (?, ?, ?, ?, ?)',
        (title, subject, file_name, file_data, academy)
    )
    conn.commit()
    conn.close()
    
    return redirect(url_for('study_materials'))


@app.route('/download-pdf/<int:material_id>')
def download_pdf(material_id):
    conn = get_db_connection()
    material = conn.execute(
        'SELECT title, file_name, file_data FROM study_materials WHERE id = ?',
        (material_id,)
    ).fetchone()
    conn.close()
    
    if material is None:
        return "Not Found", 404
        
    return send_file(
        io.BytesIO(material['file_data']),
        mimetype='application/pdf',
        as_attachment=True,
        download_name=material['file_name']
    )


# --- Authentication and PYQ Pages Implementation ---

@app.before_request
def restrict_access():
    allowed_routes = ['login', 'register', 'static']
    if 'user_id' not in session:
        if request.endpoint and request.endpoint not in allowed_routes:
            return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('index'))
        
    error = None
    if request.method == 'POST':
        username_or_email = request.form.get('username')
        password = request.form.get('password')
        
        conn = get_db_connection()
        user = conn.execute(
            'SELECT * FROM users WHERE username = ? OR email = ?',
            (username_or_email, username_or_email)
        ).fetchone()
        conn.close()
        
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            return redirect(url_for('index'))
        else:
            error = "Invalid username or password"
            
    return render_template('login.html', error=error)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('index'))
        
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not username or not email or not password:
            error = "All fields are required"
        else:
            conn = get_db_connection()
            existing_user = conn.execute(
                'SELECT * FROM users WHERE username = ? OR email = ?',
                (username, email)
            ).fetchone()
            
            if existing_user:
                error = "Username or Email already registered"
                conn.close()
            else:
                pw_hash = generate_password_hash(password)
                try:
                    conn.execute(
                        'INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)',
                        (username, email, pw_hash)
                    )
                    conn.commit()
                    conn.close()
                    
                    # Automatically log in the user
                    conn = get_db_connection()
                    user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
                    conn.close()
                    session['user_id'] = user['id']
                    session['username'] = user['username']
                    return redirect(url_for('index'))
                except Exception as e:
                    error = f"Error creating user: {e}"
                    if conn:
                        conn.close()
                        
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/pyq-papers')
def pyq_papers():
    return render_template('pyq-papers.html', papers=PYQ_PAPERS)

def generate_paper_pdf(paper_title, questions):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=54, leftMargin=54, topMargin=54, bottomMargin=54)
    
    styles = getSampleStyleSheet()
    font_name = 'Nirmala' if HAS_NIRMALA else 'Helvetica'
    
    title_style = ParagraphStyle(
        'PaperTitle',
        parent=styles['Heading1'],
        fontName=font_name,
        fontSize=18,
        leading=22,
        textColor=colors.HexColor('#6366f1'),
        alignment=1,
        spaceAfter=15
    )
    
    meta_style = ParagraphStyle(
        'PaperMeta',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#94a3b8'),
        alignment=1,
        spaceAfter=25
    )
    
    q_text_style = ParagraphStyle(
        'QuestionText',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=11,
        leading=16,
        textColor=colors.HexColor('#0f172a'),
        spaceAfter=8
    )
    
    opt_style = ParagraphStyle(
        'OptionText',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#334155'),
        leftIndent=15,
        spaceAfter=4
    )
    
    ans_style = ParagraphStyle(
        'AnswerText',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#10b981'),
        leftIndent=15,
        spaceAfter=15
    )
    
    story = []
    story.append(Paragraph(paper_title, title_style))
    story.append(Paragraph(f"TalathiIQ - Smart Preparation. Smarter Results.<br/>Total Questions: {len(questions)} | Duration: {len(questions) * 36 // 60} Minutes", meta_style))
    story.append(Spacer(1, 10))
    
    for i, q in enumerate(questions):
        q_elements = []
        q_text = f"<b>Q{i+1}. {q.get('question', '')}</b>"
        q_elements.append(Paragraph(q_text, q_text_style))
        
        for j, opt in enumerate(q.get('options', [])):
            opt_letter = chr(65 + j)
            opt_text = f"{opt_letter}) {opt}"
            q_elements.append(Paragraph(opt_text, opt_style))
            
        ans_idx = q.get('answer', 0)
        ans_letter = chr(65 + ans_idx)
        correct_opt = q.get('options', [])[ans_idx] if ans_idx < len(q.get('options', [])) else ''
        ans_text = f"<b>Correct Answer: {ans_letter}</b> ({correct_opt})"
        q_elements.append(Spacer(1, 4))
        q_elements.append(Paragraph(ans_text, ans_style))
        q_elements.append(Spacer(1, 10))
        
        story.append(KeepTogether(q_elements))
        
    doc.build(story)
    buffer.seek(0)
    return buffer

@app.route('/download-pyq-pdf/<paper_id>')
def download_pyq_pdf(paper_id):
    paper = next((p for p in PYQ_PAPERS if p['id'] == paper_id), None)
    if not paper:
        return "Paper Not Found", 404
        
    questions = load_questions()
    pyq_questions = [q for q in questions if q.get('source') == 'PYQ']
    paper_qs = pyq_questions[paper['slice_start']:paper['slice_end']]
    
    if not paper_qs:
        return "No questions found for this paper", 404
        
    pdf_buffer = generate_paper_pdf(paper['title'], paper_qs)
    filename = f"{paper['title'].replace(' ', '_')}.pdf"
    return send_file(
        pdf_buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=filename
    )


if __name__ == '__main__':
    # Running Flask app on port 5000
    app.run(debug=True, host='0.0.0.0', port=5000)
