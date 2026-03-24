import requests
import json
import re
from config import Config

class NLPtoSQL:
    def __init__(self):
        self.ollama_url = Config.OLLAMA_URL
        self.model = Config.OLLAMA_MODEL
    
    def generate_sql_query(self, natural_language_query, table_schema, table_name):
        """Generate SQL query from natural language using Ollama"""
        try:
            # Build context for the LLM
            schema_info = self._format_schema(table_schema, table_name)
            
            prompt = f"""You are an expert SQL query generator. Convert the following natural language question into a SQL query.

Database Schema:
{schema_info}

Table Name: {table_name}

Natural Language Question: {natural_language_query}

Return ONLY the SQL query without any explanation or markdown formatting. The query should be valid MySQL syntax."""

            response = self._call_ollama(self.model, prompt)

            # Retry once with explicit :latest tag for common local model naming issues.
            if response.status_code != 200 and ':' not in self.model:
                response = self._call_ollama(f"{self.model}:latest", prompt)

            if response.status_code == 200:
                result = response.json()
                sql_query = result.get('response', '').strip()
                sql_query = self._clean_sql_query(sql_query)
                return {'success': True, 'query': sql_query}

            error_text = response.text.strip()
            if len(error_text) > 250:
                error_text = error_text[:250] + '...'
            return {
                'success': False,
                'error': f"Ollama API error: {response.status_code}. {error_text}"
            }
        except requests.exceptions.ConnectionError:
            return {'success': False, 'error': 'Cannot connect to Ollama. Make sure it is running on ' + self.ollama_url}
        except requests.exceptions.Timeout:
            return {'success': False, 'error': 'Ollama request timed out. Try again or use a smaller dataset/query.'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _call_ollama(self, model_name, prompt):
        """Call Ollama generate API with stable options structure."""
        payload = {
            "model": model_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.1
            }
        }
        return requests.post(
            f"{self.ollama_url}/api/generate",
            json=payload,
            timeout=60
        )
    
    def _format_schema(self, schema, table_name):
        """Format table schema for LLM context"""
        schema_str = f"Table: {table_name}\nColumns:\n"
        for row in schema:
            col_name, col_type = row[0], row[1]
            schema_str += f"  - {col_name}: {col_type}\n"
        return schema_str
    
    def _clean_sql_query(self, query):
        """Clean SQL query from LLM response"""
        # Remove markdown code blocks if present
        query = re.sub(r'```sql\n?', '', query)
        query = re.sub(r'```\n?', '', query)
        
        # Remove common LLM prefixes
        query = re.sub(r'^(sql|query|query:)\s*', '', query, flags=re.IGNORECASE)
        
        # Clean up whitespace
        query = query.strip()
        
        return query
    
    def validate_sql_query(self, query):
        """Basic validation of SQL query"""
        query_upper = query.upper().strip()
        
        # Check for dangerous operations
        dangerous_keywords = ['DROP', 'DELETE', 'TRUNCATE', 'ALTER', 'CREATE']
        for keyword in dangerous_keywords:
            if query_upper.startswith(keyword):
                return {'valid': False, 'error': f'Query with {keyword} is not allowed'}
        
        # Check if query starts with SELECT
        if not query_upper.startswith('SELECT'):
            return {'valid': False, 'error': 'Only SELECT queries are allowed'}
        
        return {'valid': True}
