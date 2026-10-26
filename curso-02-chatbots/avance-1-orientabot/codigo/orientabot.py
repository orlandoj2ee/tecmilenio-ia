"""OrientaBot: chatbot escolar basado en reglas (NLTK).

Es el bot del notebook de clase (2026-10-15) + el reto: la intención `biblioteca`.
Se separa en su propio archivo para poder importarlo desde las pruebas.

Uso: python orientabot.py  →  chat en la terminal (escribe «salir» para terminar)
"""
import re                                   # expresiones regulares: los «patrones» de cada regla
import unicodedata                          # quitar acentos al normalizar
from nltk.chat.util import Chat, reflections   # motor de reglas de NLTK (heredero de ELIZA, 1966)

# =====================================================================
# 1. BASE DE CONOCIMIENTO — (intención, patrón regex, respuesta)
# =====================================================================
# ⚠️ EL ORDEN IMPORTA: gana la PRIMERA regla cuyo patrón coincide.
#    Por eso «desconocida» (que acepta todo con '.*') va al final.
#
# Mini guía de regex para leer los patrones:
#   ^        inicio del texto           $       fin del texto
#   .*       «cualquier cosa» (o nada)  \b      borde de palabra (evita 'beca' dentro de 'bibliobeca')
#   (a|b)    a o b                      [.!?]*  cero o más signos de puntuación
BASE = [
    ('saludo', r'^(hola|buenos dias|buenas tardes|buenas noches|hey)\b.*',
     '¡Hola! Soy OrientaBot. Consulta sobre inscripciones, horarios, becas, constancias o biblioteca.'),
    ('inscripcion', r'.*\b(inscripcion|inscripciones|inscribirme|reinscripcion)\b.*',
     'Consulta la convocatoria vigente y contacta a Control Escolar para conocer el proceso de inscripción '
     'o reinscripción. Verifica allí fechas y requisitos oficiales.'),
    ('horarios', r'.*\b(horario|horarios|clases)\b.*',
     'Consulta tu horario en el sistema escolar institucional. Si existe algún problema con tu grupo o '
     'materia, contacta a Control Escolar.'),
    ('becas', r'.*\b(beca|becas|apoyo economico)\b.*',
     'Consulta las convocatorias institucionales vigentes. El área de Becas puede orientarte sobre '
     'requisitos, documentos y fechas.'),
    ('constancias', r'.*\b(constancia|constancias|comprobante de estudios)\b.*',
     'Solicita información a Control Escolar sobre el procedimiento, documentos necesarios y tiempo de '
     'entrega de constancias.'),
    ('control_escolar', r'.*\b(control escolar|servicios escolares)\b.*',
     'Control Escolar orienta sobre trámites académicos. Consulta sus medios de contacto en el sitio '
     'oficial de tu institución.'),
    # --- RETO de la clase: nueva intención, ANTES de «desconocida» ---
    # Respuesta general que remite al área: no inventamos horarios ni requisitos.
    ('biblioteca', r'.*\b(biblioteca|libros|prestamo)\b.*',
     'La Biblioteca orienta sobre préstamos, renovaciones y consulta de libros. Revisa sus horarios y '
     'requisitos en el sitio oficial de tu institución o acude al mostrador de préstamo.'),
    ('ayuda', r'.*\b(ayuda|menu|opciones|que puedes hacer)\b.*',
     'Temas disponibles: inscripciones, horarios, becas, constancias, Control Escolar y biblioteca. '
     'Escribe salir para terminar.'),
    ('agradecimiento', r'.*\bgracias\b.*', '¡De nada! ¿Necesitas orientación sobre otro tema?'),
    ('despedida', r'^(salir|adios|hasta luego)[.!?]*$', '¡Hasta luego! Gracias por consultar OrientaBot.'),
    ('vacio', r'^$', 'Escribe una consulta para poder orientarte.'),
    # Red de seguridad (fallback): '.*' coincide con TODO, así el bot nunca se queda callado.
    ('desconocida', r'.*',
     'No identifiqué tu consulta. Intenta mencionar inscripciones, horarios, becas, constancias, '
     'Control Escolar o biblioteca.'),
]

# Chat de NLTK recibe pares (patrón, [respuestas]); si la lista trae varias, elige una al azar.
# Comprensión de lista: de cada tupla de 3 tomamos solo patrón y respuesta ('_' = «no me importa»).
chatbot = Chat([(patron, [respuesta]) for _, patron, respuesta in BASE], reflections)

# =====================================================================
# 2. FUNCIONES
# =====================================================================


