"""Texto en español de la guía. No es un módulo para importar: genera_guida.py lo ejecuta con exec() en un
espacio de nombres que ya contiene los helpers y los números comunes (fig, frac, table, num, diagram, VERSION,
ICON, IMG, UA, UB, GEAR17, um_step, dof, OBJ, APP). El texto llena la lista H con las secciones HTML.
"""
# ruff: noqa: F821  (los nombres vienen de genera_guida.py)

META = {
    "lang": "es",
    "title": "Focus Stack — Guía de uso",
    "footer": "Guía de uso",
    "pdf": "ES Focus Stack - Guía.pdf",
}


def ui(s):
    """Nombre en español de un comando de la app (la clave es el texto italiano; APP = cadenas de la app)."""
    return APP.get(s, s)


# nome dell'opzione con l'apostrofo: in una costante, perché Python 3.11 non accetta virgolette annidate nelle f-string
COIL_HOLD = "Anche quando viene disconnesso o si spegne l'applicazione"


DIAGRAM_LABELS = {
    "motor": "Motor", "gearbox": "Reductor", "pulleys": "Poleas / engranajes", "knob": "Enfoque fino", "stage": "Platina",
    "motor1": "pasos por vuelta", "motor2": "× micropaso",
    "gearbox1": "(si lo hay)", "gearbox2": "p. ej. 26,85 : 1",
    "pulleys1": "dientes conducida", "pulleys2": "÷ dientes motriz",
    "knob1": "µm por vuelta", "knob2": "del mando",
    "stage1": "se desplaza", "stage2": "en µm",
    "ratio": "relación de reducción total = reductor × poleas",
    "steps": "pasos del motor por vuelta del mando = pasos/vuelta × micropaso × relación",
}

# schema «Come li usa la fusione» (7.6): etichette dello SVG, testo semplice (&lt; per <)
CALIB_LABELS = {
    "col_dark": 'MASTER DARK',
    "col_stack": 'PILA DEL SUJETO',
    "col_flat": 'MASTER FLAT',
    "dark": 'Darks · N tomas',
    "dark1": 'tapa, mismos ISO y tiempo',
    "mean": 'media píxel a píxel',
    "D": 'D: master dark',
    "flat": 'Flats · N tomas',
    "flat1": 'campo uniforme, misma óptica',
    "flat_mean": 'media − darks de los flats',
    "norm": '÷ su propia media',
    "F": 'F: flat normalizado',
    "F1": '&lt; 1 en bordes y sobre el polvo',
    "frame": 'Cada fotograma I',
    "frame1": 'RAW, luz lineal',
    "fusion": 'alineación y fusión',
    "note1": 'Sin darks no hay resta,',
    "note2": 'sin flats no hay división.',
}

# grafico d'esempio dell'analisi del sensore (7.6)
SENSOR_LABELS = {
    "title_dr": 'Rango dinámico (pasos)',
    "title_rn": 'Ruido de lectura (electrones)',
    "unreliable": 'no fiable',
    "stops": 'pasos',
    "dcg1": 'doble ganancia:',
    "dcg2": 'de 3,0 a 1,2 e-',
    "dec": ',',
}

# tabla de la profundidad de campo (nombres de los objetivos en el idioma de la guía)
OBJ_NAMES = ["4× / 0,10", "10× / 0,25", "20× / 0,40", "40× / 0,65", "60× / 0,85", "100× / 1,25 aceite"]
dof_rows = []
for name, (mag, na) in zip(OBJ_NAMES, OBJ):
    d = dof(na, mag, 3.9)
    s = d * 0.7
    dof_rows.append([name, num(d), num(s), str(max(1, round(s / UA))), str(max(1, round(s / UB)))])
dof_note = ("con los objetivos de inmersión en aceite la fórmula de la app (índice n = 1, aire) subestima la "
            "profundidad de campo, así que el paso calculado queda del lado de la seguridad.")

H = []
add = H.append

add(f"""
<section class="cover">
  <div class="icon">{ICON}</div>
  <h1 class="title">Focus Stack</h1>
  <div class="sub">Guía de uso<br>enfocador motorizado y cámara para el apilado de enfoque en el microscopio</div>
  <div class="shot-c"><img src="{IMG}/sessione.jpg" alt=""></div>
  <div class="meta"><span>Versión de la app {VERSION}</span><span>Noviembre de 2026</span></div>
</section>
""")

add("""
<h1 style="break-before:auto">Índice</h1>
<div class="toc"><ol>
<li><span>1</span>Qué es Focus Stack<em>cómo funciona, qué se necesita</em></li>
<li><span>2</span>Instalación, inicio y actualizaciones</li>
<li><span>3</span>La interfaz de un vistazo<em>las cinco pestañas, la barra superior y la guía</em></li>
<li><span>4</span>Conectar el enfocador y la cámara<em>ajustes de la Nikon D5600 y de otras cámaras</em></li>
<li><span>5</span>El enfocador: posición, movimientos, STOP<em>movimiento continuo por tramos, el carro que no avanza</em></li>
<li><span>6</span>Cámara, foto de prueba y vista en vivo</li>
<li><span>7</span>La secuencia de apilado<em>perfiles ópticos, macro fotográfica, varias fotos por posición, los archivos de la pila,
calibración (darks, flats, exposición), progreso en el smartphone</em></li>
<li><span>8</span>El visor<em>zoom, vista en vivo, autoenfoque en un punto, Inspector</em></li>
<li><span>9</span>Límites de seguridad</li>
<li><span>10</span>Configuración mecánica: los cálculos<em>resolución en µm por paso, medición de comprobación, recorrido, velocidad, holgura</em></li>
<li><span>11</span>Elegir el paso de la secuencia<em>profundidad de campo, número de fotos, duración</em></li>
<li><span>12</span>Motor, controles manuales, autoenfoque, actualizaciones, temperatura</li>
<li><span>13</span>Una sesión típica, paso a paso</li>
<li><span>14</span>Si algo no funciona</li>
<li><span>15</span>Atajos de teclado</li>
</ol></div>
""")

# 1
add(f"""
<h1><span class="n">1</span>Qué es Focus Stack</h1>
<p class="lead">Focus Stack controla desde el Mac un enfocador motorizado, montado en el enfoque fino (tornillo
micrométrico) del microscopio o en un carro macro, y una cámara conectada por USB. Ejecuta automáticamente secuencias <b>mover → esperar →
disparar</b>: decenas de fotos con distintos planos de enfoque, listas para fundirlas en una única imagen
nítida de principio a fin con <b>Helicon Focus</b> (o un programa similar).</p>
<h2>Cómo funciona</h2>
<p>La app Focus Stack inicia en el Mac un pequeño programa (el <i>servidor</i>) que se comunica con el enfocador
(una placa Arduino con el firmware myFocuserPro2) y con la cámara. La interfaz se abre en la <b>ventana
de la app</b>: es una página web servida en la dirección <code>http://localhost:8765</code>, accesible solo desde este
Mac (también se puede abrir en un navegador).</p>
<ul>
<li>El <b>enfocador</b> gira el mando de enfoque con un motor paso a paso. Cada <i>paso</i> del motor desplaza la
  platina (o el objetivo) una fracción de micrómetro; cuánto exactamente lo calcula la <b>configuración
  mecánica</b> (capítulo 10).</li>
<li>La <b>cámara</b> se controla con el mismo protocolo que usan los programas de los fabricantes: tiempo de
  exposición, ISO, formato, disparo, descarga de las fotos y vista en vivo.</li>
<li>Los <b>botones físicos</b> del enfocador siguen funcionando con la app abierta.</li>
</ul>
<h2>Qué se necesita</h2>
<ul>
<li>Un Mac con macOS 13 o posterior (Intel) o macOS 14 o posterior (Apple Silicon).</li>
<li>Un enfocador <b>myFocuserPro2</b> (versión con driver DRV8825) o <b>Ardufocus</b> (placa rev1 con DRV8825),
  conectado con su cable USB y alimentado (12 V).</li>
<li>Una cámara Nikon, Canon o Sony con su cable USB. En esta guía el ejemplo es una <b>Nikon D5600</b>.</li>
<li>En el microscopio, un adaptador que proyecte la imagen sobre el sensor (fototubo, adaptador T2 o similar). En
  <b>macro fotográfica</b>, un objetivo macro (con tubos o lentes de aproximación, si hace falta) y un carro movido por el
  enfocador.</li>
</ul>
<div class="box warn"><span class="t">Enfocadores compatibles</span>Focus Stack funciona con las placas
<b>myFocuserPro2</b> y <b>Ardufocus</b>, con el firmware incluido en la app. Un myFocuserPro2 con su firmware original se
conecta enseguida y la app ofrece actualizarlo con un clic. En cambio, un Ardufocus con su firmware original (protocolo
Moonlite) no se reconoce: la primera vez hay que cargar a mano el firmware de Focus Stack (instrucciones en el README de
github.com/teoteo/focus-stack); después, el Ardufocus también se actualiza desde la app.</div>
<div class="box tip"><span class="t">Sin hardware</span>Las tarjetas Enfocador y Cámara tienen la casilla
<span class="ui">{ui("Simulatore")}</span>: permite probar toda la app sin conectar nada. Las capturas de esta guía
se hicieron así.</div>
""")

# 2
add(f"""
<h1><span class="n">2</span>Instalación, inicio y actualizaciones</h1>
<h2>Primera instalación</h2>
<ol class="steps">
<li>Descarga <code>FocusStack-&lt;versión&gt;.zip</code> de la página
  <b>github.com/teoteo/focus-stack/releases</b> y ábrelo: aparece la app <b>Focus Stack</b>.</li>
<li>Arrastra Focus Stack a la carpeta <b>Aplicaciones</b> antes de abrirla.</li>
<li>Ábrela. macOS avisa de que no puede verificar al desarrollador, porque la app no está firmada por Apple.
  Abre <b>Ajustes del Sistema › Privacidad y seguridad</b>, desplázate hacia abajo y haz clic en <b>Abrir igualmente</b>.
  Solo hace falta la primera vez.</li>
</ol>
<p>La app ya contiene todo lo que necesita: no hay que instalar nada más.</p>
<h2>Abrir y cerrar</h2>
<ul>
<li>Al iniciarse, Focus Stack abre su ventana y se queda en el Dock. Cerrar la ventana (<kbd>⌘W</kbd>) solo la
  oculta: la app sigue abierta y un clic en el icono del Dock la vuelve a mostrar. El visor y la guía se abren en
  ventanas separadas; los enlaces a sitios externos se abren en el navegador.</li>
<li>Para cerrarla: <kbd>⌘Q</kbd> en la app, o <span class="ui">Salir</span> en el menú del icono del Dock.
  Si hay una secuencia en curso, la app pide confirmación, la interrumpe y detiene el motor.</li>
<li>Durante una pila o una serie de calibración, el icono del Dock muestra una <b>barra de progreso</b>. Cuando
  termina, o se detiene por un error, mientras usas otra app llega una <b>notificación</b>: la primera vez macOS
  pide permiso.</li>
</ul>
<h2>Actualizaciones</h2>
<p>Al iniciarse, y luego cada 6 horas, la app comprueba si hay una versión nueva. Si la hay, arriba aparece una
barra con <span class="ui">{ui("Aggiorna e riavvia")}</span>: la app descarga la nueva versión, se cierra y se vuelve
a abrir sola. La misma comprobación puede hacerse a mano en
<span class="ui">{ui("Configurazione")} › {ui("Aggiornamenti")} › {ui("Controlla ora")}</span>.</p>
<p>El <b>firmware del enfocador</b> también se actualiza desde la app (capítulo 12): cuando el de la placa es más
antiguo que el incluido en la app, la misma barra lo indica. Conviene instalarlo: la build 5, por ejemplo, hace el
movimiento continuo sin paradas y detiene por sí sola el motor si el Mac deja de comunicarse (capítulo 12).</p>
<h2>Idioma</h2>
<p>La app habla italiano, inglés, francés, alemán y español. Con <span class="ui">{ui("Automatica (lingua del sistema)")}</span> sigue el
idioma de macOS y, para los demás idiomas, usa el inglés; en
<span class="ui">{ui("Configurazione")} › {ui("Lingua")}</span> puedes fijar un idioma. La elección se aplica a la interfaz,
los mensajes y el registro, y esta guía existe en los mismos idiomas.</p>
""")

# 3
add(f"""
<h1><span class="n">3</span>La interfaz de un vistazo</h1>
<p>La página tiene cinco pestañas, que se eligen arriba:</p>
<ul>
<li><b>{ui("Sessione")}</b>: el trabajo en el microscopio. Enfocador, secuencia, cámara y última foto.</li>
<li><b>{ui("Ottica")}</b>: los <b>perfiles</b> de objetivo, filtro e iluminación, para el microscopio o para la macro
  fotográfica, que se guardan en los datos de cada pila, y el cálculo de la profundidad de campo (capítulos 7.2, 7.3
  y 11).</li>
<li><b>{ui("Calibrazione")}</b>: la exposición de los lights y los fotogramas de calibración (darks, flats, darks de los
  flats) para el software de fusión (capítulo 7.6).</li>
<li><b>{ui("Configurazione")}</b>: límites, mecánica, controles manuales, motor, progreso en el smartphone, idioma,
  actualizaciones y temperatura. Se ajusta una vez y luego se toca rara vez.</li>
<li><b>{ui("Registro")}</b>: la lista de todo lo que ha pasado en la sesión, con la hora. Es el primer sitio
  donde mirar si algo no funciona.</li>
</ul>
{fig("sessione", layout="full", caption="La pestaña Sesión: a la izquierda el enfocador, en el centro la secuencia, a la derecha la cámara y la última foto.")}
<h2>Barra superior</h2>
{fig("barra-superiore", [
    f"<b>Pestañas</b> {ui('Sessione')}, {ui('Ottica')}, {ui('Calibrazione')}, {ui('Configurazione')} y {ui('Registro')}.",
    "<b>Estado de las conexiones</b>: Servidor, Enfocador y Cámara. Verde = conectado, gris = desconectado, rojo = error.",
    "<b>Temperatura</b> leída por la sonda del enfocador.",
    "<b>?</b> abre esta <b>guía</b> en el capítulo de la pestaña abierta.",
    "<b>Tema</b> oscuro o claro. El tema oscuro cansa menos la vista en las sesiones largas al microscopio.",
], layout="full below-marks", anchors={1: "b", 2: "b", 3: "b", 4: "b", 5: "b"})}
<p>Bajo la barra pueden aparecer dos franjas: la azul de las <b>actualizaciones</b> y la roja de <b>alarma</b>, por
ejemplo cuando los botones físicos llevan el enfocador más allá de un límite.</p>
<div class="box tip"><span class="t">La guía dentro de la app</span>Además del <b>?</b> de arriba, casi todas las
tarjetas tienen un pequeño <b>?</b> junto al título: abre esta guía directamente en la parte que explica esa tarjeta. La
guía tiene un índice y una búsqueda (tecla <kbd>/</kbd>) y se abre siempre en la misma ventana.</div>
""")

