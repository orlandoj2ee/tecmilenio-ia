"""21 conversaciones de varios turnos para probar los árboles de OrientaBot.

- 14 EXITOSAS: el estudiante llega a la respuesta final (hoja) que buscaba.
- 7 FALLIDAS: se quedan a medio camino, cada una por un motivo distinto y realista.

Cada flujo declara ANTES de correr qué hojas debe alcanzar (o ninguna, si debe fallar).
Así la prueba no se «acomoda» a lo que salió: compara contra lo que esperábamos.

Uso: python flujos.py  →  imprime las conversaciones y guarda flujos.txt (evidencia para el PDF)
"""
from pathlib import Path

from orientabot import HOJAS, OrientaBot

# Cada flujo es un diccionario:
#   estudiante → quién conversa (los perfiles de estudiantes.py)
#   resumen    → qué pasa, en una línea
#   turnos     → lo que escribe el estudiante, en orden
#   hojas      → respuestas finales que DEBE alcanzar ([] = debe fallar)
#   motivo     → solo en las fallidas: por qué se queda en el camino
EXITOSOS = [
    {'estudiante': 'Sofía', 'resumen': 'Pregunta documentos antes de decir que es de nuevo ingreso; el bot lo recuerda',
     'turnos': ['Hola', 'quiero inscribirme', '¿qué documentos necesito?', 'soy de nuevo ingreso', 'gracias'],
     'hojas': ['ni_documentos']},
    {'estudiante': 'Diego', 'resumen': 'La fecha va en la primera pregunta; se usa al aclarar que es nuevo',
     'turnos': ['Buenas tardes', '¿Cuándo abren las inscripciones?', 'es mi primera vez', 'Muchas gracias'],
     'hojas': ['ni_fechas']},
    {'estudiante': 'Andrés', 'resumen': 'Todo en un solo mensaje: baja dos niveles de golpe',
     'turnos': ['Me toca reinscripción y quiero saber de pagos', 'gracias', 'adiós'],
     'hojas': ['re_pagos']},
    {'estudiante': 'Valeria', 'resumen': 'Recorre el árbol paso a paso, un nivel por mensaje',
     'turnos': ['inscripción', 'ya estudio aquí, voy al siguiente semestre', 'es por las materias', 'ok gracias'],
     'hojas': ['re_materias']},
    {'estudiante': 'Mariana', 'resumen': 'Flujo formal completo: saludo, beca nueva, requisitos, cierre',
     'turnos': ['Hola', '¿Cómo solicito una beca?', 'Los requisitos, por favor', 'Gracias', 'Adiós'],
     'hojas': ['be_requisitos']},
    {'estudiante': 'Luis', 'resumen': 'Sin acentos ni signos, desde el celular',
     'turnos': ['necesito una beca', 'cuando sale la convocatoria', 'gracias'],
     'hojas': ['be_fechas']},
    {'estudiante': 'Jorge', 'resumen': 'Beca perdida en un mensaje y luego cambia a horarios',
     'turnos': ['Me quitaron la beca', '¿y dónde veo mi horario?', 'hasta luego'],
     'hojas': ['be_perdida']},
    {'estudiante': 'Camila', 'resumen': 'Renovación de beca: le preocupa el promedio',
     'turnos': ['quiero renovar mi beca', '¿qué promedio piden?', 'gracias'],
     'hojas': ['be_ren_promedio']},
    {'estudiante': 'Fernanda', 'resumen': 'Informal y con abreviaturas, pero las palabras clave pasan',
     'turnos': ['beca', 'renovarla', 'q papeles ocupo', 'grax'],
     'hojas': ['be_ren_documentos']},
    {'estudiante': 'Diego', 'resumen': 'Constancia con calificaciones: costo',
     'turnos': ['Necesito una constancia', 'con calificaciones', '¿cuánto cuesta?', 'Gracias'],
     'hojas': ['co_cal_costo']},
    {'estudiante': 'Sofía', 'resumen': 'El IMSS delata que es constancia de estudios',
     'turnos': ['Ocupo una constancia para el IMSS', '¿cómo la pido?'],
     'hojas': ['co_est_tramite']},
    {'estudiante': 'Andrés', 'resumen': 'Dos árboles seguidos: constancia y luego biblioteca',
     'turnos': ['constancia de estudios, ¿cuánto tarda?', 'también perdí un libro de la biblioteca', 'gracias'],
     'hojas': ['co_est_costo', 'bi_perdida']},
    {'estudiante': 'Valeria', 'resumen': 'Renovar un préstamo: gana renovación por el orden de las opciones',
     'turnos': ['¿Puedo renovar el préstamo de un libro?', 'gracias'],
     'hojas': ['bi_renovacion']},
    {'estudiante': 'Kevin', 'resumen': 'Empieza en inscripción y se cambia de árbol a biblioteca',
     'turnos': ['quiero inscribirme', 'mejor dime de la biblioteca', 'un prestamo', 'gracias'],
     'hojas': ['bi_prestamo']},
]

