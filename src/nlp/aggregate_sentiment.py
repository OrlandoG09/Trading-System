import pandas as pd
import logging 
from src.config import Config   

#Configuración de Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)    

def aggregate_daily_sentiment():
    """
    Convierte las noticias individuales en un Score Diario por Ticker.
    """
    input_path = Config.DATA_PROCESSED / "news_scored.parquet"
    output_path = Config.DATA_PROCESSED / "features_sentiment.parquet"
    
    if not input_path.exists():
        logger.error(f"No encontré: {input_path}")
        return

    logger.info("Cargando noticias puntuadas")
    df = pd.read_parquet(input_path)
    
    # Normalizar Fechas
    # Convertimos la fecha+hora exacta a solo FECHA (YYYY-MM-DD) para agrupar por día
    df['date'] = df['date'].dt.normalize()
    
    logger.info("ClassName: Agrupando noticias por día y activo")
    
    # Agrupación Matemática
    # Por cada Día y cada Ticker, calculamos:
    # mean: El promedio del sentimiento (El humor general del día)
    # count: Cuántas noticias hubo (El volumen de ruido/atención)
    daily_sentiment = df.groupby(['date', 'ticker'])['sentiment_score'].agg(['mean', 'count']).reset_index()
    
    # Renombrar columnas para que sean claras
    daily_sentiment.columns = ['date', 'ticker', 'sentiment_avg', 'news_count']
    
    # Guardado
    logger.info(f"Guardando características de sentimiento diario en: {output_path}")
    daily_sentiment.to_parquet(output_path, engine='fastparquet', compression='snappy')
    
    logger.info(f"Dimensiones finales: {daily_sentiment.shape}")
    logger.info(f"Ejemplo:\n{daily_sentiment.tail(5)}")

if __name__ == "__main__":
    aggregate_daily_sentiment()