# 4
add(f"""
<h1><span class="n">4</span>Conectar el enfocador y la cámara</h1>
<h2>Enfocador</h2>
{fig("connessione-focheggiatore", [
    "<b>Puerto serie</b> del enfocador. Suele llamarse <code>/dev/cu.usbserial-…</code> o <code>/dev/cu.wchusbserial…</code>; el nombre cambia si usas otra toma USB del Mac.",
    "<b>Actualiza la lista</b> de puertos después de conectar el cable.",
    f"<b>{ui('Simulatore')}</b>: un enfocador ficticio para probar la app.",
    f"<b>{ui('Connetti')}</b>. Al abrir el puerto el Arduino se reinicia: la conexión tarda 2–3 segundos.",
], layout="side narrow")}
<h2>Cámara</h2>
{fig("connessione-fotocamera", [
    f"<b>Cámara</b>: deja <i>{ui('Rilevamento automatico')}</i> o elige el modelo encontrado.",
    "<b>Detecta</b> las cámaras conectadas.",
    f"<b>{ui('Simulatore')}</b>: una cámara ficticia que genera imágenes de prueba.",
    f"<b>{ui('Connetti')}</b>. Antes de conectarse, la app cierra los servicios de macOS que se apropian de la cámara.",
], layout="side narrow")}
<p>Al abrirse, la app <b>se vuelve a conectar sola</b> al enfocador y a la cámara usados la última vez, si están
conectados al Mac: basta con haberlos conectado una vez con <b>{ui('Connetti')}</b>. El enfocador solo se vuelve a
conectar si es el mismo adaptador USB (otro dispositivo con el mismo nombre de puerto no se toca) y conectarse no mueve
el motor. Si una conexión falla, queda una línea en el registro, y <b>{ui('Connetti')}</b> funciona como siempre.</p>
<h3>Ajustes en la cámara</h3>
{table(["Cámara", "Qué ajustar"], [
    ["<b>Nikon D5600</b> y otras Nikon", "Dial de modo en <b>M</b> (manual). En el menú de reproducción desactiva la <b>revisión de imagen</b>. Apaga SnapBridge/Wi-Fi y Bluetooth, que pueden ocupar la conexión. Mantén una tarjeta de memoria insertada y la batería cargada (o usa el adaptador de corriente EH-5/EP-5A)."],
    ["Canon", "Modo <b>M</b>. La foto va a la memoria de la cámara o a la tarjeta según el <i>Destino</i>. Para el retardo del espejo, activa el <b>bloqueo del espejo</b> en el menú."],
    ["Sony", "Menú USB › <b>PC Remote</b>; modo <b>M</b>. Para descargar las fotos en el Mac, ajusta el destino en <b>Solo PC</b> (MENU › Ajustes › Ajustes de PC remoto › Destino guardado imágenes). Para la vista en vivo, la cámara debe permitirla en PC Remote."],
])}
<div class="box warn"><span class="t">Si la cámara no se conecta</span>macOS intenta apropiarse de la cámara en cuanto
la conectas. La app cierra ese servicio por sí sola; si no basta, cierra <b>Fotos</b>, <b>Vista Previa</b>,
<b>Captura de Imagen</b>, NX Studio y EOS Utility y vuelve a intentarlo. Desconectar y volver a conectar el cable
con la cámara encendida suele ayudar.</div>
""")

# 5
add(f"""
<h1><span class="n">5</span>El enfocador: posición, movimientos, STOP</h1>
{fig("focheggiatore", [
    f"<b>Estado</b>: {ui('Fermo')}, {ui('In movimento')}, {ui('Disconnesso')}.",
    f"<b>Conexión</b>: puerto, versión del firmware y máximo del firmware (la posición más alta admitida). <span class='ui'>{ui('Disconnetti')}</span> libera el puerto.",
    "<b>Posición</b> en pasos del motor y, debajo, en milímetros o micrómetros (si la mecánica está configurada).",
    "<b>Límites</b> establecidos y distancia que queda, hacia la muestra, antes del límite.",
    "<b>Barra de recorrido</b>: mira la figura de abajo.",
    f"<b>Tamaño del paso</b> de los botones {ui('Allontana')}/{ui('Avvicina')}: 1, 10, 100… pasos. Los tamaños disponibles se eligen en {ui('Configurazione')} › {ui('Comandi manuali')}.",
    "El mismo desplazamiento <b>en micrómetros</b>.",
    f"<b>{ui('Allontana')} / {ui('Avvicina')}</b>: un clic mueve el tamaño elegido. Si mantienes pulsado, el motor sigue avanzando, por tramos (capítulo 12), y al soltar frena hasta detenerse.",
    f"<b>Ir a la posición</b>: escribe un número de pasos y haz clic en {ui('Vai')}.",
    "<b>STOP</b>: detiene en el acto el motor y la secuencia en curso, si la hay. Con el teclado: <kbd>Esc</kbd>. Después del STOP el motor permanece parado hasta que vuelvas a pulsar un botón.",
])}
<h2>La barra de recorrido</h2>
{fig("binario", [
    "<b>Zonas rayadas en rojo</b>: fuera de los límites, prohibidas.",
    "<b>Franja azul</b>: el intervalo de la secuencia, con una marca por cada foto.",
    "<b>Línea blanca</b>: la posición actual.",
], layout="side narrow")}
<p>Bajo la barra: el límite inferior, la flecha que indica <b>en qué lado está la muestra</b> y el límite superior.
“{ui('Avvicina')}” siempre mueve hacia la muestra, sea cual sea el sentido de los números: se ajusta en
{ui('Configurazione')} › {ui('Fine corsa')} (capítulo 9).</p>
<div class="box tip"><span class="t">Teclado</span><kbd>↑</kbd> aleja, <kbd>↓</kbd> acerca: una pulsación breve da un
paso; la tecla mantenida pulsada mueve de forma continua hasta soltarla (como los botones). <kbd>⇧</kbd> junto con la flecha multiplica el paso por 10, las teclas numéricas <kbd>1</kbd> <kbd>2</kbd>
<kbd>3</kbd>… eligen el tamaño, <kbd>Esc</kbd> es el STOP. Funcionan en la pestaña {ui('Sessione')}, también
mientras miras la vista en vivo.</div>
<div class="box warn"><span class="t">Botones físicos</span>Los botones del enfocador mueven el motor sin pasar por
la app. La app los vigila y, si la posición sale de los límites, envía STOP y muestra una alarma; para una
protección completa lee el capítulo 9. Si los pulsas durante una secuencia, la secuencia se pone en pausa.</div>
<div class="box warn"><span class="t">Si el carro no avanza con pasos pequeños</span>Con
<span class="ui">{ui('Alimentazione bobine motore › Sempre quando connesso')}</span> desactivado ({ui('Configurazione')} › Motor), el motor
pierde, en cada parada, la fuerza que lo mantiene en su posición: la carga (peso de la cámara, un muelle, la correa) puede
hacerlo retroceder. El contador de pasos avanza, pero el carro se queda donde está y toda la pila sale en el mismo plano.
Durante la secuencia la app alimenta las bobinas por sí sola (capítulo 12); para los movimientos manuales de pocos pasos,
actívalas, o comprueba en la vista en vivo que la imagen se desplaza de verdad.</div>
""")

# 6
add(f"""
<h1><span class="n">6</span>Cámara, foto de prueba y vista en vivo</h1>
{fig("fotocamera", [
    f"<b>Estado</b>: {ui('Pronta')}, {ui('Scatto…')}, {ui('Disconnessa')}.",
    f"<b>Modelo</b> conectado y <span class='ui'>{ui('Disconnetti')}</span>.",
    f"<b>{ui('Tempo di posa')}</b> e <b>ISO</b>.",
    f"<b>{ui('Diaframma')}</b> y <b>{ui('Formato')}</b> (RAW, JPEG…). En el microscopio, sin objetivo en la cámara, normalmente no hay diafragma.",
    f"<b>{ui('Destinazione')}</b>: memoria de la cámara o tarjeta.",
    "<b>Bulb</b> en segundos: 0 usa el tiempo de exposición; un valor mayor que 0 hace una exposición Bulb controlada por el Mac, para tiempos de más de 30 s.",
    f"<b>{ui('Ritardo specchio (reflex)')}</b>, de 0,5 a 2,5 s: espera entre la subida del espejo y el disparo, para que se amortigüen las vibraciones. En la Nikon D5600 la app usa el <i>modo de retardo de exposición</i> de la propia cámara.",
    f"<b>{ui('Rileggi')}</b> los ajustes de la cámara. Tras cada cambio, la app vuelve a leer el valor que la cámara ha aceptado realmente.",
    f"<b>{ui('◉ Scatto di prova')}</b>: una foto en la posición actual, que aparece en {ui('Ultimo scatto')} y en el visor.",
])}
<p>Con las <b>Sony</b>, el tiempo de exposición y el ISO cambian a saltos, como al girar el dial: un valor lejano
puede tardar unos segundos. En la <b>A6400</b> el menú del ISO llega a 102400, el máximo que acepta. Si la cámara no
acepta un valor en 12 segundos, la app lo avisa: desconecta y vuelve a conectar el cable USB, o apaga y enciende la
cámara.</p>
<h2>Última foto y vista en vivo</h2>
<div class="two">
{fig("ultimo-scatto", [
    f"<b>{ui('● Live')}</b>: muestra la imagen en vivo de la cámara.",
    f"<b>{ui('Apri visualizzatore ↗')}</b> en una ventana aparte (capítulo 8).",
    f"<b>{ui('Ultimo scatto')}</b>: un clic la abre en el visor.",
    "Nombre del archivo, posición y temperatura en el momento de la foto.",
], layout="stack")}
{fig("live", [
    f"<b>{ui('■ Ferma live')}</b> apaga la vista en vivo.",
    f"Estado: <b>{ui('LIVE')}</b>, o bien <b>{ui('SCATTO…')}</b> durante una foto de prueba.",
    "Modelo de la cámara. Doble clic en la imagen: pantalla completa.",
], layout="stack")}
</div>
<p>La vista en vivo llega hasta 15 imágenes por segundo y es la forma más cómoda de encontrar el inicio y el fin de
la secuencia mientras mueves el enfocador con el teclado. Cuando empieza la secuencia, la vista en vivo sigue
activa mientras el enfocador vuelve a la posición inicial, para que puedas vigilarlo; al llegar se pone en pausa (el
espejo tiene que bajar y la cámara tiene que disparar con normalidad) y se cierra con la primera foto: el recuadro
vuelve a mostrar la última foto, también en el visor. Terminada la pila, vuelve a activarla con
<span class="ui">{ui('● Live')}</span>. En las réflex el espejo permanece subido mientras la vista en vivo está activa.
La vista en vivo activada desde la ventana principal arranca también en el visor, si está abierto;
<span class="ui">{ui('■ Ferma live')}</span> la apaga en las dos ventanas. Con <span class="ui">{ui('◉ Scatto di prova')}</span>
y la vista en vivo activa, el recuadro muestra la foto y la vista en vivo vuelve sola en cuanto mueves el enfocador,
desde la app o con sus botones.</p>
<div class="box tip"><span class="t">Para enfocar con precisión</span>Abre la vista en vivo en el <b>visor</b>: puedes
ampliar al 100% y más, y desplazarte hasta el detalle que te interesa (capítulo 8).</div>
""")

