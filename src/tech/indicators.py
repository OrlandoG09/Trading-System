import pandas as pd
import numpy as np
import logging
from src.config import Config
import warnings
# Configuración de Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def calculate_rsi(series, period=14):
    """
    Calcula el Relative Strength Index (RSI) manualmente con Pandas.
    Fórmula: 100 - (100 / (1 + RS))
    """
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_atr(df, period=14):
    """
    Calcula el Average True Range (ATR) para medir volatilidad absoluta ($).
    TR = Max(High-Low, Abs(High-PrevClose), Abs(Low-PrevClose))
    """
    high = df['high']
    low = df['low']
    close = df['close']
    prev_close = close.shift(1)
    
    # True Range (El mayor de 3 distancias)
    tr1 = high - low
    tr2 = (high - prev_close).abs()
    tr3 = (low - prev_close).abs()
    
    true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    
    #  Average True Range (Promedio móvil del TR)
    atr = true_range.rolling(window=period).mean()
    return atr

def add_indicators(group):

    """
    Función que recibe el DataFrame de UN SOLO Ticker y le agrega columnas técnicas.
    """
    # Ordenar por fecha es vital para cálculos temporales
    group = group.sort_values('date')

    # Si es sábado/domingo y hay NaNs, rellenamos con el precio del viernes.
    # Esto evita que se borren filas y mantiene la continuidad para Bitcoin.
    group[['close', 'high', 'low', 'open']] = group[['close', 'high', 'low', 'open']].ffill()

    # Retornos (Cambio porcentual diario)
    group['returns'] = group['close'].pct_change(fill_method=None)
    
    # Log Returns (Mejor para modelos matemáticos)
    group['log_returns'] = np.log(group['close'] / group['close'].shift(1))
    
    # Volatilidad (Desviación estándar de 21 días / 1 mes)
    # Anualizada superficialmente (multiplicada por raíz de 252) para referencia
    group['volatility_21d'] = group['log_returns'].rolling(window=21).std() * np.sqrt(252)
    
    # Tendencia (EMAs) - Usamos los params de Config
    group['ema_fast'] = group['close'].ewm(span=Config.SMA_FAST, adjust=False).mean()
    group['ema_slow'] = group['close'].ewm(span=Config.SMA_SLOW, adjust=False).mean()
    
    # Momentum (RSI)
    group['rsi'] = calculate_rsi(group['close'], period=14)
    
    # Riesgo Absoluto (ATR)
    group['atr'] = calculate_atr(group, period=14)
    
    # Distancia a la Media (Para detectar sobre-extensión)
    # (Precio - EMA_Slow) / EMA_Slow
    group['trend_strength'] = (group['close'] - group['ema_slow']) / group['ema_slow']
    
    return group

def build_technical_features():
    """
    Pipeline principal: Carga precios -> Calcula indicadores -> Guarda Features
    """
    warnings.simplefilter(action='ignore', category=FutureWarning)
    input_path = Config.DATA_RAW / "prices_5y.parquet"
    output_path = Config.DATA_PROCESSED / "features_technical.parquet"
    
    if not input_path.exists():
        logger.error(f" No encontré el archivo de precios: {input_path}")
        return

    # Cargar datos
    logger.info(" Cargando precios históricos...")
    df = pd.read_parquet(input_path)
    
    # Validar que tengamos las columnas necesarias 
    required_cols = ['date', 'ticker', 'close', 'high', 'low']
    if not all(col in df.columns for col in required_cols):
        logger.error(f"Faltan columnas. Tu archivo tiene: {df.columns}")
        return
    
    logger.info(f"Calculando indicadores para {len(df['ticker'].unique())} activos.")
    
    # Aplicamos indicadores (incluye el rellenado de fines de semana)
    df_features = df.groupby('ticker', group_keys=False).apply(add_indicators)
    
    # Borramos solo las filas iniciales (warm-up) donde NO se pudo calcular la EMA.
    # Como ya hicimos ffill, los fines de semana ya tienen precio, así que no se borrarán.
    df_features = df_features.dropna(subset=['ema_slow'])

    # Guardar
    Config.DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
    df_features.to_parquet(output_path, engine='fastparquet', compression='snappy')
    
    logger.info(f" Ingeniería de Características terminada.")
    logger.info(f" Guardado en: {output_path}")
    logger.info(f"Nuevas Dimensiones: {df_features.shape}")
    logger.info(f"Ejemplo:\n{df_features[['date', 'ticker', 'close', 'ema_slow', 'rsi']].tail(5)}")

if __name__ == "__main__":
    build_technical_features()

    
    