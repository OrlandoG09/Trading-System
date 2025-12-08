import vectorbt as vbt
import pandas as pd
import numpy as np
import logging
from src.config import Config

# Configuración de Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def optimize_alpha_score():
    """
    Optimización Paramétrica:
    Ejecuta la estrategia Híbrida múltiples veces con distintos pesos (Impact Factors)
    para encontrar el equilibrio perfecto entre Técnica y Noticias.
    """
    input_path = Config.DATA_PROCESSED / "features_master.parquet"
    if not input_path.exists(): return

    logger.info("Cargando datos...")
    df = pd.read_parquet(input_path)

    # PREPARACIÓN DE DATOS
    close = df.pivot(index='date', columns='ticker', values='close').ffill()
    ema_fast = df.pivot(index='date', columns='ticker', values='ema_fast').ffill()
    ema_slow = df.pivot(index='date', columns='ticker', values='ema_slow').ffill()
    
    # Sentimiento suavizado (7 días)
    sentiment_raw = df.pivot(index='date', columns='ticker', values='sentiment_avg').ffill().fillna(0.0)
    sentiment_smooth = sentiment_raw.rolling(window=7).mean().fillna(0.0)

    # DEFINIR EL MOTOR DE INDICADORES (Indicator Factory)
    # Esta es la magia de vbt. Definimos una función que acepta un parámetro 'impact'.
    # vbt correrá esta función para cada valor del rango que le demos.
    
    def calculate_alpha(tech_spread, sentiment, impact):
        # Fórmula: Score Técnico + (Sentimiento * Peso)
        return tech_spread + (sentiment * impact)

    AlphaIndicator = vbt.IndicatorFactory(
        class_name='AlphaOptimizer',
        input_names=['tech_spread', 'sentiment'],
        param_names=['impact'], # <--- Este es el parámetro a optimizar
        output_names=['alpha_score']
    ).from_apply_func(calculate_alpha)

    #COMPONENTE TÉCNICO BASE
    tech_score = (ema_fast - ema_slow) / close

    # EJECUCIÓN MASIVA (El Torneo)
    # Probamos pesos desde 0.0 hasta 2.0 en pasos de 0.1
    # np.arange(start, stop, step) -> [0.0, 0.1, 0.2 ... 2.0]
    test_range = np.arange(0.0, 2.1, 0.1)
    
    logger.info(f"Probando {len(test_range)} configuraciones distintas...")
    
    # Run: Ejecuta todas las combinaciones a la vez
    alpha = AlphaIndicator.run(
        tech_score, 
        sentiment_smooth, 
        impact=test_range,
        param_product=True # Prueba cada peso contra cada activo
    )

    # GENERAR SEÑALES
    # Entrada cuando Alpha > 0, Salida cuando Alpha < 0
    entries = alpha.alpha_score > 0.0
    exits = alpha.alpha_score < 0.0
    
    # SIMULACIÓN DE PORTAFOLIO (Portfolio)
    # vbt calcula el retorno para las 20 versiones x 5 activos = 100 backtests en 1 segundo.
    pf = vbt.Portfolio.from_signals(
        close=close, 
        entries=entries, 
        exits=exits, 
        init_cash=10000, 
        fees=0.001, 
        freq='1D'
    )

    # ANÁLISIS DE RESULTADOS
    # Obtenemos el Sharpe Ratio para cada combinación
    sharpe = pf.sharpe_ratio()
    
    # Promediamos el Sharpe de todos los activos para ver qué peso es mejor EN GENERAL
    # El índice del resultado será el valor de 'impact'
    avg_sharpe_by_impact = sharpe.groupby('alphaoptimizer_impact').mean()
    
    # Encontramos el ganador
    best_impact = avg_sharpe_by_impact.idxmax()
    best_sharpe = avg_sharpe_by_impact.max()

    print("\n" + "="*60)
    print(f"RESULTADOS DE LA OPTIMIZACIÓN ({len(test_range)} Escenarios)")
    print("="*60)
    print(f"El MEJOR Factor de Impacto Global es: {best_impact:.1f}")
    print(f"Sharpe Ratio Promedio: {best_sharpe:.4f}")
    print("-" * 60)
    
    print("\nTOP 5 CONFIGURACIONES:")
    print(avg_sharpe_by_impact.sort_values(ascending=False).head(5))
    
    print("\n" + "="*60)
    print("ANÁLISIS POR ACTIVO (Mejor Peso Individual)")
    print("="*60)
    # Ver cuál es el mejor peso para cada activo individualmente
    # unstack para ver tabla: Filas=Impacto, Columnas=Ticker
    sharpe_table = sharpe.unstack(level='alphaoptimizer_impact')
    print(sharpe_table.idxmax(axis=1)) # Muestra el mejor peso para cada ticker
    
    print("\n" + "="*60)
    print("CURVA DE RENDIMIENTO (Impacto vs Sharpe)")
    print("="*60)
    print(avg_sharpe_by_impact)

if __name__ == "__main__":
    optimize_alpha_score()