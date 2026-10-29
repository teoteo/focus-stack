"""Texto en español de la guía. No es un módulo para importar: genera_guida.py lo ejecuta con exec() en un
espacio de nombres que ya contiene los helpers y los números comunes (fig, frac, table, num, diagram, VERSION,
ICON, IMG, UA, UB, GEAR17, um_step, dof, OBJ, APP). El texto llena la lista H con las secciones HTML.
"""
# ruff: noqa: F821  (los nombres vienen de genera_guida.py)

META = {
    "lang": "es",
    "title": "Focus Stack — Guía de uso",
    "footer": "Guía de uso",
    "pdf": "Guía Focus Stack.pdf",
}


def ui(s):
    """Nombre en español de un comando de la app (la clave es el texto italiano; APP = cadenas de la app)."""
    return APP.get(s, s)


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
  <div class="shot-c"><img src="{IMG}/sessione.png" alt=""></div>
  <div class="meta"><span>Versión de la app {VERSION}</span><span>Octubre de 2026</span></div>
</section>
""")

add("""
<h1 style="break-before:auto">Índice</h1>
<div class="toc"><ol>
<li><span>1</span>Qué es Focus Stack<em>cómo funciona, qué se necesita</em></li>
<li><span>2</span>Instalación, inicio y actualizaciones</li>
<li><span>3</span>La interfaz de un vistazo<em>las tres pestañas y la barra superior</em></li>
<li><span>4</span>Conectar el enfocador y la cámara<em>ajustes de la Nikon D5600 y de otras cámaras</em></li>
<li><span>5</span>El enfocador: posición, movimientos, STOP</li>
<li><span>6</span>Cámara, foto de prueba y vista en vivo</li>
<li><span>7</span>La secuencia de apilado</li>
<li><span>8</span>El visor</li>
<li><span>9</span>Límites de seguridad</li>
<li><span>10</span>Configuración mecánica: los cálculos<em>resolución en µm por paso, medición de comprobación, recorrido, velocidad, holgura</em></li>
<li><span>11</span>Elegir el paso de la secuencia<em>profundidad de campo, número de fotos, duración</em></li>
<li><span>12</span>Motor, controles manuales, actualizaciones, temperatura</li>
<li><span>13</span>Una sesión típica, paso a paso</li>
<li><span>14</span>Si algo no funciona</li>
<li><span>15</span>Atajos de teclado</li>
</ol></div>
""")

# 1
add(f"""
<h1><span class="n">1</span>Qué es Focus Stack</h1>
<p class="lead">Focus Stack controla desde el Mac un enfocador motorizado montado en el enfoque fino (tornillo
micrométrico) del microscopio y una cámara conectada por USB. Ejecuta automáticamente secuencias <b>mover → esperar →
disparar</b>: decenas de fotos con distintos planos de enfoque, listas para fundirlas en una única imagen
nítida de principio a fin con <b>Helicon Focus</b> (o un programa similar).</p>
<h2>Cómo funciona</h2>
<p>La app Focus Stack inicia en el Mac un pequeño programa (el <i>servidor</i>) que se comunica con el enfocador
(una placa Arduino con el firmware myFocuserPro2) y con la cámara. La interfaz se abre en <b>Safari</b>, en la
dirección <code>http://localhost:8765</code>, y solo es accesible desde este Mac.</p>
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
<li>Un Mac con macOS 13 o posterior (Intel) o macOS 14 o posterior (Apple Silicon), con Safari.</li>
<li>El enfocador, conectado con su cable USB y alimentado (12 V).</li>
<li>Una cámara Nikon, Canon o Sony con su cable USB. En esta guía el ejemplo es una <b>Nikon D5600</b>.</li>
<li>Un adaptador que proyecte la imagen del microscopio sobre el sensor (fototubo, adaptador T2 o similar).</li>
</ul>
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
<li>Al iniciarse, Focus Stack abre su página en Safari y se queda en el Dock. Un clic en el icono del Dock
  vuelve a traer la página al frente.</li>
<li>Para cerrarla: <kbd>⌘Q</kbd> en la app, o <span class="ui">Salir</span> en el menú del icono del Dock.
  Si hay una secuencia en curso, la app pide confirmación, la interrumpe y detiene el motor.</li>
