"""Pseudoestudiantes: genera un pool de preguntas realistas para probar OrientaBot.

- 10 perfiles × 20 preguntas = 200.
- Mezcla no uniforme de temas (MEZCLA), como en la vida real.
- Cada perfil escribe «sucio» con distinta frecuencia (~1 de cada 3 en promedio):
  tecla vecina, letras cambiadas, letra que falta o sobra, sin acentos, abreviaturas.
- La intención esperada es la que el estudiante QUIERE, aunque escriba mal.
- Semilla fija: siempre genera el mismo pool.

Uso: python estudiantes.py  →  pool_preguntas.csv
"""
# --- Importaciones: solo la biblioteca estándar, nada que instalar ---
import csv                # escribir el resultado como tabla .csv (se abre en Excel)
import random             # azar controlado: elegir plantillas, errores, perfiles
import unicodedata        # separar letras de sus acentos (á → a + ´)
from pathlib import Path  # manejar rutas de archivos sin pelear con / o \

# =====================================================================
# 1. CONFIGURACIÓN — lo único que deberías tocar para cambiar el pool
# =====================================================================

# Semilla: con el mismo número, random da SIEMPRE la misma secuencia.
# Así el pool es reproducible: tú y el profe obtienen las mismas 200 preguntas.
SEMILLA = 42
PREGUNTAS_POR_ESTUDIANTE = 20

# Diccionario tema → porcentaje del pool (suma 100).
# No es uniforme a propósito: en la vida real casi todos preguntan por inscripción.
MEZCLA = {
    'inscripcion': 22, 'horarios': 15, 'constancias': 12, 'becas': 10,
    'desconocida': 12, 'saludo': 4, 'agradecimiento': 3, 'despedida': 3,
    'biblioteca': 6, 'control_escolar': 5, 'ayuda': 3, 'dos_temas': 5,
}

# Lista de tuplas (nombre, cómo escribe, probabilidad de escribir «sucio»).
# 0.05 = se equivoca 1 de cada 20 veces; 0.70 = 7 de cada 10.
# El promedio de la columna da ~0.33: 1 de cada 3 preguntas sucia.
PERFILES = [
    ('Mariana', 'formal, revisa antes de enviar', 0.05),
    ('Diego', 'cuidadoso, frases completas', 0.10),
    ('Sofía', 'aspirante de nuevo ingreso, pregunta todo', 0.15),
    ('Andrés', 'directo, pocas palabras', 0.20),
    ('Valeria', 'escribe rápido entre clases', 0.30),
    ('Luis', 'desde el celular, sin acentos', 0.35),
    ('Fernanda', 'informal, usa abreviaturas', 0.40),
    ('Jorge', 'trabaja y estudia, siempre con prisa', 0.50),
    ('Camila', 'escribe con el pulgar, muchos dedazos', 0.55),
    ('Kevin', 'no revisa nada, puro dedazo', 0.70),
]