# 7
add(f"""
<h1><span class="n">7</span>La secuencia de apilado</h1>
<h2 style="margin-top:0">7.1 Configurar la secuencia</h2>
{fig("sequenza", [
    f"<b>Estado</b>: {ui('Pronta')}, {ui('In corso')}, {ui('In pausa')}, {ui('Completata')}, {ui('Errore')}.",
    f"<b>{ui('Nome della pila')}</b>: las fotos van a una subcarpeta <code>nombre_fecha-hora</code>, con nombres <code>nombre_0001</code>, <code>nombre_0002</code>…",
    f"<b>{ui('＋ Nuova pila')}</b>: terminada una pila, prepara la siguiente (el estado vuelve a {ui('Pronta')}). Aunque tenga el mismo nombre, cada pila va a una carpeta nueva.",
    f"<b>{ui('Inizio')}</b> y <b>{ui('Fine')}</b> en pasos. <span class='ui'>⌖ {ui('qui')}</span> copia la posición actual.",
    "<b>Paso</b> entre una foto y la siguiente, en pasos del motor (cap. 11).",
    f"<b>{ui('Numero di scatti')}</b>. Si cambias {ui('Inizio')}, {ui('Fine')} o Paso, se recalcula el número de fotos; si cambias el número de fotos, se recalcula el paso. Cuando el paso cambia solo, se vuelve naranja y muestra <span class='ui'>↺ era …</span>: un clic deshace el cambio.",
    "<b>Espera tras el movimiento</b>: deja que se amortigüen las vibraciones antes del disparo (1–3 s en el microscopio).",
    f"<b>{ui('Ottica e filtro (profilo)')}</b>: el perfil de objetivo, filtro e iluminación que se escribe en los datos de la pila (7.2). <span class='ui'>{ui('Modifica')}</span> lo abre en la pestaña {ui('Ottica')}. Sin perfil, la pila figura como «{ui('nessun filtro')}». Con un perfil macro que indica el diafragma, elegirlo ajusta también el diafragma de la cámara; si después no coinciden, el resumen lo avisa.",
    "<b>Resumen</b>: fotos, recorrido en pasos y µm, paso en µm y duración estimada. Un clic en el resumen (▶ a la derecha) muestra también el perfil óptico usado y la calibración que se vinculará a la pila. Si la secuencia sale de los límites, aparece un aviso rojo y no se inicia.",
    f"<b>{ui('Salva in')}</b>: carpeta de las fotos. <span class='ui'>{ui('Scegli…')}</span> abre el panel del Finder, <span class='ui'>{ui('Apri')}</span> la muestra en el Finder.",
    f"<b>{ui('Scatti per posizione')}</b>: cuántas fotos se toman en cada posición (por defecto 1). Con varias, el software de fusión puede promediarlas y reducir el ruido (7.4).",
    "<b>Pausa tras el disparo</b>: tiempo para escribir en la tarjeta y recargar el flash.",
    "<b>Compensación de holgura</b>: antes de la primera foto el motor retrocede estos pasos y luego avanza, para llegar a cada foto desde la misma dirección.",
    f"<b>{ui('Modalità di scatto')}</b>: <i>{ui('Scarica sul Mac')}</i> (recomendado), <i>{ui('Solo sulla scheda')}</i>, <i>{ui('Solo trigger (veloce)')}</i> (con destino tarjeta).",
    "<b>Volver al inicio</b> al terminar.",
    f"<b>{ui('Suono sul Mac a fine sequenza')}</b>: un sonido claro si la pila se ha completado, uno grave si se ha detenido por un error o se ha puesto en pausa sola.",
    f"<b>{ui('Preset')}</b>: guarda y recupera los ajustes de la secuencia, p. ej. uno por objetivo.",
    "<b>Progreso</b>: fotos tomadas, tiempo restante, posición.",
    f"<b>{ui('▶ Avvia sequenza')}</b>, <b>{ui('❚❚ Pausa')}</b>/<b>{ui('Riprendi')}</b> e <b>{ui('■ Interrompi')}</b>.",
    f"<b>{ui('Apri nel Finder')}</b>: al terminar, abre la carpeta de la pila, con las fotos, <code>sequence.json</code> y <code>sequence.txt</code> (7.5).",
])}
<p>Las fotos por posición, la pausa tras el disparo, la holgura, el modo, la vuelta al inicio y el sonido están en la
sección plegable <span class="ui">{ui('Tempi, gioco e scatti per posizione')}</span>. Si las bobinas del motor están
apagadas y la app no las alimenta durante la secuencia, debajo aparece un aviso naranja (capítulo 12).</p>
<h2>Durante la secuencia</h2>
{fig("sequenza-in-corso", [
    f"El estado pasa a <b>{ui('In corso')}</b> (ámbar).",
    "Fotos tomadas sobre el total, tiempo restante estimado y posición actual. En la barra de recorrido las marcas de las fotos ya tomadas cambian de color.",
    f"<b>{ui('❚❚ Pausa')}</b> se detiene después de la foto en curso; <b>{ui('■ Interrompi')}</b> termina la secuencia. El <b>STOP</b> del enfocador también detiene el motor en el acto.",
], layout="side narrow")}
<ul>
<li>Si pulsas los <b>botones físicos</b> del enfocador, la secuencia se pone en pausa; al reanudarla vuelve a la
  posición correcta y repite la foto.</li>
<li><b>Si una foto falla</b>, la app lo reintenta al cabo de 3 s; al segundo error vuelve a conectar la cámara por sí
  sola y lo intenta de nuevo. Si no basta, la secuencia <b>se pone en pausa</b> (no se detiene) y el mensaje dice qué
  comprobar: arregla la cámara (batería, cable, tarjeta) y pulsa <span class="ui">{ui('Riprendi')}</span>. La app vuelve a
  conectar la cámara, regresa a la misma posición y repite la foto; las fotos siguen en la misma carpeta.</li>
<li><b>El Mac no entra en reposo</b> mientras la secuencia está en curso: el reposo suspendería el USB y la cámara
  desaparecería a mitad de la pila. La pantalla sí puede apagarse. Atención: si cierras la tapa de un portátil sin
  monitor externo, el Mac entra en reposo de todos modos.</li>
<li>Si las bobinas del motor están apagadas con el motor parado, la app las alimenta durante toda la pila y las vuelve a
  apagar después de la vuelta al inicio (capítulo 12).</li>
<li>Los campos de la secuencia están bloqueados mientras la secuencia está en curso.</li>
<li>Cada foto nueva aparece en {ui('Ultimo scatto')} y en el visor. Para seguir la pila lejos del Mac existe el
  progreso en el smartphone (7.7).</li>
</ul>

<h2>7.2 Óptica y filtro: los perfiles</h2>
<p>El software de fusión trabaja mejor si sabe con qué se tomaron las fotos: con el aumento y el píxel del sensor
puede dar el mapa de profundidad y la vista 3D en micrómetros reales. Estos datos se guardan en la pestaña
<b>{ui('Ottica')}</b> como <b>perfiles</b> con nombre, uno por cada combinación de objetivo, filtro e iluminación
(por ejemplo «10× GFP», «4× campo claro»), y se eligen en la secuencia (número 8 de la figura anterior). Cada perfil
es de tipo <b>{ui('Microscopio')}</b> o <b>{ui('Macro fotografica')}</b> (7.3). En la figura, un perfil para microscopio:
un objetivo 10× con el cambiador de aumento Optovar 1,6× y la cámara en un adaptador T2 sin lentes.</p>
{fig("ottica", [
    f"<b>{ui('Profilo da modificare')}</b>: elígelo para cargar sus valores; <i>{ui('— nuovo profilo —')}</i> empieza con un formulario vacío.",
    f"<b>{ui('Salva come nuovo profilo…')}</b>, en la barra que aparece arriba: pide un nombre y guarda una copia, sin tocar el perfil de partida.",
    f"<b>{ui('Elimina profilo')}</b>, tras una confirmación. <b>{ui('Rinomina…')}</b> cambia el nombre también en la secuencia y en los flats de la biblioteca de calibración.",
    f"<b>{ui('Tipo di ottica')}</b>, las dos pestañas arriba del panel {ui('Ottica')}, que cambian los campos de abajo: <i>{ui('Microscopio')}</i> (objetivo con aumento y NA grabados) o <i>{ui('Macro fotografica')}</i> (objetivo fotográfico, tubos y lentes de aproximación, 7.3).",
    f"<b>{ui('Pixel del sensore (pixel pitch in µm)')}</b>. Nikon D5600: <b>3,9 µm</b> (23,5 mm ÷ 6.000 píxeles). Se encuentra en la ficha técnica de la cámara, en <b>digicamdb.com</b> (cámaras fotográficas) o en la base de datos de sensores de <b>AstroBin</b> (cámaras dedicadas, buscando por ejemplo IMX571).",
    f"<b>{ui('Adattatore / oculare di proiezione')}</b> entre el microscopio y la cámara: nombre y factor, por ejemplo un adaptador C-mount de 0,5× o 0,63×, un fotocular de 2,5×, un adaptador T2 sin lentes de 1×. Vacío = 1×.",
    f'''<b>{ui("Cambio d'ingrandimento intermedio")}</b>, si el estativo lo tiene: nombre y factor, por ejemplo <i>Optovar</i> 1,25×, 1,6× o 2×. Vacío = 1×.''',
    "<b>Objetivo</b>: un nombre libre, tal como está grabado en el objetivo.",
    f'''<b>{ui("Ingrandimento dell'obiettivo")}</b>: el primer número grabado en el objetivo (<b>10</b>×/0,25).''',
    f"<b>{ui('Apertura numerica (NA)')}</b>: el segundo número grabado en el objetivo (10×/<b>0,25</b>).",
    f"<b>{ui('Immersione')}</b>: aire, agua, aceite, glicerina o silicona.",
    "<b>µm por píxel en la muestra, medidos</b> con un micrómetro objetivo: si se indican, valen más que el cálculo.",
    f"<b>{ui('Ingrandimento sul sensore')}</b> = objetivo × cambiador intermedio × adaptador (aquí 10 × 1,6 × 1 = 16×) y <b>escala en la muestra</b>: el valor medido o bien píxel del sensor ÷ aumento. Con una medida aparece también el <b>aumento real</b> (píxel del sensor ÷ µm por píxel medidos), que incluye lo que la cadena no dice, como la distancia del sensor o el tubo fotográfico; si la desviación es grande, junto al adaptador aparece el factor <i>sugerido por la medida</i>: un clic lo escribe en el campo.",
    f"<b>{ui('Filtro')}</b>: <i>{ui('Non indicato')}</i> (no se sabe), <i>{ui('Nessun filtro')}</i> o <i>{ui('Filtro montato')}</i>.",
    "<b>Nombre</b> y <b>tipo</b> del filtro: paso banda, paso largo (long pass), paso corto (short pass), densidad neutra, polarizador, otro.",
    "<b>Centro</b> y <b>ancho de banda</b> en nm para un paso banda; para paso largo y paso corto, la longitud de onda de corte.",
    f"<b>{ui('Illuminazione')}</b> (texto libre, con sugerencias), <b>intensidad</b> en % y <b>temperatura de color</b> en K (por ejemplo 4000 K para una luz neutra).",
    f"<b>{ui('Note')}</b> libres, que se guardan en los datos de la pila.",
    f"<b>{ui('Salva profilo')}</b>, en la barra <i>{ui('Modifiche non salvate')}</i> que aparece arriba en cuanto cambias un valor, con <b>{ui('Annulla')}</b> (vuelve al perfil guardado): sobrescribe el perfil elegido; si es nuevo, pide el nombre.",
    "El <b>perfil</b> abierto; en ámbar si hay cambios sin guardar.",
    "<b>Índice</b> de las secciones, con búsqueda: un clic lleva a la sección. Con Microscopio o Macro muestra solo las secciones de ese tipo.",
    "<b>Resumen</b>, siempre a la vista mientras escribes: aumento sobre el sensor, escala sobre la muestra (medida o calculada, con la desviación), profundidad de campo y paso recomendado.",
], layout="full")}
<p>Un campo vacío significa «no indicado» y no se escribe. Si en la secuencia no eliges ningún perfil, la pila
figura como tomada <b>sin filtro</b> y sin datos ópticos. Los mismos valores de NA, aumento y píxel sirven también para
el cálculo de la profundidad de campo (capítulo 11). Acuérdate de cambiar de perfil cuando cambies de objetivo o de
filtro: el resumen de la secuencia muestra siempre lo que se va a escribir.</p>

<h2>7.3 Macro fotográfica</h2>
<p>Con el tipo <span class="ui">{ui('Macro fotografica')}</span> el perfil describe un objetivo fotográfico en lugar de un
objetivo de microscopio. La app calcula a partir de él el aumento sobre el sensor, el diafragma efectivo y una NA
equivalente, que sirven para la escala en µm y para la profundidad de campo exactamente igual que en el microscopio.</p>
{fig("ottica-macro", [
    f"<b>{ui('Macro fotografica')}</b>: muestra los campos del objetivo fotográfico en lugar de los del microscopio.",
    f"<b>{ui('Cerca nel database')}</b>: escribe parte del nombre (por ejemplo «90 macro») y elige el objetivo. La base de datos es la de <b>Lensfun</b> (1162 objetivos), más algunos macro específicos que Lensfun no tiene (Canon MP-E 65, Laowa 25/90/100, OM 90) y tu lista personal.",
    f"<b>{ui('Marca')}</b> y <b>{ui('Modello').lower()}</b>: los rellena la búsqueda, o se escriben a mano.",
    "<b>Focal</b> y <b>diafragma más abierto</b>. Con un zoom, indica la focal usada.",
    f"<b>{ui('＋ Aggiungi al mio elenco')}</b>: guarda un objetivo que la base de datos no tiene, para encontrarlo en la búsqueda.",
    "<b>Relación de reproducción del objetivo</b>, leída en su escala a la distancia de enfoque usada: 1 = 1:1, 0,5 = 1:2, 0 = enfocado a infinito.",
    "<b>Diafragma ajustado</b> en el objetivo.",
    "<b>Tubos de extensión / fuelle</b>: la longitud total añadida entre el objetivo y la cámara, en mm.",
    "<b>Lentes de aproximación</b> delante del objetivo (Raynox y similares), hasta 3, con su potencia en dioptrías.",
    "<b>Resultado</b>: aumento sobre el sensor, diafragma efectivo, NA equivalente y escala en la muestra en µm por píxel.",
], layout="full")}
<p>Los cálculos son los de la óptica fotográfica de aproximación, con <i>f</i> = focal, <i>m₀</i> = relación del
objetivo, <i>e</i> = tubos en mm, <i>D</i> = dioptrías de las lentes de aproximación y <i>N</i> = diafragma ajustado:</p>
<div class="formula">m₁ = m₀ + {frac("e", "f")} &nbsp;&nbsp;&nbsp; aumento m = m₁ + {frac("ΣD", "1000")} · f · (1 + m₁)
<span class="lbl">diafragma efectivo = N · (1 + m₁) &nbsp;·&nbsp; NA equivalente = {frac("m", "2 · N · (1 + m₁)")}</span></div>
<div class="calc">Ejemplo: objetivo macro de 90 mm a 1:2 (m₀ = 0,5), f/8, sin tubos, lente de aproximación de +8 dioptrías
m₁ = 0,5 + 0 = 0,5
m  = 0,5 + 8 ÷ 1000 × 90 × (1 + 0,5) = 0,5 + 1,08 = <b>1,58×</b>
diafragma efectivo = 8 × 1,5 = <b>f/12</b>      NA equivalente = 1,58 ÷ (2 × 8 × 1,5) = <b>0,066</b>
con un sensor de 3,9 µm: 3,9 ÷ 1,58 = <b>2,47 µm por píxel</b> en la muestra</div>
<p>Como en el microscopio, un valor medido con una regla milimetrada (campo <span class="ui">µm por píxel en la muestra,
medidos</span>) tiene prioridad sobre el cálculo, que con las lentes de aproximación es solo una estimación. En macro la
profundidad de campo suele ser de decenas o cientos de µm: si un paso del carro resulta más largo que el paso
recomendado, la pestaña {ui('Ottica')} lo indica y sugiere el micropaso adecuado (capítulo 10.2).</p>

<h2>7.4 Varias fotos por posición</h2>
<p>Con <span class="ui">{ui('Scatti per posizione')}</span> mayor que 1 la cámara dispara varias veces en cada posición,
sin mover el motor entre una foto y otra: la espera contra las vibraciones solo se hace después del movimiento; entre
las fotos solo hay la pausa tras el disparo. El software de fusión las promedia: con 4 fotos el ruido se reduce a la
mitad. Los archivos se llaman <code>stack_0001_1</code>, <code>stack_0001_2</code>…; con una sola foto siguen siendo
<code>stack_0001</code>, <code>stack_0002</code>… El resumen muestra posiciones × fotos y la duración correcta.</p>

<h2>7.5 Los archivos de la pila</h2>
<p>En la carpeta de la pila, junto a las fotos, la app escribe dos archivos. Los reescribe después de cada foto, así que
son válidos aunque la secuencia se interrumpa. Las fotos nunca se modifican.</p>
<ul>
<li><code>sequence.json</code>: todos los datos para el <b>software de fusión</b>: posición de cada foto en pasos
  y en µm, hora, temperatura, guía, cámara, perfil óptico (microscopio o macro), filtro, iluminación y los conjuntos de
  calibración adecuados (7.6). El formato se describe en <code>docs/sequence-json.md</code> en GitHub.</li>
<li><code>sequence.txt</code>: un <b>resumen para leer</b>, en el idioma de la app. Por ejemplo:</li>
</ul>
<div class="calc long">{SEQ_TXT}</div>

<h2>7.6 Calibración: exposición, darks y flats</h2>
<p>La pestaña <b>{ui('Calibrazione')}</b> prepara lo que el software de fusión necesita para corregir las fotos: un tiempo
de exposición adecuado para la pila y los <b>fotogramas de calibración</b>. Los niveles se miden sobre los <b>RAW
reales</b>, sin conversión de color, con <i>fs-rawstat</i>, un pequeño programa incluido en la app y basado en LibRaw;
los píxeles quemados se detectan canal por canal. Con el simulador los niveles son solo una estimación.</p>
<h3>{ui('Esposizione dei light')}</h3>
{fig("calibrazione-esposizione", [
    f"<b>{ui('Misura su')}</b>: <i>{ui('Luci')}</i> (el percentil 99,5, es decir, las partes más claras) o <i>{ui('Media (livello medio)')}</i>.",
    "<b>Nivel objetivo</b> en % de la saturación del sensor, por ejemplo 85% sobre las luces.",
    f"<b>{ui('Calcola e imposta il tempo')}</b>: la app hace unas fotos de prueba, mide los RAW y ajusta el tiempo de exposición, prefiriendo los tiempos sin píxeles quemados. El ISO y el diafragma se mantienen.",
    "<b>Resultado</b>: tiempo elegido, nivel medido y píxeles quemados.",
], layout="side")}
<p>Lleva el enfocador a la mitad de la pila y enciende la iluminación como para la secuencia. La exposición se
calcula <b>una vez, antes de la pila</b>: cambiarla entre un plano y otro haría distinta la luminosidad de los
fotogramas.</p>
<h3>{ui('Frame di calibrazione')}</h3>
{fig("calibrazione-frame", [
    f"<b>{ui('Tipo')}</b>: <i>{ui('Dark')}</i> (tapa en el objetivo, mismos ISO y tiempo que los lights: ruido térmico y píxeles calientes), <i>{ui('Flat')}</i> (campo iluminado de forma uniforme, misma óptica y diafragma: viñeteo y polvo) o <i>{ui('Dark dei flat')}</i> (tapa, mismos ISO y tiempo que los flats).",
    f"<b>{ui('Fotogrammi')}</b> que hay que hacer, por ejemplo 16.",
    "<b>Nivel de los flats</b> en % de la saturación, por ejemplo 50%: el tiempo de exposición lo encuentra la app.",
    "<b>Progreso</b>: fotogramas hechos y nivel medido.",
    f"<b>{ui('▶ Scatta i frame').lstrip('▶ ')}</b> e <b>{ui('Interrompi')}</b>.",
], layout="side")}
<ul>
<li><b>Darks</b>: tapa en el objetivo y ocular del visor tapado, mismos ISO y tiempo de exposición (o pose B) que los
  lights, a ser posible a la misma temperatura.</li>
<li><b>Flats</b>: campo iluminado de forma uniforme (un portaobjetos vacío, un difusor), con el mismo perfil óptico y el
  mismo diafragma que la pila: corrigen el viñeteo y el polvo solo si la óptica es la misma.</li>
<li><b>Darks de los flats</b>: justo después de los flats, con la tapa: la app usa por sí sola el ISO y el tiempo de los
  flats más recientes.</li>
</ul>
<h3>Cómo los usa la fusión</h3>
<p>Focus Stack toma los frames y los indica en el <code>sequence.json</code> de la pila; la corrección la hace el
software de fusión (por ejemplo Focus Fusion) en cada fotograma, antes de alinearlo. El dark se <b>resta</b>: quita el
ruido térmico y los píxeles calientes. El flat <b>divide</b>: devuelve la luz que la viñeta y las sombras del polvo
habían quitado.</p>
{calib_diagram(CALIB_LABELS)}
{fig("calibrazione-esempio", [
    '<b>Flat normalizado</b> F, con el contraste aumentado: las esquinas reciben el 70% de la luz del centro y cada punto es una mota de polvo en el sensor.',
    '<b>Un fotograma de la pila</b> tal cual: el fondo se oscurece hacia las esquinas (64% del centro) y la misma mancha de polvo se ve en el fondo (recuadro ampliado 4×).',
    '<b>El mismo fotograma corregido</b>, (I − D) ÷ F, con la misma presentación: esquinas al 94% del centro y la mancha desaparece.',
], layout="full", caption='Un lápiz: Sony A6400 con el 70-350 mm a 350 mm, lente de aproximación +8 dioptrías, f/20, ISO 400, 1/20 s; 10 flats, 10 darks y 10 darks de los flats.')}
<h3>La {ui('Libreria di calibrazione').lower()}</h3>
{fig("calibrazione-libreria", [
    f"<b>Carpeta</b> de la biblioteca: <code>_calibrazione</code> dentro de la carpeta de las pilas. <span class='ui'>{ui('Apri nel Finder')}</span> la muestra.",
    "<b>Conjuntos adecuados</b> para una pila iniciada ahora, con la cámara y los ajustes actuales.",
    "<b>Tabla de los conjuntos</b>: tipo, fecha, cámara, ISO, tiempo, perfil óptico, fotogramas, nivel medio y temperatura. <span class='ui'>Eliminar</span> mueve el conjunto a la Papelera del Mac (recuperable desde el Finder). Con las casillas delante del tipo eliges varios (la de la cabecera los selecciona todos) y los eliminas juntos con <span class='ui'>Eliminar seleccionados</span>: por seguridad hay que escribir la palabra ELIMINAR.",
], layout="full")}
<p>Cada conjunto tiene su carpeta con los fotogramas y un <code>calibration.json</code> (formato en
<code>docs/calibration-json.md</code>). Al iniciar una pila, <code>sequence.json</code> indica los conjuntos adecuados más
recientes: para los darks, misma cámara, ISO y tiempo; para los flats, también el mismo perfil óptico. Los fotogramas no
se copian. Es la misma biblioteca que usa <b>Focus Fusion</b>, que guarda en ella, al lado, sus «masters».</p>
<p><b>Fotogramas distintos de los demás.</b> Un conjunto solo sirve si sus fotogramas se parecen: un flat tomado
después de que la luz se apagara o cambiara, o un dark sin la tapa, estropea la media. Durante la serie la app compara
cada fotograma con los ya tomados y, si es muy distinto (flats a más de ±10 % del nivel de los demás, darks más de un
punto más claros), lo avisa enseguida en la tarjeta y en el Registro, cuando aún puedes detenerte. En la tabla el
conjunto muestra ⚠ y cuántos junto al número de fotogramas (al pasar por encima, cuáles); los resúmenes también lo
avisan. Conviene repetir el conjunto: los fotogramas se quedan en la carpeta, marcados en <code>calibration.json</code>.</p>

<p>A la derecha, el <b>resumen</b> queda a la vista mientras trabajas en la pestaña.</p>
{fig("calibrazione-riepilogo", [
    f"<b>{ui('Per la prossima pila')}</b>: para darks, flats y darks de los flats, ✓ con la fecha del conjunto que se usaría, o <i>{ui('manca')}</i> en naranja. Si falta un conjunto, aparece también un punto naranja junto a <i>{ui('Libreria')}</i> en el índice.",
    "<b>Temperatura</b> actual de la sonda.",
    "Evolución de los <b>últimos 60 minutos</b>: compárala con la temperatura de los darks en la tabla.",
    f"<b>{ui('Sensore')}</b>: rango dinámico esperado al ISO ajustado, con el gráfico (ISO recomendados en verde, el actual en un círculo). Aparece después del análisis del sensor.",
], layout="side narrow")}

<h3>{ui('Analisi del sensore')}</h3>
<p>Una vez por cámara, <b>{ui('Calibrazione')} › {ui('Sensore')} › {ui('Analisi del sensore')}</b> mide cómo se comporta el
sensor a cada ISO: <b>ganancia</b> (cuántos electrones vale una unidad del RAW), <b>ruido de lectura</b>, <b>pozo
lleno</b> (cuánta luz recoge un píxel antes de saturarse) y <b>rango dinámico</b> en pasos. Para 19 ISO hacen falta unos
20 minutos.</p>
<ol>
<li><b>{ui('Prepara')}</b>: delante del objetivo, el difusor iluminado, como para los flats; cámara en RAW y enfoque manual.
  Elige el intervalo de ISO (de 100 a 6400 en tercios de paso es un buen comienzo) y cuántas tomas por ISO (2 bastan).</li>
<li><b>Flat</b>: para cada ISO la app encuentra el tiempo para un flat al 50% y dispara. Los ISO que la cámara rechaza aparecen tachados.</li>
<li><b>{ui('Tappo')}</b>: la app se detiene y pide poner la tapa; después pulsa <i>{ui('Ho messo il tappo: scatta i dark')}</i>.</li>
<li><b>Dark</b>: mismos ISO y tiempos, a oscuras.</li>
<li><b>{ui('Risultato')}</b>: dos gráficos, rango dinámico y ruido de lectura por ISO, y los ISO recomendados.</li>
</ol>
{fig("calibrazione-sensore", [
    'Los <b>pasos</b> del procedimiento: el que está en curso en azul, los terminados con una marca.',
    '<b>Gráficos</b> de rango dinámico y ruido de lectura por ISO: ISO recomendados en verde, el ISO ajustado en la cámara en un círculo, franja gris y línea discontinua para los ISO no fiables.',
    '<b>Recomendado</b>, <b>Recomendado con poca luz</b> y <b>Mejor evitar</b>, cada uno con el porqué.',
    '<b>Tabla</b>: para cada ISO el tiempo de los flats, el rango, el ruido, el pozo lleno y la ganancia.',
    '<b>Exportar CSV</b> guarda la tabla en Descargas; <b>Repetir el análisis</b> vuelve a empezar desde la preparación.',
], layout="full")}
<figure class="shot">{sensor_chart(SENSOR_LABELS)}<figcaption>Análisis del sensor de una Sony A6400: 19 ISO de 100 a 102400, 2 flats y 2 darks cada uno. ISO 400 en un círculo.</figcaption></figure>
<p>Cómo se lee, con el ejemplo de una Sony A6400. ISO 100 tiene el rango más amplio, 13,3 pasos, porque recoge más luz.
A ISO 400 el sensor pasa a una segunda ganancia y el ruido de lectura baja de 3 a 1,2 electrones: 12,9 pasos con tiempos
cuatro veces más cortos. Por encima el ruido ya no baja y cada vez que se duplica el ISO se pierde un paso: si falta luz,
conviene quedarse en 400 y aclarar después. Los ISO de 160 a 320 dan menos rango que ISO 400 con tiempos más largos: mejor
evitarlos. Por encima de 3200 la cámara ya filtra el ruido en el RAW, y esos valores se marcan como no fiables.</p>
<p>El resultado se guarda como <b>perfil del sensor</b> de la cámara, en <code>_calibrazione/_sensore</code>. El resumen de
la Calibración y el de la secuencia (al abrir sus detalles) muestran el rango dinámico esperado al ISO ajustado, con el punto en el gráfico; cada
pila escribe en su <code>sequence.json</code> los valores de su ISO (<code>"sensor"</code>), que Focus Fusion puede usar.
Los fotogramas del análisis están en la misma carpeta, fuera de la biblioteca de conjuntos, y nunca se eligen para una
pila. Repite el análisis si cambias de cámara o actualizas su firmware.</p>

<h2>7.7 Progreso en el smartphone</h2>
<p>Para seguir una pila larga lejos del Mac, en <span class="ui">{ui('Configurazione')} › {ui('Avanzamento da smartphone')}</span>
se activa una página <b>de solo lectura</b> en la red local.</p>
{fig("smartphone", [
    f'''<b>{ui("Mostra l'avanzamento sulla rete locale")}</b>: activa la página (desactivada hasta que la actives).''',
    "<b>Código QR</b>: escanéalo con la cámara del smartphone, que debe estar en la misma red Wi-Fi que el Mac.",
    f"<b>{ui('Nuovo link')}</b>: cambia el código del enlace; el anterior deja de funcionar.",
], layout="side")}
{fig("smartphone-pagina", [
    "Nombre de la pila, estado, fotos hechas, tiempo restante y hora prevista de fin.",
    f"<b>{ui('Avvisami con un suono a fine sequenza')}</b>: el smartphone suena (y en Android vibra) cuando la pila termina, se detiene por un error o se pone en pausa sola; mientras el sonido está activado, la pantalla permanece encendida.",
    f'''<b>{ui("Mostra l'ultimo scatto")} / {ui("Aggiorna l'ultimo scatto")}</b>: la última foto, a todo lo ancho.''',
    f"La última foto: separa dos dedos, arrastra o toca dos veces para ampliar. Al ampliar se carga un detalle en alta resolución; el zoom se mantiene al pasar a la foto siguiente, para comparar la misma zona. <span class='ui'>{ui('Adatta')}</span> vuelve a la imagen completa.",
], layout="side narrow", width="70%")}
<p>Desde la página <b>no se controla nada</b> y sin el código del enlace no se ve nada. La primera vez, macOS pregunta si
se permiten las conexiones entrantes: responde <b>Permitir</b>. Para el sonido, mantén la página abierta en primer plano:
mientras el sonido está activado, la página mantiene la pantalla encendida. Si el teléfono se bloquea de todos modos,
ajusta el bloqueo automático en <b>Nunca</b> mientras esperas (iPhone: Ajustes › Pantalla y brillo › Bloqueo
automático): un teléfono bloqueado suspende las páginas web y el sonido no llega.</p>
""")