def normalizar(texto):
    """Limpia el texto antes de compararlo: '  ¿Cómo  ME Inscribo? ' → '¿como me inscribo?'.

    Así «Inscripción», «inscripcion» e «INSCRIPCIÓN» caen en la misma regla.
    """
    texto = unicodedata.normalize('NFD', texto.lower().strip())             # minúsculas, sin espacios en orillas, separa acentos
    texto = ''.join(c for c in texto if unicodedata.category(c) != 'Mn')    # tira los acentos
    return re.sub(r'\s+', ' ', texto)                                        # varios espacios seguidos → uno


def responder(texto):
    """Recibe lo que escribió el usuario y regresa {'intencion': …, 'respuesta': …}.

    La intención la calculamos nosotros (para medir); la respuesta la da NLTK.
    Coinciden porque ambos recorren los MISMOS patrones en el MISMO orden.
    """
    limpio = normalizar(texto)
    # next(generador): devuelve el PRIMER elemento que cumple la condición → «gana la primera regla».
    # Nunca falla porque «desconocida» ('.*') siempre coincide.
    intencion = next(nombre for nombre, patron, _ in BASE if re.match(patron, limpio, re.IGNORECASE))
    return {'intencion': intencion, 'respuesta': chatbot.respond(limpio)}


# =====================================================================
# 3. ÁRBOLES DE DECISIÓN — de lo general a lo específico
# =====================================================================
#   inscripcion ─┬─ nuevo_ingreso ─┬─ documentos         becas ─┬─ perdida (hoja)
#                │                 └─ fechas                    ├─ renovar ─┬─ documentos
#                └─ reinscripcion ─┬─ pagos                     │           └─ promedio
#                                  └─ materias                  └─ solicitar ─┬─ requisitos
#                                                                              └─ fechas
#   constancias ─┬─ calificaciones ─┬─ trámite           biblioteca ─┬─ perdida   (hoja)
#                │                  └─ costo y tiempo                ├─ renovacion (hoja)
#                └─ estudios ───────┬─ trámite                       └─ prestamo  (hoja)
#                                   └─ costo y tiempo
#
# Cada NODO hace una pregunta y tiene opciones: (patrón, a dónde lleva).
# Si «a dónde lleva» es otro nodo, seguimos bajando; si está en HOJAS, respondemos y salimos.
# La RAÍZ de cada árbol se llama igual que su intención en BASE: así sabemos por dónde entrar.
# ⚠️ Dentro de cada nodo también importa el orden: «renovar el préstamo» debe caer en renovación,
#    por eso renovación va antes que préstamo.
ARBOL = {
    # --- Inscripción ---
    'inscripcion': {
        'pregunta': '¿Eres de nuevo ingreso o vas a reinscribirte?',
        'opciones': [(r'\b(nuevo|primer|primera vez|aspirante|ingresar)\b', 'nuevo_ingreso'),
                     (r'\b(reinscri\w*|ya estudio|siguiente semestre)\b', 'reinscripcion')],
    },
    'nuevo_ingreso': {
        'pregunta': 'Nuevo ingreso. ¿Quieres saber de documentos o de fechas?',
        'opciones': [(r'\b(documento\w*|requisito\w*|papeles)\b', 'ni_documentos'),
                     (r'\b(fecha\w*|cuando|convocatoria)\b', 'ni_fechas')],
    },
    'reinscripcion': {
        'pregunta': 'Reinscripción. ¿Tu duda es sobre pagos o sobre materias?',
        'opciones': [(r'\b(pago\w*|pagar|costo\w*|cuanto)\b', 're_pagos'),
                     (r'\b(materia\w*|carga|grupo\w*)\b', 're_materias')],
    },
    # --- Becas ---
    'becas': {
        'pregunta': '¿Quieres solicitar una beca, renovar la que tienes, o la perdiste?',
        'opciones': [(r'\b(perdi\w*|quitaron|cancel\w*|suspend\w*)\b', 'be_perdida'),
                     (r'\b(renov\w*|mantener|conservar)\b', 'becas_renovar'),
                     (r'\b(solicit\w*|pedir|nueva|necesito|conseguir|aplicar|quiero)\b', 'becas_solicitar')],
    },
    'becas_renovar': {
        'pregunta': 'Renovación. ¿Tu duda es sobre documentos o sobre el promedio que piden?',
        'opciones': [(r'\b(documento\w*|papeles|requisito\w*)\b', 'be_ren_documentos'),
                     (r'\b(promedio|calificacion\w*|reprobe|reprobada)\b', 'be_ren_promedio')],
    },
    'becas_solicitar': {
        'pregunta': 'Solicitud nueva. ¿Quieres conocer los requisitos o las fechas de la convocatoria?',
        'opciones': [(r'\b(requisito\w*|documento\w*|promedio|papeles)\b', 'be_requisitos'),
                     (r'\b(fecha\w*|cuando|convocatoria|plazo)\b', 'be_fechas')],
    },
    # --- Constancias ---
    'constancias': {
        'pregunta': '¿La necesitas de estudios (simple) o con calificaciones?',
        'opciones': [(r'\b(calificacion\w*|kardex|promedio|historial)\b', 'const_calificaciones'),
                     (r'\b(estudios|simple|normal|inscrito|imss|trabajo)\b', 'const_estudios')],
    },
    'const_calificaciones': {
        'pregunta': 'Con calificaciones. ¿Quieres saber cómo pedirla o cuánto cuesta y tarda?',
        'opciones': [(r'\b(costo|cuesta|precio|pagar|tarda|tiempo|dias)\b', 'co_cal_costo'),
                     (r'\b(como|pedir\w*|solicit\w*|donde|tramit\w*|sacar\w*)\b', 'co_cal_tramite')],
    },
    'const_estudios': {
        'pregunta': 'De estudios. ¿Quieres saber cómo pedirla o cuánto cuesta y tarda?',
        'opciones': [(r'\b(costo|cuesta|precio|pagar|tarda|tiempo|dias)\b', 'co_est_costo'),
                     (r'\b(como|pedir\w*|solicit\w*|donde|tramit\w*|sacar\w*)\b', 'co_est_tramite')],
    },
    # --- Biblioteca ---
    'biblioteca': {
        'pregunta': '¿Es sobre un préstamo, una renovación, o un libro perdido o dañado?',
        'opciones': [(r'\b(perdi\w*|perdido|dan\w*|maltrat\w*|rompi\w*)\b', 'bi_perdida'),
                     (r'\b(renov\w*|extender|mas tiempo)\b', 'bi_renovacion'),
                     (r'\b(prestamo|pedir|llevar\w*|sacar)\b', 'bi_prestamo')],
    },
}

