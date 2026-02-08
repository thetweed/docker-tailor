# 🎯 Job Application Tracker

An AI-powered job application tracking system that helps you manage job postings, organize your resume components, and get intelligent recommendations for tailoring your resume to specific positions.

## ✨ Features

- **Job Scraping & Analysis**: Automatically scrape job postings and extract key information using Claude AI
- **Resume Component Library**: Store and organize your experiences, bullet points, skills, and education
- **Resume Import**: Upload your existing resume and let AI extract and organize all components
- **AI-Powered Matching**: Get intelligent recommendations on which resume components to use for each job
- **Smart Suggestions**: Receive AI suggestions for alternate job titles, improved bullet points, and additional skills
- **Application Tracking**: Keep track of saved job postings and match analyses

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher **OR** Docker
- Anthropic API key ([Get one here](https://console.anthropic.com/settings/keys))

### Installation

#### Option 1: Docker (Recommended for Easy Setup)

The easiest way to run this application is using Docker:

1. Install [Docker](https://docs.docker.com/get-docker/)
2. Clone this repository
3. Copy `.env.example` to `.env` and add your API key
4. Run:
   ```bash
   docker-compose up -d
   ```
5. Open [http://localhost:5000](http://localhost:5000)

See [DOCKER.md](DOCKER.md) for detailed Docker instructions and troubleshooting.

#### Option 2: Manual Installation

#### Quick Setup (Automated)

For a one-command setup, use the provided setup scripts:

**Mac/Linux:**
```bash
chmod +x setup.sh
./setup.sh
```

**Windows:**
```bash
setup.bat
```

Then skip to step 6 below and edit your `.env` file!

#### Manual Setup

1. **Clone or download this repository**

2. **Navigate to the project directory**
```bash
cd job-tracker
```

3. **Create a virtual environment** (recommended)
```bash
# On Mac/Linux:
python3 -m venv venv
source venv/bin/activate

# On Windows:
python -m venv venv
venv\Scripts\activate
```

4. **Install dependencies**
```bash
pip install -r requirements.txt
```

5. **Install Playwright browsers** (for job scraping)
```bash
playwright install chromium
```

6. **Set up your API key**
   - Copy `.env.example` to `.env`
   - Edit `.env` and add your Anthropic API key:
```
ANTHROPIC_API_KEY=sk-ant-api03-xxxxx
FLASK_SECRET_KEY=your-random-secret-key-here
```

7. **Run the application**
```bash
python app.py
```

8. **Open your browser**
   - Navigate to: `http://localhost:5000`
   - Start tracking jobs!

## 📖 User Guide

### First-Time Setup

1. **Import Your Resume** (recommended)
   - Click "Resume Library" → "📤 Import Resume"
   - Upload your resume (PDF, DOCX, or TXT)
   - AI will extract your experiences, bullets, skills, and education
   - Review AI suggestions for improvements

2. **Or Add Components Manually**
   - Navigate to "Resume Library"
   - Click "+ Add Experience", "+ Add Bullet", etc.
   - Build your component library piece by piece

### Adding Jobs

**Option 1: Automatic Scraping**
- Click "Jobs" → "+ Add Job"
- Paste the job posting URL
- AI will scrape and extract: company, title, location, compensation, and requirements

**Option 2: Manual Entry**
- Use "Add Manually" if scraping fails
- Enter job details by hand

### Matching Resume to Jobs

1. Go to "Match" page
2. Click "🔍 Analyze Match" on any job
3. Get AI recommendations on:
   - Which experiences to include
   - Which title variant to use
   - Which bullets are most relevant
   - Which skills to highlight
   - Overall positioning strategy

### Managing AI Suggestions

1. Go to "AI Suggestions"
2. Review suggestions grouped by type:
   - **Clarifying Questions**: Answer to get personalized suggestions
   - **Title Variations**: Add alternate titles to experiences
   - **Bullet Improvements**: Replace or add improved versions
   - **New Skills**: Add implied skills from your experience
3. Apply, dismiss, or skip each suggestion

## 💰 Cost Information

This app uses the Anthropic Claude API. Each operation makes a fresh API call:

- **Job Analysis**: ~$0.015 per job (Claude Haiku)
- **Resume Import**: ~$0.05-0.10 per import (Claude Sonnet)
- **Resume Matching**: ~$0.03-0.05 per match (Claude Sonnet)
- **AI Suggestions**: ~$0.03-0.05 per suggestion generation (Claude Sonnet)

Since this app is designed for "analyze once, save locally" workflows, the costs are minimal for typical use. New Anthropic accounts include $5 in free credits, which is enough for approximately:
- ~300 job analyses
- ~50-100 resume imports
- ~100-150 job matches

**Tip**: Save your match analyses and suggestions locally to avoid re-analyzing the same content.

## 🏗️ Project Structure
```
job-tracker/
├── app.py                  # Application factory (main entry point)
├── config.py              # Configuration management
├── requirements.txt       # Python dependencies
├── .env                   # Your API keys (not in git)
│
├── models/                # Database models
│   ├── database.py       # DB connection & initialization
│   ├── job.py           # Job CRUD operations
│   ├── resume.py        # Resume components CRUD
│   └── suggestion.py    # AI suggestions CRUD
│
├── services/             # Business logic
│   ├── ai_service.py    # Claude API integration
│   └── scraper_service.py # Web scraping (Playwright + requests fallback)
│
├── routes/               # HTTP route handlers
│   ├── main.py          # Dashboard
│   ├── jobs.py          # Job management
│   ├── resume.py        # Resume components
│   ├── suggestions.py   # AI suggestions
│   └── matching.py      # Job-resume matching
│
├── utils/                # Helper functions
│   ├── prompts.py       # AI prompt templates
│   └── file_helpers.py  # File upload/extraction
│
├── templates/            # HTML templates
├── static/              # CSS, JS, images
├── uploads/             # Temporary file storage
├── flask_session/       # Session data
└── jobs.db             # SQLite database (created automatically)
```

## 🛠️ Technical Details

### Built With

- **Backend**: Flask (Python web framework)
- **Database**: SQLite (local file-based database)
- **AI**: Anthropic Claude API (Haiku 4.5 & Sonnet 4.5)
- **Web Scraping**: Playwright (headless browser) with requests fallback
- **Document Parsing**: PyPDF2, python-docx, BeautifulSoup4

### Database Schema

The app uses SQLite with the following tables:
- `jobs` - Job postings with scraped content
- `experiences` - Work experience entries
- `bullets` - Achievement bullet points
- `skills` - Skills list
- `education` - Education history
- `suggestions` - AI improvement suggestions

All tables are created automatically on first run.

### Key Features

**Modular Architecture**: Clean separation of concerns
- Models handle database operations
- Services contain business logic
- Routes handle HTTP requests
- Utils provide reusable helpers

**Intelligent Scraping**: Tries Playwright first (for JS-heavy sites), falls back to requests (for static sites)

**Error Handling**: Database context managers prevent connection leaks

**Session Management**: Secure file-based sessions

## 🔒 Privacy & Security

- **All data stays local**: Your resume and job data are stored in a local SQLite database
- **API calls**: Job data is sent to Anthropic's API for analysis
- **No tracking**: This app doesn't track you or send data anywhere except Anthropic's API
- **Secure your API key**: Never commit your `.env` file to git
- **CSRF Protection**: Forms are protected against cross-site request forgery

## 🐛 Troubleshooting

### "API key not found"
- Make sure you created a `.env` file (copy from `.env.example`)
- Check that your API key is correct
- Restart the application after adding the key

### Job scraping fails
- Some job sites block automated access (especially LinkedIn)
- The app will automatically try a simpler scraping method as fallback
- If both methods fail, use "Add Manually" to enter job details
- Scraping works best with standard ATS sites (Greenhouse, Workday, Lever)

### Import fails
- Make sure your resume is PDF, DOCX, or TXT format
- Check that the file isn't password-protected
- Try a simpler format (TXT) if issues persist

### Database errors
- Delete `jobs.db` and restart the app to recreate from scratch
- Make sure you're not running multiple instances of the app

### Template/URL errors
- If you see `BuildError`, make sure all templates use the new blueprint URLs
- Example: `url_for('jobs')` should be `url_for('jobs.list_jobs')`

## 📝 Tips for Best Results

1. **Resume Import**: Use a well-formatted resume with clear sections
2. **Job Scraping**: Works best with standard ATS sites; some sites (like LinkedIn) may block scraping
3. **Bullet Points**: More specific bullets = better AI suggestions
4. **Skills**: Add both hard skills (tools/tech) and soft skills
5. **Matching**: Review AI suggestions critically - they're helpful but not perfect
6. **Save Locally**: Export and save your match analyses to avoid re-analyzing

## 🤝 Contributing

This is a personal project, but suggestions and improvements are welcome! If you find bugs or have feature requests, please open an issue.

### Development Setup
```bash
# Install development dependencies
pip install -r requirements.txt

# Run in debug mode
python app.py  # Debug mode is default

# Project follows Flask best practices
# - Models: Database operations only
# - Services: Business logic
# - Routes: HTTP handling only
# - Utils: Reusable helpers
```

### Code Style

- Follow PEP 8
- Use meaningful variable names
- Add docstrings to functions
- Keep functions focused (single responsibility)
- Use type hints where helpful

## 📄 License

This project is for personal use. Feel free to modify for your own job search.

## 🙏 Acknowledgments

- Built with assistance from [Anthropic Claude](https://www.anthropic.com/claude)
- Inspired by the tedious process of tailoring resumes for every job application

## 📧 Support

For questions, issues, or feature requests:
1. Check the Troubleshooting section above
2. Review the code structure in the project organization
3. Consult the inline documentation in the code

---

**Happy job hunting! 🎉**

Made with ❤️ to make job applications less painful.