# 8
add(f"""
<h1><span class="n">8</span>El visor</h1>
<p>Se abre con <span class="ui">{ui('Apri visualizzatore ↗')}</span> o con un clic en la última foto, en una ventana
aparte. Con dos monitores se abre sola a pantalla completa en el otro; se puede desactivar en
<span class="ui">{ui('Configurazione')} › {ui('Visualizzatore')}</span>. Muestra las fotos a resolución completa (también los RAW, convertidos
al vuelo) con zoom y desplazamiento, y la vista en vivo de la cámara.</p>
{fig("visualizzatore", [
    "<b>◀ ▶</b> foto anterior y siguiente (flechas <kbd>←</kbd> <kbd>→</kbd>).",
    "<b>Contador de la pila</b>: durante la secuencia, la última foto hecha sobre el total (por ejemplo 75/115, <i>en curso</i>), después <i>completada</i>; con las fotos de prueba, cuántas hay. Al lado, el nombre del archivo y, debajo, número de la foto, posición, temperatura y hora. Durante la pila, una línea azul a lo largo del borde superior de la ventana muestra el progreso.",
    f"<b>{ui('● Live')}</b> (<kbd>L</kbd>): la vista en vivo en la misma ventana, con zoom y desplazamiento.",
    "<b>Zoom</b> − y + (<kbd>−</kbd> <kbd>+</kbd>) y nivel de ampliación.",
    f"<b>{ui('Adatta')}</b> (<kbd>0</kbd>), <b>100%</b> (<kbd>1</kbd>: un píxel del sensor = un píxel de la pantalla), <b>{ui('Reset')}</b> (<kbd>R</kbd>).",
    f"<b>{ui('Segui ultimo')}</b> (<kbd>U</kbd>): muestra automáticamente cada foto nueva. Como los dos botones siguientes es un icono, resaltado cuando está activo; al abrir el visor está activo.",
    f"<b>{ui('Blocca vista')}</b> (<kbd>K</kbd>): al cambiar de foto mantiene el zoom y la posición, para comparar el enfoque en el mismo punto. Activo al abrir el visor.",
    "<b>Guías de composición</b> (<kbd>G</kbd>): cada clic alterna tercios, cruz en el centro, tercios y centro, ninguna. Líneas de 1 píxel que siguen el zoom y el desplazamiento; funcionan también en la vista en vivo.",
    f"<b>{ui('Ispettore')}</b> (<kbd>I</kbd>): histogramas, píxeles quemados y negros, valores bajo el puntero (mira más abajo). Abierto al abrir el visor.",
    "<b>Pantalla completa</b> (<kbd>F</kbd>).",
    "<b>?</b>: esta guía, en el capítulo del visor.",
    "<b>Miniaturas</b>: un clic abre la foto. <i>P</i> = foto de prueba, <i>C</i> = fotograma de calibración, <i>E</i> = foto para la exposición, <i>AF</i> = tomas del autoenfoque, los números son las fotos de la secuencia. La tira muestra solo la secuencia en curso o la última: se vacía al arrancar una secuencia, y la primera foto de prueba hecha después empieza una nueva. Los archivos se quedan en la carpeta.",
    f"<b>{ui('Svuota')}</b>, abajo a la derecha en la tira de miniaturas cuando hay fotos: empieza de cero. Las fotos salen del visor y la secuencia vuelve a {ui('Pronta')}; los archivos se quedan en la carpeta.",
], layout="full", anchors={n: "bb" if n in (7, 9, 11) else "b" for n in range(1, 12)})}
<p>Con el ratón: arrastra para desplazar la imagen, rueda (o pellizco en el trackpad) para el zoom centrado en el
puntero, doble clic para pasar de “ajustar” al 100% y viceversa. Por encima del 150% los píxeles se ven nítidos,
sin desenfoque.</p>
{fig("visualizzatore-live", [
    f"<b>{ui('■ Ferma live')}</b> vuelve a las fotos; ◀ ▶ o un clic en una miniatura también salen de la vista en vivo.",
    f"Estado de la vista en vivo: {ui('LIVE')}, {ui('SCATTO…')}, {ui('IN PAUSA')} durante la secuencia.",
], layout="full", anchors={1: "b"}, caption="La vista en vivo en el visor, aquí con el simulador enfocado (el tablero de ajedrez se ve nítido). Al 100% la vista en vivo tiene la resolución de la previsualización de la cámara, más baja que la de las fotos.")}
<h2>Autoenfoque en un punto</h2>
<p>El autoenfoque encuentra por sí solo la posición del enfocador en la que un detalle elegido está más nítido: un
marcador, un pelo, el borde de una estructura. Sirve, por ejemplo, para fijar con precisión el inicio o el fin de la
pila.</p>
<ol class="steps">
<li>Pulsa <span class="ui">⌖ Autoenfoque</span> (tecla <kbd>A</kbd>) y haz clic en el detalle: aparece un cuadrado azul,
  el área medida. Su lado se cambia con el control <b>Área</b> o con <kbd>[</kbd> <kbd>]</kbd>; otro clic mueve el
  cuadrado. Arrastrar y el zoom funcionan como siempre.</li>
<li>Elige el <b>modo</b> (Rápido, Preciso o Tomas reales) y comprueba el <b>recorrido</b>: la barra y la línea de debajo
  indican cuánto se moverá el enfocador y hasta dónde se acercará a la muestra. Luego pulsa <span class="ui">Iniciar</span>:
  el enfocador se mueve en la misma dirección que la pila y la curva de nitidez crece un punto cada vez.</li>
<li>Al final el enfocador vuelve a la posición más nítida: primero la sobrepasa del <b>sobrerrecorrido</b> y llega en
  el mismo sentido del barrido, para que la holgura de la mecánica no desplace el enfoque. Luego hace una <b>toma de
  verificación</b>, el rombo verde del gráfico. En la fila de abajo, <span class="ui">Usar el enfoque como</span>
  <span class="ui">inicio de la pila</span> o <span class="ui">fin de la pila</span> escribe la posición en la secuencia, en la ventana principal.</li>
</ol>
{fig("visualizzatore-autofocus", [
    "<b>⌖ Autoenfoque</b> (<kbd>A</kbd>): abre el panel; el clic en la imagen elige el área. <kbd>Esc</kbd> lo cierra.",
    "<b>Área medida</b>: discontinua mientras funciona el autoenfoque. Se queda en el mismo punto aunque cambies de toma o pases a la vista en vivo.",
    "<b>Modo</b>: <i>Rápido</i>, <i>Preciso</i> (predeterminado) o <i>Tomas reales</i>; debajo, lo que hará. <b>Búsqueda amplia</b> la activa para cuando toda la imagen está desenfocada. <b>Área</b>: lado del cuadrado en píxeles del sensor. La <b>barra del recorrido</b> va de − a + la excursión máxima alrededor de la partida: en claro el recorrido previsto, más oscuro el tramo ya recorrido, la línea es la posición actual.",
    "<b>Curva de nitidez</b>: un punto por medida, en horizontal la posición del enfocador; debajo, el paso. Las pasadas anteriores quedan más tenues bajo la que está en curso, y el gráfico se amplía en la zona de la pasada fina. Los cuadrados naranjas son las tomas reales de confirmación, la línea verde la posición elegida, el rombo verde la toma de verificación. Con el puntero sobre un punto se leen su posición y su nitidez (en % del máximo).",
    "<b>Estado</b>: pasada, toma en curso y posición, luego el resultado con la verificación y la anchura del pico, o el motivo por el que no encontró el enfoque.",
    "<b>Repetir</b> y, debajo, <b>Usar el enfoque como inicio / fin de la pila</b>, mientras el enfocador siga en la posición encontrada. <b>Repetir</b> vuelve a hacer el autoenfoque; un clic en otro punto mueve el área sin cerrar el panel. Durante la medida está <b>Detener</b>.",
], layout="full", anchors={6: "r"})}
<p>En cada toma la app mide lo nítidos que son los bordes dentro del área (el gradiente de la luminosidad, dividido por
la luminosidad media, para que la exposición no cuente). Lejos del enfoque la curva es plana; cerca, sube en un pico
estrecho. La app ajusta una curva a los puntos alrededor del máximo, así que la posición encontrada puede caer también
entre dos tomas. La pasada se detiene sola en cuanto se supera el pico; si el pico está más allá de la última toma
continúa, si está antes de la primera vuelve a empezar más atrás. Con los RAW mide la vista previa JPEG que hay dentro
del archivo: en las pruebas con pilas reales da el mismo enfoque que el RAW revelado.</p>
<div class="box tip"><span class="t">Elegir el área</span>Un detalle contrastado, todo a la misma profundidad. Si en el
área hay dos cosas a distinto enfoque (la pata y el cuerpo de un insecto) la curva tiene dos picos y la app lo indica
en naranja: reduce el área al detalle que te interesa. Sobre un fondo uniforme no hay nada que medir y el autoenfoque se
detiene con un mensaje.</div>
<h3>Los modos</h3>
<p>La <b>vista en vivo</b> es más rápida, pero su fotograma es pequeño y comprimido, y con poca luz tiene ruido; las
<b>tomas reales</b> miden la foto tal como estará en la pila, pero tardan unos segundos cada una. Los modos combinan
ambas cosas:</p>
<ul>
<li><b>Rápido</b>: solo vista en vivo, una pasada. Para buscar el enfoque y para las pruebas.</li>
<li><b>Preciso</b> (predeterminado): dos pasadas con la vista en vivo y luego <b>3 tomas reales de confirmación</b>
  alrededor del enfoque encontrado. El enfoque se recalcula con estas tomas (si la más nítida está en el borde se añaden
  una o dos) y la toma de verificación también es real. Es el modo para fijar el inicio o el fin de una pila.</li>
<li><b>Tomas reales</b>: todo el barrido con tomas reales. El más seguro y el más lento.</li>
</ul>
<p>Cada modo recuerda sus parámetros (paso, tomas por pasada, pasadas, imágenes, tomas de confirmación), que se cambian
en <span class="ui">Configuración › Autoenfoque</span>.</p>
<p>Con tomas reales (<i>Preciso</i> y <i>Tomas reales</i>) la vista en vivo se apaga antes de la primera toma,
como con una foto de prueba, y sigue apagada hasta el final del autoenfoque: la cámara no pasa una y otra vez de la
vista en vivo al disparo. Vuelve sola cuando mueves el enfocador. Si la cámara se desconecta durante una toma, la app
lo reintenta y la vuelve a conectar; si las desconexiones se repiten, revisa la alimentación: una batería falsa
(<i>dummy battery</i>) que no aguanta el pico del disparo desconecta la cámara del USB.</p>
<div class="box warn"><span class="t">Excursión máxima: protege el sujeto</span>El autoenfoque nunca se aleja de la
posición de partida más que la <b>excursión máxima</b> (± pasos, en la barra del recorrido). Si la pasada tuviera que
alargarse más allá, porque el enfoque está más lejos de lo previsto, se detiene y lo indica en lugar de seguir hacia la
muestra. El valor calculado cubre el recorrido previsto con un margen; redúcelo si la muestra está cerca del
objetivo.</div>
<div class="box warn"><span class="t">Verificación baja: la holgura</span>Si la toma de verificación es mucho menos nítida
que el máximo de la curva (por debajo del 80 %), la app lo indica en naranja: normalmente la holgura de la mecánica es
mayor que el sobrerrecorrido. Auméntalo en <span class="ui">Configuración › Autoenfoque</span>; al principio vale la
compensación de holgura de la secuencia, pero al menos una anchura del pico.</div>
<p>Todos los valores están en <span class="ui">Configuración › Autoenfoque</span>, capítulo 12.</p>
<h2>{ui('Ispettore')}</h2>
<p>El panel <span class="ui">{ui('Ispettore')}</span> (tecla <kbd>I</kbd>) comprueba la exposición de una foto con las
mismas reglas que Focus Fusion. Es de solo lectura: no modifica las fotos. Funciona también sobre la vista en vivo,
actualizado cada medio segundo.</p>
{fig("ispettore", [
    f'''<b>Píxeles quemados y negros</b>: porcentaje y reglas usadas. <span class='ui'>{ui("Evidenzia sull'immagine")}</span> marca en rojo los quemados y en azul los negros; los dos botones los muestran u ocultan por separado.''',
    "<b>Histogramas</b> del rojo, el verde, el azul y la luminancia. Con el puntero sobre un nivel se lee cuántos píxeles hay.",
    "<b>Bajo el puntero</b>: los valores R, G, B y la luminancia del píxel sobre el que está el ratón.",
], layout="full")}
<p>Con las fotos RAW el {ui('Ispettore')} trabaja sobre la previsualización convertida; para el nivel exacto del sensor usa
<span class="ui">{ui('Esposizione dei light')}</span> (7.6), que mide los RAW reales.</p>
""")

