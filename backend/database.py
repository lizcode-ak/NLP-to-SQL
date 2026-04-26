import os
import re
import sys
from datetime import datetime

import mysql.connector
import pandas as pd
from mysql.connector import Error

from config import Config


class DatabaseManager:
    def __init__(self):
        self.upload_folder = Config.UPLOAD_FOLDER
        os.makedirs(self.upload_folder, exist_ok=True)
        self.database = Config.MYSQL_DATABASE

    def _get_server_connection(self):
        try:
            return mysql.connector.connect(
                host=Config.MYSQL_HOST,
                user=Config.MYSQL_USER,
                password=Config.MYSQL_PASSWORD,
                port=Config.MYSQL_PORT,
            )
        except Error as err:
            raise Exception(f"Database connection error: {err}")

    def get_connection(self, db_name=None):
        try:
            database = db_name or self.database
            return mysql.connector.connect(
                host=Config.MYSQL_HOST,
                user=Config.MYSQL_USER,
                password=Config.MYSQL_PASSWORD,
                port=Config.MYSQL_PORT,
                database=database,
            )
        except Error as err:
            raise Exception(f"Database connection error: {err}")

    def create_database_if_not_exists(self, db_name):
        """Create a database if it doesn't exist"""
        try:
            conn = self._get_server_connection()
            cursor = conn.cursor()
            cursor.execute(
                f"CREATE DATABASE IF NOT EXISTS {self._quote_identifier(db_name)} "
                "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
            conn.commit()
            cursor.close()
            conn.close()
            return True
        except Exception as e:
            raise Exception(f"Error creating database: {e}")

    def execute_query(self, query, db_name):
        """Execute a query and return results"""
        try:
            conn = self.get_connection(db_name)
            cursor = conn.cursor()
            cursor.execute(query)

            if query.strip().upper().startswith("SELECT"):
                results = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description]
                cursor.close()
                conn.close()
                return {"success": True, "data": results, "columns": columns}

            conn.commit()
            affected = cursor.rowcount
            cursor.close()
            conn.close()
            return {"success": True, "affected_rows": affected}
        except Exception as e:
            return {"success": False, "error": str(e)}

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
            conn = self.get_connection(db_name)
            cursor = conn.cursor()
            table_name_q = self._quote_identifier(table_name)
            cursor.execute(f"DROP TABLE IF EXISTS {table_name_q}")

            safe_columns = self._sanitize_column_names(df.columns)
            df.columns = safe_columns

            for col in df.select_dtypes(include=["object"]):
                sample = df[col].dropna().astype(str).tolist()[:20]
                is_numeric_like = all(
                    re.match(r"^\s*[\$\€\£]?\s*[\d\.,-]+\s*$", s)
                    for s in sample
                    if s.strip()
                )

                if is_numeric_like and sample:
                    try:
                        temp_col = df[col].astype(str).str.replace(r"[\$\€\£,\s]", "", regex=True)
                        temp_col = pd.to_numeric(temp_col, errors="coerce")
                        if temp_col.notnull().sum() > (df[col].notnull().sum() * 0.8):
                            df[col] = temp_col
                    except Exception:
                        pass

            columns_sql = []
            for col_name in df.columns:
                dtype = df[col_name].dtype

                if pd.api.types.is_integer_dtype(dtype):
                    col_type = "INT"
                elif pd.api.types.is_float_dtype(dtype):
                    col_type = "DOUBLE"
                elif pd.api.types.is_bool_dtype(dtype):
                    col_type = "TINYINT(1)"
                else:
                    col_type = "TEXT"

                columns_sql.append(f"{self._quote_identifier(col_name)} {col_type}")

            create_table_query = f"CREATE TABLE {table_name_q} ({', '.join(columns_sql)})"
            cursor.execute(create_table_query)

            df_insert = df.where(pd.notnull(df), None)

            placeholders = ", ".join(["%s"] * len(df.columns))
            column_list = ", ".join([self._quote_identifier(col) for col in df.columns])
            insert_query = f"INSERT INTO {table_name_q} ({column_list}) VALUES ({placeholders})"

            rows = [tuple(row) for row in df_insert.itertuples(index=False, name=None)]
            if rows:
                cursor.executemany(insert_query, rows)

            conn.commit()
            cursor.close()
            conn.close()

            return {
                "success": True,
                "table_name": table_name,
                "rows_imported": len(df),
                "columns": list(df.columns),
            }
        except Exception as e:
            raise Exception(f"Error creating table: {e}")

    def _sanitize_column_names(self, columns):
        """Create SQL-safe, unique column names from arbitrary headers."""
        used = set()
        sanitized = []

        for index, raw_name in enumerate(columns, start=1):
            name = str(raw_name or "").strip()
            name = re.sub(r"[^0-9a-zA-Z_]+", "_", name)
            name = re.sub(r"_+", "_", name).strip("_")

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
        """Quote MySQL identifiers defensively."""
        escaped = str(identifier).replace("`", "``")
        return f"`{escaped}`"

    def get_table_schema(self, db_name, table_name):
        """Get table schema for context using DESCRIBE"""
        try:
            conn = self.get_connection(db_name)
            cursor = conn.cursor()
            cursor.execute(f"DESCRIBE {self._quote_identifier(table_name)}")
            schema = [(row[0], row[1]) for row in cursor.fetchall()]
            cursor.close()
            conn.close()
            return schema
        except Exception as e:
            raise Exception(f"Error getting schema: {e}")

    def get_all_tables(self, db_name):
        """Get all tables in MySQL database"""
        try:
            conn = self.get_connection(db_name)
            cursor = conn.cursor()
            cursor.execute("SHOW TABLES")
            tables = [row[0] for row in cursor.fetchall()]
            cursor.close()
            conn.close()
            return tables
        except Exception as e:
            raise Exception(f"Error getting tables: {e}")

    def get_table_stats(self, db_name, table_name):
        """Get statistics and sample data for a table in MySQL"""
        try:
            conn = self.get_connection(db_name)

            cursor = conn.cursor()
            cursor.execute(f"SELECT COUNT(*) FROM {self._quote_identifier(table_name)}")
            row_count = cursor.fetchone()[0]

            cursor.execute(f"DESCRIBE {self._quote_identifier(table_name)}")
            columns_info = cursor.fetchall()

            stats = {
                "row_count": row_count,
                "columns": [],
                "sample_data": [],
            }

            for col in columns_info:
                col_name = col[0]
                col_type = col[1]

                cursor.execute(
                    f"SELECT COUNT(*) FROM {self._quote_identifier(table_name)} "
                    f"WHERE {self._quote_identifier(col_name)} IS NULL"
                )
                null_count = cursor.fetchone()[0]

                col_stats = {
                    "name": col_name,
                    "type": col_type,
                    "null_count": null_count,
                }

                if any(t in col_type.upper() for t in ["INT", "REAL", "DECIMAL", "NUMERIC", "FLOAT", "DOUBLE"]):
                    try:
                        cursor.execute(
                            f"SELECT MIN({self._quote_identifier(col_name)}), "
                            f"MAX({self._quote_identifier(col_name)}), "
                            f"AVG({self._quote_identifier(col_name)}), "
                            f"SUM({self._quote_identifier(col_name)}), "
                            f"COUNT({self._quote_identifier(col_name)}) "
                            f"FROM {self._quote_identifier(table_name)}"
                        )
                        m_min, m_max, m_avg, m_sum, m_count = cursor.fetchone()

                        def safe_float_round(val):
                            try:
                                if val is None:
                                    return None
                                return round(float(val), 2)
                            except Exception:
                                return None

                        col_stats["min"] = m_min
                        col_stats["max"] = m_max
                        col_stats["avg"] = safe_float_round(m_avg)
                        col_stats["sum"] = safe_float_round(m_sum)
                        col_stats["count"] = m_count
                    except Exception as sql_e:
                        sys.stderr.write(
                            f"DEBUG: SQL STATS ERROR on column {col_name}: {str(sql_e)}\n"
                        )

                stats["columns"].append(col_stats)

            try:
                cursor.execute(f"SELECT * FROM {self._quote_identifier(table_name)} LIMIT 100")
                sample_rows = cursor.fetchall()
                col_names = [desc[0] for desc in cursor.description]

                for row in sample_rows:
                    stats["sample_data"].append(dict(zip(col_names, row)))
            except Exception as sample_e:
                sys.stderr.write(f"DEBUG: SAMPLE DATA ERROR: {str(sample_e)}\n")

            cursor.close()
            conn.close()
            return {"success": True, "stats": stats}
        except Exception as e:
            sys.stderr.write(f"DEBUG: GLOBAL GET_TABLE_STATS ERROR: {str(e)}\n")
            return {"success": False, "error": str(e)}