# Hojas = respuestas finales. Generales y remitiendo al área: no inventamos datos oficiales.
HOJAS = {
    'ni_documentos': 'Los documentos de nuevo ingreso vienen en la convocatoria vigente. Control Escolar '
                     'te confirma la lista oficial.',
    'ni_fechas': 'Las fechas de nuevo ingreso se publican en la convocatoria del sitio oficial.',
    're_pagos': 'El monto y la forma de pago de la reinscripción los informa Control Escolar o el portal '
                'de pagos institucional.',
    're_materias': 'La selección de materias se hace en el sistema escolar. Si tienes adeudos o empalmes, '
                   'contacta a Control Escolar.',
    'be_perdida': 'Si perdiste tu beca, acude al área de Becas: te explican la causa y si puedes '
                  'apelar o volver a solicitarla en la siguiente convocatoria.',
    'be_ren_documentos': 'Los documentos para renovar vienen en la convocatoria de renovación. El área de '
                         'Becas te confirma la lista.',
    'be_ren_promedio': 'El promedio mínimo para conservar la beca lo fija el reglamento de Becas. Si estás '
                       'en riesgo, consúltalo con el área antes del cierre de periodo.',
    'be_requisitos': 'Los requisitos de cada beca vienen en su convocatoria. El área de Becas te orienta '
                     'sobre cuál te conviene.',
    'be_fechas': 'Las convocatorias de becas se publican en el sitio oficial; revisa ahí los plazos.',
    'co_cal_tramite': 'La constancia con calificaciones se solicita en Control Escolar o en el portal de '
                      'trámites, si tu institución lo tiene.',
    'co_cal_costo': 'El costo y el tiempo de entrega de la constancia con calificaciones los informa '
                    'Control Escolar.',
    'co_est_tramite': 'La constancia de estudios se solicita en Control Escolar o en el portal de trámites, '
                      'si tu institución lo tiene.',
    'co_est_costo': 'El costo y el tiempo de entrega de la constancia de estudios los informa Control Escolar.',
    'bi_perdida': 'Si perdiste o dañaste un libro, repórtalo en el mostrador de la Biblioteca: te indican '
                  'cómo reponerlo.',
    'bi_renovacion': 'Las renovaciones se hacen en el mostrador de la Biblioteca o en su catálogo en línea, '
                     'antes de la fecha de vencimiento.',
    'bi_prestamo': 'Para un préstamo acude al mostrador de la Biblioteca con tu credencial vigente.',
}