# 9
add(f"""
<h1><span class="n">9</span>Límites de seguridad</h1>
<p class="lead">Los límites evitan que el objetivo toque el portaobjetos o que la mecánica llegue al tope. Hay que
establecerlos antes que nada, con calma.</p>
<p>La pestaña <b>{ui('Configurazione')}</b> es una página única, dividida en los grupos {ui('Focheggiatore')},
{ui('App')} y {ui('Sistema')}. Las pestañas {ui('Ottica')} y {ui('Calibrazione')} están hechas igual.</p>
{fig("configurazione", [
    f"<b>{ui('Cerca')}</b>: escribe parte de un nombre (por ejemplo «holgura») y solo quedan las filas que lo contienen.",
    "<b>Índice</b>: un clic lleva a la sección; la entrada resaltada sigue el desplazamiento. Un punto señala cambios sin guardar o una actualización disponible.",
    "<b>Título de la sección</b>; el <b>?</b> abre la guía en ese punto.",
    f"<b>{ui('Dettagli')}</b>: las explicaciones más largas, cerradas al principio.",
    f"<b>{ui('Riepilogo')}</b>, siempre a la vista: resolución, recorrido útil, firmware, versión de la app y progreso en el smartphone.",
], layout="full")}
<p>Casi todo se guarda en cuanto cambias un valor: los ajustes del motor van directamente al firmware, la mecánica y
las demás opciones a los ajustes de la app. La excepción son los límites, aquí abajo.</p>
{fig("fine-corsa", [
    f"<b>{ui('Fine corsa inferiore')}</b> en pasos; <span class='ui'>⌖ {ui('Usa posizione attuale')}</span> lo toma de la posición del enfocador.",
    f"<b>{ui('Fine corsa superiore')}</b>. Vacío = el máximo del firmware.",
    f"<b>Hacia la muestra</b>: si al acercarse a la muestra los pasos disminuyen o aumentan. Sirve para etiquetar correctamente {ui('Avvicina')}/{ui('Allontana')}.",
    f"<b>{ui('Salva fine corsa')}</b>, en la barra <i>{ui('Modifiche non salvate')}</i> que aparece cuando cambias un valor; <b>{ui('Annulla')}</b> vuelve a los valores guardados. Es la única parte de la Configuración que no se guarda sola.",
    f"<b>{ui('Imposta qui lo zero')}</b>: la posición actual pasa a ser 0; los límites y la secuencia se desplazan en consecuencia.",
    f"<b>{ui('Scrivi il massimo nel firmware')}</b>: el límite superior pasa a ser el límite del firmware.",
], layout="full")}
<h2>Qué protege qué</h2>
<ul>
<li><b>Movimientos ordenados por la app</b> (ir a, {ui('Allontana')}/{ui('Avvicina')}, secuencia, compensación de
  holgura): la app los comprueba <i>antes</i> de mover el motor. El movimiento continuo se detiene en el límite; una
  secuencia que saldría de los límites no se inicia.</li>
<li><b>Botones físicos</b>: la app lee la posición cada 0,2–0,5 s; si sale de los límites, envía STOP y muestra la
  alarma. Sin embargo, entre una lectura y la siguiente el motor puede superar el límite en unas decenas de pasos.</li>
</ul>
<h2>Protección recomendada: límites en el firmware</h2>
<p>El firmware aplica sus límites también a los botones físicos: nunca baja de 0 ni sube por encima de su
máximo.</p>
<ol class="steps">
<li>Con un objetivo en seco y sin portaobjetos, o con mucha prudencia, lleva la platina a la posición <b>más cercana
  a la muestra que siga siendo segura</b> y pulsa <span class="ui">{ui('Imposta qui lo zero')}</span>.</li>
<li>Lleva la platina a la posición útil más alejada, pulsa <span class="ui">⌖ {ui('Usa posizione attuale')}</span>
  en el límite superior y luego <span class="ui">{ui('Salva fine corsa')}</span> y <span class="ui">{ui('Scrivi il massimo nel firmware')}</span>.</li>
<li>Comprueba una vez, a mano y despacio con los botones físicos, que el enfocador se detiene de verdad en 0 y en
  el máximo.</li>
</ol>
<div class="box danger"><span class="t">Atención</span>El límite “hacia la muestra” depende del objetivo y del grosor
del portaobjetos: con un objetivo de distancia de trabajo corta (40×, 100×) el margen es de pocas décimas de
milímetro. Vuelve a comprobar los límites cada vez que cambies de objetivo y después de cambiar el
<b>micropaso</b>, que cambia la escala de las posiciones.</div>
""")

