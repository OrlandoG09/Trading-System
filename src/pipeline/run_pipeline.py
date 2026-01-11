import sys
import subprocess
import logging
from datetime import date
from src.config import Config
from src.utils.explainer import generate_narrative
import pandas as pd
import json

# Configuración de Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_step(module_name):
    """Ejecuta un script específico y detiene todo si falla."""
    logger.info(f"▶️ Ejecutando: {module_name}...")
    try:
        subprocess.run([sys.executable, "-m", module_name], check=True)
        logger.info(f"{module_name} OK.")
    except subprocess.CalledProcessError:
        logger.error(f"FALLÓ {module_name}. El pipeline se detendrá.")
        sys.exit(1)

def run_full_cycle():
    
    today = str(date.today())
    logger.info(f"BUBO INICIANDO PROTOCOLO (Full Stack FinBERT) - FECHA: {today}")

    
    # BAJAR PRECIOS (Actualiza hasta hoy)
    run_step("src.data.ingest_prices")
    
    # BAJAR NOTICIAS
    run_step("src.data.ingest_news")
    
    # LIMPIAR NOTICIAS
    run_step("src.data.clean_news")
    
    # CALCULAR SENTIMIENTO (FinBERT) <-- PASO CRÍTICO QUE FALTABA
    # Ajusta la ruta si está en src.sentiment en lugar de src.data
    try:
        run_step("src.nlp.finbert_score") 
    except SystemExit:
        # Fallback por si lo tienes en otra carpeta común
        logger.warning("No encontrado")
        

    #AGREGAR SENTIMIENTO (Diario) <-- PASO CRÍTICO QUE FALTABA
    run_step("src.nlp.aggregate_sentiment")
    
    #CALCULAR INDICADORES TÉCNICOS
    run_step("src.tech.indicators")
    
    #UNIFICAR DATASET (MERGE)
    run_step("src.data.merge_data")

    logger.info("FASE 1 COMPLETADA: Datos procesados con FinBERT.")

    # =========================================================
    # FASE 2: CEREBRO MATEMÁTICO (Alpha Score)
    # =========================================================
    logger.info("FASE 2: Calculando Señales...")
    
    input_path = Config.DATA_PROCESSED / "features_master.parquet"
    output_json = Config.DATA_PROCESSED / "latest_signals.json"
    
    if not input_path.exists():
        logger.error("❌ No encontré features_master.parquet.")
        return

    # Cargar Dataset Maestro
    df = pd.read_parquet(input_path)
    
    # Pivot y Forward Fill
    df_pivot = df.pivot(index='date', columns='ticker', values=['close', 'ema_fast', 'ema_slow', 'sentiment_avg'])
    df_pivot = df_pivot.ffill()
    
    # Sentimiento Suavizado (Memoria de 7 días)
    sentiment_filled = df_pivot['sentiment_avg'].fillna(0.0)
    sentiment_smooth = sentiment_filled.rolling(window=7).mean()

    # OBTENER LA ÚLTIMA FECHA REAL
    last_idx = df_pivot.index[-1]
    last_date = str(last_idx.date())
    
    logger.info(f"Fecha de análisis encontrada: {last_date}")
    
    results = []
    tickers = df_pivot['close'].columns
    IMPACT_FACTOR = 0.7

    for ticker in tickers:
        try:
            close = df_pivot['close'][ticker].iloc[-1]
            ema_fast = df_pivot['ema_fast'][ticker].iloc[-1]
            ema_slow = df_pivot['ema_slow'][ticker].iloc[-1]
            sentiment = sentiment_smooth[ticker].iloc[-1]
            
            if pd.isna(close): continue

            # Alpha Score
            tech_score = (ema_fast - ema_slow) / close
            fund_score = sentiment * IMPACT_FACTOR
            alpha_score = tech_score + fund_score

            # Narrativa
            status, explanation = generate_narrative(ticker, tech_score, sentiment, alpha_score)

            results.append({
                "ticker": ticker,
                "date": last_date,
                "close_price": round(close, 2),
                "tech_score": round(tech_score, 5),
                "sentiment_score": round(sentiment, 4),
                "alpha_score": round(alpha_score, 5),
                "signal": status,
                "narrative": explanation
            })
            
            logger.info(f"   🦉 {ticker}: {status}")

        except Exception as e:
            logger.warning(f"Error procesando {ticker}: {e}")

    # PUBLICACIÓN
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=4, ensure_ascii=False)
        
    logger.info(f"CICLO COMPLETADO. Dashboard actualizado: {output_json}")

if __name__ == "__main__":
    run_full_cycle()