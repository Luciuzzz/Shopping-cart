import sqlite3
import os
from typing import Optional

class Database:
    def __init__(self, db_path: str = "database/supermarket.db"):
        self.db_path = db_path
        self._ensure_database_exists()
    
    def _ensure_database_exists(self):
        """Verificar que la base de datos y tablas existan"""
        if not os.path.exists(self.db_path):
            self._create_database()
    
    def _create_database(self):
        """Crear base de datos con estructura completa"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Ejecutar script SQL completo (tu estructura)
        with open('database/schema.sql', 'r') as f:
            sql_script = f.read()
            cursor.executescript(sql_script)
        
        # Insertar datos iniciales
        with open('database/seed_data.sql', 'r') as f:
            seed_script = f.read()
            cursor.executescript(seed_script)
        
        conn.commit()
        conn.close()
    
    def get_connection(self) -> sqlite3.Connection:
        """Obtener conexión a la base de datos"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Para acceso por nombre de columna
        return conn
    
    def execute_query(self, query: str, params: tuple = ()):
        """Ejecutar consulta y retornar resultados"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        
        if query.strip().upper().startswith('SELECT'):
            results = cursor.fetchall()
            conn.close()
            return results
        else:
            conn.commit()
            last_id = cursor.lastrowid
            conn.close()
            return last_id
    
    def execute_many(self, query: str, params_list: list):
        """Ejecutar múltiples inserciones"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.executemany(query, params_list)
        conn.commit()
        conn.close()

# Instancia global
db = Database()