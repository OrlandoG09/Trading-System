import vectorbt as vbt 
import pandas as pd 
import logging 
from src.config import Config 

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)        

def run_trend_simulation():
 
    """
    Ejecuta un backtest vectorizado de la estrategia Trend Following (Cruce de EMAs).
    """
    # Cargar los datos procesados (con indicadores)
    input_path = Config.DATA_PROCESSED / "features_technical.parquet"
    if not input_path.exists():
        logger.error("No encontré el archivo de features. Ejecuta primero src.tech.indicators")
        return

    logger.info("Cargando datos y preparando matrices...")
    df = pd.read_parquet(input_path)

    # Transformación a Formato 'Wide' (Requisito de VectorBT)
    # VectorBT necesita que cada COLUMNA sea un Ticker y el ÍNDICE sea la Fecha.
    # Usamos pivot() para transformar la tabla.
    
    # Precios de Cierre
    close_price = df.pivot(index='date', columns='ticker', values='close')
    
    # Indicadores
    ema_fast = df.pivot(index='date', columns='ticker', values='ema_fast')
    ema_slow = df.pivot(index='date', columns='ticker', values='ema_slow')

    # Definir la Lógica de la Estrategia
    # Regla de Entrada: EMA Rápida > EMA Lenta (Cruce Dorado)
    entries = ema_fast > ema_slow
    
    # Regla de Salida: EMA Rápida < EMA Lenta (Cruce de la Muerte)
    exits = ema_fast < ema_slow

    # Limpieza: Eliminar señales en zonas donde no hay datos (al principio de la historia)
    entries = entries.vbt.signals.clean()
    exits = exits.vbt.signals.clean()

    logger.info(f"Ejecutando simulación para: {close_price.columns.tolist()}")

    # El Motor de Backtesting (Portfolio)
    # Simulamos con $10,000 iniciales, fees de 0.1% (común en crypto/brokers)
    # freq='1D' indica que los datos son diarios para calcular métricas anualizadas correctamente
    portfolio = vbt.Portfolio.from_signals(
        close=close_price,
        entries=entries,
        exits=exits,
        init_cash=10000,
        fees=0.001,      # 0.1% comisión por operación
        slippage=0.001,  # 0.1% deslizamiento (precio real vs teórico)
        freq='1D'        # Frecuencia diaria
    )

    # Reporte de Resultados
    print("\n" + "="*50)
    print("REPORTE DE ESTRATEGIA: TREND FOLLOWING (EMA CRUCE)")
    print("="*50)
    
    # Estadísticas Totales (Promedio de todos los activos)
    print(portfolio.stats())

    print("\n" + "="*50)
    print("RENDIMIENTO POR ACTIVO")
    print("="*50)
    # Rendimiento individual
    print(portfolio.total_return() * 100)

    # Guardar métricas (Opcional para futuro dashboard)
    # Por ahora solo lo vemos en consola.

if __name__ == "__main__":
    run_trend_simulation()
