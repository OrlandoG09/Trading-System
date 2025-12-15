def generate_narrative(ticker, tech_score, sentiment_score, alpha_score):
    """
    Narrativa generada por 'Bubo', el Búho de Datos.
    Arquetipo: El Sabio Guardián / El Vigilante Nocturno.
    Tono: Calmado, analítico, prudente, visionario.
    """
    # Umbrales
    STRONG_THRESHOLD = 0.05
    
    explanation = ""
    status = "NEUTRAL"

    # Variables de Estado
    is_tech_bullish = tech_score > 0
    is_news_good = sentiment_score > 0
    
    # Encabezado del Personaje (La firma de Bubo)
    intro = "🦉 **La Visión de Bubo:**\n"
    
    #LÓGICA DE PERSONALIDAD
    
    # CASO: COMPRA FUERTE (Sinergia Total)
    if alpha_score > 0 and is_tech_bullish and is_news_good:
        status = "🟢 VUELO CONFIRMADO"
        explanation = (f"{intro}La niebla se ha disipado en **{ticker}**. "
                       f"Mis análisis confirman que la tendencia técnica está respaldada por noticias sólidas. "
                       f"Es un trayecto claro y seguro para tu capital. Proceda con sabiduría.")

    # CASO: COMPRA POR OPORTUNIDAD (Fundamental)
    elif alpha_score > 0 and not is_tech_bullish and is_news_good:
        status = "🟢 VISIÓN NOCTURNA (Smart Buy)"
        explanation = (f"{intro}He detectado movimiento en la oscuridad sobre **{ticker}**. "
                       f"Aunque el precio parece dormido, la información fundamental (noticias) está muy despierta y positiva. "
                       f"La sabiduría dicta anticiparse antes de que amanezca para el resto.")

    # CASO: COMPRA TÉCNICA (Inercia)
    elif alpha_score > 0 and tech_score > 0:
        status = "📈 VUELO ESTABLE"
        explanation = (f"{intro}**{ticker}** mantiene un planeo ascendente constante. "
                       f"No hay ruido en el entorno (noticias neutrales), pero la inercia es favorable. "
                       f"A veces, la acción más sabia es simplemente dejar que la corriente te lleve.")

    # CASO: ESCUDO ACTIVADO (Veto por Noticias) -> CLAVE DE IDENTIDAD
    elif alpha_score <= 0 and is_tech_bullish and sentiment_score < 0:
        status = "🛡️ ALERTA DE PRUDENCIA"
        explanation = (f"{intro}Mi visión ha detectado un riesgo oculto bajo la superficie de **{ticker}**. "
                       f"La gráfica parece atractiva a simple vista, pero el trasfondo fundamental es negativo y peligroso. "
                       f"El inversor sabio sabe cuándo observar desde la rama y no arriesgar sus alas. Te protejo.")
    
    # CASO: VENTA / ESPERAR
    elif alpha_score < 0:
        status = "🔴 OBSERVACIÓN (WAIT)"
        explanation = (f"{intro}El panorama en **{ticker}** es incierto y turbio. "
                       f"No hay claridad ni en los gráficos ni en las noticias. "
                       f"La noche es larga; es mejor preservar la energía (capital) y esperar una señal clara.")

    return status, explanation
