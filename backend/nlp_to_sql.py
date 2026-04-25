import sys
import requests
import json
import re
from config import Config

class NLPtoSQL:
    def __init__(self):
        self.ollama_url = Config.OLLAMA_URL
        self.model = Config.OLLAMA_MODEL
    
    def generate_sql_query(self, natural_language_query, table_schema, table_name):
        """Generate SQL query from natural language using Ollama (Gemini mode)"""
        try:
            schema_info = self._format_schema(table_schema, table_name)
            
            prompt = f"""You are Gemini, a highly sophisticated and helpful AI data analyst.
Your task is to write a clean, efficient SQLite query to answer the user's question perfectly.

[SCHEMA]
{schema_info}

[RULES]
1. Reply ONLY with the SQL query string.
2. Start the response directly with the SELECT keyword.
3. No markdown blocks, no commentary, no triple backticks.

[QUESTION]
{natural_language_query}

SQL:"""

            sys.stderr.write(f"DEBUG: Gemini SQL Gen initiating...\n")
            response = self._call_ollama(self.model, prompt)
            
            if response.status_code == 200:
                result = response.json()
                sql_query = result.get('response', '').strip()
                sql_query = self._clean_sql_query(sql_query)
                return {'success': True, 'query': sql_query}

            return {'success': False, 'error': f"Ollama error: {response.status_code}"}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _call_ollama(self, model_name, prompt):
        """Call Ollama generate API with stable options structure."""
        payload = {
            "model": model_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.1,
                "num_predict": 350
            }
        }
        return requests.post(
            f"{self.ollama_url}/api/generate",
            json=payload,
            timeout=120
        )
    
    def _format_schema(self, schema, table_name):
        """Format table schema for LLM context"""
        schema_str = f"Table: {table_name}\nColumns:\n"
        for row in schema:
            col_name, col_type = row[0], row[1]
            schema_str += f"  - {col_name} ({col_type})\n"
        return schema_str
    
    def _clean_sql_query(self, query):
        """Clean SQL query from LLM response"""
        query = re.sub(r'```sql\n?', '', query, flags=re.IGNORECASE)
        query = re.sub(r'```\n?', '', query)
        match = re.search(r'\bSELECT\b', query, flags=re.IGNORECASE)
        if match:
            query = query[match.start():]
        query = query.split('\n\n')[0].strip('`"\' ')
        if ';' in query:
            query = query.split(';')[0] + ';'
        return query
    
    def validate_sql_query(self, query):
        """Basic validation of SQL query"""
        query_upper = query.upper().strip()
        dangerous_keywords = ['DROP', 'DELETE', 'TRUNCATE', 'ALTER', 'CREATE']
        for keyword in dangerous_keywords:
            if keyword in query_upper:
                return {'valid': False, 'error': f'Query with {keyword} is not allowed'}
        if not query_upper.startswith('SELECT'):
            return {'valid': False, 'error': 'Only SELECT queries allowed'}
        return {'valid': True}

    def generate_dataset_summary(self, table_stats, table_name):
        """Dynamic summary generation with strict column mapping and auto-healing"""
        try:
            if not table_stats.get('success'):
                error_msg = table_stats.get('error', 'Unknown database error')
                sys.stderr.write(f"DEBUG: Skipping summary - stats failed: {error_msg}\n")
                return {'success': False, 'error': f"Database stats failure: {error_msg}"}

            stats = table_stats['stats']
            col_list = [c['name'] for c in stats['columns']]
            cols_info = [f"{c['name']} ({c['type']}): Avg {c.get('avg')}, Sum {c.get('sum')}" for c in stats['columns']]
            cols_str = "\n".join(cols_info)

            prompt = f"""Analyze the dataset:
- Describe exactly what information this file consists of (topics, entities, data types).
- Provide 2-3 specific suggestions on how to improve this file (data cleaning, missing types, or better structuring).

FORMAT:
SUMMARY:
- CONTENTS: [Describe composition]
- IMPROVEMENTS: [Suggestions to improve the file]
"""

            sys.stderr.write(f"DEBUG: Initiating summary for {table_name}...\n")
            response = self._call_ollama(self.model, prompt)
            
            if response.status_code == 200:
                result = response.json()
                raw = result.get('response', '').strip()
                sys.stderr.write(f"DEBUG: RAW response: {raw}\n")
                
                summary = raw
                viz_config = {"type": "none"}
                
                if "SUMMARY:" in raw.upper():
                    try:
                        summary = raw.split("SUMMARY:")[1].split("VISUALIZATION:")[0].strip()
                    except:
                        pass
                
                try:
                    json_match = re.search(r'\{.*\}', raw, re.DOTALL)
                    if json_match:
                        viz_config = json.loads(json_match.group(0))
                        
                        # --- HEALER STEP: Validate Columns ---
                        x, y = viz_config.get('x_axis'), viz_config.get('y_axis')
                        if x not in col_list or y not in col_list:
                            sys.stderr.write(f"DEBUG: Healing column mapping for {x}/{y}...\n")
                            # Try to find a numeric column for Y and a string/label for X
                            num_cols = [c['name'] for c in stats['columns'] if c.get('avg') is not None]
                            all_cols = [c['name'] for c in stats['columns']]
                            if num_cols:
                                viz_config['y_axis'] = num_cols[0]
                                viz_config['x_axis'] = all_cols[0] if all_cols[0] != num_cols[0] else (all_cols[1] if len(all_cols) > 1 else all_cols[0])
                except:
                    pass
                
                return {'success': True, 'summary': summary, 'visualization': viz_config}

            return {'success': False, 'error': f"Ollama error {response.status_code}"}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def generate_result_explanation(self, query_results, sql_query, user_message):
        """Dynamic explanation generation with strict column mapping and auto-healing"""
        try:
            cols = query_results.get('columns', [])
            sample = query_results.get('data', [])[:5]
            
            prompt = f"""
Return ONLY valid output in this exact format.
No instructions.
No examples.
No steps.
No markdown.

QUESTION:
{user_message}

COLUMNS:
{cols}

SAMPLE:
{sample}

Output exactly:

EXPLANATION: Short explanation of result.

VISUALIZATION:
{{"type":"bar",
"x_axis":"{cols[0]}",
"y_axis":"{cols[1] if len(cols)>1 else cols[0]}",
"title":"Data Visualization"}}
"""

            sys.stderr.write(f"DEBUG: Gemini explaining... using {self.model}\n")
            response = self._call_ollama(self.model, prompt)
            
            if response.status_code == 200:
                result = response.json()
                raw = result.get('response', '').strip()
                sys.stderr.write(f"DEBUG: RAW explanation: {raw}\n")
                
                explanation = raw
                # default fallback if model behaves badly
                if len(cols) >= 2:
                    viz_config = {
                    "type":"bar",
                    "x_axis": cols[0],
                    "y_axis": cols[1],
                    "title":"Automatic Visualization"
                    }
                else:
                    viz_config = {"type":"none"}
                
                if "EXPLANATION:" in raw.upper():
                    try:
                        explanation = raw.split("EXPLANATION:")[1].split("VISUALIZATION:")[0].strip()
                    except:
                        pass
                
                try:
                    json_match = re.search(r'\{.*\}', raw, re.DOTALL)
                    if json_match:
                        viz_config = json.loads(json_match.group(0))
                        
                        # --- HEALER STEP: Validate Columns ---
                        x, y = viz_config.get('x_axis'), viz_config.get('y_axis')
                        if x not in cols or y not in cols:
                            sys.stderr.write(f"DEBUG: Healing chat mapping for {x}/{y}...\n")
                            # For chat results, we usually want the first two columns if mapping fails
                            if len(cols) >= 2:
                                viz_config['x_axis'] = cols[0]
                                viz_config['y_axis'] = cols[1]
                except:
                    pass
                
                return {'success': True, 'explanation': explanation, 'visualization': viz_config}

            return {'success': False, 'error': f"Ollama error {response.status_code}"}
        except Exception as e:
            return {'success': False, 'error': str(e)}
