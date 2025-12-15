import os
from pathlib import Path
from dotenv import load_dotenv

# BLOQUE DE CARGA ROBUSTA
# Encontrar la raíz del proyecto (2 niveles arriba de este archivo)
BASE_DIR = Path(__file__).resolve().parent.parent

#  Construir la ruta exacta al archivo .env
ENV_PATH = BASE_DIR / ".env"

# Forzar la carga desde esa ruta específica
print(f"Intentando cargar .env desde: {ENV_PATH}") # Debug temporal
if ENV_PATH.exists():
    load_dotenv(dotenv_path=ENV_PATH)
    print(" Archivo .env encontrado.")
else:
    print(" ALERTA: El archivo .env NO existe en la ruta esperada.")



class Config:
    """
    Configuración centralizada del sistema Hybrid Market Intel.
    """
    
    # Rutas Base
    BASE_DIR = BASE_DIR # Usamos la que calculamos arriba
    DATA_DIR = BASE_DIR / "data"
    DATA_RAW = DATA_DIR / "raw"
    DATA_PROCESSED = DATA_DIR / "processed"
    MODELS_DIR = BASE_DIR / "models"
    LOGS_DIR = BASE_DIR / "logs"

    # Universos y Estrategia
    # DICCIONARIO DE ACTIVOS ORGANIZADOS POR SECTOR
    TICKER_CATEGORIES = {
        "🚀 Big Tech & IA": [
            "AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META", "TSLA", "AMD", "INTC", "IBM",
            "ORCL", "CRM", "ADBE", "CSCO", "NFLX", "QCOM", "TXN", "AVGO", "PLTR", "UBER"
        ],
        "🦉 Criptomonedas": [
            "BTC-USD", "ETH-USD", "SOL-USD", "BNB-USD", "XRP-USD", "ADA-USD", "DOGE-USD",
            "AVAX-USD", "DOT-USD", "MATIC-USD", "LTC-USD", "SHIB-USD", "LINK-USD", "UNI7083-USD", "ATOM-USD"
        ],
        "🌎 Índices & ETFs": [
            "SPY", "QQQ", "DIA", "IWM", "VOO", "VTI", "TQQQ", "SQQQ", "ARKK", "EEM",
            "XLF", "XLK", "XLV", "XLE", "GLD", "SLV", "GDX", "TLT", "HYG", "VIXY"
        ],
        "💱 Forex (Divisas)": [
            "EURUSD=X", "USDMXN=X", "GBPUSD=X", "USDJPY=X", "AUDUSD=X", "USDCAD=X",
            "USDCHF=X", "NZDUSD=X", "EURGBP=X", "EURJPY=X"
        ],
        "🏭 Industria & Consumo": [
            "WMT", "KO", "PEP", "MCD", "DIS", "NKE", "SBUX", "COST", "TGT", "PG",
            "JNJ", "PFE", "MRK", "BA", "CAT", "GE", "MMM", "F", "GM", "TM"
        ],
        "🏦 Finanzas & Bancos": [
            "JPM", "BAC", "WFC", "C", "GS", "MS", "BLK", "V", "MA", "AXP",
            "PYPL", "SQ", "COIN", "HOOD", "SOFI"
        ],
        "🛢️ Commodities & Energía": [
            "XOM", "CVX", "BP", "SHEL", "COP", "OXY", "VALE", "RIO", "BHP", "FCX",
            "CL=F", "GC=F", "SI=F", "NG=F", "HG=F" 
        ]
    }

   
    # Esta línea aplana el diccionario para crear la lista simple que necesita tu pipeline.
    # Así no tienes que escribir los tickers dos veces.
    TICKERS = [ticker for category in TICKER_CATEGORIES.values() for ticker in category]

    MOMENTUM_WINDOWS = [21, 63, 252] 
    SMA_FAST = 20
    SMA_SLOW = 50 
    SMA_VERY_SLOW = 200
    VOL_TARGET = 0.10 
    
    # --- INTELIGENCIA ARTIFICIAL & API KEYS ---
    FINBERT_MODEL = "ProsusAI/finbert"
    
    # Aquí leemos la variable cargada
    FINNHUB_KEY = os.getenv("FINNHUB_API_KEY")
    
    # Validación inmediata al importar
    if not FINNHUB_KEY:
        print("ADVERTENCIA: La variable FINNHUB_API_KEY está vacía o es None.")
    
    NEWS_HISTORY_DAYS = 365
    NEWS_TOP_N = 50
    
    DEVICE = "cuda" if os.environ.get("CUDA_VISIBLE_DEVICES") else "cpu"

if __name__ == "__main__":
    # Test rápido si ejecutas este archivo solo
    print(f" Llave cargada: {str(Config.FINNHUB_KEY)[:5]}")