<li>Cerrar Safari <b>no</b> cierra la app. Si la página sigue abierta, muestra “{ui("Focus Stack è chiuso")}” y
  se recarga sola cuando vuelves a abrir la app.</li>
</ul>
<h2>Actualizaciones</h2>
<p>Al iniciarse, y luego cada 6 horas, la app comprueba si hay una versión nueva. Si la hay, arriba aparece una
barra con <span class="ui">{ui("Aggiorna e riavvia")}</span>: la app descarga la nueva versión, se cierra y se vuelve
a abrir sola. La misma comprobación puede hacerse a mano en
<span class="ui">{ui("Configurazione")} › {ui("Aggiornamenti")} › {ui("Controlla ora")}</span>.</p>
<p>El <b>firmware del enfocador</b> también se actualiza desde la app (capítulo 12): cuando el de la placa es más
antiguo que el incluido en la app, la misma barra lo indica.</p>
<h2>Idioma</h2>
<p>La app habla italiano, inglés, francés, alemán y español. Con <span class="ui">{ui("Automatica (lingua del sistema)")}</span> sigue el
idioma de macOS y, para los demás idiomas, usa el inglés; en
<span class="ui">{ui("Configurazione")} › {ui("Lingua")}</span> puedes fijar un idioma. La elección se aplica a la interfaz,
los mensajes y el registro, y esta guía existe en los mismos idiomas.</p>
""")

# 3
add(f"""
<h1><span class="n">3</span>La interfaz de un vistazo</h1>
<p>La página tiene tres pestañas, que se eligen arriba:</p>
<ul>
<li><b>{ui("Sessione")}</b>: el trabajo en el microscopio. Enfocador, secuencia, cámara y última foto.</li>
<li><b>{ui("Configurazione")}</b>: límites, mecánica, controles manuales, motor, actualizaciones, temperatura y
  cálculo de la profundidad de campo. Se ajusta una vez y luego se toca rara vez.</li>
<li><b>{ui("Registro")}</b>: la lista de todo lo que ha pasado en la sesión, con la hora. Es el primer sitio
  donde mirar si algo no funciona.</li>