# 10 — mecánica
add(f"""
<h1><span class="n">10</span>Configuración mecánica: los cálculos</h1>
<p class="lead">La app razona en <b>pasos del motor</b>. Para mostrarte desplazamientos, recorridos y pasos de la
secuencia en <b>micrómetros</b>, y para calcular el paso adecuado a partir de la profundidad de campo, necesita saber
cuántos micrómetros vale un paso. Este número se llama <b>resolución</b> (µm/paso) y depende de cómo esté acoplado el
motor al enfoque fino.</p>
{fig("meccanica", [
    f"<b>Modo</b>: <i>{ui('Calcola dalla meccanica')}</i> (a partir de los datos de abajo) o <i>{ui('Inserisci µm/passo')}</i> (un valor medido).",
    f"<b>{ui('Passi motore per giro')}</b>: 200 para un motor de 1,8°, 400 para uno de 0,9°.",
    f"<b>{ui('Microstep')}</b>: se lee del firmware, aquí no se modifica (mira Motor).",
    f"<b>{ui('Rapporto di riduzione')}</b>: cuántas vueltas da el motor por cada vuelta del mando.",
    f"<b>{ui('Corsa per giro manopola (µm)')}</b>: cuántos µm se desplaza la platina en cada vuelta del mando del enfoque fino.",
    "<b>Resultado</b>: µm por paso, pasos por µm, µm cada 1000 pasos. Los cambios se guardan solos.",
])}
<h2>10.1 La cadena de transmisión</h2>
<p>Del motor a la platina el movimiento pasa por varias etapas, y cada una multiplica o divide:</p>
{diagram(DIAGRAM_LABELS)}
<div class="formula">
  resolución (µm/paso) = {frac("recorrido por vuelta del mando (µm)", "pasos por vuelta × micropaso × relación de reducción")}
  <span class="lbl">Es exactamente el cálculo que hace la app en “{ui('Calcola dalla meccanica')}”.</span>
</div>
<h2>10.2 Los cuatro números, uno a uno</h2>
<h3>Pasos del motor por vuelta</h3>
<p>Se obtienen del ángulo de paso indicado en la etiqueta o en la hoja de datos del motor:</p>
<div class="formula">pasos por vuelta = {frac("360°", "ángulo de paso")}
<span class="lbl">1,8° → 200 pasos · 0,9° → 400 pasos · 7,5° → 48 pasos</span></div>
<p>El NEMA 14 OMC 14HM11-0404S del enfocador myFocuserPro2 es de 0,9°: <b>400</b>. El NEMA 17
17HS13-0404S-PG27 con reductor es de 1,8°: <b>200</b>, y el reductor entra en la relación (más abajo), no aquí.</p>
<h3>Micropaso</h3>
<p>El driver puede dividir cada paso en 2, 4, 8, 16 o 32 micropasos. Con micropaso 1/8 una vuelta del motor requiere
8 veces más pasos y la resolución se vuelve 8 veces más fina (pero el par por micropaso baja y la velocidad máxima en
µm/s se reduce 8 veces).</p>
<ul>
<li><b>myFocuserPro2</b>: el micropaso lo establece el firmware y se cambia en {ui('Configurazione')} › Motor. La app
  lo lee y lo usa sola en el cálculo.</li>
<li><b>Ardufocus</b>: el micropaso está fijado en la placa (puentes o conexiones del driver) y el firmware no lo
  controla. Ajusta en {ui('Configurazione')} › Motor <b>el mismo valor que la placa</b>; si no, el cálculo se
  equivoca en ese mismo factor. Si no sabes cuál es, mídelo (10.4).</li>
</ul>
<h3>Relación de reducción</h3>
<p>Es el número de vueltas del motor por <b>una</b> vuelta del mando. Se multiplican entre sí todas las etapas:</p>
<div class="formula">relación = reductor × {frac("dientes de la polea del mando", "dientes de la polea del motor")}
<span class="lbl">con ruedas de fricción o juntas tóricas: en lugar de los dientes, los diámetros</span></div>
<ul>
<li><b>Acoplamiento directo</b> (motor en el eje del mando, sin reductor): relación 1.</li>
<li><b>Correa dentada</b> de una polea GT2 de 20 dientes en el motor a una de 60 en el mando: 60 ÷ 20 = <b>3</b>.</li>
<li><b>Reductor planetario</b>: la relación indicada en el motor. El PG27 del 17HS13 es 26 103/121 = 26 + 103 ÷ 121
  = <b>26,851</b> (no exactamente 27: usa el valor preciso). Con acoplamiento directo la relación es 26,851; con una
  correa de 20 → 40 dientes pasa a ser 26,851 × 2 = 53,70.</li>
</ul>
<h3>Recorrido por vuelta del mando</h3>
<p>Cuánto se desplaza la platina (o el tubo, en los microscopios que mueven el objetivo) en cada vuelta del mando que
gira el motor, normalmente el del <b>enfoque fino</b>. Muchos microscopios tienen 100 µm por vuelta, algunos 200 µm
u otros valores. La forma más segura de saberlo es contar las divisiones del mando:</p>
<div class="formula">recorrido por vuelta = número de divisiones del mando × µm por división
<span class="lbl">ejemplo: 100 divisiones de 1 µm = 100 µm por vuelta · 50 divisiones de 2 µm = 100 µm por vuelta</span></div>
<p>El valor por división suele estar grabado en el mando o en el cuerpo del microscopio (“1 µm”, “2 µm”) o figura en
el manual. Si el motor mueve el <b>enfoque grueso</b> en lugar del fino, el recorrido por vuelta es de varios
milímetros: la resolución es mucho más basta y hay que comprobarla con cuidado.</p>

<h2>10.3 Ejemplos resueltos</h2>
<h3>Ejemplo A: myFocuserPro2 con NEMA 14 y correa</h3>
<div class="calc">motor 0,9°               → pasos por vuelta = 360 ÷ 0,9 = 400
micropaso                → 1 (paso completo)
poleas 20 → 60 dientes   → relación = 60 ÷ 20 = 3
enfoque fino             → 100 µm por vuelta

pasos por vuelta del mando = 400 × 1 × 3 = 1.200
resolución = 100 ÷ 1.200 = <b>{num(UA, 4)} µm/paso</b>   (12 pasos = 1 µm; 1.000 pasos = {num(UA * 1000, 1)} µm)</div>
<p>Es la configuración de las capturas de esta guía. Con micropaso 1/8 el mismo enfocador daría
100 ÷ (400 × 8 × 3) = <b>{num(um_step(100, 400, 8, 3), 4)} µm/paso</b>.</p>
<h3>Ejemplo B: Ardufocus con NEMA 17 y reductor PG27</h3>
<div class="calc">motor 1,8°               → pasos por vuelta = 200
micropaso (en la placa)  → 1
reductor 26 103/121      → 26,851, acoplado directamente al mando
enfoque fino             → 100 µm por vuelta

pasos por vuelta del mando = 200 × 1 × 26,851 = {num(200 * GEAR17, 0)}
resolución = 100 ÷ {num(200 * GEAR17, 0)} = <b>{num(UB, 4)} µm/paso</b>   (1 µm = {num(1 / UB, 1)} pasos)</div>
<p>El reductor hace la resolución unas 4,5 veces más fina que en el ejemplo A y da mucho más par, pero hacen falta
muchos más pasos para el mismo desplazamiento: por eso la app admite tamaños de paso de hasta 100.000 pasos
(capítulo 12).</p>

<h2>10.4 Comprobar con una medición</h2>
<p>El cálculo es válido si todos los datos son correctos y nada patina (una correa floja, una polea que gira sobre
su eje). Siempre conviene comprobarlo, y es imprescindible si no conoces alguno de los números.</p>
<h3>Con las divisiones del enfoque fino</h3>
<ol class="steps">
<li>Llega siempre desde la misma dirección (para descartar la holgura): mueve unos cientos de pasos en un sentido y
  luego anota la división del mando alineada con la marca de referencia.</li>
<li>Con <span class="ui">Ir a la posición</span> mueve un número grande de pasos <b>N</b>, en el mismo sentido, de
  forma que el mando dé al menos media vuelta (ejemplo A: N = 1.000; ejemplo B: N = 5.000).</li>
<li>Cuenta las divisiones recorridas, <b>T</b>, y multiplica por los µm por división.</li>
</ol>
<div class="formula">resolución medida = {frac("T × µm por división", "N")}</div>
<div class="calc">Ejemplo A: N = 1.000 pasos, el mando avanza 83 divisiones de 1 µm
resolución = 83 × 1 ÷ 1.000 = <b>0,083 µm/paso</b>   (el cálculo daba {num(UA, 4)}: cuadra)</div>
<h3>Con un comparador</h3>
<p>Un comparador de reloj de centésimas o milésimas de milímetro apoyado en la platina mide directamente el
desplazamiento. Mueve N pasos (siempre desde la misma dirección) y divide el desplazamiento en µm entre N. Cuanto
mayor sea N, más precisa será la medición.</p>
<h3>Si la medición no cuadra</h3>
<ul>
<li>Diferencia de un factor 2, 4, 8, 16: el <b>micropaso</b> no es el que crees (típico del Ardufocus).</li>
<li>Diferencia de un factor 2 exacto: un motor de 0,9° confundido con uno de 1,8° o viceversa.</li>
<li>Diferencia irregular, que cambia de una medición a otra: algo <b>patina</b> (correa, prisionero de la polea) o el
  motor <b>pierde pasos</b> (velocidad demasiado alta, corriente demasiado baja).</li>
<li>Si los datos de la mecánica son inciertos pero la medición es repetible, elige
  <span class="ui">{ui('Inserisci µm/passo')}</span> e introduce el valor medido.</li>
</ul>
{fig("meccanica-manuale", [
    f"<b>{ui('Inserisci µm/passo')}</b>: para usar un valor medido.",
    f"<b>{ui('µm per passo')}</b> medidos.",
    "El resultado se actualiza mientras escribes.",
], layout="side narrow")}

<h2>10.5 Otros cálculos útiles</h2>
<h3>Recorrido útil en milímetros</h3>
<div class="calc">recorrido (µm) = (límite superior − límite inferior) × resolución
ejemplo A: (45.000 − 2.000) × {num(UA, 4)} = <b>{num(43000 * UA, 0)} µm ≈ {num(43000 * UA / 1000, 2)} mm</b></div>
<h3>Velocidad en µm por segundo</h3>
<div class="calc">velocidad (µm/s) = pasos por segundo × resolución
ejemplo A, firmware a 400 pasos/s:   400 × {num(UA, 4)} ≈ <b>{num(400 * UA, 0)} µm/s</b>
ejemplo B, firmware a 2.000 pasos/s: 2.000 × {num(UB, 4)} ≈ <b>{num(2000 * UB, 0)} µm/s</b></div>
<p>Sirve para saber cuánto tarda un desplazamiento largo: 1 mm en el ejemplo A tarda unos
{num(1000 / (400 * UA), 0)} segundos.</p>
<h3>La holgura (backlash) en pasos</h3>
<p>Cuando el motor invierte el sentido, durante unos pasos el mando no se mueve: es la <b>holgura</b> de la
transmisión (correa, dientes, reductor, rosca del enfoque fino). Se compensa en pasos, así que conviene medirla en
pasos:</p>
<ol class="steps">
<li>Abre la vista en vivo en el visor al 100% o más, sobre un detalle pequeño y bien contrastado.</li>
<li>Mueve unos cientos de pasos en un sentido y luego invierte con un tamaño de paso de 1 o 10.</li>
<li>Cuenta los pasos tras la inversión hasta que la imagen empiece a moverse: esa es la holgura. Repite unas
  cuantas veces y toma el valor más alto, con un pequeño margen.</li>
</ol>
<p>La holgura angular declarada da un orden de magnitud. El reductor PG27 declara como máximo 1° de holgura en la
salida, es decir, 1/360 de vuelta del mando:</p>
<div class="calc">holgura en pasos = (1° ÷ 360°) × pasos por vuelta del mando = {num(200 * GEAR17, 0)} ÷ 360 ≈ <b>{num(200 * GEAR17 / 360, 0)} pasos</b>
holgura en µm    = (1° ÷ 360°) × 100 µm ≈ <b>{num(100 / 360, 2)} µm</b></div>
<p>A esta se suman la holgura de la correa y la del enfoque fino: la medición con la vista en vivo sigue siendo el
dato fiable. El valor va luego en <b>uno solo</b> de dos sitios: la <b>compensación de la secuencia</b> (capítulo 7)
o la <b>holgura IN/OUT del firmware</b> (capítulo 12, como máximo 255 pasos), no en ambos.</p>
<h3>Qué fina tiene que ser la resolución</h3>
<p>El paso de la secuencia (capítulo 11) debería equivaler al menos a una decena de pasos del motor, para que el
redondeo a pasos enteros importe poco. Con el ejemplo A y un objetivo 60× el paso recomendado es de unos 7 pasos: se
puede trabajar, pero para objetivos muy potentes conviene una resolución más fina (micropaso o mayor reducción).</p>
""")

