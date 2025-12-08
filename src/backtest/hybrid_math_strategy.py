import vectorbt as vbt
import pandas as pd
import numpy as np
import logging
from src.config import Config

# Configuración de Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_math_strategy():
    """
    Estrategia Cuantitativa Avanzada: Alpha Score.
    No usa lógica booleana (AND/OR). Usa Álgebra Lineal (Sumas Ponderadas).
    """
    input_path = Config.DATA_PROCESSED / "features_master.parquet"
    if not input_path.exists(): return

    logger.info("Cargando Master Dataset...")
    df = pd.read_parquet(input_path)

    # PREPARACIÓN DE MATRICES

    # Usamos ffill() para persistencia de datos 
    close = df.pivot(index='date', columns='ticker', values='close').ffill()
    ema_fast = df.pivot(index='date', columns='ticker', values='ema_fast').ffill()
    ema_slow = df.pivot(index='date', columns='ticker', values='ema_slow').ffill()
    
    # Sentimiento con memoria de 7 días (suavizado)
    sentiment_raw = df.pivot(index='date', columns='ticker', values='sentiment_avg').ffill().fillna(0.0)
    sentiment_smooth = sentiment_raw.rolling(window=7).mean().fillna(0.0)

    # INGENIERÍA MATEMÁTICA (EL INDICADOR ROBUSTO)

    
    # A) Componente Técnico: Spread Normalizado
    # Calculamos la distancia porcentual entre las EMAs.
    # Si es > 0, es tendencia alcista. Si es 0.05, es una tendencia MUY fuerte.
    tech_score = (ema_fast - ema_slow) / close
    
    # B) Componente Fundamental: Impacto de IA
    # El sentimiento suele ser pequeño (0.1, 0.05). Lo multiplicamos por un "Factor de Impacto"
    # para que tenga peso contra la tendencia.
    # IMPACT_FACTOR = 0.5 significa que una noticia fuerte vale tanto como un 50% de tendencia.
    IMPACT_FACTOR = 0.2
    fund_score = sentiment_smooth * IMPACT_FACTOR
    
    # EL ALPHA SCORE (La Fusión) 



    # Sumamos ambos vectores.
    # Alpha = (Tendencia) + (Noticias)
    alpha_score = tech_score + fund_score

    #GENERACIÓN DE SEÑALES
  
    
    # Regla: Compramos cuando el Alpha Score cruza CERO hacia arriba
    # Esto significa que la suma de fuerzas es positiva.
    entries_hybrid = alpha_score > 0.0
    exits_hybrid = alpha_score < 0.0

    # Limpieza de señales (Evitar re-compras diarias)
    entries_hybrid = entries_hybrid.vbt.signals.clean()
    exits_hybrid = exits_hybrid.vbt.signals.clean()
    
    # Benchmark (Solo Técnico) para comparar
    entries_tech = tech_score > 0.0
    exits_tech = tech_score < 0.0
    entries_tech = entries_tech.vbt.signals.clean()
    exits_tech = exits_tech.vbt.signals.clean()

    # SIMULACIÓN
 
    logger.info("Ejecutando Math Backtest...")
    
    pf_tech = vbt.Portfolio.from_signals(
        close=close, entries=entries_tech, exits=exits_tech, 
        init_cash=10000, fees=0.001, slippage=0.001, freq='1D'
    )
    
    pf_hybrid = vbt.Portfolio.from_signals(
        close=close, entries=entries_hybrid, exits=exits_hybrid, 
        init_cash=10000, fees=0.001, slippage=0.001, freq='1D'
    )

    # REPORTE
  
    print("\n" + "="*60)
    print("ESTRATEGIA MATEMÁTICA: ALPHA SCORE (Suma Ponderada)")
    print("="*60)
    
    print(f"{'MÉTRICA':<20} | {'TÉCNICO':<15} | {'ALPHA SCORE (IA)':<15}")
    print("-" * 60)
    print(f"{'Retorno Total':<20} | {pf_tech.total_return().mean()*100:14.2f}% | {pf_hybrid.total_return().mean()*100:14.2f}%")
    print(f"{'Win Rate':<20} | {pf_tech.trades.win_rate().mean()*100:14.2f}% | {pf_hybrid.trades.win_rate().mean()*100:14.2f}%")
    print(f"{'Sharpe Ratio':<20} | {pf_tech.sharpe_ratio().mean():14.4f}  | {pf_hybrid.sharpe_ratio().mean():14.4f}")
    print("-" * 60)
    
    print("\nDETALLE POR ACTIVO:")
    comparison = pd.DataFrame({
        'Tecnico_%': pf_tech.total_return() * 100,
        'Hibrido_%': pf_hybrid.total_return() * 100,
        'Diferencia': (pf_hybrid.total_return() - pf_tech.total_return()) * 100,
        'Trades_IA': pf_hybrid.trades.count()
    })
    print(comparison)
    print("="*60)

if __name__ == "__main__":
    run_math_strategy()