# Diccionario intención → lista de frases «limpias».
# La CLAVE es la etiqueta correcta (lo que el estudiante quiere);
# el bot tendrá que adivinarla solo con el texto.
PLANTILLAS = {
    'inscripcion': [
        '¿Cómo puedo inscribirme?', '¿Cuándo abren las inscripciones?',
        '¿Qué necesito para la reinscripción?', 'Quiero inscribirme al siguiente semestre',
        '¿Hasta cuándo hay inscripciones?', 'No sé cómo hacer mi reinscripción',
        '¿Dónde hago la inscripción?', 'Me quiero inscribir, ¿qué hago?',
        '¿Qué documentos piden para la inscripción?', '¿La reinscripción es en línea?',
        'Perdí la fecha de inscripción, ¿todavía puedo?', '¿Cuánto cuesta la inscripción?',
    ],
    'horarios': [
        '¿Dónde veo mi horario?', '¿Ya salieron los horarios?', '¿A qué hora son mis clases?',
        'No me aparece mi horario', 'Quiero cambiar mi horario', '¿Cuándo empiezan las clases?',
        'Tengo un empalme en mi horario', '¿Dónde consulto los horarios del grupo?',
        '¿Las clases son presenciales?', 'Mi horario está mal',
    ],
    'constancias': [
        'Necesito una constancia de estudios', '¿Cómo saco una constancia?',
        '¿Cuánto tarda la constancia?', 'Quiero un comprobante de estudios',
        '¿Dónde pido constancias?', 'Ocupo una constancia para el IMSS',
        '¿La constancia tiene costo?', 'Necesito constancia con calificaciones',
    ],
    'becas': [
        '¿Hay becas?', '¿Cómo solicito una beca?', 'Necesito apoyo económico',
        '¿Cuándo sale la convocatoria de becas?', '¿Qué promedio piden para la beca?',
        'Me quitaron la beca, ¿qué hago?', '¿Puedo renovar mi beca?',
        'No tengo beca pero la necesito',
    ],
    'biblioteca': [
        'Quiero pedir libros', '¿A qué hora abre la biblioteca?', '¿Cómo pido un préstamo?',
        '¿Puedo renovar el préstamo de un libro?', '¿Dónde está la biblioteca?',
        'Perdí un libro de la biblioteca',
    ],
    'control_escolar': [
        '¿Dónde está Control Escolar?', '¿Cuál es el teléfono de Servicios Escolares?',
        '¿A qué hora atiende Control Escolar?', 'Necesito hablar con Control Escolar',
        '¿Control escolar tiene correo?',
    ],
    'ayuda': ['¿Qué puedes hacer?', 'Ayuda', 'Menú', '¿Qué opciones tienes?', 'No sé qué preguntar'],
    'saludo': ['Hola', 'Buenos días', 'Buenas tardes', 'Hey', 'Buenas noches', 'Hola, buen día'],
    'agradecimiento': ['Gracias', 'Muchas gracias', 'Gracias por la info', 'Ok, gracias'],
    'despedida': ['Adiós', 'Hasta luego', 'Salir', 'Bye', 'Nos vemos'],
    # «desconocida» = fuera de alcance. Lo CORRECTO aquí es que el bot diga «no sé».
    'desconocida': [
        '¿Cómo pago la colegiatura?', 'Olvidé mi contraseña del portal', '¿Qué clima hará mañana?',
        '¿Hay estacionamiento?', '¿Dónde está la cafetería?', '¿Cómo me doy de baja?',
        'No puedo entrar a la plataforma', '¿Cuándo son vacaciones?', '¿Hay servicio médico?',
        '¿Venden uniformes?', '¿Cuándo es la graduación?', 'Quiero cambiarme de carrera',
    ],
}

# Frases con dos temas: (texto, intención principal).
# Tomamos como correcta la que el estudiante quiere de verdad (en la negación, la segunda).
DOS_TEMAS = [
    ('Quiero saber de becas y horarios', 'becas'),
    ('Necesito una constancia y también inscribirme', 'constancias'),
    ('¿Dónde veo mi horario y dónde está Control Escolar?', 'horarios'),
    ('Ocupo inscribirme y saber si hay becas', 'inscripcion'),
    ('No quiero beca, quiero una constancia', 'constancias'),
    ('¿La biblioteca tiene horario en vacaciones?', 'biblioteca'),
]

# Muletillas al inicio y al final. Las '' repetidas hacen que «nada» salga más seguido:
# random.choice elige con la misma probabilidad cada elemento de la lista.
ABRIDORES = ['', '', '', 'Oye, ', 'Disculpa, ', 'Una pregunta, ', 'Hola, ']
CIERRES = ['', '', '', ' por favor', ' gracias', '!!']

# Cómo abrevia la gente en el chat: palabra completa → abreviatura.
ABREVIATURAS = {'que': 'q', 'por favor': 'xfa', 'para': 'pa', 'porque': 'xq',
                'también': 'tmb', 'gracias': 'grax', 'quiero': 'kiero', 'dónde': 'dnd'}

# Mapa del teclado QWERTY en español: cada letra → las letras que la rodean.
# Así un dedazo es realista: «c» se vuelve «v» (vecina), no «z» (lejana).
VECINAS = {
    'q': 'wa', 'w': 'qes', 'e': 'wrd', 'r': 'etf', 't': 'ryg', 'y': 'tuh', 'u': 'yij',
    'i': 'uok', 'o': 'ipl', 'p': 'oñ', 'a': 'qsz', 's': 'adwx', 'd': 'sfec', 'f': 'dgrv',
    'g': 'fhtb', 'h': 'gjyn', 'j': 'hkum', 'k': 'jli', 'l': 'kñ', 'ñ': 'lp', 'z': 'xa',
    'x': 'zcs', 'c': 'xvd', 'v': 'cbf', 'b': 'vng', 'n': 'bmh', 'm': 'nj',
}

