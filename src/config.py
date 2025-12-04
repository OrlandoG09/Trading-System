import os
from pathlib import Path

class Config:
    
   
    
  
    #RUTAS DEL PROYECTO 
  
   
    BASE_DIR = Path(__file__).resolve().parent.parent
    
    DATA_DIR = BASE_DIR / "data"
    DATA_RAW = DATA_DIR / "raw"
    DATA_PROCESSED = DATA_DIR / "processed"
    MODELS_DIR = BASE_DIR / "models"
    LOGS_DIR = BASE_DIR / "logs"

    # Archivos específicos
    PRICES_PARQUET = DATA_RAW / "prices_sample.parquet"
    
   
    #UNIVERSO DE ACTIVOS
   
    TICKERS = ['AAPL', 'SPY', 'EURUSD=X', 'GLD', 'BTC-USD']


    #ESTRATEGIA (Trend Following + AQR Logic)
  
    # Ventanas de Momentum (Días de trading: 21=1 mes, 63=3 meses, 252=1 año)

    MOMENTUM_WINDOWS = [21, 63, 252] 
    
    # Medias Móviles para filtros de tendencia rápida
    SMA_FAST = 20
    SMA_SLOW = 50 
    
    # Gestión de Riesgo
    # Target Volatility: 10% anualizado (0.10). 
    VOL_TARGET = 0.10 
    
  
    # INTELIGENCIA ARTIFICIAL (NLP)
    # Modelo pre-entrenado financiero (HuggingFace)
    FINBERT_MODEL = "ProsusAI/finbert"

    # Parámetros de Ingesta de Noticias
    NEWS_HISTORY_DAYS = 3   
    NEWS_TOP_N = 50         
    
    # Configuración de Hardware (Detecta si tienes GPU disponible, si no CPU)
    DEVICE = "cuda" if os.environ.get("CUDA_VISIBLE_DEVICES") else "cpu"

# Bloque de inicialización automática de carpetas
# Solo se ejecuta si corres este archivo directamente para probar
if __name__ == "__main__":
    print(f"Configurando directorios en: {Config.BASE_DIR}")
    for path in [Config.DATA_RAW, Config.DATA_PROCESSED, Config.MODELS_DIR, Config.LOGS_DIR]:
        path.mkdir(parents=True, exist_ok=True)
        print(f"Verificado: {path}") 