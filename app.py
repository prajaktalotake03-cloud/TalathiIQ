import os
import sys
import json
import sqlite3

# Reconfigure stdout for Unicode support on Windows console
sys.stdout.reconfigure(encoding='utf-8')
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
            stage TEXT DEFAULT 'Prelims',
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    # Check if 'academy' column exists, otherwise alter table
    try:
        conn.execute('SELECT academy FROM study_materials LIMIT 1')
    except sqlite3.OperationalError:
        conn.execute('ALTER TABLE study_materials ADD COLUMN academy TEXT DEFAULT "Standard Academy"')
        conn.commit()

    # Check if 'stage' column exists, otherwise alter table
    try:
        conn.execute('SELECT stage FROM study_materials LIMIT 1')
    except sqlite3.OperationalError:
        conn.execute("ALTER TABLE study_materials ADD COLUMN stage TEXT DEFAULT 'Prelims'")
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
    conn.execute('''
        CREATE TABLE IF NOT EXISTS download_info (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            mobile TEXT NOT NULL,
            district TEXT NOT NULL,
            submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS imp_topics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            subject TEXT NOT NULL,
            file_name TEXT NOT NULL,
            file_data BLOB NOT NULL,
            description TEXT,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()


def seed_pdf_notes():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    data_dir = os.path.join(app.root_path, 'data')
    if not os.path.exists(data_dir):
        conn.close()
        return
        
    seeded_count = 0
    updated_count = 0
    for filename in os.listdir(data_dir):
        if filename.lower().endswith('.pdf'):
            filepath = os.path.join(data_dir, filename)
            try:
                with open(filepath, 'rb') as f:
                    file_data = f.read()
                    title = filename.replace('_', ' ').replace('.pdf', '')
                    fn_lower = filename.lower()
                    
                    # Determine Academy
                    ignite_files = {
                        "indian polity notes.pdf",
                        "maharashtra geography notes (1).pdf",
                        "maharashtra history notes.pdf",
                        "mpsc maths reasoning marathi book.pdf",
                        "phy-che book notes final.pdf"
                    }
                    prajakta_files = {
                        "economics_notes_logo_added.pdf",
                        "geography_notes_final_bold_border.pdf",
                        "इतिहास_notes_economics_style_border.pdf",
                        "भारतीय_संविधान_final_no_stars (1).pdf",
                        "science.pdf"
                    }
                    if "ignite" in fn_lower or fn_lower in ignite_files:
                        academy = "Ignite Academy Notes"
                    elif "prajakta" in fn_lower or fn_lower in prajakta_files:
                        academy = "Prajakta Lotake Notes"
                    elif "pyq" in fn_lower or "analysis" in fn_lower:
                        academy = "PYQ"
                    else:
                        academy = "Standard Academy"
                        
                    # Determine Subject
                    if "history" in fn_lower or "इतिहास" in fn_lower or "प्राचीन" in fn_lower:
                        subject = "History"
                    elif "geography" in fn_lower or "भूगोल" in fn_lower or "geo" in fn_lower:
                        if academy == "Prajakta Lotake Notes":
                            subject = "Geography & General Science"
                        else:
                            subject = "Geography"
                    elif "science" in fn_lower or "विज्ञान" in fn_lower or "biology" in fn_lower or "physics" in fn_lower or "chemistry" in fn_lower or "phy" in fn_lower or "che" in fn_lower:
                        if academy == "Prajakta Lotake Notes":
                            subject = "Geography & General Science"
                        else:
                            subject = "General Science"
                    elif "economics" in fn_lower or "अर्थशास्त्र" in fn_lower or "eco" in fn_lower:
                        subject = "Economics"
                    elif "constitution" in fn_lower or "polity" in fn_lower or "संविधान" in fn_lower or "राज्यशास्त्र" in fn_lower:
                        subject = "Polity"
                    elif "marathi" in fn_lower or "मराठी" in fn_lower:
                        subject = "Marathi"
                    elif "english" in fn_lower or "eng" in fn_lower or "इंग्रजी" in fn_lower:
                        subject = "English"
                    elif "math" in fn_lower or "reasoning" in fn_lower or "बुद्धिमत्ता" in fn_lower or "गणित" in fn_lower:
                        subject = "Mathematics"
                    elif "current" in fn_lower or "चालू घडामोडी" in fn_lower or "ca" in fn_lower:
                        subject = "Current Affairs"
                    else:
                        subject = "General Knowledge"
                        
                    # Determine Stage
                    if "mains" in fn_lower or "मुख्य" in fn_lower:
                        stage = "Mains"
                    else:
                        stage = "Prelims"
                        
                    existing = conn.execute(
                        'SELECT id FROM study_materials WHERE file_name = ?',
                        (filename,)
                    ).fetchone()
                    
                    if existing:
                        conn.execute(
                            'UPDATE study_materials SET title = ?, subject = ?, academy = ?, stage = ? WHERE file_name = ?',
                            (title, subject, academy, stage, filename)
                        )
                        print(f"Successfully updated note category: {filename}")
                    else:
                        conn.execute(
                            'INSERT INTO study_materials (title, subject, file_name, file_data, academy, stage) VALUES (?, ?, ?, ?, ?, ?)',
                            (title, subject, filename, file_data, academy, stage)
                        )
                        print(f"Successfully seeded new note: {filename}")
                    conn.commit()
            except Exception as e:
                print(f"Error seeding note {filename}: {e}")
    conn.close()


# Initialize DB on startup
init_db()
seed_pdf_notes()

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

NEWS_ARTICLES = [
    {
        "category": "Maharashtra",
        "cat_slug": "maharashtra",
        "date": "August 15, 2026",
        "title": "Maharashtra launches 'Pramod Mahajan Skill Development Scheme' phase-II",
        "title_mr": "महाराष्ट्र शासनातर्फे 'प्रमोद महाजन कौशल्य विकास योजना' टप्पा-२ चा शुभारंभ",
        "content": "Under this phase, the government aims to establish skill centers in more than 500 rural blocks to empower rural youth with employment and self-employment training. This scheme targets the training of over 2 lakh candidates annually with active integration of technology partners.",
        "content_mr": "या टप्प्यांतर्गत, ग्रामीण तरुणांना रोजगार आणि स्वयंरोजगार प्रशिक्षण देऊन सक्षम करण्यासाठी ५०० हून अधिक ग्रामीण ब्लॉकमध्ये कौशल्य केंद्रे स्थापन करण्याचे शासनाचे उद्दिष्ट आहे. हे अभियान तंत्रज्ञान भागीदारांच्या सक्रिय सहभागासह वर्षाला २ लाख उमेदवारांना प्रशिक्षित करेल."
    },
    {
        "category": "India",
        "cat_slug": "india",
        "date": "August 14, 2026",
        "title": "ISRO launches new earth observation satellite EOS-09",
        "title_mr": "इस्रोकडून नवीन पृथ्वी निरीक्षण उपग्रह 'EOS-09' चे यशस्वी प्रक्षेपण",
        "content": "The Indian Space Research Organisation (ISRO) successfully injected the Earth Observation Satellite (EOS-09) into its orbit using the SSLV-D4 launcher from Sriharikota. The satellite will provide high-resolution imagery for agricultural monitoring, forestry, hydrology, and disaster management.",
        "content_mr": "भारतीय अंतराळ संशोधन संस्थेने (ISRO) श्रीहरीकोटा येथून SSLV-D4 प्रक्षेपकाचा वापर करून पृथ्वी निरीक्षण उपग्रह (EOS-09) त्याच्या कक्षेत यशस्वीरित्या प्रस्थापित केला. हा उपग्रह शेती नियंत्रण, वनीकरण, जलविज्ञान आणि आपत्ती व्यवस्थापनासाठी उच्च-रिझोल्यूशन चित्रे प्रदान करेल."
    },
    {
        "category": "Gov Schemes",
        "cat_slug": "schemes",
        "date": "August 12, 2026",
        "title": "CM Majhi Ladki Bahin Yojana Updates: Over 1.5 Crore Applications Approved",
        "title_mr": "मुख्यमंत्री माझी लाडकी बहीण योजना अपडेट: १.५ कोटींहून अधिक अर्ज मंजूर",
        "content": "The Maharashtra state government announced that more than 1.5 crore eligible women have successfully registered under the Majhi Ladki Bahin Yojana. Beneficiaries will receive a direct benefit transfer of 1,500 rupees per month. The verification process has been fully digitized to speed up approvals.",
        "content_mr": "महाराष्ट्र सरकारने जाहीर केले की माझी लाडकी बहीण योजनेअंतर्गत १.५ कोटींहून अधिक पात्र महिलांची यशस्वी नोंदणी झाली आहे. लाभार्थी महिलांना दरमहा १५०० रुपयांचे थेट बँक हस्तांतरण (DBT) मिळेल. मंजुरी वेगवान करण्यासाठी पडताळणी पूर्णपणे डिजिटल करण्यात आली आहे."
    },
    {
        "category": "Awards",
        "cat_slug": "awards",
        "date": "August 10, 2026",
        "title": "Lata Mangeshkar Award 2026 Announced",
        "title_mr": "गानकोकिळा लता मंगेशकर पुरस्कार २०२६ ची घोषणा",
        "content": "The Maharashtra state government has declared the prestigious Lata Mangeshkar Award for Lifetime Achievement in music to a veteran classical vocalist. The award consists of a cash prize of 5 lakh rupees, a citation, and a memento to be presented at a cultural event in Mumbai next month.",
        "content_mr": "महाराष्ट्र सरकारने शास्त्रीय संगीतातील ज्येष्ठ गायकाला संगीत क्षेत्रातील जीवनगौरव योगदानाबद्दल प्रतिष्ठित लता मंगेशकर पुरस्कार जाहीर केला आहे. या पुरस्कारामध्ये ५ लाख रुपये रोख, सन्मानपत्र आणि स्मृतीचिन्ह यांचा समावेश आहे."
    },
    {
        "category": "Sports",
        "cat_slug": "sports",
        "date": "August 08, 2026",
        "title": "National Games 2026 to be hosted in Maharashtra",
        "title_mr": "२०२६ च्या राष्ट्रीय क्रीडा स्पर्धांचे यजमानपद महाराष्ट्राला",
        "content": "The Indian Olympic Association has officially confirmed that the upcoming National Games will take place across Mumbai, Pune, and Nagpur. The state is developing sports infrastructures to match global athletic standards, expecting participation from over 10,000 athletes.",
        "content_mr": "भारतीय ऑलिम्पिक असोसिएशनने अधिकृतपणे पुष्टी केली आहे की आगामी राष्ट्रीय क्रीडा स्पर्धा मुंबई, पुणे आणि नागपूर येथे आयोजित केल्या जातील. जागतिक क्रीडा मानकांशी सुसंगत क्रीडा पायाभूत सुविधा राज्य विकसित करत आहे."
    },
    {
        "category": "Important Days",
        "cat_slug": "days",
        "date": "August 09, 2026",
        "title": "August Kranti Din observed on 9th August",
        "title_mr": "९ ऑगस्ट रोजी क्रांती दिन साजरा",
        "content": "The nation observed August Kranti Din, commemorating the anniversary of the Quit India Movement launched in 1942 under Mahatma Gandhi. Tributes were paid to freedom fighters at Kranti Maidan (Gowalia Tank) in Mumbai, where the historic resolution was passed.",
        "content_mr": "महात्मा गांधींच्या नेतृत्वाखाली १९४२ मध्ये सुरू झालेल्या भारत छोडो आंदोलनाच्या वर्धापन दिनानिमित्त देशाने ऑगस्ट क्रांती दिन पाळला. मुंबईतील ऑगस्ट क्रांती मैदानावर स्वातंत्र्यसैनिकांना आदरांजली वाहण्यात आली."
    },
    {
        "category": "International",
        "cat_slug": "international",
        "date": "August 05, 2026",
        "title": "UN Climate Summit 2026 sets new net-zero targets",
        "title_mr": "संयुक्त राष्ट्र हवामान शिखर परिषद २०२६ चे नवीन उद्दिष्ट निश्चित",
        "content": "World leaders gathered in Geneva for the COP31 preparatory assembly to outline tighter emissions thresholds. Emerging economies requested financial assistance and green tech sharing models from developed countries to meet their sustainability timelines.",
        "content_mr": "कडक उत्सर्जन मर्यादा निश्चित करण्यासाठी जागतिक नेते जिनिव्हा येथे COP31 च्या तयारी बैठकीसाठी जमले होते. उदयोन्मुख अर्थव्यवस्थांनी विकसित देशांकडून हरित तंत्रज्ञान भागीदारी आणि आर्थिक मदतीची मागणी केली."
    },
    {
        "category": "Economy",
        "cat_slug": "economy",
        "date": "August 01, 2026",
        "title": "RBI monetary policy maintains repo rate at 6.50%",
        "title_mr": "रिझर्व्ह बँकेचे मौद्रिक धोरण: रेपो दर ६.५०% वर कायम",
        "content": "The Monetary Policy Committee (MPC) of the Reserve Bank of India decided to keep the policy repo rate unchanged. RBI Governor cited retail inflation stability and robust GDP projection for the quarter as the primary factors for the status quo.",
        "content_mr": "भारतीय रिझर्व्ह बँकेच्या मौद्रिक धोरण समितीने (MPC) रेपो दर बदल न करता कायम ठेवण्याचा निर्णय घेतला. आरबीआय गव्हर्नर यांनी किरकोळ महागाईतील स्थिरता आणि तिमाहीसाठी मजबूत जीडीपी अंदाजाचे दाखले दिले."
    }
]

@app.route('/current-affairs')
def current_affairs():
    return render_template('current-affairs.html', articles=NEWS_ARTICLES)

@app.route('/current-affairs/book')
def current_affairs_book():
    return render_template('ca-book.html', articles=NEWS_ARTICLES)

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
        if source.lower() != 'all':
            questions = [q for q in questions if q.get('source', 'Standard').lower() == source.lower()]
    else:
        questions = [q for q in questions if q.get('source', 'Standard').lower() == 'standard']
        
    # Filter by difficulty
    if difficulty:
        if difficulty.lower() != 'all':
            diff_val = 'Hard' if difficulty.lower() == 'hardest' else difficulty.capitalize()
            questions = [q for q in questions if q.get('difficulty', 'Medium').capitalize() == diff_val]
        
    # Filter by subject
    if subject and subject.lower() != 'all':
        subj_lower = subject.lower()
        if 'geography' in subj_lower or 'भूगोल' in subj_lower:
            questions = [q for q in questions if q.get('subject', '').lower() == 'geography' or 'geography' in q.get('topic', '').lower() or 'भूगोल' in q.get('topic', '').lower()]
        elif 'history' in subj_lower or 'इतिहास' in subj_lower:
            questions = [q for q in questions if q.get('subject', '').lower() == 'history' or 'history' in q.get('topic', '').lower() or 'इतिहास' in q.get('topic', '').lower() or 'सुधारक' in q.get('topic', '').lower()]
        elif 'polity' in subj_lower or 'राज्यशास्त्र' in subj_lower or 'संविधान' in subj_lower:
            questions = [q for q in questions if q.get('subject', '').lower() == 'polity' or 'polity' in q.get('topic', '').lower() or 'राज्यशास्त्र' in q.get('topic', '').lower() or 'संविधान' in q.get('topic', '').lower() or 'न्यायव्यवस्था' in q.get('topic', '').lower() or 'संसद' in q.get('topic', '').lower() or 'पंचायतराज' in q.get('topic', '').lower()]
        elif 'rti' in subj_lower or 'service' in subj_lower or 'हक्क' in subj_lower:
            questions = [q for q in questions if 'rti' in q.get('topic', '').lower() or 'rts' in q.get('topic', '').lower() or 'हक्क' in q.get('topic', '').lower() or 'माहिती' in q.get('topic', '').lower()]
        elif 'economics' in subj_lower or 'अर्थशास्त्र' in subj_lower:
            questions = [q for q in questions if q.get('subject', '').lower() == 'economics' or 'economics' in q.get('topic', '').lower() or 'अर्थशास्त्र' in q.get('topic', '').lower() or 'योजना' in q.get('topic', '').lower() or 'वित्त' in q.get('topic', '').lower()]
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
            q["source"] = "PYQ"
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
    stage = request.args.get('stage', 'Prelims')
    conn = get_db_connection()
    materials = conn.execute(
        'SELECT id, title, subject, file_name, uploaded_at, academy, stage FROM study_materials WHERE stage = ? ORDER BY uploaded_at DESC',
        (stage,)
    ).fetchall()
    requests_list = conn.execute(
        'SELECT name, request_text, submitted_at FROM material_requests ORDER BY submitted_at DESC'
    ).fetchall()
    
    # Fetch IMP topics
    imp_topics_db = []
    try:
        imp_topics_db = conn.execute(
            'SELECT id, title, subject, file_name, description, uploaded_at FROM imp_topics ORDER BY uploaded_at DESC'
        ).fetchall()
    except sqlite3.OperationalError:
        # Table might not be created yet if startup hasn't run the updated init_db()
        pass
        
    conn.close()
    
    # Group all materials into Prajakta Lotake notes vs other notes vs PYQs vs Ignite Notes
    prajakta_notes = {}
    other_notes = {}
    pyq_notes = {}
    ignite_notes = {}
    for item in materials:
        subject = item['subject']
        academy_name = item['academy'] or ''
        title_lower = item['title'].lower()
        file_name_lower = item['file_name'].lower()
        academy_lower = academy_name.lower()
        
        is_pyq = (stage == 'Mains') or ('pyq' in title_lower or 'pyq' in file_name_lower or 'pyq' in academy_lower)
        
        if is_pyq:
            if subject not in pyq_notes:
                pyq_notes[subject] = []
            pyq_notes[subject].append(item)
        elif 'prajakta' in academy_lower:
            if subject not in prajakta_notes:
                prajakta_notes[subject] = []
            prajakta_notes[subject].append(item)
        elif 'ignite' in academy_lower or 'ignite' in title_lower or 'ignite' in file_name_lower:
            if subject not in ignite_notes:
                ignite_notes[subject] = []
            ignite_notes[subject].append(item)
        else:
            if subject not in other_notes:
                other_notes[subject] = []
            other_notes[subject].append(item)
        
    # Group all IMP topics by subject
    imp_topics = {}
    for item in imp_topics_db:
        subject = item['subject']
        if subject not in imp_topics:
            imp_topics[subject] = []
        imp_topics[subject].append(item)
            
    return render_template(
        'study-materials.html', 
        prajakta_notes=prajakta_notes,
        other_notes=other_notes,
        pyq_notes=pyq_notes,
        ignite_notes=ignite_notes,
        imp_topics=imp_topics,
        requests_list=requests_list,
        active_stage=stage
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
    stage = request.form.get('stage') or 'Prelims'
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
        'INSERT INTO study_materials (title, subject, file_name, file_data, academy, stage) VALUES (?, ?, ?, ?, ?, ?)',
        (title, subject, file_name, file_data, academy, stage)
    )
    conn.commit()
    conn.close()
    
    return redirect(url_for('study_materials', stage=stage))


@app.route('/admin/upload-imp-topic', methods=['POST'])
def upload_imp_topic():
    passcode = request.form.get('passcode')
    if passcode != 'admin123':
        return "Unauthorized: Invalid Passcode", 401
        
    title = request.form.get('title')
    subject = request.form.get('subject')
    description = request.form.get('description') or ''
    file = request.files.get('file')
    
    if not title or not subject or not file or file.filename == '':
        return "Bad Request: Missing fields or file", 400
        
    allowed_extensions = {'.png', '.jpg', '.jpeg', '.webp', '.gif'}
    ext = os.path.splitext(file.filename.lower())[1]
    if ext not in allowed_extensions:
        return "Bad Request: Only image files are allowed", 400
        
    file_name = file.filename
    file_data = file.read()
    
    conn = get_db_connection()
    conn.execute(
        'INSERT INTO imp_topics (title, subject, file_name, file_data, description) VALUES (?, ?, ?, ?, ?)',
        (title, subject, file_name, file_data, description)
    )
    conn.commit()
    conn.close()
    
    return redirect(url_for('study_materials') + '?tab=imp')


@app.route('/view-imp-image/<int:topic_id>')
def view_imp_image(topic_id):
    conn = get_db_connection()
    topic = conn.execute(
        'SELECT file_name, file_data FROM imp_topics WHERE id = ?',
        (topic_id,)
    ).fetchone()
    conn.close()
    
    if topic is None:
        return "Not Found", 404
        
    ext = os.path.splitext(topic['file_name'].lower())[1]
    mimetype = 'image/png'
    if ext in ['.jpg', '.jpeg']:
        mimetype = 'image/jpeg'
    elif ext == '.webp':
        mimetype = 'image/webp'
    elif ext == '.gif':
        mimetype = 'image/gif'
        
    return send_file(
        io.BytesIO(topic['file_data']),
        mimetype=mimetype,
        download_name=topic['file_name']
    )


@app.route('/download-imp-image/<int:topic_id>')
def download_imp_image(topic_id):
    conn = get_db_connection()
    topic = conn.execute(
        'SELECT file_name, file_data FROM imp_topics WHERE id = ?',
        (topic_id,)
    ).fetchone()
    conn.close()
    
    if topic is None:
        return "Not Found", 404
        
    return send_file(
        io.BytesIO(topic['file_data']),
        mimetype='application/octet-stream',
        as_attachment=True,
        download_name=topic['file_name']
    )



@app.route('/submit-download-info', methods=['POST'])
def submit_download_info():
    data = request.get_json() or {}
    name = data.get('name')
    mobile = data.get('mobile')
    district = data.get('district')
    
    if not name or not mobile or not district:
        return jsonify({"success": False, "error": "All fields are required"}), 400
        
    conn = get_db_connection()
    conn.execute(
        'INSERT INTO download_info (name, mobile, district) VALUES (?, ?, ?)',
        (name, mobile, district)
    )
    conn.commit()
    conn.close()
    
    session['download_info_submitted'] = True
    return jsonify({"success": True})


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
        as_attachment=False,
        download_name=material['file_name']
    )


@app.route('/download-all-pdfs')
def download_all_pdfs():
    import zipfile
    conn = get_db_connection()
    materials = conn.execute(
        'SELECT file_name, file_data FROM study_materials'
    ).fetchall()
    conn.close()
    
    if not materials:
        return "No study notes found to download", 404
        
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        used_names = set()
        for item in materials:
            orig_name = item['file_name'] or "untitled.pdf"
            file_data = item['file_data']
            
            # De-duplicate filename in ZIP
            name, ext = os.path.splitext(orig_name)
            counter = 1
            unique_name = orig_name
            while unique_name in used_names:
                unique_name = f"{name} ({counter}){ext}"
                counter += 1
                
            used_names.add(unique_name)
            zip_file.writestr(unique_name, file_data)
            
    zip_buffer.seek(0)
    return send_file(
        zip_buffer,
        mimetype='application/zip',
        as_attachment=True,
        download_name='TalathiIQ_All_Study_Notes.zip'
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




@app.route('/download-custom-pdf')
def download_custom_pdf():
    ids_str = request.args.get('ids')
    title = request.args.get('title', 'Custom_Test_Paper')
    if not ids_str:
        return "Missing question IDs", 400
        
    try:
        ids = [int(x) for x in ids_str.split(',')]
    except ValueError:
        return "Invalid question IDs format", 400
        
    questions = load_questions()
    selected_qs = [q for q in questions if q.get('id') in ids]
    
    # Sort them in the order of requested ids to preserve test layout
    selected_qs.sort(key=lambda q: ids.index(q.get('id')))
    
    if not selected_qs:
        return "No questions found for the provided IDs", 404
        
    pdf_buffer = generate_paper_pdf("Talathi Bharti Mock Test - Answer Key", selected_qs)
    filename = f"{title}.pdf"
    return send_file(
        pdf_buffer,
        mimetype='application/pdf',
        as_attachment=False,
        download_name=filename
    )


@app.route('/current-affairs/book/download')
def current_affairs_book_download():
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=54, leftMargin=54, topMargin=54, bottomMargin=54)
    
    styles = getSampleStyleSheet()
    font_name = 'Nirmala' if HAS_NIRMALA else 'Helvetica'
    
    title_style = ParagraphStyle(
        'BookTitle',
        parent=styles['Heading1'],
        fontName=font_name,
        fontSize=22,
        leading=26,
        textColor=colors.HexColor('#6366f1'),
        alignment=1,
        spaceAfter=10
    )
    
    meta_style = ParagraphStyle(
        'BookMeta',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=11,
        leading=15,
        textColor=colors.HexColor('#64748b'),
        alignment=1,
        spaceAfter=30
    )
    
    heading_style = ParagraphStyle(
        'ArticleHeading',
        parent=styles['Heading2'],
        fontName=font_name,
        fontSize=14,
        leading=18,
        textColor=colors.HexColor('#0f172a'),
        spaceBefore=15,
        spaceAfter=10
    )
    
    content_mr_style = ParagraphStyle(
        'ContentMr',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=10,
        leading=15,
        textColor=colors.HexColor('#334155'),
        spaceAfter=8
    )
    
    content_en_style = ParagraphStyle(
        'ContentEn',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#475569'),
        leftIndent=15,
        spaceAfter=20
    )
    
    story = []
    story.append(Paragraph("चालू घडामोडी २०२६ ई-बुक", title_style))
    story.append(Paragraph("TalathiIQ Premium Current Affairs Booklet<br/>संकलन: Prajakta Lotake", meta_style))
    story.append(Spacer(1, 10))
    
    for article in NEWS_ARTICLES:
        story.append(Paragraph(article.get('title_mr', ''), heading_style))
        story.append(Paragraph(article.get('content_mr', ''), content_mr_style))
        story.append(Paragraph(f"<b>English Summary:</b> {article.get('content', '')}", content_en_style))
        story.append(Spacer(1, 10))
        
    doc.build(story)
    buffer.seek(0)
    
    return send_file(
        buffer,
        mimetype='application/pdf',
        as_attachment=False,
        download_name='TalathiIQ_Current_Affairs_Booklet.pdf'
    )


@app.route('/api/chat', methods=['POST'])
def api_chat():
    data = request.get_json() or {}
    message = data.get('message', '').strip()
    if not message:
        return jsonify({"response": "कृपया तुमचा प्रश्न टाईप करा! (Please type your question!)"})
        
    response_text = get_chat_response(message)
    return jsonify({"response": response_text})

def get_chat_response(message):
    msg = message.lower()
    
    # 1. Fundamental Rights
    if "fundamental" in msg or "حق" in msg or "हक्क" in msg or "right" in msg:
        return """<strong>भारतीय संविधानातील मूलभूत हक्क (Fundamental Rights - Part III):</strong><br><br>
        भारतीय राज्यघटनेच्या <strong>भाग ३ (कलम १२ ते ३५)</strong> मध्ये नागरिकांना ६ मूलभूत हक्क देण्यात आले आहेत:<br>
        1. <strong>समानतेचा हक्क (Right to Equality)</strong> - कलम १४ ते १८<br>
        2. <strong>स्वातंत्र्याचा हक्क (Right to Freedom)</strong> - कलम १९ ते २२<br>
        3. <strong>शोषणाविरुद्धचा हक्क (Right against Exploitation)</strong> - कलम २३ व २४<br>
        4. <strong>धार्मिक स्वातंत्र्याचा हक्क (Right to Freedom of Religion)</strong> - कलम २५ ते २८<br>
        5. <strong>सांस्कृतिक आणि शैक्षणिक हक्क (Cultural & Educational Rights)</strong> - कलम २९ व ३०<br>
        6. <strong>घटनात्मक उपाययोजनांचा हक्क (Right to Constitutional Remedies)</strong> - कलम ३२ (डॉ. आंबेडकरांनी या कलमाला 'घटनेचा आत्मा' म्हटले आहे).<br><br>
        <em>💡 टिप: मालमत्तेचा हक्क (कलम ३१) ४४ व्या घटनादुरुस्तीने (१९७८) मूलभूत हक्कांमधून वगळण्यात आला असून तो आता कलम ३००A नुसार कायदेशीर हक्क आहे.</em>"""

    # 2. Geography MCQs
    elif "geography" in msg or "भूगोल" in msg or "mcq" in msg or "प्रश्न" in msg:
        return """<strong>भूगोल सराव प्रश्न (Geography Practice Questions):</strong><br><br>
        <strong>Q1. महाराष्ट्रातील सर्वात उंच शिखर कोणते आहे?</strong><br>
        A) साल्हेर &nbsp;&nbsp; B) महाबळेश्वर &nbsp;&nbsp; C) कळसूबाई &nbsp;&nbsp; D) हरिश्चंद्रगड<br>
        👉 <em>उत्तर: C) कळसूबाई (उंची: १६४६ मीटर)</em><br><br>
        <strong>Q2. गोदावरी नदीचा उगम महाराष्ट्रात कोठे होतो?</strong><br>
        A) भीमाशंकर &nbsp;&nbsp; B) त्र्यंबकेश्वर &nbsp;&nbsp; C) महाबळेश्वर &nbsp;&nbsp; D) मुलताई<br>
        👉 <em>उत्तर: B) त्र्यंबकेश्वर (नाशिक जिल्हा)</em><br><br>
        <strong>Q3. क्षेत्रफळाच्या दृष्टीने महाराष्ट्रातील सर्वात मोठा जिल्हा कोणता आहे?</strong><br>
        A) पुणे &nbsp;&nbsp; B) अहिल्यानगर (अहमदनगर) &nbsp;&nbsp; C) नाशिक &nbsp;&nbsp; D) सोलापूर<br>
        👉 <em>उत्तर: B) अहिल्यानगर</em><br><br>
        💡 <em>अधिक सराव करण्यासाठी, आपल्या मुख्य मेनू मधील <strong>AI MCQs</strong> किंवा <strong>Mock Tests</strong> विभाग वापरा!</em>"""

    # 3. Maharashtra History
    elif "history" in msg or "इतिहास" in msg or "maharashtra" in msg:
        return """<strong>महाराष्ट्राचा इतिहास - महत्वाचे मुद्दे (Maharashtra History Revision):</strong><br><br>
        1. <strong>प्राचीन काळ:</strong> सातवाहनांचे राज्य (राजधानी: पैठण), वाकाटक घराणे, राष्ट्रकूट आणि यादव घराणे (राजधानी: देवगिरी).<br>
        2. <strong>मध्ययुगीन काळ:</strong> छत्रपती शिवाजी महाराज यांनी १६७४ मध्ये हिंदवी स्वराज्याची स्थापना केली आणि रायगडावर राज्याभिषेक केला.<br>
        3. <strong>आधुनिक समाजसुधारक:</strong><br>
        &nbsp;&nbsp; • <strong>महात्मा ज्योतिराव फुले:</strong> १८७३ मध्ये सत्यशोधक समाजाची स्थापना केली. मुलींची पहिली शाळा पुण्यात सुरू केली.<br>
        &nbsp;&nbsp; • <strong>राजर्षी छत्रपती शाहू महाराज:</strong> कोल्हापूर संस्थानात मागासवर्गीयांना ५०% आरक्षण दिले, प्राथमिक शिक्षण मोफत केले.<br>
        &nbsp;&nbsp; • <strong>भारतरत्न डॉ. बाबासाहेब आंबेडकर:</strong> महाडचा चवदार तळे सत्याग्रह (१९२७) आणि काळाराम मंदिर सत्याग्रह केला. मूकनायक व बहिष्कृत भारत वृत्तपत्रे सुरू केली.<br><br>
        🎯 <em>या समाजसुधारकांच्या कार्यावर तलाठी परीक्षेत नक्की ३-४ प्रश्न विचारले जातात!</em>"""

    # 4. Wrong Answer
    elif "wrong" in msg or "चुकलेले" in msg or "चूक" in msg or "explain" in msg:
        return """<strong>चुकलेल्या प्रश्नांचे विश्लेषण व स्मार्ट रिव्हिजन (Analyzing Mistakes):</strong><br><br>
        * <strong>रिव्हिजन ट्रॅकर:</strong> तुम्ही सोडवलेल्या सराव चाचण्यांमध्ये जे प्रश्न चुकतात, ते आमचे सिस्टम आपोआप रेकॉर्ड करते.<br>
        * <strong>कसे तपासायचे?</strong>: मुख्य नेव्हिगेशन बार मधील <strong>Smart Revision</strong> (स्मार्ट रिव्हिजन) या पेजवर जा.<br>
        * तिथे तुम्हाला तुमचे सर्व चुकलेले प्रश्न एकत्र मिळतील. तुम्ही ते पुन्हा सोडवू शकता आणि कन्सेप्ट क्लिअर झाल्यावर यादीतून काढून टाकू (Clear) करू शकता.<br>
        * <strong>महत्त्वाची टीप:</strong> परीक्षेच्या शेवटच्या दिवसांत नवीन वाचण्यापेक्षा स्वतःच्या चुका सुधारणे जास्त महत्त्वाचे असते! 📖🎯"""

    # 5. Study Plan
    elif "plan" in msg or "नियोजन" in msg or "time" in msg or "शेड्युल" in msg:
        return """<strong>७ दिवसांचे तलाठी भरती सराव नियोजन (7-Day Study Plan):</strong><br><br>
        * <strong>Day 1 (मराठी व्याकरण):</strong> समानार्थी, विरुद्धार्थी शब्द, संधी आणि प्रयोग सराव.<br>
        * <strong>Day 2 (English Grammar):</strong> Tenses, Change the Voice, Direct-Indirect, Spot the Error.<br>
        * <strong>Day 3 (अंकगणित):</strong> शेकडेवारी, नफा-तोटा, काळ-काम-वेग आणि सरळव्याज.<br>
        * <strong>Day 4 (बुद्धिमत्ता चाचणी):</strong> नातेसंबंध, दिशा ज्ञान, अक्षरमाला व संख्यामाला.<br>
        * <strong>Day 5 (सामान्य ज्ञान):</strong> महाराष्ट्राचा भूगोल, इतिहास आणि राज्यघटना प्रमुख कलमे.<br>
        * <strong>Day 6 (चालू घडामोडी):</strong> मागील ६ महिन्यांतील प्रमुख चालू घडामोडी आणि सरकारी योजना.<br>
        * <strong>Day 7 (मॉक टेस्ट):</strong> २ पूर्ण मॉक टेस्ट (१०० प्रश्न) सोडवून वेळेचे नियोजन तपासा.<br><br>
        🔥 <em>सातत्य ठेवा, दररोज किमान ६-८ तास अभ्यास आणि सराव चाचण्या आवश्यक आहेत!</em>"""

    # 6. Syllabus
    elif "syllabus" in msg or "अभ्यासक्रम" in msg or "format" in msg:
        return """<strong>तलाठी भरती परीक्षा अभ्यासक्रम (Talathi Bharti Exam Syllabus):</strong><br><br>
        एकूण प्रश्न: <strong>१००</strong> | एकूण गुण: <strong>२००</strong> (प्रत्येक प्रश्नाला २ गुण, नकारात्मक गुणपद्धती नसते)<br><br>
        1. <strong>मराठी व्याकरण व शब्दसंग्रह</strong> (२५ प्रश्न - ५० गुण)<br>
        2. <strong>English Grammar & Vocabulary</strong> (२५ प्रश्न - ५० गुण)<br>
        3. <strong>अंकगणित व बुद्धिमत्ता चाचणी</strong> (२५ प्रश्न - ५० गुण)<br>
        4. <strong>सामान्य ज्ञान (GK)</strong> (२५ प्रश्न - ५० गुण - इतिहास, भूगोल, विज्ञान, राज्यघटना व चालू घडामोडी)<br><br>
        ⏱️ <em>वेळ मर्यादा: २ तास (१२० मिनिटे). सराव करण्यासाठी <strong>Mock Tests</strong> चा वापर करा!</em>"""

    # 7. Greetings
    elif "hello" in msg or "hi" in msg or "hey" in msg or "नमस्कार" in msg or "welcome" in msg:
        return """नमस्कार! मी तुमचा <strong>TalathiIQ AI Mentor</strong> आहे. <br><br>
        मी तुम्हाला तलाठी भरती परीक्षेची तयारी, अभ्यासक्रम (Syllabus), ७ दिवसांचे नियोजन (Study Plan) किंवा विषयांचे स्पष्टीकरण मिळवण्यात मदत करू शकतो. <br><br>
        कृपया तुमचा अभ्यासविषयक प्रश्न विचारा किंवा डाव्या बाजूला दिलेल्या पर्यायांपैकी एकावर क्लिक करा! 😊🎯"""

    # Default Fallback
    else:
        return f"""<strong>TalathiIQ AI Mentor Response:</strong><br><br>
        तुम्ही विचारलेला प्रश्न: <em>"{message}"</em><br><br>
        या प्रश्नाचे उत्तर मिळवण्यासाठी तुम्ही आमच्या <strong>Syllabus</strong> आणि <strong>Study Notes</strong> या विभागांना भेट देऊ शकता. <br><br>
        तलाठी परीक्षेमध्ये उत्तम यश मिळवण्यासाठी तुम्ही खालील सराव सुरू ठेवा:<br>
        1. <strong>AI MCQs</strong> मध्ये जाऊन रोज १०-२० प्रश्नांचा सराव करा.<br>
        2. <strong>Mock Tests</strong> सोडवून वेळेचे नियोजन सुधारा.<br>
        3. <strong>Performance</strong> मध्ये जाऊन तुमच्या प्रगतीचा आलेख तपासा.<br><br>
        <em>प्रयत्न करत राहा, यश तुमचेच आहे! 🎯💪</em>"""


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