# 11 — paso de la secuencia
add(f"""
<h1><span class="n">11</span>Elegir el paso de la secuencia</h1>
<p class="lead">Cada foto es nítida solo en una capa fina de la muestra, la <b>profundidad de campo</b>. Para tenerlo
todo enfocado después del apilado, entre una foto y la siguiente el enfoque no debe moverse más que esa capa, con
un poco de solapamiento.</p>
<p>El cálculo está al final de la pestaña <b>{ui('Ottica')}</b>, en el grupo <b>{ui('Strumenti')}</b> (el resultado aparece también en el resumen de la derecha), y usa la apertura numérica, el aumento sobre el sensor
(objetivo × cambiador intermedio × adaptador) y el píxel del sensor del perfil abierto (capítulo 7.2).</p>
{fig("profondita", [
    "<b>Solapamiento</b> entre una capa nítida y la siguiente; un 20–30% es un buen valor.",
    "<b>Resultado</b>: profundidad de campo, paso recomendado en µm y en pasos del motor.",
    f"<b>{ui('Usa come passo della sequenza')}</b>: copia el valor en pasos en el campo Paso de la secuencia.",
], layout="side narrow")}
<h2>11.1 La fórmula</h2>
<p>La app usa la fórmula de Berek, la más empleada en microscopía:</p>
<div class="formula">profundidad de campo (µm) = {frac("λ · n", "NA²")} + {frac("n · e", "M · NA")}
<span class="lbl">λ = longitud de onda = 0,55 µm (luz verde) · n = índice del medio entre objetivo y portaobjetos = 1 (aire) ·
e = tamaño del píxel del sensor (µm) · M = aumento sobre el sensor</span></div>
<p>El primer término es el límite de la óptica (difracción); el segundo, el del sensor. Después:</p>
<div class="formula">paso (µm) = profundidad de campo × (1 − solapamiento)<br>paso (pasos de motor) = {frac("paso (µm)", "resolución (µm/paso)")}</div>
<h3>Ejemplo resuelto: objetivo 10×/0,25, Nikon D5600, adaptador 1×</h3>
<div class="calc">primer término       = 0,55 × 1 ÷ 0,25²       = 0,55 ÷ 0,0625 = 8,80 µm
segundo término      = 1 × 3,9 ÷ (10 × 0,25)  = 3,9 ÷ 2,5     = 1,56 µm
profundidad de campo = 8,80 + 1,56 = <b>10,36 µm</b>
paso con un 30% de solapamiento = 10,36 × 0,70 = <b>7,25 µm</b>
en pasos, ejemplo A: 7,25 ÷ {num(UA, 4)} = 87,0 → <b>87 pasos</b>
          ejemplo B: 7,25 ÷ {num(UB, 4)} → <b>{max(1, round(dof(.25, 10, 3.9) * .7 / UB))} pasos</b></div>
<h3>Valores típicos (D5600, adaptador 1×, solapamiento 30%)</h3>
{table(["Objetivo", "Profundidad de campo (µm)", "Paso (µm)", "Pasos, ejemplo A", "Pasos, ejemplo B"], dof_rows, right=(1, 2, 3, 4))}
<p style="font-size:9pt;color:#5a6b80">Ejemplo A = {num(UA, 4)} µm/paso; ejemplo B = {num(UB, 4)} µm/paso (apartado 10.3). Nota: {dof_note}</p>
<div class="box tip"><span class="t">Optovar, adaptadores y oculares de proyección</span>En el perfil óptico
(capítulo 7.2) indica el factor del cambiador de aumento intermedio y el del adaptador o del ocular de proyección: la app
los multiplica por el aumento del objetivo. Por ejemplo, 10× con Optovar 1,6× y adaptador 0,63× = 10 × 1,6 × 0,63
≈ 10,1× sobre el sensor. Solo cambia el segundo término de la fórmula, que pesa más con los objetivos de poco aumento.
Para una escala exacta en µm, mide los µm por píxel con un micrómetro objetivo: los factores grabados en los accesorios
son nominales.</div>

<h2>11.2 Inicio, fin y número de fotos</h2>
<ol class="steps">
<li>Activa la vista en vivo (mejor en el visor, ampliada) y lleva el enfoque <b>justo por encima</b> de la parte más
  alta del sujeto que quieres nítida: pulsa <span class="ui">⌖ {ui('qui')}</span> junto a <b>{ui('Inizio')}</b>.</li>
<li>Baja hasta <b>justo por debajo</b> de la parte más baja y pulsa <span class="ui">⌖ {ui('qui')}</span> junto a <b>{ui('Fine')}</b>.</li>
<li>Escribe el paso (o usa <span class="ui">{ui('Usa come passo della sequenza')}</span>): la app calcula el número de fotos.</li>
</ol>
<div class="formula">número de fotos = {frac("|fin − inicio|", "paso")} + 1
<span class="lbl">redondeado hacia abajo, más una foto final exacta en el fin si la división no es entera</span></div>
<div class="calc">ejemplo: inicio 24.000, fin 26.000, paso 87
2.000 ÷ 87 = 22,99 → 22 + 1 = 23, más la foto final en 26.000 = <b>24 fotos</b>
recorrido = 2.000 × {num(UA, 4)} = <b>{num(2000 * UA, 1)} µm</b></div>
<p>A la inversa, si escribes el <b>número de fotos</b>, la app recalcula el paso: paso = recorrido ÷ (fotos − 1),
redondeado a un paso entero.</p>
<h2>11.3 Duración estimada</h2>
<p>Para cada foto la app suma:</p>
<div class="formula">espera + pausa + retardo del espejo + exposición + 1,5 s + {frac("paso", "400")} s</div>
<p>donde «espera» es la espera tras el movimiento, «pausa» la pausa tras el disparo, «exposición» el tiempo de
exposición, 1,5 s una estimación del tiempo de disparo y transferencia, y paso ÷ 400 el tiempo de desplazamiento. Con
el ejemplo (1,5 s + 0,5 s + 0 + 1/60 s + 1,5 s + 0,22 s ≈ 3,7 s por foto × 24 fotos) la duración es de
<b>un minuto y medio</b> aproximadamente, como en la captura del capítulo 7. Durante la secuencia la estimación se
actualiza con los tiempos reales.</p>
<div class="box warn"><span class="t">La espera tras el movimiento importa</span>Un microscopio sigue vibrando un rato
después de cada desplazamiento. Si las fotos salen movidas o “dobles”, aumenta la espera (2–3 s) y, en las réflex,
el retardo del espejo, antes de buscar otras causas.</div>
""")

