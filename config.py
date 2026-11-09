"""Carrega as configurações do arquivo .env (nunca coloque senha no código)."""
import os
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_USER = os.getenv("DB_USER", "")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "consumozero")

# Coordenadas usadas na consulta de clima (padrão: Hortolândia-SP)
CLIMA_LAT = float(os.getenv("CLIMA_LAT", "-22.858"))
CLIMA_LON = float(os.getenv("CLIMA_LON", "-47.220"))

# Servidor de alertas (socket TCP)
ALERTA_HOST = os.getenv("ALERTA_HOST", "127.0.0.1")
ALERTA_PORT = int(os.getenv("ALERTA_PORT", "5050"))

FLASK_DEBUG = os.getenv("FLASK_DEBUG", "0") == "1"