# =====================================================================
# 2. FUNCIONES — cada una hace UNA cosa
# =====================================================================


def sin_acentos(texto):
    """Quita acentos: 'inscripción' → 'inscripcion'.

    Truco: NFD separa cada letra de su acento ('ó' → 'o' + '´').
    Luego descartamos los caracteres de categoría 'Mn' (marcas = acentos).
    """
    texto = unicodedata.normalize('NFD', texto)                            # separa letra y acento
    return ''.join(c for c in texto if unicodedata.category(c) != 'Mn')   # se queda solo con letras


def dedazo(palabra, rng):
    """Mete UN error de tecleo en una palabra y dice cuál fue.

    Regresa una tupla (palabra_con_error, tipo_de_error), por ejemplo
    ('horaruo', 'tecla_vecina'). Python permite regresar varios valores así.
    """
    # Posición del error: nunca la primera ni la última letra
    # (la gente casi siempre atina al inicio de la palabra).
    i = rng.randrange(1, len(palabra) - 1)
    tipo = rng.choice(['tecla_vecina', 'letras_cambiadas', 'falta_letra', 'sobra_letra'])

    # Rebanadas (slicing): palabra[:i] = todo ANTES de i, palabra[i+1:] = todo DESPUÉS.
    # Reemplazar la letra i es pegar: antes + letra_nueva + después.
    if tipo == 'tecla_vecina' and palabra[i].lower() in VECINAS:
        return palabra[:i] + rng.choice(VECINAS[palabra[i].lower()]) + palabra[i + 1:], tipo   # horario → horaruo
    # Intercambiar i e i+1; si son iguales («ss») el cambio sería invisible, así que lo saltamos.
    if tipo == 'letras_cambiadas' and palabra[i] != palabra[i + 1]:
        return palabra[:i] + palabra[i + 1] + palabra[i] + palabra[i + 2:], tipo               # becas → beacs
    if tipo == 'falta_letra':
        return palabra[:i] + palabra[i + 1:], tipo                                             # constancia → constacia
    # Caso por defecto (y respaldo si un caso de arriba no aplicó): duplicar la letra i.
    return palabra[:i] + palabra[i] + palabra[i:], 'sobra_letra'                               # horario → horrario


def ensuciar(texto, rng):
    """Convierte una frase limpia en una escrita «con prisa».

    Aplica capas de error al azar y regresa (texto_sucio, lista_de_errores).
    La lista sirve después para saber QUÉ tipo de error tumbó al bot.
    """
    errores = []

    # Capa 1 (60 %): todo en minúsculas, sin acentos y sin '¿' — como en el celular.
    if rng.random() < 0.6:                    # random() da un número entre 0 y 1
        texto = sin_acentos(texto).lower().replace('¿', '')
        errores.append('sin_acentos')

    # Capa 2 (40 %): cambia UNA palabra por su abreviatura (q, xfa, pa…).
    if rng.random() < 0.4:
        for largo, corto in ABREVIATURAS.items():
            # Los espacios alrededor evitan falsos positivos: 'que' NO debe pegar dentro de 'quedan'.
            if f' {largo} ' in f' {texto} ':
                texto = texto.replace(largo, corto)
                errores.append('abreviatura')
                break                         # basta con una abreviatura por frase

    # Capa 3 (siempre): 1 o 2 dedazos en palabras de 4+ letras.
    palabras = texto.split()                  # 'hola que tal' → ['hola', 'que', 'tal']
    # Comprensión de lista: guardamos los ÍNDICES de las palabras largas (sin contar signos).
    largas = [i for i, p in enumerate(palabras) if len(p.strip('¿?,.!')) >= 4]
    # [1, 1, 2]: dos tercios de las veces 1 dedazo, un tercio 2. min() evita pedir más de las que hay.
    for i in rng.sample(largas, k=min(len(largas), rng.choice([1, 1, 2]))):
        palabras[i], tipo = dedazo(palabras[i], rng)   # desempaquetado: la tupla se reparte en 2 variables
        errores.append(tipo)
    return ' '.join(palabras), errores        # volvemos a unir la lista en una frase