# 12
add(f"""
<h1><span class="n">12</span>Motor, controles manuales, autoenfoque, actualizaciones, temperatura</h1>
<h2>{ui('Motore (firmware)')}</h2>
{fig("motore", [
    f"<b>{ui('Microstep')}</b>: {ui('passo intero')}, 1/2 … 1/32 (mira 10.2). Cambiarlo cambia la escala de las posiciones: después, vuelve a comprobar los límites.",
    f"<b>{ui('Velocità')}</b> del firmware: lenta, media, rápida. Con el myFocuserPro2 y el firmware build 7 la velocidad máxima de los movimientos es de 80, 200 y 400 pasos por segundo; cada movimiento arranca a 40 pasos por segundo y acelera.",
    f"<b>{ui('Alimentazione bobine motore')}</b>: con <b>{ui('Sempre quando connesso')}</b> el motor mantiene la posición parado, pero se calienta. <b>{ui(COIL_HOLD)}</b> (desactivada al principio; solo con la primera activada): si la dejas desactivada, las bobinas se apagan al desconectar el enfocador o cerrar la app, y el motor no se calienta durante horas; el primer movimiento las vuelve a encender. Actívala si el peso puede hacer bajar una corredera vertical. Requiere el firmware build 8.",
    f"<b>{ui('Alimentale comunque durante la sequenza')}</b> (aparece con las bobinas apagadas; activada por defecto): las bobinas se encienden al iniciar la pila y se vuelven a apagar después de la vuelta al inicio.",
    f"<b>{ui('Inverti verso di rotazione')}</b>.",
    "<b>Compensar holgura IN / OUT</b>: en cada inversión hacia posiciones más bajas (IN) o más altas (OUT) el firmware da unos pasos de más sin contarlos, también con los botones físicos.",
    "<b>Holgura IN / OUT</b> en pasos, de 0 a 255 (mira 10.5).",
    f"<b>{ui('Rileggi')}</b> los valores del firmware.",
])}
<div class="box warn"><span class="t">Bobinas apagadas: el carro puede no avanzar</span>Sin corriente con el motor parado,
en cada parada la carga puede hacer retroceder el carro, y con el micropaso el motor vuelve además al paso completo más
cercano: el contador avanza pero el carro no. Por eso, con las bobinas apagadas, la app las enciende durante la secuencia
(número 4) y un aviso naranja lo recuerda si quitas la opción. Si el motor se calienta demasiado, baja la corriente en el
driver en lugar de apagar las bobinas.</div>
<h2>{ui('Comandi manuali')}</h2>
{fig("comandi-manuali", [
    f"<b>Tamaños de paso</b> de los botones {ui('Allontana')}/{ui('Avvicina')}: en potencias de diez hasta 1.000, 10.000 o 100.000 pasos. Con un reductor hacen falta tamaños grandes.",
    f"<b>{ui('Tieni premuto per muovere senza fermarti')}</b>: al soltar, el motor frena y se detiene; en cualquier caso se detiene en el límite y, si la página deja de responder, al cabo de un segundo aproximadamente.",
    f"<b>{ui('Tratto massimo per comando (passi)').replace(' (pasos)', '')}</b>: si mantienes pulsado, el motor nunca va más de un tramo (500 pasos por defecto) más allá de la última confirmación de la página de que el botón sigue pulsado.",
], layout="side")}
<p>El movimiento continuo funciona así por seguridad: si la comunicación se interrumpe (red, app bloqueada, cable), el
motor recorre como máximo un tramo. Con el <b>firmware build 5</b>, con cada confirmación el destino se desplaza un tramo
más adelante y el motor no se detiene nunca; con firmware más antiguo avanza un tramo cada vez, con una breve parada entre
un tramo y otro (los tramos cortos son más seguros, pero van más a saltos). Desde la <b>build 4</b> hay una protección
más: durante el movimiento continuo el enfocador se detiene por sí solo si durante 1,5 s deja de recibir órdenes del Mac. En cambio, <span class="ui">{ui('Vai')}</span>,
los botones con un solo clic y la secuencia siempre llegan a su destino, aunque el movimiento dure muchos segundos.</p>
<h2>Autoenfoque</h2>
<p>Los ajustes del autoenfoque en un punto (capítulo 8): primero el modo y sus parámetros, luego los comunes a todos los
modos. Los campos vacíos usan el valor predeterminado, escrito en gris en el campo; pasos y tomas se calculan a partir
de la <b>anchura del pico</b>, es decir, el intervalo de pasos en el que la nitidez se mantiene por encima de la mitad
del máximo.</p>
{fig("autofocus-config", [
    "<b>Modo</b> que usa el visor, con el resumen de lo que hace. También se elige en el panel.",
    "<b>Parámetros del modo</b>: imágenes (vista en vivo o tomas reales), paso y tomas de la pasada fina, pasadas. Vacío = predeterminado del modo o calculado a partir de la anchura del pico. <b>Restablecer el modo</b> vuelve a los valores iniciales.",
    "<b>Confirmación con tomas reales</b> (solo con la vista en vivo): cuántas tomas reales alrededor del enfoque encontrado; 0 = sin confirmación.",
    "<b>Búsqueda amplia</b> si toda la imagen está desenfocada, con su amplitud (± pasos) y su paso, una anchura del pico: unas pocas tomas muy espaciadas.",
    "<b>Excursión máxima ±</b> desde la posición de partida: más allá, el autoenfoque se detiene. Debajo, espera tras el movimiento y <b>sobrerrecorrido para la holgura</b>.",
    "<b>Anchura del pico</b> usada para los cálculos y de dónde viene. <b>Olvidar la medida</b> vuelve a la estimación.",
], layout="side", anchors={2: "r", 4: "r"})}
<p>La primera vez la anchura del pico se estima a partir de la profundidad de campo del perfil óptico elegido en la
secuencia y de la mecánica (µm por paso); sin perfil, a partir del recorrido entre los límites. Tras cada autoenfoque
logrado la app guarda la anchura medida para ese perfil y la usa en adelante. La primera estimación es aproximada: si
el pico es más ancho de lo previsto la pasada se alarga sola, si es más estrecho repite la medida con un paso más fino.
El <b>sobrerrecorrido para la holgura</b> es cuánto sobrepasa el enfocador una posición antes de volver a ella: debe
superar la holgura de la mecánica. <span class="ui">Restablecer valores calculados</span> vacía los campos comunes
escritos a mano. Si la búsqueda amplia está desactivada y el enfoque está lejos, el autoenfoque se detiene y propone
activarla.</p>
<h2>{ui('Aggiornamenti')}</h2>
{fig("aggiornamenti", [
    "Versión de la <b>app</b> y resultado de la última comprobación.",
    "Versión del <b>firmware</b> del enfocador.",
    f"<b>{ui('Aggiorna firmware')}</b>: unos 20 segundos; los ajustes del enfocador se conservan. No desconectes el cable; si algo sale mal, basta con repetirlo. La build 5 hace continuo el movimiento con el botón mantenido pulsado; desde la build 4 está la parada automática si el Mac deja de comunicarse. La build 7 arranca los movimientos más suavemente (40 pasos por segundo) y reduce a la mitad la velocidad lenta del myFocuserPro2.",
    f"<b>{ui('Controlla ora')}</b> si hay actualizaciones de la app.",
], layout="side")}
<p>La app elige sola el firmware adecuado para la placa (myFocuserPro2 o Ardufocus). El <b>Ardufocus</b> no se
reinicia por el cable USB: durante la actualización la app te pide que pulses el <b>botón de reset</b> de la placa.</p>
<p>La placa guarda la posición y los ajustes en su memoria permanente solo unos diez segundos después del último
movimiento. Para no perder la posición, la app hace que la guarde enseguida cada vez que cierra la conexión
({ui('Disconnetti')}, salida de la app, actualización).</p>
<h2>{ui('Temperatura')}</h2>
<p>La temperatura actual de la sonda está en la barra superior. La gráfica de los últimos 60 minutos está en el resumen
de la pestaña <b>{ui('Calibrazione')}</b> (capítulo 7.6), junto a los darks. La temperatura de cada foto se guarda en
<code>sequence.json</code> y se resume en <code>sequence.txt</code>: es útil porque el enfoque se desplaza con la
dilatación térmica.</p>
""")

# 13
add(f"""
<h1><span class="n">13</span>Una sesión típica, paso a paso</h1>
<h2>Una sola vez (o cuando cambie la mecánica)</h2>
<ol class="steps">
<li><b>Mecánica</b>: introduce los datos y comprueba la resolución con una medición (capítulo 10).</li>
<li><b>Sentido de la muestra</b> y <b>límites</b>, con los límites escritos en el firmware (capítulo 9).</li>
<li><b>Holgura</b>: mídela con la vista en vivo y elige dónde compensarla (secuencia o firmware).</li>
<li><b>Motor</b>: revisa las bobinas (capítulo 12) y, si la app lo propone, actualiza el firmware.</li>
<li><b>Perfiles ópticos</b>: en la pestaña {ui('Ottica')} guarda un perfil por cada combinación de objetivo, filtro e
  iluminación, en el microscopio o en macro (capítulos 7.2 y 7.3).</li>
<li><b>Preajustes</b>: para cada objetivo, calcula el paso a partir de la profundidad de campo y guarda un preajuste;
  el preajuste recuerda también el perfil óptico.</li>
</ol>
<h2>En cada sesión</h2>
<ol class="steps">
<li>Enciende el enfocador y la cámara (modo M), conecta los cables y abre Focus Stack.</li>
<li>El enfocador y la cámara se conectan solos; si no ocurre, pulsa <b>{ui('Connetti')}</b> en la pestaña {ui('Sessione')}.</li>
<li>Ajusta el tiempo de exposición, el ISO y el formato; haz una <b>foto de prueba</b> y revísala en el visor al 100%.</li>
<li>Elige el <b>preajuste</b> del objetivo (o el paso) y comprueba el <b>perfil óptico</b> en la secuencia.</li>
<li>Con la <b>vista en vivo</b> y el teclado, busca el <b>fin</b> y el <b>inicio</b> de la secuencia y pulsa ⌖ {ui('qui')}.</li>
<li>Si hacen falta, prepara los <b>darks</b> y los <b>flats</b> y calcula la exposición de los lights (capítulo 7.6).</li>
<li>Revisa el resumen: número de fotos, recorrido, duración, ningún aviso rojo.</li>
<li><b>{ui('▶ Avvia sequenza')}</b>. No toques el microscopio: las vibraciones estropean las fotos. Para seguirla de
  lejos, usa el progreso en el smartphone (capítulo 7.7).</li>
<li>Al terminar la secuencia, pulsa <b>{ui('Apri nel Finder')}</b> y abre la carpeta en el software de fusión.</li>
</ol>
""")

# 14
add(f"""<h1><span class="n">14</span>Si algo no funciona</h1>
<p>El <b>{ui('Registro')}</b> (la última pestaña) recoge con la hora cada conexión, movimiento, foto y error: cuando
algo no funciona, léelo antes que nada. Arriba puedes buscar palabras y mostrar solo los avisos (⚠) y los errores (✖).
Si informas de un problema, pulsa <b>{ui('Esporta')}</b>: el registro se guarda en un archivo de texto en la carpeta
Descargas, con las versiones de la app y del firmware y los datos del enfocador y la cámara, sin la clave del enlace
para el smartphone ni tu nombre de usuario. Adjunta ese archivo al informe.</p>
""")
add(table(["Problema", "Qué hacer"], [
    ["La cámara no se conecta", "Cierra Fotos, Vista Previa, Captura de Imagen, NX Studio, EOS Utility; desconecta y vuelve a conectar el cable con la cámara encendida; comprueba que esté en modo M y que Wi-Fi/SnapBridge estén apagados."],
    ["La vista en vivo no arranca (Nikon D5600)", f"Dial en <b>M</b> (con los modos de escena la vista en vivo por USB puede quedar bloqueada), tarjeta insertada, batería cargada, revisión de imagen desactivada. El mensaje exacto aparece abajo y en el <b>{ui('Registro')}</b> (“Vista en vivo interrumpida: …”): es lo primero que hay que mirar. Comprueba también que tienes la última versión de la app."],
    ["La vista en vivo va lenta con dos ventanas abiertas", "Actualiza la app: desde la versión 1.0.6 la ventana principal y el visor reciben todos los fotogramas."],
    ["El enfocador no aparece entre los puertos", "Pulsa ⟳ después de conectar el cable; prueba otra toma USB u otro cable (algunos cables solo cargan)."],
    ["El motor vibra pero no gira, o pierde pasos", "Velocidad demasiado alta para la carga o corriente del driver demasiado baja; comprueba también que la polea no patine sobre el eje."],
    ["Las distancias en µm no cuadran", "Repite la medición del apartado 10.4; en el Ardufocus comprueba el micropaso."],
    ["Alarma roja “fuera de los límites”", f"Un botón físico ha llevado el enfocador más allá de un límite. Devuelve la posición dentro de los límites con {ui('Allontana')}/{ui('Avvicina')}; para evitarlo, escribe los límites en el firmware (capítulo 9)."],
    ["La secuencia no se inicia", "Lee el aviso rojo del resumen: normalmente la secuencia, con la compensación de holgura, sale de los límites."],
    ["Fotos movidas o dobles", "Aumenta la espera tras el movimiento y el retardo del espejo; usa la exposición Bulb o el obturador silencioso si la cámara lo permite."],
    [f"“{ui('Focus Stack è chiuso')}” en la página", "La app se ha cerrado: vuelve a abrirla y la página se recarga sola."],
    ["Toda la pila sale en el mismo plano: el carro no avanza", f"Las bobinas del motor están apagadas y la carga hace retroceder el carro en cada parada (capítulo 12): deja activada <i>{ui('Alimentale comunque durante la sequenza')}</i>. Prueba con un movimiento pequeño mirando la vista en vivo."],
    ["La secuencia se ha puesto en pausa sola", f"La foto ha fallado incluso después de volver a conectar la cámara. Lee el mensaje, comprueba la batería, el cable y la tarjeta y pulsa <i>{ui('Riprendi')}</i>: la foto se repite desde la misma posición."],
    ["La cámara desaparece a mitad de la pila", "Normalmente el Mac ha entrado en reposo y ha suspendido el USB. Durante la secuencia la app lo impide, pero no si cierras la tapa de un portátil sin monitor externo. Comprueba también la batería de la cámara."],
    ["El smartphone no abre la página del progreso", f"El teléfono debe estar en la misma red Wi-Fi que el Mac; la primera vez macOS pide permitir las conexiones entrantes (responde Permitir). Después de <i>{ui('Nuovo link')}</i> el código anterior deja de valer."],
]))

# 15
add(f"""<h1><span class="n">15</span>Atajos de teclado</h1>
<div class="two">
<div class="keep"><h2 style="margin-top:0">Pestaña {ui('Sessione')}</h2>
<table><tbody>
<tr><td><kbd>↑</kbd></td><td>aleja el objetivo de la muestra</td></tr>
<tr><td><kbd>↓</kbd></td><td>acerca el objetivo a la muestra</td></tr>
<tr><td><kbd>↑</kbd>/<kbd>↓</kbd> mantenidas pulsadas</td><td>movimiento continuo hasta soltarlas</td></tr>
<tr><td><kbd>⇧</kbd> + <kbd>↑</kbd>/<kbd>↓</kbd></td><td>paso × 10</td></tr>
<tr><td><kbd>1</kbd> <kbd>2</kbd> <kbd>3</kbd> …</td><td>tamaño del paso: 1, 10, 100 …</td></tr>
<tr><td><kbd>Esc</kbd></td><td>STOP</td></tr>
</tbody></table></div>
<div class="keep"><h2 style="margin-top:0">{ui('Visualizzatore')}</h2>
<table><tbody>
<tr><td><kbd>←</kbd> <kbd>→</kbd></td><td>foto anterior / siguiente</td></tr>
<tr><td><kbd>L</kbd></td><td>vista en vivo activada / desactivada</td></tr>
<tr><td><kbd>−</kbd> <kbd>+</kbd></td><td>zoom</td></tr>
<tr><td><kbd>0</kbd> o <kbd>R</kbd></td><td>ajustar a la ventana</td></tr>
<tr><td><kbd>1</kbd></td><td>100%</td></tr>
<tr><td><kbd>U</kbd></td><td>seguir última</td></tr>
<tr><td><kbd>K</kbd></td><td>bloquear vista</td></tr>
<tr><td><kbd>I</kbd></td><td>{ui('Ispettore')}</td></tr>
<tr><td><kbd>G</kbd></td><td>guías de composición</td></tr>
<tr><td><kbd>A</kbd></td><td>autoenfoque: abre el panel, luego clic en el detalle</td></tr>
<tr><td><kbd>[</kbd> <kbd>]</kbd></td><td>área del autoenfoque más pequeña / más grande</td></tr>
<tr><td><kbd>Esc</kbd></td><td>cierra el autoenfoque</td></tr>
<tr><td><kbd>F</kbd></td><td>pantalla completa</td></tr>
</tbody></table></div>
</div>
<p style="margin-top:8mm;color:#5a6b80;font-size:9pt">Focus Stack es software libre (licencia MIT) ·
github.com/teoteo/focus-stack · El firmware deriva de myFocuserPro2 de Robert Brown (licencia MIT).</p>
""")
