# AI-Powered Share of Voice Analysis Tool

> Advanced competitive intelligence platform for smart fan market analysis, featuring real-time data collection, NLP-powered insights, and strategic recommendations.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/flask-3.0+-green.svg)](https://flask.palletsprojects.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Live Demo

- **Web Dashboard**: `http://localhost:5000` (after setup)
- **CLI Interface**: `python -m src.cli analyze`

## Key Features

### Multi-Platform Data Collection
- **Google Search Results** via SerpAPI integration
- **YouTube Video Analytics** via YouTube Data API v3
- **Real-time data processing** with rate limiting and quota management

### Advanced NLP Analytics
- **VADER Sentiment Analysis** for brand perception scoring
- **Fuzzy Brand Matching** using RapidFuzz for accurate mention detection
- **Context-aware content analysis** with NLTK processing

### Intelligent Share of Voice Calculation
```python
SoV_score = (rank_weight × engagement_weight × mention_weight × sentiment_weight)
```
- **Mathematical precision** with weighted scoring algorithms
- **Cross-platform aggregation** for holistic market view
- **Competitive positioning** with real-time rankings

### AI-Powered Strategic Insights
- **Platform-specific recommendations** (Google SEO vs YouTube optimization)
- **Keyword opportunity analysis** with priority scoring
- **Competitive gap identification** and actionable strategies
- **Performance tracking KPIs** with trend analysis

### Professional Web Interface
- **Real-time progress tracking** for background analysis
- **Interactive dashboard** with Bootstrap UI
- **Export capabilities** (CSV, JSON, Parquet)
- **Analysis history management** with download functionality

## Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Backend** | Python 3.10+, Flask 3.0+ | Core application and web server |
| **Data Collection** | SerpAPI, YouTube Data API v3 | Search results and video analytics |
| **NLP Processing** | NLTK, VADER, RapidFuzz | Text analysis and sentiment scoring |
| **Data Storage** | Pandas, PyArrow, JSON | Data manipulation and persistence |
| **Web Frontend** | Bootstrap 5.1, Chart.js | Responsive UI and data visualization |
| **Analysis Engine** | NumPy, Custom algorithms | Mathematical SoV calculations |

## Installation

### Prerequisites
- Python 3.10 or higher
- API Keys: SerpAPI, YouTube Data API v3

### Quick Setup

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/smart-fan-sov.git
cd smart-fan-sov
```

2. **Create virtual environment**
```bash
python -m venv .venv
# Windows
.\.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure API keys**
```bash
cp .env.example .env
# Edit .env with your API keys
```

5. **Run the application**
```bash
# Web Interface
python web/app.py

# CLI Analysis
python -m src.cli analyze
```

##  Configuration

### **Environment Variables (.env)**
```env
# API Keys
SERPAPI_KEY=your_serpapi_key_here
YOUTUBE_API_KEY=your_youtube_api_key_here

# Analysis Settings
TARGET_BRAND=Atomberg
GOOGLE_RESULTS_COUNT=30
YOUTUBE_RESULTS_COUNT=30

# Output Settings
OUTPUT_FORMAT=both  # csv, json, both
SAVE_RAW_DATA=true
```

## 🎮 **Usage Examples**

### **Web Dashboard**
```bash
python web/app.py
# Navigate to http://localhost:5000
# Configure keywords and platforms
# Start analysis and monitor progress
# Download results and insights
```

### **CLI Analysis**
```bash
# Basic analysis
python -m src.cli analyze

# Custom keywords
python -m src.cli analyze --keywords "smart fan,BLDC fan,IoT fan"

# Specific platforms
python -m src.cli analyze --platforms google,youtube

# Limited results
python -m src.cli analyze --max-results 50
```

### **Programmatic Usage**
```python
from src.cli import SovAnalysisPipeline

# Initialize pipeline
pipeline = SovAnalysisPipeline()

# Run analysis
results = pipeline.run_full_analysis(
    keywords=['smart fan', 'BLDC fan'],
    platforms=['google', 'youtube'],
    max_results=30
)

# Access insights
executive_summary = results['insights']['marketing_insights']['executive_summary']
recommendations = executive_summary['key_recommendations']
```

##  **Project Structure**

```
smart-fan-sov/
├── src/
│   ├── analytics/          # Cross-platform analysis and insights
│   ├── collectors/         # Data collection from APIs
│   ├── config/            # Configuration and settings
│   ├── nlp/               # NLP processing and sentiment analysis
│   ├── scoring/           # SoV calculation algorithms
│   └── storage/           # Data models and I/O operations
├── web/
│   ├── templates/         # HTML templates for dashboard
│   ├── static/           # CSS, JS, and assets
│   └── app.py            # Flask web application
├── data/
│   ├── raw/              # Raw API responses
│   ├── processed/        # Cleaned and enriched data
│   └── reports/          # Analysis results and insights
├── tests/                # Unit and integration tests
├── scripts/              # Utility and deployment scripts
└── requirements.txt      # Python dependencies
```


