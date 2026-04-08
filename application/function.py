import json
import re
from collections import Counter


def lambda_handler(event, context):
    """
    Lambda Function: Analizador de Texto
    -------------------------------------
    Recibe un texto en el body del evento y devuelve estadísticas básicas:
    - Total de caracteres
    - Total de palabras
    - Total de oraciones
    - Tiempo de lectura estimado (min)
    - Top 5 palabras más frecuentes

    Sin dependencias externas — solo usa la biblioteca estándar de Python.

    Ejemplo de invocación (payload):
        {
            "body": "{\"texto\": \"Hola mundo. Este es un ejemplo de texto para analizar.\"}"
        }

    O directamente (invocación directa desde consola / test en AWS):
        {
            "texto": "Hola mundo. Este es un ejemplo de texto para analizar."
        }
    """

    # --- 1. Parseo del evento ---
    try:
        # Soporta tanto API Gateway (body como string JSON) como invocación directa
        if isinstance(event.get("body"), str):
            body = json.loads(event["body"])
        elif isinstance(event.get("body"), dict):
            body = event["body"]
        else:
            body = event  # invocación directa

        texto = body.get("texto", "").strip()

        if not texto:
            return _respuesta(400, {"error": "El campo 'texto' es obligatorio y no puede estar vacío."})

    except (json.JSONDecodeError, AttributeError) as e:
        return _respuesta(400, {"error": f"Payload inválido: {str(e)}"})

    # --- 2. Análisis ---
    resultado = analizar_texto(texto)

    # --- 3. Respuesta ---
    return _respuesta(200, resultado)


# ---------------------------------------------------------------------------
# Lógica de análisis (sin imports externos)
# ---------------------------------------------------------------------------

def analizar_texto(texto: str) -> dict:
    """Calcula estadísticas básicas sobre el texto recibido."""

    # Caracteres
    total_chars = len(texto)
    chars_sin_espacios = len(texto.replace(" ", "").replace("\n", "").replace("\t", ""))

    # Palabras (split por espacios y signos de puntuación)
    palabras_raw = re.findall(r"\b[a-záéíóúüñA-ZÁÉÍÓÚÜÑ]{2,}\b", texto)
    total_palabras = len(palabras_raw)

    # Oraciones (terminan en . ! ?)
    oraciones = re.split(r"[.!?]+", texto)
    oraciones = [o.strip() for o in oraciones if o.strip()]
    total_oraciones = len(oraciones)

    # Tiempo de lectura estimado (velocidad promedio: 200 palabras/min)
    tiempo_lectura_min = round(total_palabras / 200, 2)

    # Top 5 palabras más frecuentes (normalizadas a minúsculas)
    stop_words = {
        "de", "la", "el", "en", "y", "a", "que", "los", "las", "un",
        "una", "es", "se", "no", "por", "con", "del", "lo", "su", "para",
    }
    palabras_filtradas = [p.lower() for p in palabras_raw if p.lower() not in stop_words]
    top_palabras = Counter(palabras_filtradas).most_common(5)

    return {
        "resumen": {
            "caracteres_totales": total_chars,
            "caracteres_sin_espacios": chars_sin_espacios,
            "palabras": total_palabras,
            "oraciones": total_oraciones,
            "tiempo_lectura_estimado_min": tiempo_lectura_min,
        },
        "top_5_palabras": [
            {"palabra": palabra, "frecuencia": freq}
            for palabra, freq in top_palabras
        ],
        "texto_original": texto[:200] + ("..." if len(texto) > 200 else ""),
    }


# ---------------------------------------------------------------------------
# Helper de respuesta compatible con API Gateway
# ---------------------------------------------------------------------------

def _respuesta(status_code: int, body: dict) -> dict:
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body, ensure_ascii=False, indent=2),
    }


# ---------------------------------------------------------------------------
# Ejecución local para pruebas rápidas
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    evento_prueba = {
        "texto": (
            "Amazon Web Services lanzó AWS Lambda en 2014, revolucionando "
            "el cómputo sin servidor. Lambda permite ejecutar código sin "
            "aprovisionar ni gestionar servidores. Solo pagas por el tiempo "
            "de cómputo que consumes. Lambda escala automáticamente desde "
            "unas pocas solicitudes por día hasta miles por segundo."
        )
    }

    respuesta = lambda_handler(evento_prueba, {})
    print(json.dumps(json.loads(respuesta["body"]), ensure_ascii=False, indent=2))