</ul>
{fig("sessione", layout="full", caption="La pestaña Sesión: a la izquierda el enfocador, en el centro la secuencia, a la derecha la cámara y la última foto.")}
<h2>Barra superior</h2>
{fig("barra-superiore", [
    f"<b>Pestañas</b> {ui('Sessione')}, {ui('Configurazione')} y {ui('Registro')}.",
    "<b>Estado de las conexiones</b>: Servidor, Enfocador y Cámara. Verde = conectado, gris = desconectado, rojo = error.",
    "<b>Temperatura</b> leída por la sonda del enfocador.",
    "<b>Tema</b> oscuro o claro. El tema oscuro cansa menos la vista en las sesiones largas al microscopio.",
], layout="full below-marks", anchors={1: "b", 2: "b", 3: "b", 4: "b"})}
<p>Bajo la barra pueden aparecer dos franjas: la azul de las <b>actualizaciones</b> y la roja de <b>alarma</b>, por
ejemplo cuando los botones físicos llevan el enfocador más allá de un límite.</p>
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
<h3>Ajustes en la cámara</h3>
{table(["Cámara", "Qué ajustar"], [
    ["<b>Nikon D5600</b> y otras Nikon", "Dial de modo en <b>M</b> (manual). En el menú de reproducción desactiva la <b>revisión de imagen</b>. Apaga SnapBridge/Wi-Fi y Bluetooth, que pueden ocupar la conexión. Mantén una tarjeta de memoria insertada y la batería cargada (o usa el adaptador de corriente EH-5/EP-5A)."],
    ["Canon", "Modo <b>M</b>. La foto va a la memoria de la cámara o a la tarjeta según el <i>Destino</i>. Para el retardo del espejo, activa el <b>bloqueo del espejo</b> en el menú."],
    ["Sony", "Menú USB › <b>PC Remote</b>; modo <b>M</b>. Para la vista en vivo, la cámara debe permitirla en PC Remote."],
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
    f"<b>{ui('Allontana')} / {ui('Avvicina')}</b>: un clic mueve el tamaño elegido. Si mantienes pulsado, el motor se mueve sin parar y, al soltar, frena hasta detenerse.",
    f"<b>Ir a la posición</b>: escribe un número de pasos y haz clic en {ui('Vai')}.",
    "<b>STOP</b>: detiene en el acto el motor y la secuencia en curso, si la hay. Con el teclado: <kbd>Esc</kbd>.",
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
<div class="box tip"><span class="t">Teclado</span><kbd>↑</kbd> aleja, <kbd>↓</kbd> acerca,
<kbd>⇧</kbd> junto con la flecha multiplica el paso por 10, las teclas numéricas <kbd>1</kbd> <kbd>2</kbd>
<kbd>3</kbd>… eligen el tamaño, <kbd>Esc</kbd> es el STOP. Funcionan en la pestaña {ui('Sessione')}, también
mientras miras la vista en vivo.</div>
<div class="box warn"><span class="t">Botones físicos</span>Los botones del enfocador mueven el motor sin pasar por
la app. La app los vigila y, si la posición sale de los límites, envía STOP y muestra una alarma; para una
protección completa lee el capítulo 9. Si los pulsas durante una secuencia, la secuencia se pone en pausa.</div>
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
    f"Estado: <b>{ui('LIVE')}</b>, <b>{ui('SCATTO…')}</b> durante una foto de prueba, <b>{ui('IN PAUSA')}</b> durante la secuencia.",
    "Modelo de la cámara. Doble clic en la imagen: pantalla completa.",
], layout="stack")}
</div>
<p>La vista en vivo llega hasta 15 imágenes por segundo y es la forma más cómoda de encontrar el inicio y el fin de
la secuencia mientras mueves el enfocador con el teclado. Durante la secuencia se apaga (el espejo tiene que bajar y
la cámara tiene que disparar con normalidad) y vuelve sola al final. En las réflex el espejo permanece subido
mientras la vista en vivo está activa.</p>
<div class="box tip"><span class="t">Para enfocar con precisión</span>Abre la vista en vivo en el <b>visor</b>: puedes
ampliar al 100% y más, y desplazarte hasta el detalle que te interesa (capítulo 8).</div>
""")

# 7
add(f"""
<h1><span class="n">7</span>La secuencia de apilado</h1>
{fig("sequenza", [
    f"<b>Estado</b>: {ui('Pronta')}, {ui('In corso')}, {ui('In pausa')}, {ui('Completata')}, {ui('Errore')}.",
    f"<b>{ui('Inizio')}</b> y <b>{ui('Fine')}</b> en pasos. <span class='ui'>{ui('⌖ qui')}</span> copia la posición actual.",
    "<b>Paso</b> entre una foto y la siguiente, en pasos del motor (cap. 11).",
    f"<b>{ui('Numero di scatti')}</b>. Ligado al paso: si cambias uno, el otro se recalcula.",
    "<b>Resumen</b>: fotos, recorrido en pasos y µm, paso en µm, duración estimada. Si la secuencia sale de los límites, aparece un aviso rojo y no se inicia.",
    f"<b>{ui('Salva in')}</b>: carpeta de las fotos. <span class='ui'>{ui('Scegli…')}</span> abre el panel del Finder, <span class='ui'>{ui('Apri')}</span> la muestra en el Finder.",
    "<b>Espera tras el movimiento</b>: deja que se amortigüen las vibraciones (1–3 s en el microscopio). <b>Pausa tras el disparo</b>: tiempo para escribir en la tarjeta y recargar el flash.",
    "<b>Compensación de holgura</b>: antes de la primera foto el motor retrocede estos pasos y luego avanza, para llegar a cada foto desde la misma dirección.",
    f"<b>{ui('Modalità di scatto')}</b>: <i>{ui('Scarica sul Mac')}</i> (recomendado), <i>{ui('Solo sulla scheda')}</i>, <i>{ui('Solo trigger (veloce)')}</i> (con destino tarjeta).",
    "<b>Nombre de la sesión</b>: subcarpeta <code>nombre_fecha-hora</code>, fotos <code>nombre_0001</code>, <code>nombre_0002</code>…",
    "<b>Volver al inicio</b> al terminar.",
    f"<b>{ui('Preset')}</b>: guarda y recupera los ajustes de la secuencia, p. ej. uno por objetivo.",
    "<b>Progreso</b>: fotos tomadas, tiempo restante, posición.",
    f"<b>{ui('▶ Avvia sequenza')}</b>, <b>{ui('❚❚ Pausa')}</b>/<b>{ui('Riprendi')}</b> e <b>{ui('■ Interrompi')}</b>.",
    f"<b>{ui('Apri in Helicon Focus')}</b>: al terminar, carga todas las fotos en Helicon Focus.",
])}
<p>Los ajustes de tiempos y holgura están en la sección plegable <span class="ui">{ui('Tempi, gioco e nome della sessione')}</span>.
En la misma carpeta de las fotos la app guarda <code>sequence.json</code>, con los parámetros usados y la posición y
la temperatura de cada foto.</p>
<h2>Durante la secuencia</h2>
{fig("sequenza-in-corso", [
    f"El estado pasa a <b>{ui('In corso')}</b> (ámbar).",
    "Fotos tomadas sobre el total, tiempo restante estimado y posición actual. En la barra de recorrido las marcas de las fotos ya tomadas cambian de color.",
    f"<b>{ui('❚❚ Pausa')}</b> se detiene después de la foto en curso; <b>{ui('■ Interrompi')}</b> termina la secuencia. El <b>STOP</b> del enfocador también detiene el motor en el acto.",
], layout="side narrow")}
<ul>
<li>Si pulsas los <b>botones físicos</b> del enfocador, la secuencia se pone en pausa; al reanudarla vuelve a la
  posición correcta y repite la foto.</li>