class OrientaBot:
    """Bot CON memoria: recuerda en qué árbol y en qué rama va la conversación.

    Una clase junta datos (el estado) y funciones (métodos) que los usan.
    Cada estudiante tendría su propio objeto: OrientaBot() → conversación nueva.
    """

    def __init__(self):
        # __init__ corre al crear el objeto. «self» es el propio objeto.
        self.tema = None          # árbol actual: 'inscripcion', 'becas'… (None = fuera de los árboles)
        self.nodo = None          # rama actual dentro de ese árbol
        self.pendiente = None     # mensaje que no supimos ubicar aún (p. ej. «¿qué documentos?»)

    def _bajar(self, limpio):
        """Intenta avanzar por el árbol con este texto. Regresa la hoja si llegó a una, o None.

        El guion bajo inicial (_bajar) es convención: «método interno, no lo llames desde fuera».
        """
        avanzo = True
        # Mientras estemos en un nodo y el texto encaje en alguna opción, seguimos bajando.
        # Así «me reinscribo y quiero saber de pagos» llega a la hoja en UN solo mensaje.
        while self.nodo and avanzo:
            avanzo = False
            for patron, destino in ARBOL[self.nodo]['opciones']:
                if re.search(patron, limpio):        # search busca en cualquier parte (match solo al inicio)
                    if destino in HOJAS:
                        self.nodo = None             # llegamos al final: salimos del árbol
                        return destino
                    self.nodo, avanzo = destino, True
                    break
        return None

    def _salida(self, hoja=None, prefijo=''):
        """Arma la respuesta: la hoja si llegamos a una, o la pregunta del nodo actual."""
        tema = self.tema
        if hoja:
            self.tema = self.pendiente = None        # conversación del árbol terminada
            return {'intencion': tema, 'nodo': hoja, 'respuesta': HOJAS[hoja]}
        return {'intencion': tema, 'nodo': self.nodo, 'respuesta': prefijo + ARBOL[self.nodo]['pregunta']}

    def _entrar(self, tema, limpio):
        """Entra a un árbol por su raíz e intenta bajar con el mismo mensaje."""
        self.tema, self.nodo, self.pendiente = tema, tema, None
        hoja = self._bajar(limpio)
        if not hoja:
            # Guardamos el mensaje: puede traer un detalle que sirva más abajo.
            # «¿Cuándo abren las inscripciones?» → al llegar a nuevo_ingreso, «cuándo» elige fechas.
            self.pendiente = limpio
        return self._salida(hoja, prefijo='Con gusto. ')

    def responder(self, texto):
        """Como responder() de arriba, pero usando y actualizando el estado."""
        limpio = normalizar(texto)
        global_ = responder(texto)                   # lo que diría el bot sin memoria
        intencion = global_['intencion']

        # Caso A: estamos dentro de un árbol.
        if self.nodo:
            antes = self.nodo                        # para saber si este mensaje nos hizo avanzar
            hoja = self._bajar(limpio)
            # Si avanzamos y había algo pendiente, lo usamos ahora:
            # «quiero inscribirme» → «¿qué documentos?» → «nuevo ingreso» ⇒ responde documentos.
            if self.pendiente and not hoja and self.nodo != antes:
                hoja = self._bajar(self.pendiente)
            if hoja:
                return self._salida(hoja)
            if self.nodo != antes:                   # avanzó a otra rama → hacemos su pregunta
                return self._salida()
            # No avanzó: ¿cambió de tema?
            if intencion in ARBOL and intencion != self.tema:        # a otro árbol → entramos a ese
                return self._entrar(intencion, limpio)
            if intencion not in ('desconocida', self.tema):          # a un tema simple → salimos
                self.tema = self.nodo = self.pendiente = None
                return {**global_, 'nodo': None}
            # Ni avanzó ni cambió de tema: guardamos su mensaje y repetimos la pregunta.
            self.pendiente = limpio
            return self._salida(prefijo='Para orientarte mejor: ')

        # Caso B: fuera de los árboles. Si el tema tiene árbol, entramos por su raíz.
        if intencion in ARBOL:
            return self._entrar(intencion, limpio)

        # Cualquier otro tema: respuesta normal de una sola pregunta.
        return {**global_, 'nodo': None}


# =====================================================================
# 4. CHAT EN LA TERMINAL (solo si ejecutas este archivo directo)
# =====================================================================
if __name__ == '__main__':
    bot = OrientaBot()                       # una conversación con memoria
    print('OrientaBot: ¡Hola! Escribe tu consulta o «salir».')
    while True:                              # bucle infinito… hasta el break
        salida = bot.responder(input('Tú: '))
        print('OrientaBot:', salida['respuesta'], f"  [{salida['intencion']} · nodo={salida['nodo']}]")
        if salida['intencion'] == 'despedida':
            break
