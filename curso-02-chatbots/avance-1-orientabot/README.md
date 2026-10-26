# OrientaBot · Avance de proyecto 1

[![Abrir en Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/orlandoj2ee/tecmilenio-ia/blob/main/curso-02-chatbots/avance-1-orientabot/OrientaBot_Avance1.ipynb)

Asistente escolar **basado en reglas** con Python 3.10+ y NLTK. Tiene árboles de decisión con memoria de conversación y se prueba con pseudoestudiantes. La información es demostrativa: no contiene fechas ni requisitos oficiales.

## Cómo correrlo

**En Colab (recomendado):** pulsa el botón de arriba y luego *Entorno de ejecución → Ejecutar todas*.

**En local:**
```bash
cd codigo
pip install -r ../requirements.txt
python evaluar.py      # 200 preguntas de 10 pseudoestudiantes → resultados.csv
python flujos.py       # 21 conversaciones completas → flujos.txt
```

## Archivos

| Archivo | Qué es |
|---|---|
| `OrientaBot_Avance1.ipynb` | Notebook completo: bot, pruebas y evidencias |
| `codigo/orientabot.py` | El chatbot: intenciones, patrones regex y árboles de decisión |
| `codigo/estudiantes.py` | Genera las preguntas de prueba (`pool_preguntas.csv`) |
| `codigo/evaluar.py` | Mide precisión y fallback por intención (`resultados.csv`) |
| `codigo/flujos.py` | 21 conversaciones de varios turnos: 14 exitosas, 7 fallidas (`flujos.txt`) |

## Resultados

- **200 preguntas:** 65 % de precisión y 25 % de fallback.
- **21 flujos:** 14 exitosos y 7 fallidos. Los 21 se comportaron como se declaró.
