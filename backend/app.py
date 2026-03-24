from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
from datetime import datetime, timedelta
from config import Config
from database import DatabaseManager
from nlp_to_sql import NLPtoSQL

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
    """Test database connection"""
    try:
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        cursor.close()
        conn.close()
        return jsonify({'success': True, 'message': 'Database connection successful'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/sessions', methods=['POST'])
def create_session():
    """Create a new chat session"""
    try:
        session_id = datetime.now().strftime('%Y%m%d%H%M%S%f')
        db_name = f"chat_db_{session_id}"
        
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

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Upload and import CSV/Excel file"""
    try:
        session_id = request.form.get('session_id')
        
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
        else:
            result = db_manager.import_excel_to_table(file_path, session['db_name'], table_name)
        
        # Clean up temporary file
        os.remove(file_path)
        
        if result['success']:
            session['tables'].append(table_name)
            return jsonify({
                'success': True,
                'table_name': table_name,
                'rows_imported': result['rows_imported'],
                'columns': result['columns']
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
            
            session['messages'].append({
                'role': 'assistant',
                'content': {
                    'sql_query': sql_query,
                    'data': [dict(zip(query_result['columns'], row)) for row in query_result['data']],
                    'columns': query_result['columns'],
                    'rows': len(query_result['data'])
                },
                'timestamp': datetime.now().isoformat()
            })
            
            return jsonify({
                'success': True,
                'sql_query': sql_query,
                'data': [dict(zip(query_result['columns'], row)) for row in query_result['data']],
                'columns': query_result['columns'],
                'rows': len(query_result['data'])
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
