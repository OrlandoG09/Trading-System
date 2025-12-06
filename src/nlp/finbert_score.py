import pandas as pd
import torch
import logging
from transformers import BertTokenizer, BertForSequenceClassification
from src.config import Config
import numpy as np

# Configuración de Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_sentiment_score(text, tokenizer, model):
    """
    Recibe un texto y devuelve un puntaje numérico entre -1 y 1.
    -1 = Muy Negativo
     0 = Neutral
    +1 = Muy Positivo
    """
    if not text or pd.isna(text):
        return 0.0
        
    # Tokenización (Convertir texto a números para la IA)
    inputs = tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=512)
    
    #Inferencia (El modelo piensa)
    with torch.no_grad(): # No necesitamos entrenar, solo predecir 
        outputs = model(**inputs)
    
    # Procesar Probabilidades
    probs = torch.nn.functional.softmax(outputs.logits, dim=-1)
    probs = probs.numpy()[0] # [Positivo, Negativo, Neutral] (El orden depende del modelo)
    
    # FinBERT de ProsusAI devuelve: [Positive, Negative, Neutral] en ese orden específico.
    # Verificamos el config del modelo para estar seguros, pero este es el estándar.
    score_pos = probs[0]
    score_neg = probs[1]
    score_neu = probs[2]
    
    # órmula Maestra de Sentimiento
    # Restamos lo negativo de lo positivo. Lo neutral diluye el score hacia 0.
    final_score = score_pos - score_neg
    
    return final_score

def run_finbert_pipeline():
    input_path = Config.DATA_PROCESSED / "news_clean.parquet"
    output_path = Config.DATA_PROCESSED / "news_scored.parquet"
    
    if not input_path.exists():
        logger.error(f" No encontré noticias limpias en: {input_path}")
        return

    logger.info("Cargando modelo FinBERT")
    
    # Usamos el modelo específico de ProsusAI entrenado para finanzas
    model_name = Config.FINBERT_MODEL 
    tokenizer = BertTokenizer.from_pretrained(model_name)
    model = BertForSequenceClassification.from_pretrained(model_name)
    
    # Poner el modelo en modo evaluación (más rápido)
    model.eval()
    
    logger.info("Cargando noticias...")
    df = pd.read_parquet(input_path)
    
    # Para pruebas rápidas, si tienes muchas noticias, procesamos todas.
    # Como tienes ~700, la CPU lo hará en 1-3 minutos.
    total_news = len(df)
    logger.info(f"Analizando sentimiento de {total_news} titulares...")
    
    # Aplicamos la función fila por fila
    # Nota: Para millones de datos usaríamos 'batching', pero para <5000 esto es perfecto.
    scores = []
    
    # Usamos un bucle simple con contador para que veas el progreso
    for i, row in df.iterrows():
        # Combinamos Titular + Punto + Resumen 
        headline = str(row['headline_clean'])
        summary = str(row['summary_clean']) if 'summary_clean' in row else ""
        # Unimos todo para que FinBERT tenga más contexto
        text = f"{headline}. {summary}"
        
        score = get_sentiment_score(text, tokenizer, model)
        scores.append(score)
        
        if i % 50 == 0:
            logger.info(f"   Progreso: {i}/{total_news} noticias procesadas...")
            
    df['sentiment_score'] = scores
    
    # Guardar
    df.to_parquet(output_path, engine='fastparquet', compression='snappy')
    
    logger.info(f"Análisis completado. Guardado en: {output_path}")
    
    # Mostrar los extremos (Lo más positivo y lo más negativo)
    print("\n" + "="*50)
    print(" NOTICIA MÁS POSITIVA:")
    print(df.sort_values('sentiment_score', ascending=False).iloc[0][['headline', 'sentiment_score']])
    print("-" * 50)
    print("NOTICIA MÁS NEGATIVA:")
    print(df.sort_values('sentiment_score', ascending=True).iloc[0][['headline', 'sentiment_score']])
    print("="*50 + "\n")

if __name__ == "__main__":
    run_finbert_pipeline()