FALLIDOS = [
    {'estudiante': 'Kevin', 'motivo': 'Abandono',
     'resumen': 'Entra al árbol, contesta «ok» y se va sin elegir rama',
     'turnos': ['quiero inscribirme', 'ok'], 'hojas': []},
    {'estudiante': 'Camila', 'motivo': 'Dedazo dentro del árbol',
     'resumen': '«requsitos» no coincide con el patrón; el bot repite la pregunta hasta que ella se rinde',
     'turnos': ['necesito una beca', 'los requsitos', 'requsitos xfa', 'olvidalo'], 'hojas': []},
    {'estudiante': 'Jorge', 'motivo': 'Dedazo al entrar',
     'resumen': 'Ni «kiero inscirbirme» ni «inscirpcion» activan la regla: cae dos veces en el fallback',
     'turnos': ['kiero inscirbirme', 'inscirpcion', 'bye'], 'hojas': []},
    {'estudiante': 'Luis', 'motivo': 'El saludo se come la consulta',
     'resumen': '«Hola, necesito una constancia» cae en saludo; nunca entra al árbol',
     'turnos': ['Hola, necesito una constancia', 'ok'], 'hojas': []},
    {'estudiante': 'Fernanda', 'motivo': 'Respuesta fuera de las opciones',
     'resumen': 'Contesta con algo que el nodo no prevé (la visa) y no sabe nombrar el tipo',
     'turnos': ['constancias', 'la que piden para la visa', 'no se cual', 'ya vere'], 'hojas': []},
    {'estudiante': 'Mariana', 'motivo': 'Vocabulario no previsto',
     'resumen': '«Me quiero inscribir» no está en el patrón (solo «inscribirme»); se va al menú y desiste',
     'turnos': ['Me quiero inscribir', '¿Qué puedes hacer?', 'Hasta luego'], 'hojas': []},
    {'estudiante': 'Andrés', 'motivo': 'Pierde el contexto al cambiar de tema',
     'resumen': 'Iba a renovar su beca, pregunta su horario y al volver el bot ya olvidó «renovar»',
     'turnos': ['quiero renovar mi beca', '¿dónde veo mi horario?', '¿y lo de la beca?', 'adios'], 'hojas': []},
]


def correr(flujo):
    """Corre un flujo con un bot NUEVO (sin memoria previa). Regresa (transcripción, hojas alcanzadas)."""
    bot = OrientaBot()
    lineas, hojas = [], []
    for turno in flujo['turnos']:
        salida = bot.responder(turno)
        # Una hoja es una respuesta final: su nombre está en HOJAS (no es un nodo ni una intención simple).
        if salida['nodo'] in HOJAS:
            hojas.append(salida['nodo'])
        lineas.append(f"  {flujo['estudiante']}: {turno}")
        lineas.append(f"  OrientaBot: {salida['respuesta']}   [{salida['intencion']} · {salida['nodo']}]")
    return lineas, hojas


if __name__ == '__main__':
    texto, ok = [], 0
    # enumerate(..., 1) empieza a contar en 1 en vez de 0.
    for n, flujo in enumerate(EXITOSOS + FALLIDOS, 1):
        lineas, hojas = correr(flujo)
        cumple = hojas == flujo['hojas']           # ¿pasó exactamente lo que declaramos?
        ok += cumple
        tipo = 'EXITOSO' if flujo['hojas'] else f"FALLIDO · {flujo['motivo']}"
        texto.append(f"=== Flujo {n:02d} · {tipo} · {'✅' if cumple else '❌ REVISAR'} ===")
        texto.append(f"  {flujo['resumen']}")
        texto += lineas + ['']
    texto.append(f'{ok}/{len(EXITOSOS + FALLIDOS)} flujos se comportan como se declaró.')
    print('\n'.join(texto))
    Path(__file__).with_name('flujos.txt').write_text('\n'.join(texto), encoding='utf-8')