def generar_pool(semilla=SEMILLA):
    """Arma las 200 preguntas: a cada estudiante le toca su porción de temas.

    Regresa una lista de diccionarios; cada diccionario es una fila del CSV.
    """
    # Generador de azar PROPIO con semilla: no depende de nada externo, siempre igual.
    rng = random.Random(semilla)

    # Paso 1: convertir porcentajes en una «bolsa» de temas.
    # 22 % de 200 = 44 → la lista lleva 'inscripcion' 44 veces, y así con cada tema.
    total = len(PERFILES) * PREGUNTAS_POR_ESTUDIANTE
    temas = [tema for tema, pct in MEZCLA.items() for _ in range(round(total * pct / 100))]
    rng.shuffle(temas)                        # revolvemos la bolsa (modifica la lista en su lugar)

    pool = []
    # enumerate da (número, elemento); la tupla del perfil se desempaqueta en 3 variables.
    for n, (nombre, estilo, tasa_sucio) in enumerate(PERFILES):
        # Rebanada de 20 temas para este estudiante: el 0 toma [0:20], el 1 toma [20:40]…
        for tema in temas[n * PREGUNTAS_POR_ESTUDIANTE:(n + 1) * PREGUNTAS_POR_ESTUDIANTE]:

            # Paso 2: elegir la frase limpia y su respuesta correcta.
            if tema == 'dos_temas':
                texto, esperada = rng.choice(DOS_TEMAS)            # la tupla trae su propia etiqueta
            else:
                texto, esperada = rng.choice(PLANTILLAS[tema]), tema

            # Paso 3: muletillas («Oye, …», «… por favor»). No a saludos ni despedidas:
            # «Oye, hola gracias» no lo escribe nadie.
            if tema not in ('saludo', 'agradecimiento', 'despedida', 'ayuda'):
                abridor = rng.choice(ABRIDORES)
                if abridor:
                    # Tras la muletilla la frase sigue en minúscula: «Oye, ¿cómo…».
                    # k salta el '¿' para bajar la primera LETRA, no el signo.
                    k = 1 if texto.startswith('¿') else 0
                    texto = abridor + texto[:k] + texto[k].lower() + texto[k + 1:]
                texto += rng.choice(CIERRES)

            # Paso 4: ¿este estudiante escribe sucio esta vez? Depende de su perfil.
            errores = []
            if rng.random() < tasa_sucio:
                texto, errores = ensuciar(texto, rng)

            # Paso 5: guardar la fila. bool([]) es False y bool(['x']) es True.
            pool.append({'estudiante': nombre, 'estilo': estilo, 'tipo': tema, 'pregunta': texto,
                         'esperada': esperada, 'sucia': bool(errores), 'errores': '+'.join(errores)})
    return pool


# =====================================================================
# 3. PROGRAMA PRINCIPAL
# =====================================================================
# Este bloque solo corre si ejecutas el archivo directo (python estudiantes.py).
# Si otro script hace «import estudiantes», NO corre: solo se cargan las funciones.
if __name__ == '__main__':
    pool = generar_pool()

    # El CSV queda en la misma carpeta que este archivo, sin importar desde dónde lo corras.
    salida = Path(__file__).with_name('pool_preguntas.csv')
    # «with» abre el archivo y lo cierra solo al terminar, aunque haya un error.
    # newline='' evita líneas en blanco extra en Windows; utf-8 respeta los acentos.
    with salida.open('w', newline='', encoding='utf-8') as f:
        escritor = csv.DictWriter(f, fieldnames=list(pool[0]))   # columnas = llaves del 1er diccionario
        escritor.writeheader()                                   # fila de títulos
        escritor.writerows(pool)                                 # las 200 filas

    # sum() sobre booleanos cuenta los True (True vale 1, False vale 0).
    sucias = sum(p['sucia'] for p in pool)
    # f-string: {…:.0%} formatea 0.35 como «35%».
    print(f'{len(pool)} preguntas → {salida.name} · sucias: {sucias} ({sucias / len(pool):.0%})')