<li>Los campos de la secuencia están bloqueados mientras la secuencia está en curso.</li>
<li>Cada foto nueva aparece en {ui('Ultimo scatto')} y en el visor.</li>
</ul>
""")

# 8
add(f"""
<h1><span class="n">8</span>El visor</h1>
<p>Se abre con <span class="ui">{ui('Apri visualizzatore ↗')}</span> o con un clic en la última foto, en una ventana
aparte que puedes llevar a un segundo monitor. Muestra las fotos a resolución completa (también los RAW, convertidos
al vuelo) con zoom y desplazamiento, y la vista en vivo de la cámara.</p>
{fig("visualizzatore", [
    "<b>◀ ▶</b> foto anterior y siguiente (flechas <kbd>←</kbd> <kbd>→</kbd>).",
    "Nombre del archivo; número de la foto, tipo, posición, temperatura y hora.",
    f"<b>{ui('● Live')}</b> (<kbd>L</kbd>): la vista en vivo en la misma ventana, con zoom y desplazamiento.",
    "<b>Zoom</b> − y + (<kbd>−</kbd> <kbd>+</kbd>) y nivel de ampliación.",
    f"<b>{ui('Adatta')}</b> (<kbd>0</kbd>), <b>100%</b> (<kbd>1</kbd>: un píxel del sensor = un píxel de la pantalla), <b>{ui('Reset')}</b> (<kbd>R</kbd>).",
    f"<b>{ui('Segui ultimo')}</b> (<kbd>U</kbd>): muestra automáticamente cada foto nueva.",
    f"<b>{ui('Blocca vista')}</b> (<kbd>K</kbd>): al cambiar de foto mantiene el zoom y la posición, para comparar el enfoque en el mismo punto.",
    f"<b>{ui('Finder')}</b>: muestra el archivo en el Finder.",
    "<b>Pantalla completa</b> (<kbd>F</kbd>).",
    "<b>Miniaturas</b>: un clic abre la foto. <i>P</i> = foto de prueba, los números son las fotos de la secuencia.",
], layout="full", anchors={n: "b" for n in range(1, 10)})}
<p>Con el ratón: arrastra para desplazar la imagen, rueda (o pellizco en el trackpad) para el zoom centrado en el
puntero, doble clic para pasar de “ajustar” al 100% y viceversa. Por encima del 150% los píxeles se ven nítidos,
sin desenfoque.</p>
{fig("visualizzatore-live", [
    f"<b>{ui('■ Ferma live')}</b> vuelve a las fotos; ◀ ▶ o un clic en una miniatura también salen de la vista en vivo.",
    f"Estado de la vista en vivo: {ui('LIVE')}, {ui('SCATTO…')}, {ui('IN PAUSA')} durante la secuencia.",
], layout="full", anchors={1: "b"}, caption="La vista en vivo en el visor, aquí con el simulador enfocado (el tablero de ajedrez se ve nítido). Al 100% la vista en vivo tiene la resolución de la previsualización de la cámara, más baja que la de las fotos.")}
""")

# 9
add(f"""
<h1><span class="n">9</span>Límites de seguridad</h1>
<p class="lead">Los límites evitan que el objetivo toque el portaobjetos o que la mecánica llegue al tope. Hay que
establecerlos antes que nada, con calma.</p>
{fig("fine-corsa", [
    f"<b>{ui('Fine corsa inferiore')}</b> en pasos; <span class='ui'>{ui('⌖ Usa posizione attuale')}</span> lo toma de la posición del enfocador.",
    f"<b>{ui('Fine corsa superiore')}</b>. Vacío = el máximo del firmware.",
    f"<b>Hacia la muestra</b>: si al acercarse a la muestra los pasos disminuyen o aumentan. Sirve para etiquetar correctamente {ui('Avvicina')}/{ui('Allontana')}.",
    f"<b>{ui('Salva fine corsa')}</b>.",
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
<li>Lleva la platina a la posición útil más alejada, pulsa <span class="ui">{ui('⌖ Usa posizione attuale')}</span>
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
    "<b>Resultado</b>: µm por paso, pasos por µm, µm cada 1000 pasos.",
    f"<b>{ui('Salva meccanica')}</b>.",
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
{fig("profondita", [
    f"<b>{ui('Apertura numerica (NA)')}</b>: el segundo número grabado en el objetivo (10×/<b>0,25</b>).",
    f"<b>{ui('Ingrandimento sul sensore')}</b>: aumento del objetivo × factor del adaptador de la cámara.",
    f"<b>{ui('Pixel del sensore (µm)')}</b>. Nikon D5600: <b>3,9 µm</b> (23,5 mm ÷ 6.000 píxeles).",
    "<b>Solapamiento</b> entre una capa nítida y la siguiente; un 20–30% es un buen valor.",
    "<b>Resultado</b>: profundidad de campo, paso recomendado en µm y en pasos del motor.",
    f"<b>{ui('Usa come passo della sequenza')}</b>: copia el valor en pasos en el campo Paso de la secuencia.",
])}
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
<div class="box tip"><span class="t">El adaptador de la cámara</span>Si el adaptador tiene un factor distinto de 1
(por ejemplo 0,5× o 2,5×), multiplica el aumento del objetivo por ese factor: 10× con un adaptador de 0,5× = 5 sobre
el sensor. Solo cambia el segundo término de la fórmula, que pesa más con los objetivos de poco aumento.</div>

<h2>11.2 Inicio, fin y número de fotos</h2>
<ol class="steps">
<li>Activa la vista en vivo (mejor en el visor, ampliada) y lleva el enfoque <b>justo por encima</b> de la parte más
  alta del sujeto que quieres nítida: pulsa <span class="ui">{ui('⌖ qui')}</span> junto a <b>{ui('Inizio')}</b>.</li>
<li>Baja hasta <b>justo por debajo</b> de la parte más baja y pulsa <span class="ui">{ui('⌖ qui')}</span> junto a <b>{ui('Fine')}</b>.</li>
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
<h1><span class="n">12</span>Motor, controles manuales, actualizaciones, temperatura</h1>
<h2>{ui('Motore (firmware)')}</h2>
{fig("motore", [
    f"<b>{ui('Microstep')}</b>: {ui('passo intero')}, 1/2 … 1/32 (mira 10.2). Cambiarlo cambia la escala de las posiciones: después, vuelve a comprobar los límites.",
    f"<b>{ui('Velocità')}</b> del firmware: lenta, media, rápida.",
    f"<b>{ui('Bobine alimentate a motore fermo')}</b>: el motor mantiene la posición, pero se calienta.",
    f"<b>{ui('Inverti verso di rotazione')}</b>.",
    "<b>Compensar holgura IN / OUT</b>: en cada inversión hacia posiciones más bajas (IN) o más altas (OUT) el firmware da unos pasos de más sin contarlos, también con los botones físicos.",
    "<b>Holgura IN / OUT</b> en pasos, de 0 a 255 (mira 10.5).",
    f"<b>{ui('Rileggi')}</b> los valores del firmware.",
])}
<h2>{ui('Comandi manuali')}</h2>
{fig("comandi-manuali", [
    f"<b>Tamaños de paso</b> de los botones {ui('Allontana')}/{ui('Avvicina')}: en potencias de diez hasta 1.000, 10.000 o 100.000 pasos. Con un reductor hacen falta tamaños grandes.",
    f"<b>{ui('Tieni premuto per muovere senza fermarti')}</b>: al soltar, el motor frena y se detiene; en cualquier caso se detiene en el límite y, si la página deja de responder, al cabo de un segundo aproximadamente.",
], layout="side")}
<h2>{ui('Aggiornamenti')}</h2>
{fig("aggiornamenti", [
    "Versión de la <b>app</b> y resultado de la última comprobación.",
    "Versión del <b>firmware</b> del enfocador.",
    f"<b>{ui('Aggiorna firmware')}</b>: unos 20 segundos; los ajustes del enfocador se conservan. No desconectes el cable; si algo sale mal, basta con repetirlo.",
    f"<b>{ui('Controlla ora')}</b> si hay actualizaciones de la app.",
], layout="side")}
<p>La app elige sola el firmware adecuado para la placa (myFocuserPro2 o Ardufocus). El <b>Ardufocus</b> no se
reinicia por el cable USB: durante la actualización la app te pide que pulses el <b>botón de reset</b> de la placa.</p>
<h2>{ui('Temperatura')}</h2>
{fig("temperatura", [
    "Temperatura actual de la sonda.",
    "Evolución de los últimos 60 minutos. La temperatura de cada foto se guarda en <code>sequence.json</code>: es útil porque el enfoque se desplaza con la dilatación térmica.",
], layout="side")}
""")

# 13
add(f"""
<h1><span class="n">13</span>Una sesión típica, paso a paso</h1>
<h2>Una sola vez (o cuando cambie la mecánica)</h2>
<ol class="steps">
<li><b>Mecánica</b>: introduce los datos y comprueba la resolución con una medición (capítulo 10).</li>
<li><b>Sentido de la muestra</b> y <b>límites</b>, con los límites escritos en el firmware (capítulo 9).</li>
<li><b>Holgura</b>: mídela con la vista en vivo y elige dónde compensarla (secuencia o firmware).</li>
<li><b>Preajustes</b>: para cada objetivo, calcula el paso a partir de la profundidad de campo y guarda un preajuste.</li>
</ol>
<h2>En cada sesión</h2>
<ol class="steps">
<li>Enciende el enfocador y la cámara (modo M), conecta los cables y abre Focus Stack.</li>
<li>Conecta el enfocador y la cámara desde la pestaña {ui('Sessione')}.</li>
<li>Ajusta el tiempo de exposición, el ISO y el formato; haz una <b>foto de prueba</b> y revísala en el visor al 100%.</li>
<li>Elige el <b>preajuste</b> del objetivo (o el paso).</li>
<li>Con la <b>vista en vivo</b> y el teclado, busca el <b>fin</b> y el <b>inicio</b> de la secuencia y pulsa {ui('⌖ qui')}.</li>
<li>Revisa el resumen: número de fotos, recorrido, duración, ningún aviso rojo.</li>
<li><b>{ui('▶ Avvia sequenza')}</b>. No toques el microscopio: las vibraciones estropean las fotos.</li>
<li>Al terminar la secuencia, pulsa <b>{ui('Apri in Helicon Focus')}</b>.</li>
</ol>
""")

# 14
add(f"""<h1><span class="n">14</span>Si algo no funciona</h1>
<p>El <b>{ui('Registro')}</b> (tercera pestaña) recoge con la hora cada conexión, movimiento, foto y error: cuando
algo no funciona, léelo antes que nada.</p>
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
]))

# 15
add(f"""<h1><span class="n">15</span>Atajos de teclado</h1>
<div class="two">
<div class="keep"><h2 style="margin-top:0">Pestaña {ui('Sessione')}</h2>
<table><tbody>
<tr><td><kbd>↑</kbd></td><td>aleja el objetivo de la muestra</td></tr>
<tr><td><kbd>↓</kbd></td><td>acerca el objetivo a la muestra</td></tr>
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
<tr><td><kbd>F</kbd></td><td>pantalla completa</td></tr>
</tbody></table></div>
</div>
<p style="margin-top:8mm;color:#5a6b80;font-size:9pt">Focus Stack es software libre (licencia MIT) ·
github.com/teoteo/focus-stack · El firmware deriva de myFocuserPro2 de Robert Brown (licencia MIT).</p>
""")
