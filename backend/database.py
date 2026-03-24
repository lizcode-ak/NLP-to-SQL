import mysql.connector
from config import Config
import pandas as pd
from datetime import datetime
import os
import re

class DatabaseManager:
    def __init__(self):
        self.config = {
            'host': Config.MYSQL_HOST,
            'user': Config.MYSQL_USER,
            'password': Config.MYSQL_PASSWORD,
            'port': Config.MYSQL_PORT
        }
    
    def get_connection(self):
        try:
            conn = mysql.connector.connect(**self.config)
            return conn
        except mysql.connector.Error as err:
            raise Exception(f"Database connection error: {err}")
    
    def create_database_if_not_exists(self, db_name):
        """Create a database if it doesn't exist"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name}")
            cursor.close()
            conn.close()
            return True
        except Exception as e:
            raise Exception(f"Error creating database: {e}")
    
    def execute_query(self, query, db_name):
        """Execute a query and return results"""
        try:
            config_with_db = {**self.config, 'database': db_name}
            conn = mysql.connector.connect(**config_with_db)
            cursor = conn.cursor()
            cursor.execute(query)
            
            # Check if it's a SELECT query
            if query.strip().upper().startswith('SELECT'):
                results = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description]
                cursor.close()
                conn.close()
                return {'success': True, 'data': results, 'columns': columns}
            else:
                conn.commit()
                affected = cursor.rowcount
                cursor.close()
                conn.close()
                return {'success': True, 'affected_rows': affected}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def import_csv_to_table(self, file_path, db_name, table_name):
        """Import CSV file to MySQL table"""
        try:
            df = pd.read_csv(file_path)
            return self._create_table_from_dataframe(df, db_name, table_name)
        except Exception as e:
            raise Exception(f"Error reading CSV: {e}")
    
    def import_excel_to_table(self, file_path, db_name, table_name, sheet_name=0):
        """Import Excel file to MySQL table"""
        try:
            df = pd.read_excel(file_path, sheet_name=sheet_name)
            return self._create_table_from_dataframe(df, db_name, table_name)
        except Exception as e:
            raise Exception(f"Error reading Excel: {e}")
    
    def _create_table_from_dataframe(self, df, db_name, table_name):
        """Helper to create table from dataframe"""
        try:
            # Drop table if exists
            config_with_db = {**self.config, 'database': db_name}
            conn = mysql.connector.connect(**config_with_db)
            cursor = conn.cursor()
            table_name_q = self._quote_identifier(table_name)
            cursor.execute(f"DROP TABLE IF EXISTS {table_name_q}")

            # Normalize missing values and sanitize column names so SQL stays valid.
            df = df.astype(object).where(pd.notnull(df), None)
            safe_columns = self._sanitize_column_names(df.columns)
            df.columns = safe_columns
            
            # Create table with appropriate data types
            columns_sql = []
            for col_name in df.columns:
                dtype = df[col_name].dtype
                
                if dtype == 'int64':
                    col_type = 'INT'
                elif dtype == 'float64':
                    col_type = 'FLOAT'
                elif dtype == 'bool':
                    col_type = 'BOOLEAN'
                else:
                    col_type = 'VARCHAR(255)'
                
                columns_sql.append(f"{self._quote_identifier(col_name)} {col_type}")
            
            create_table_query = f"CREATE TABLE {table_name_q} ({', '.join(columns_sql)})"
            cursor.execute(create_table_query)
            
            # Insert data
            placeholders = ', '.join(['%s'] * len(df.columns))
            column_list = ', '.join([self._quote_identifier(col) for col in df.columns])
            insert_query = f"INSERT INTO {table_name_q} ({column_list}) VALUES ({placeholders})"
            
            for row in df.itertuples(index=False):
                cursor.execute(insert_query, tuple(row))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            return {
                'success': True,
                'table_name': table_name,
                'rows_imported': len(df),
                'columns': list(df.columns)
            }
        except Exception as e:
            raise Exception(f"Error creating table: {e}")

    def _sanitize_column_names(self, columns):
        """Create SQL-safe, unique column names from arbitrary headers."""
        used = set()
        sanitized = []

        for index, raw_name in enumerate(columns, start=1):
            name = str(raw_name or '').strip()
            name = re.sub(r'[^0-9a-zA-Z_]+', '_', name)
            name = re.sub(r'_+', '_', name).strip('_')

            if not name:
                name = f"column_{index}"
            if name[0].isdigit():
                name = f"col_{name}"

            base = name
            suffix = 1
            while name.lower() in used:
                name = f"{base}_{suffix}"
                suffix += 1

            used.add(name.lower())
            sanitized.append(name)

        return sanitized

    def _quote_identifier(self, identifier):
        """Quote MySQL identifiers defensively to handle reserved keywords."""
        escaped = str(identifier).replace('`', '``')
        return f"`{escaped}`"
    
    def get_table_schema(self, db_name, table_name):
        """Get table schema for context"""
        try:
            config_with_db = {**self.config, 'database': db_name}
            conn = mysql.connector.connect(**config_with_db)
            cursor = conn.cursor()
            cursor.execute(f"DESCRIBE {table_name}")
            schema = cursor.fetchall()
            cursor.close()
            conn.close()
            return schema
        except Exception as e:
            raise Exception(f"Error getting schema: {e}")
    
    def get_all_tables(self, db_name):
        """Get all tables in database"""
        try:
            config_with_db = {**self.config, 'database': db_name}
            conn = mysql.connector.connect(**config_with_db)
            cursor = conn.cursor()
            cursor.execute("SHOW TABLES")
            tables = [row[0] for row in cursor.fetchall()]
            cursor.close()
            conn.close()
            return tables
        except Exception as e:
            raise Exception(f"Error getting tables: {e}")
