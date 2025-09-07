from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
import os
import json
import threading
import uuid
from datetime import datetime
import sys
from pathlib import Path

# Add project root and src to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'src'))

try:
    from src.cli import SovAnalysisPipeline
    from src.config.settings import settings
except ImportError as e:
    print(f"Warning: Could not import modules: {e}")
    print("Running in demo mode without actual analysis functionality")
    SovAnalysisPipeline = None
    settings = None

app = Flask(__name__)
CORS(app)

# Store running analyses
running_analyses = {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/config')
def get_config():
    if settings is None:
        return jsonify({
            'api_keys_configured': False,
            'target_brand': 'Atomberg',
            'competitors': ['Havells', 'Orient', 'Bajaj', 'Crompton', 'Usha'],
            'default_keywords': ['smart fan', 'BLDC fan', 'energy saving fan'],
            'platforms': ['google', 'youtube'],
            'demo_mode': True
        })
    
    return jsonify({
        'api_keys_configured': settings.validate(),
        'target_brand': settings.TARGET_BRAND,
        'competitors': settings.COMPETITOR_BRANDS,
        'default_keywords': settings.PRIMARY_KEYWORDS,
        'platforms': ['google', 'youtube'],
        'demo_mode': False
    })

@app.route('/api/start-analysis', methods=['POST'])
def start_analysis():
    if SovAnalysisPipeline is None:
        return jsonify({'error': 'Analysis module not available. Please check configuration.'}), 500
        
    data = request.json
    
    # Validate input
    default_keywords = settings.PRIMARY_KEYWORDS if settings else ['smart fan', 'BLDC fan']
    keywords = data.get('keywords', default_keywords)
    platforms = data.get('platforms', ['google', 'youtube'])
    max_results = data.get('max_results', 30)
    
    if not keywords:
        return jsonify({'error': 'Keywords are required'}), 400
    
    # Generate unique analysis ID
    analysis_id = str(uuid.uuid4())[:8]
    
    # Store analysis info
    running_analyses[analysis_id] = {
        'status': 'starting',
        'progress': 0,
        'keywords': keywords,
        'platforms': platforms,
        'max_results': max_results,
        'started_at': datetime.now().isoformat(),
        'results': None,
        'error': None
    }
    
    # Start analysis in background thread
    thread = threading.Thread(
        target=run_analysis_background,
        args=(analysis_id, keywords, platforms, max_results)
    )
    thread.daemon = True
    thread.start()
    
    return jsonify({
        'analysis_id': analysis_id,
        'status': 'started',
        'message': 'Analysis started successfully'
    })

@app.route('/api/analysis/<analysis_id>/status')
def get_analysis_status(analysis_id):
    if analysis_id not in running_analyses:
        return jsonify({'error': 'Analysis not found'}), 404
    
    analysis = running_analyses[analysis_id]
    return jsonify(analysis)

@app.route('/api/analysis/<analysis_id>/results')
def get_analysis_results(analysis_id):
    if analysis_id not in running_analyses:
        return jsonify({'error': 'Analysis not found'}), 404
    
    analysis = running_analyses[analysis_id]
    if analysis['status'] != 'completed':
        return jsonify({'error': 'Analysis not completed yet'}), 400
    
    return jsonify(analysis['results'])

@app.route('/api/recent-analyses')
def get_recent_analyses():
    # Get recent result files using absolute path
    project_root = Path(__file__).parent.parent
    reports_dir = project_root / 'data' / 'reports'
    
    if not reports_dir.exists():
        return jsonify([])
    
    files = []
    for filename in os.listdir(str(reports_dir)):
        if filename.startswith('insights_') and filename.endswith('.json'):
            filepath = reports_dir / filename
            try:
                with open(filepath, 'r') as f:
                    data = json.load(f)
                    exec_summary = data.get('marketing_insights', {}).get('executive_summary', {})
                    files.append({
                        'filename': filename,
                        'date': filename.split('_')[1].split('.')[0],
                        'target_brand': exec_summary.get('target_brand', 'Unknown'),
                        'sov': exec_summary.get('key_metrics', {}).get('overall_sov', 0),
                        'position': exec_summary.get('key_metrics', {}).get('competitive_position', 'Unknown')
                    })
            except Exception as e:
                print(f"Error reading {filename}: {e}")
                continue
    
    # Sort by date (newest first)
    files.sort(key=lambda x: x['date'], reverse=True)
    return jsonify(files[:10])  # Return last 10

@app.route('/api/download/<filename>')
def download_file(filename):
    project_root = Path(__file__).parent.parent
    filepath = project_root / 'data' / 'reports' / filename
    
    if filepath.exists():
        return send_file(str(filepath), as_attachment=True)
    return jsonify({'error': 'File not found'}), 404

def run_analysis_background(analysis_id, keywords, platforms, max_results):
    try:
        # Update status
        running_analyses[analysis_id]['status'] = 'running'
        running_analyses[analysis_id]['progress'] = 10
        
        # Initialize pipeline
        pipeline = SovAnalysisPipeline()
        
        # Update progress incrementally
        running_analyses[analysis_id]['progress'] = 25
        
        # Run analysis
        results = pipeline.run_full_analysis(keywords, platforms, max_results)
        
        running_analyses[analysis_id]['progress'] = 90
        
        # Extract key insights for frontend
        insights = results.get('insights', {})
        marketing_insights = insights.get('marketing_insights', {})
        exec_summary = marketing_insights.get('executive_summary', {})
        
        # Prepare frontend-friendly results
        frontend_results = {
            'executive_summary': exec_summary,
            'key_metrics': exec_summary.get('key_metrics', {}),
            'recommendations': exec_summary.get('key_recommendations', []),
            'competitive_analysis': marketing_insights.get('competitive_strategy', {}),
            'total_documents': len(results.get('enriched_documents', [])),
            'total_mentions': len(results.get('scored_mentions', [])),
            'platforms_analyzed': platforms,
            'keywords_analyzed': keywords
        }
        
        # Update final status
        running_analyses[analysis_id].update({
            'status': 'completed',
            'progress': 100,
            'completed_at': datetime.now().isoformat(),
            'results': frontend_results
        })
        
    except Exception as e:
        running_analyses[analysis_id].update({
            'status': 'error',
            'error': str(e),
            'completed_at': datetime.now().isoformat()
        })

if __name__ == '__main__':
    # Create necessary directories using absolute paths
    project_root = Path(__file__).parent.parent
    reports_dir = project_root / 'data' / 'reports'
    reports_dir.mkdir(parents=True, exist_ok=True)
    
    print("Starting Share of Voice Analysis Web Server...")
    print("Dashboard will be available at: http://localhost:5000")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
