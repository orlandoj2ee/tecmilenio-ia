"""Evalúa OrientaBot con las 200 preguntas de los pseudoestudiantes.

Métricas del tema 4:
- Precisión de intención = % de preguntas donde el bot detectó lo que el estudiante quería.
- Tasa de fallback       = % de preguntas que cayeron en «desconocida».

Uso: python evaluar.py  →  imprime el reporte y guarda resultados.csv
"""
import csv
from collections import Counter, defaultdict   # Counter cuenta cosas; defaultdict crea llaves solas
from pathlib import Path

from estudiantes import generar_pool   # gracias al «if __name__…» de allá, importar NO regenera el CSV
from orientabot import responder

CARPETA = Path(__file__).parent        # carpeta de este archivo


def pct(parte, total):
    """Porcentaje con formato bonito: pct(3, 4) → ' 75%'. Evita dividir entre cero."""
    return f'{parte / total:4.0%}' if total else '   —'


def evaluar(pool):
    """Le pasa cada pregunta al bot y anota si acertó. Regresa la lista de filas con resultado."""
    resultados = []
    for fila in pool:
        salida = responder(fila['pregunta'])
        # {**fila, …}: copia todas las columnas de la fila y le agrega las nuevas.
        resultados.append({**fila, 'detectada': salida['intencion'],
                           'correcto': salida['intencion'] == fila['esperada']})
    return resultados


def reporte(resultados):
    """Imprime las métricas, de lo general a lo particular."""
    total = len(resultados)
    aciertos = sum(r['correcto'] for r in resultados)                  # True cuenta como 1
    fallback = sum(r['detectada'] == 'desconocida' for r in resultados)
    print(f'\n== OrientaBot vs. {total} preguntas ==')
    print(f'Precisión de intención: {aciertos}/{total} = {pct(aciertos, total)}')
    print(f'Tasa de fallback:       {fallback}/{total} = {pct(fallback, total)}')

    # --- ¿Escribir mal le pega al bot? Comparamos limpias contra sucias ---
    print('\n-- Limpias vs. sucias --')
    for sucia in (False, True):
        grupo = [r for r in resultados if r['sucia'] == sucia]
        ok = sum(r['correcto'] for r in grupo)
        print(f"{'sucias ' if sucia else 'limpias'}: {ok}/{len(grupo)} = {pct(ok, len(grupo))}")

    # --- Precisión por intención esperada ---
    # defaultdict(list): si la llave no existe, la crea con una lista vacía (sin if).
    por_intencion = defaultdict(list)
    for r in resultados:
        por_intencion[r['esperada']].append(r['correcto'])
    print('\n-- Por intención --')
    # sorted(..., key=…): ordena de la intención con más preguntas a la de menos.
    for intencion, lista in sorted(por_intencion.items(), key=lambda par: -len(par[1])):
        print(f'{intencion:16} {sum(lista):3}/{len(lista):<3} {pct(sum(lista), len(lista))}')

    # --- Por estudiante: ¿Kevin la pasa peor que Mariana? ---
    por_estudiante = defaultdict(list)
    for r in resultados:
        por_estudiante[r['estudiante']].append(r['correcto'])
    print('\n-- Por estudiante --')
    for nombre, lista in por_estudiante.items():   # los dicts conservan el orden de inserción
        print(f'{nombre:9} {pct(sum(lista), len(lista))}')

    # --- Confusiones más comunes: qué se esperaba → qué detectó ---
    confusiones = Counter((r['esperada'], r['detectada']) for r in resultados if not r['correcto'])
    print('\n-- Confusiones más comunes (esperada → detectada) --')
    for (esperada, detectada), n in confusiones.most_common(8):
        print(f'{n:3} × {esperada} → {detectada}')


def guardar(resultados):
    """Guarda cada pregunta con su resultado; sirve de evidencia para el PDF."""
    salida = CARPETA / 'resultados.csv'
    with salida.open('w', newline='', encoding='utf-8') as f:
        escritor = csv.DictWriter(f, fieldnames=list(resultados[0]))
        escritor.writeheader()
        escritor.writerows(resultados)
    print(f'\nDetalle guardado en {salida.name}')


if __name__ == '__main__':
    resultados = evaluar(generar_pool())
    reporte(resultados)
    guardar(resultados)
