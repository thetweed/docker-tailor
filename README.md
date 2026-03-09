# 🎯 Job Application Tracker

An AI-powered job application tracking system that helps you manage job postings, organize your resume components, and get intelligent recommendations for tailoring your resume to specific positions.

## ✨ Features

- **Job Scraping & Analysis**: Automatically scrape job postings and extract key information using Claude AI
- **Resume Component Library**: Store and organize your experiences, bullet points, skills, and education
- **Resume Import**: Upload your existing resume and let AI extract and organize all components
- **AI-Powered Matching**: Get intelligent recommendations on which resume components to use for each job
- **Smart Suggestions**: Receive AI suggestions for alternate job titles, improved bullet points, and additional skills
- **Bullet Variant Generator**: Generate multiple AI-reworded versions of any bullet point, then selectively save them to your library as a grouped set of alternates
- **Application Tracking**: Keep track of saved job postings and match analyses
- **Export Profiles**: Create reusable export profiles with rules to transform your resume (rename categories, merge/split skill groups, reorder sections, use alternate titles, anonymize company names) and a personal header (name, contact info) — all applied at export time without modifying your source data
- **Multiple Export Formats**: Export resumes as TXT, Markdown, HTML, DOCX, or PDF

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
5. Open [http://localhost:8080](http://localhost:8080)

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
> Debug mode is off by default. Set `FLASK_CONFIG=development` in your `.env` for local debug mode.

8. **Open your browser**
   - Navigate to: `http://localhost:5000`
   - Start tracking jobs!

## 📖 User Guide

### First-Time Setup

1. **Import Your Resume** (recommended)
   - Click "Components" → "📤 Import Resume"
   - Upload your resume (PDF, DOCX, or TXT)
   - AI will extract your experiences, bullets, skills, and education
   - Review AI suggestions for improvements

2. **Or Add Components Manually**
   - Navigate to "Components"
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

### Generating Bullet Variants

1. Go to "Components" → click **✦ Variants** in the Bullets section header
2. Choose a source:
   - **From Library**: pick an existing bullet from a dropdown (grouped by experience)
   - **From Scratch**: type a new bullet and optionally link it to an experience
3. Set how many variants to generate (default: 3, max: 10)
4. Click **Generate Variants** — AI rewrites the bullet with different phrasing, verbs, and structure
5. Check the variants you want to keep, optionally include the original in the group, then **Save Selected**

Saved variants are stored as a bullet group — during export the group default is shown, but you can swap in any alternate at any time from the Resume page.

### Managing AI Suggestions

1. Go to "AI Suggestions"
2. Review suggestions grouped by type:
   - **Clarifying Questions**: Answer to get personalized suggestions
   - **Title Variations**: Add alternate titles to experiences
   - **Bullet Improvements**: Replace or add improved versions
   - **New Skills**: Add implied skills from your experience
3. Apply, dismiss, or skip each suggestion

### Export Profiles & Rules

Export profiles let you save reusable transformation rules that are applied when exporting your resume, without changing your underlying data.

**Creating a Profile:**
1. Go to "Export" → "+ New Profile"
2. Give it a name/description
3. Add rules, set a personal header, and optionally mark it as default

**Available Rule Types:**
- **Rename Category**: Change a skill or bullet category name (e.g., "Soft Skills" → "Skills")
- **Merge Categories**: Combine multiple categories into one
- **Split Category**: Break a skill category into sub-groups by selecting individual skills
- **Section Order**: Control the order sections appear (Experience, Skills, Education)
- **Use Alternate Title**: Swap in an alternate job title for a specific experience
- **Rename Company**: Replace a company name with an anonymized display name for a specific experience (e.g., "Acme Corp" → "Company A") — useful for submitting resumes for AI analysis without exposing employer details, then restoring real names at export time

**Personal Header:**
Each profile can include contact info (name, email, phone, location, links) that appears at the top of the exported resume. This keeps personal info out of your stored resume components and API calls.

**Exporting with a Profile:**
1. Go to "Export" → "Export Resume"
2. Select a profile from the dropdown (or leave blank for default behavior)
3. Toggle individual rules on/off for this specific export
4. Choose your components and format, then export

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
├── extensions.py          # Shared Flask extensions (rate limiter)
├── requirements.txt       # Python dependencies
├── .env                   # Your API keys (not in git)
│
├── models/                # Database models
│   ├── database.py       # DB connection & initialization
│   ├── job.py           # Job CRUD operations
│   ├── resume.py        # Resume components CRUD
│   ├── suggestion.py    # AI suggestions CRUD
│   ├── tailor_analysis.py # Saved AI analyses CRUD
│   └── export_profile.py # Export profiles & rules CRUD
│
├── services/             # Business logic
│   ├── ai_service.py    # Claude API integration
│   ├── export_transform.py # Export rule application engine
│   └── scraper_service.py # Web scraping (Playwright + requests fallback)
│
├── routes/               # HTTP route handlers
│   ├── main.py          # Dashboard
│   ├── jobs.py          # Job management
│   ├── resume.py        # Resume components & import
│   ├── export.py        # Export, profiles & format generation
│   ├── suggestions.py   # AI suggestions
│   └── tailoring.py     # Job-resume tailoring
│
├── utils/                # Helper functions
│   ├── __init__.py      # File upload/extraction helpers
│   ├── prompts.py       # AI prompt templates
│   └── file_helpers.py  # File type utilities
│
├── templates/            # HTML templates
├── static/              # CSS, JS, images
├── uploads/             # Temporary file storage
├── flask_session/       # Session data
└── data/               # SQLite database (created automatically)
```

## 🛠️ Technical Details

### Built With

- **Backend**: Flask (Python web framework)
- **Database**: SQLite (local file-based database)
- **AI**: Anthropic Claude API (Haiku 4.5 & Sonnet 4.5)
- **Web Scraping**: Playwright (headless browser) with requests fallback
- **Document Parsing**: pypdf, python-docx, BeautifulSoup4
- **Export Generation**: python-docx (DOCX), ReportLab (PDF), Markdown
- **Security**: Flask-WTF (CSRF protection), Flask-Limiter (AI endpoint rate limiting)

### Database Schema

The app uses SQLite with the following tables:
- `jobs` - Job postings with scraped content
- `experiences` - Work experience entries
- `bullets` - Achievement bullet points
- `skills` - Skills list
- `education` - Education history
- `suggestions` - AI improvement suggestions
- `export_profiles` - Reusable export profiles with personal header info
- `export_rules` - Transformation rules belonging to export profiles

All tables are created automatically on first run.

### Key Features

**Modular Architecture**: Clean separation of concerns
- Models handle database operations
- Services contain business logic
- Routes handle HTTP requests
- Utils provide reusable helpers

**Intelligent Scraping**: Tries Playwright first (for JS-heavy sites), falls back to requests (for static sites)

**Error Handling**: Database context managers prevent connection leaks

**Session Management**: Secure file-based sessions stored in `flask_session/`. When running via Docker, a `session-cleanup` sidecar service automatically purges session files older than 7 days. For manual installs, periodically run `find flask_session/ -type f -atime +7 -delete` or set up an equivalent cron job.

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
- Delete `data/resume_tailor.db` (or whatever file is in `data/`) and restart the app to recreate from scratch
- Make sure you're not running multiple instances of the app

### "CSRF session token is missing" after a rebuild
- Your browser has a stale session cookie pointing to a session file that no longer exists
- Clear cookies for `localhost:8080` (or your app URL) in your browser and reload

## 📝 Tips for Best Results

1. **Resume Import**: Use a well-formatted resume with clear sections
2. **Job Scraping**: Works best with standard ATS sites; some sites (like LinkedIn) may block scraping; can add jobs manually as well
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

## 📄 License

This project is for personal use. Feel free to modify for your own job search.

## 📧 Support

For questions, issues, or feature requests:
1. Check the Troubleshooting section above
2. Review the code structure in the project organization
3. Consult the inline documentation in the code

---

**Happy job hunting! 🎉**

Made with ❤️ to make job applications less painful.