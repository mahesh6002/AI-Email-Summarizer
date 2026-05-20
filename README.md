<!-- AI Email Summarizer - Professional README -->

<div align="center">
  <img src="https://img.shields.io/badge/AI-Email-Summarizer-purple?style=for-the-badge&logo=ai&logoColor=white" alt="AI Email Summarizer" />
  <img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" alt="License" />
  <img src="https://img.shields.io/badge/Python-3.11+-blue?style=for-the-badge&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/React-Next.js-black?style=for-the-badge&logo=react&logoColor=white" alt="React" />
  <br /><br />
  <h1>AI Email Summarizer</h1>
  <p>LLM-powered email summarization tool with tone detection, multi-language support, and more</p>
  <br />
  <a href="#-features"><strong>Features</strong></a> · <a href="#-tech-stack"><strong>Tech Stack</strong></a> · <a href="#-getting-started"><strong>Getting Started</strong></a> · <a href="#-api-documentation"><strong>API Docs</strong></a> · <a href="#-license"><strong>License</strong></a>
</div>

---

## 📌 Features

### Core Features
- **Email Summarization** — Condenses lengthy email threads into clear, actionable summaries
- **Action Items Extraction** — Automatically extracts key tasks from email conversations
- **Deadline Detection** — Identifies dates and deadlines mentioned in emails
- **Priority Tagging** — Assigns High/Medium/Low priority based on urgency signals

### Advanced Features
- **Tone Detection** — Detects email tone (Urgent, Formal, Friendly, Aggressive, Neutral, Apologetic, Demanding)
- **Multi-Language Support** — Automatically detects email language and returns summary in English
- **Follow-Up Q&A Chat** — Ask follow-up questions about any summarized email
- **Auto-Draft Reply** — Generate professional replies based on email summary
- **Bulk Processing** — Upload multiple email files (.txt, .csv, .eml) for batch summarization
- **Summary History** — View, search, and manage past summaries
- **Analytics Dashboard** — Track usage statistics and trends
- **User Authentication** — Secure JWT-based registration and login
- **Rate Limiting** — API protection against abuse

---

## 🛠 Tech Stack

| Layer | Technology |
|-------|------------|
| **Backend** | FastAPI, Python 3.11+, SQLAlchemy |
| **LLM** | Groq (Llama 3.1) |
| **Database** | SQLite |
| **Frontend** | Next.js 14, TypeScript, Tailwind CSS |
| **UI Components** | Shadcn UI |
| **Authentication** | JWT (python-jose, bcrypt) |

---

## 🚀 Getting Started

### Prerequisites

- Python 3.11 or higher
- Node.js 18+ and npm
- Groq API Key (free tier available)

### Installation

#### 1. Clone the repository

```bash
git clone https://github.com/yourusername/ai-email-summarizer.git
cd ai-email-summarizer
```

#### 2. Backend Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your GROQ_API_KEY
```

#### 3. Frontend Setup

```bash
cd frontend
npm install
```

### Running the Application

#### Start Backend Server

```bash
cd ai-email-summarizer
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### Start Frontend Server

```bash
cd frontend
npm run dev
```

#### Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

---

## 📖 API Documentation

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check |
| `POST` | `/summarize` | Summarize an email |
| `GET` | `/history` | Get summary history |
| `GET` | `/history/search` | Search summaries |
| `DELETE` | `/history/{request_id}` | Delete a summary |
| `POST` | `/chat` | Ask follow-up questions |
| `POST` | `/reply/draft` | Generate email reply |
| `POST` | `/bulk/summarize` | Bulk process emails |
| `GET` | `/bulk/status/{job_id}` | Get bulk job status |
| `GET` | `/bulk/download/{job_id}` | Download bulk results |
| `POST` | `/auth/register` | Register new user |
| `POST` | `/auth/login` | User login |
| `GET` | `/auth/me` | Get current user |
| `GET` | `/analytics/summary` | Get usage analytics |

### Example Usage

#### Summarize an Email

```bash
curl -X POST http://localhost:8000/summarize \
  -H "Content-Type: application/json" \
  -d '{
    "email_text": "Please review the attached document and provide feedback by Friday. This is urgent.",
    "source": "manual"
  }'
```

#### Response

```json
{
  "request_id": "uuid-here",
  "summary": "The sender requests the recipient to review an attached document and provide feedback by Friday...",
  "action_items": ["Review the attached document", "Provide feedback by Friday"],
  "deadlines": "Friday",
  "priority": "High",
  "tone": "Urgent",
  "language": "English",
  "processing_time_ms": 1234
}
```

---

## 📁 Project Structure

```
ai-email-summarizer/
├── app/
│   ├── main.py                 # FastAPI application entry point
│   ├── config.py               # Environment configuration
│   ├── models.py               # Pydantic request/response models
│   ├── logger.py               # Logging configuration
│   │
│   ├── database/               # Database layer
│   │   ├── connection.py       # SQLAlchemy engine & session
│   │   ├── models.py           # ORM table definitions
│   │   └── crud.py             # Database operations
│   │
│   ├── summarizer/             # LLM integration
│   │   ├── client.py           # Groq API client
│   │   ├── prompt.py           # Prompt templates
│   │   └── parser.py           # Response parsing
│   │
│   ├── email_sources/          # Email input sources
│   │   ├── base.py             # Abstract base class
│   │   ├── manual.py           # Manual text input
│   │   └── gmail.py            # Gmail integration
│   │
│   ├── routers/                # API endpoints
│   │   ├── health.py           # Health check
│   │   ├── summarize.py        # Main summarization
│   │   ├── history.py          # Summary history
│   │   ├── chat.py             # Q&A chat
│   │   ├── bulk.py             # Bulk processing
│   │   ├── users.py            # User authentication
│   │   └── analytics.py        # Analytics
│   │
│   └── auth/                   # Authentication
│       ├── jwt_handler.py      # JWT token handling
│       ├── password.py         # Password hashing
│       └── dependencies.py    # Auth dependencies
│
├── frontend/                   # Next.js frontend
│   ├── src/
│   │   ├── app/               # Next.js pages
│   │   ├── components/        # React components
│   │   └── lib/               # Utilities
│   └── package.json
│
├── tests/                     # Test suite
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

---

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=app --cov-report=term-missing
```

---

## 📝 Configuration

Create a `.env` file in the root directory:

```env
# Groq API (required)
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.1-8b-instant

# Database
DATABASE_URL=sqlite:///./summaries.db

# JWT Authentication
JWT_SECRET_KEY=your-secret-key-min-32-chars
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=60

# Rate Limiting
RATE_LIMIT_PER_MINUTE=10

# Server
API_HOST=0.0.0.0
API_PORT=8000
```

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- [Groq](https://groq.com/) for providing the free LLM API
- [Shadcn UI](https://ui.shadcn.com/) for the beautiful UI components
- [FastAPI](https://fastapi.tiangolo.com/) for the excellent backend framework

---

<div align="center">
  <br />
  <p>Built with ❤️ using FastAPI, Groq, and Next.js</p>
  <br />
</div>