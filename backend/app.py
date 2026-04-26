from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
from datetime import datetime, timedelta
from config import Config
from database import DatabaseManager
from nlp_to_sql import NLPtoSQL
from document_processor import DocumentProcessor
from vision_processor import VisionProcessor
from chart_generator import ChartGenerator
from flask import send_from_directory

app = Flask(__name__)
CORS(app)

# Configuration
app.config['UPLOAD_FOLDER'] = Config.UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = Config.MAX_CONTENT_LENGTH
app.config['JSON_SORT_KEYS'] = False

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize managers
db_manager = DatabaseManager()
nlp_to_sql = NLPtoSQL()
chart_generator = ChartGenerator(os.path.join(Config.UPLOAD_FOLDER, "static", "charts"))

# Store active sessions (in production, use Redis or database)
sessions = {}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

@app.route('/api/test-connection', methods=['GET'])
def test_connection():
    """Test database connectivity"""
    try:
        db_manager.create_database_if_not_exists(Config.MYSQL_DATABASE)
        conn = db_manager.get_connection(Config.MYSQL_DATABASE)
        conn.close()
        return jsonify({'success': True, 'message': 'MySQL database system is ready'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/charts/<path:filename>')
def serve_chart(filename):
    """Serve generated chart images"""
    return send_from_directory(os.path.join(Config.UPLOAD_FOLDER, "static", "charts"), filename)

@app.route('/api/sessions', methods=['POST'])
def create_session():
    """Create a new chat session"""
    try:
        session_id = datetime.now().strftime('%Y%m%d%H%M%S%f')
        db_name = Config.MYSQL_DATABASE

        db_manager.create_database_if_not_exists(db_name)
        
        sessions[session_id] = {
            'db_name': db_name,
            'created_at': datetime.now(),
            'tables': [],
            'messages': []
        }
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'db_name': db_name
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/sessions/<session_id>', methods=['GET'])
def get_session(session_id):
    """Get session details"""
    if session_id not in sessions:
        return jsonify({'success': False, 'error': 'Session not found'}), 404
    
    try:
        session = sessions[session_id]
        tables = db_manager.get_all_tables(session['db_name'])
        session['tables'] = tables
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'created_at': session['created_at'].isoformat(),
            'tables': tables,
            'messages': session['messages']
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def generate_fallback_summary(table_stats, table_name, reason="Ollama is currently offline or unreachable"):
    """Generate a high-quality non-AI summary if Ollama is unavailable"""
    stats = table_stats.get('stats', {})
    row_count = stats.get('row_count', 'Unknown')
    cols = stats.get('columns', [])
    col_names = ", ".join([c['name'] for c in cols])
    
    # Extract some basic numeric stats for the fallback
    stat_lines = []
    for c in cols:
        if c.get('avg') is not None:
            stat_lines.append(f"* **{c['name']}**: Avg {c['avg']}, Min {c['min']}, Max {c['max']}")
    
    stats_text = "\n".join(stat_lines)
    
    summary = f"""**Dataset Summary (Insight Mode):** This dataset `{table_name}` contains **{row_count} rows** and **{len(cols)} columns**.
**Columns:** {col_names}.
**Key Statistics:**
{stats_text}

> [!NOTE]
> {reason}. Using a calculated analytical summary instead."""
    
    return {'summary': summary, 'visualization': {'type': 'none'}, 'success': True}

import sys

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Upload and import CSV/Excel file"""
    sys.stderr.write(f"DEBUG: Received upload request at {datetime.now()}\n")
    try:
        session_id = request.form.get('session_id')
        sys.stderr.write(f"DEBUG: Session ID: {session_id}\n")
        
        if not session_id or session_id not in sessions:
            return jsonify({'success': False, 'error': 'Invalid session'}), 400
        
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'success': False, 'error': 'File type not allowed. Use CSV or Excel files'}), 400
        
        # Save file temporarily
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{timestamp}_{filename}")
        file.save(file_path)
        
        # Import to database
        table_name = os.path.splitext(filename)[0].replace('-', '_').replace(' ', '_').lower()
        table_name = f"table_{timestamp}_{table_name}"
        
        session = sessions[session_id]
        
        if filename.lower().endswith('.csv'):
            result = db_manager.import_csv_to_table(file_path, session['db_name'], table_name)
        elif filename.lower().endswith(('.xlsx', '.xls')):
            result = db_manager.import_excel_to_table(file_path, session['db_name'], table_name)
        else:
            # Handle text and audio files
            doc_processor = DocumentProcessor()
            try:
                if filename.lower().endswith('.txt'):
                    text_content = doc_processor.extract_text_from_txt(file_path)
                elif filename.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                    vision_processor = VisionProcessor()
                    vision_result = vision_processor.analyze_image(file_path)
                    if vision_result['success']:
                        text_content = vision_result['analysis']
                    else:
                        raise Exception(f"Vision analysis failed: {vision_result['error']}")
                else:
                    text_content = doc_processor.transcribe_audio(file_path)
                
                # Import as a 1-row table for the LLM to query
                import pandas as pd
                df = pd.DataFrame([{"document_content": text_content}])
                result = db_manager._create_table_from_dataframe(df, session['db_name'], table_name)
            except Exception as e:
                result = {'success': False, 'error': str(e)}

        # Clean up temporary file
        if os.path.exists(file_path):
            os.remove(file_path)
        
        if result.get('success'):
            session['tables'].append(table_name)
            
            # Generate dataset summary
            table_stats = db_manager.get_table_stats(session['db_name'], table_name)
            sys.stderr.write(f"DEBUG: ABOUT TO CALL NLP_TO_SQL for {table_name}\n")
            summary_result = nlp_to_sql.generate_dataset_summary(table_stats, table_name)
            
            if summary_result['success']:
                viz_config = summary_result.get('visualization', {'type': 'none'})
                summary_data = {
                    'summary': summary_result.get('summary', 'Could not generate summary.'),
                    'visualization': viz_config,
                    'image_url': None,
                    'data': table_stats['stats']['sample_data'],
                    'columns': [c['name'] for c in table_stats['stats']['columns']]
                }
            else:
                reason = summary_result.get('error', 'Ollama is unreachable')
                summary_data = generate_fallback_summary(table_stats, table_name, reason=reason)
                viz_config = summary_data.get('visualization', {'type': 'none'})
                summary_data.update({
                    'data': table_stats['stats']['sample_data'],
                    'columns': [c['name'] for c in table_stats['stats']['columns']],
                    'image_url': None
                })

            if table_stats.get('success'):
                if viz_config.get('type') == 'none':
                    columns = table_stats['stats']['columns']
                    numeric_cols = [c['name'] for c in columns if c.get('avg') is not None]
                    all_cols = [c['name'] for c in columns]

                    if numeric_cols:
                        x_col = all_cols[0] if all_cols[0] != numeric_cols[0] else (all_cols[1] if len(all_cols) > 1 else all_cols[0])
                        y_col = numeric_cols[0]

                        viz_config = {
                            "type": "bar",
                            "x_axis": x_col,
                            "y_axis": y_col,
                            "title": "Automatic Data Visualization"
                        }

                if viz_config.get('type') != 'none':
                    image_url = chart_generator.generate_chart(
                        table_stats['stats']['sample_data'],
                        viz_config
                    )
                    summary_data['image_url'] = image_url
                    summary_data['visualization'] = viz_config
            
            # Store summary as an assistant message
            session['messages'].append({
                'role': 'assistant',
                'content': summary_data,
                'timestamp': datetime.now().isoformat(),
                'type': 'summary'
            })
            
            return jsonify({
                'success': True,
                'table_name': table_name,
                'rows_imported': result['rows_imported'],
                'columns': result['columns'],
                'summary_data': summary_data
            })
        else:
            return jsonify({'success': False, 'error': result.get('error', 'Import failed')}), 500
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/chat', methods=['POST'])
def chat():
    """Process natural language query and return SQL results"""
    try:
        data = request.json
        session_id = data.get('session_id')
        user_message = data.get('message')
        table_name = data.get('table_name')
        
        if not session_id or session_id not in sessions:
            return jsonify({'success': False, 'error': 'Invalid session'}), 400
        
        if not user_message or not table_name:
            return jsonify({'success': False, 'error': 'Message and table name required'}), 400
        
        session = sessions[session_id]
        
        # Get table schema
        schema = db_manager.get_table_schema(session['db_name'], table_name)
        
        # Generate SQL query
        sql_result = nlp_to_sql.generate_sql_query(user_message, schema, table_name)
        
        if not sql_result['success']:
            return jsonify({'success': False, 'error': sql_result['error']}), 500
        
        sql_query = sql_result['query']
        
        # Validate SQL query
        validation = nlp_to_sql.validate_sql_query(sql_query)
        if not validation['valid']:
            return jsonify({'success': False, 'error': validation['error']}), 400
        
        # Execute query
        query_result = db_manager.execute_query(sql_query, session['db_name'])
        
        if query_result['success']:
            # Store message
            session['messages'].append({
                'role': 'user',
                'content': user_message,
                'timestamp': datetime.now().isoformat()
            })
            
            # Generate explanation
            explanation_result = nlp_to_sql.generate_result_explanation(query_result, sql_query, user_message)
            explanation = explanation_result.get('explanation', '') if explanation_result['success'] else 'Could not generate explanation.'
            
            # auto force chart for 2-column aggregated results
            viz_config = explanation_result.get('visualization', {'type': 'none'})
            if viz_config.get('type') == 'none' and len(query_result['columns']) == 2:
                viz_config = {
                    "type": "bar",
                    "x_axis": query_result['columns'][0],
                    "y_axis": query_result['columns'][1],
                    "title": "Query Result Chart"
                }
            
            # Fetch table_stats for potential fallback
            table_stats = db_manager.get_table_stats(session['db_name'], table_name)
            
            sample_rows = [
    dict(zip(query_result['columns'], row))
    for row in query_result['data'][:20]
]

# force bar chart for two-column query results
            if len(query_result['columns']) >= 2:

                viz_config = {
                "type":"bar",
                "x_axis": query_result['columns'][0],
                "y_axis": query_result['columns'][-1],
                "title":"Query Result Chart"
                }

                image_url = chart_generator.generate_chart(
                sample_rows,
                viz_config
                )

                print("IMAGE_URL =", image_url)
                print("VIZ_CONFIG =", viz_config)
                print("SAMPLE_ROWS =", sample_rows[:3])

            else:
                image_url = None

                if viz_config.get('type') != 'none':
                    image_url = chart_generator.generate_chart(
                    sample_rows,
                    viz_config
                    )

            # fallback auto chart if LLM chart fails OR no chart was suggested
            if image_url is None and table_stats.get('success'):
                columns = table_stats['stats']['columns']
                numeric_cols = [c['name'] for c in columns if c.get('avg') is not None]
                all_cols = [c['name'] for c in columns]

                if numeric_cols:
                    x_col = all_cols[0] if all_cols[0] != numeric_cols[0] else (all_cols[1] if len(all_cols) > 1 else all_cols[0])
                    y_col = numeric_cols[0]
                    
                    fallback_viz = {
                        "type": "bar",
                        "x_axis": x_col,
                        "y_axis": y_col,
                        "title": "Automatic Data Visualization"
                    }
                    
                    image_url = chart_generator.generate_chart(
                        table_stats['stats']['sample_data'], 
                        fallback_viz
                    )

            chat_response = {
                'sql_query': sql_query,
                'data': [dict(zip(query_result['columns'], row)) for row in query_result['data']],
                'columns': query_result['columns'],
                'rows': len(query_result['data']),
                'explanation': explanation,
                'visualization': viz_config,
                'image_url': image_url
            }
            
            session['messages'].append({
                'role': 'assistant',
                'content': chat_response,
                'timestamp': datetime.now().isoformat()
            })
            
            return jsonify({
                'success': True,
                **chat_response
            })
        else:
            return jsonify({'success': False, 'error': query_result['error']}), 500
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/query', methods=['POST'])
def execute_custom_query():
    """Execute custom SQL query"""
    try:
        data = request.json
        session_id = data.get('session_id')
        sql_query = data.get('query')
        
        if not session_id or session_id not in sessions:
            return jsonify({'success': False, 'error': 'Invalid session'}), 400
        
        if not sql_query:
            return jsonify({'success': False, 'error': 'Query required'}), 400
        
        # Validate query
        validation = nlp_to_sql.validate_sql_query(sql_query)
        if not validation['valid']:
            return jsonify({'success': False, 'error': validation['error']}), 400
        
        session = sessions[session_id]
        
        # Execute query
        query_result = db_manager.execute_query(sql_query, session['db_name'])
        
        if query_result['success']:
            return jsonify({
                'success': True,
                'data': [dict(zip(query_result['columns'], row)) for row in query_result['data']],
                'columns': query_result['columns'],
                'rows': len(query_result['data'])
            })
        else:
            return jsonify({'success': False, 'error': query_result['error']}), 500
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({'success': False, 'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'success': False, 'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(debug=Config.FLASK_DEBUG, host='0.0.0.0', port=5000)
