"""Texte français du guide. Ce n'est pas un module à importer : genera_guida.py l'exécute avec exec() dans un
espace de noms qui contient déjà les fonctions et les nombres communs (fig, frac, table, num, diagram, VERSION,
ICON, IMG, UA, UB, GEAR17, um_step, dof, OBJ, APP). Le texte remplit la liste H avec les sections HTML.
"""
# ruff: noqa: F821  (les noms viennent de genera_guida.py)

META = {
    "lang": "fr",
    "title": "Focus Stack — Guide d'utilisation",
    "footer": "Guide d'utilisation",
    "pdf": "Guide Focus Stack.pdf",
}


def ui(s):
    """Nom français d'une commande de l'app (le texte italien est la clé) : le même que dans l'app."""
    return APP.get(s, s)


DIAGRAM_LABELS = {
    "motor": "Moteur", "gearbox": "Réducteur", "pulleys": "Poulies / engrenages", "knob": "Micrométrique", "stage": "Platine",
    "motor1": "pas par tour", "motor2": "× micropas",
    "gearbox1": "(s'il y en a un)", "gearbox2": "ex. 26,85 : 1",
    "pulleys1": "dents menée", "pulleys2": "÷ dents menante",
    "knob1": "µm par tour", "knob2": "de la molette",
    "stage1": "se déplace", "stage2": "en µm",
    "ratio": "rapport de réduction total = réducteur × poulies",
    "steps": "pas moteur par tour de molette = pas/tour × micropas × rapport",
}

# tableau de la profondeur de champ (noms des objectifs dans la langue du guide)
OBJ_NAMES = ["4× / 0,10", "10× / 0,25", "20× / 0,40", "40× / 0,65", "60× / 0,85", "100× / 1,25 huile"]
dof_rows = []
for name, (mag, na) in zip(OBJ_NAMES, OBJ):
    d = dof(na, mag, 3.9)
    s = d * 0.7
    dof_rows.append([name, num(d), num(s), str(max(1, round(s / UA))), str(max(1, round(s / UB)))])
dof_note = ("pour les objectifs à immersion dans l'huile, la formule de l'app (indice n = 1, air) sous-estime la "
            "profondeur de champ : le pas calculé est donc prudent.")

H = []
add = H.append

add(f"""
<section class="cover">
  <div class="icon">{ICON}</div>
  <h1 class="title">Focus Stack</h1>
  <div class="sub">Guide d'utilisation<br>focuser motorisé et appareil photo pour le focus stacking au microscope</div>
  <div class="shot-c"><img src="{IMG}/sessione.png" alt=""></div>
  <div class="meta"><span>Version de l'app {VERSION}</span><span>Octobre 2026</span></div>
</section>
""")

add("""
<h1 style="break-before:auto">Sommaire</h1>
<div class="toc"><ol>
<li><span>1</span>Qu'est-ce que Focus Stack<em>principe de fonctionnement, matériel nécessaire</em></li>
<li><span>2</span>Installation, lancement et mises à jour</li>
<li><span>3</span>L'interface en bref<em>les trois onglets et la barre supérieure</em></li>
<li><span>4</span>Connecter le focuser et l'appareil photo<em>réglages du Nikon D5600 et des autres appareils</em></li>
<li><span>5</span>Le focuser : position, déplacements, STOP</li>
<li><span>6</span>Appareil photo, photo test et visée en direct</li>
<li><span>7</span>La séquence de stacking</li>
<li><span>8</span>La visionneuse</li>
<li><span>9</span>Limites de sécurité</li>
<li><span>10</span>Configuration mécanique : les calculs<em>résolution en µm par pas, mesure de contrôle, course, vitesse, jeu</em></li>
<li><span>11</span>Choisir le pas de la séquence<em>profondeur de champ, nombre de photos, durée</em></li>
<li><span>12</span>Moteur, commandes manuelles, mises à jour, température</li>
<li><span>13</span>Une session type, étape par étape</li>
<li><span>14</span>En cas de problème</li>
<li><span>15</span>Raccourcis clavier</li>
</ol></div>
""")

# 1
add(f"""
<h1><span class="n">1</span>Qu'est-ce que Focus Stack</h1>
<p class="lead">Focus Stack pilote depuis le Mac un focuser motorisé monté sur la vis micrométrique du microscope
et un appareil photo connecté en USB. Il exécute automatiquement des séquences <b>déplacer → attendre →
déclencher</b> : des dizaines de photos à des mises au point différentes, prêtes à être fusionnées en une seule
image entièrement nette avec <b>Helicon Focus</b> (ou un programme similaire).</p>
<h2>Principe de fonctionnement</h2>
<p>L'app Focus Stack lance sur le Mac un petit programme (le <i>serveur</i>) qui dialogue avec le focuser (une
carte Arduino équipée du firmware myFocuserPro2) et avec l'appareil photo. L'interface s'ouvre dans
<b>Safari</b>, à l'adresse <code>http://localhost:8765</code>, et n'est accessible que depuis ce Mac.</p>
<ul>
<li>Le <b>focuser</b> fait tourner la molette de mise au point avec un moteur pas à pas. Chaque <i>pas</i> du
  moteur déplace la platine (ou l'objectif) d'une fraction de micromètre : de combien, c'est la
  <b>configuration mécanique</b> qui le calcule (chapitre 10).</li>
<li>L'<b>appareil photo</b> est piloté avec le même protocole que les logiciels des fabricants : temps de pose,
  ISO, format, déclenchement, téléchargement des photos et visée en direct.</li>
<li>Les <b>boutons physiques</b> du focuser continuent de fonctionner quand l'app est ouverte.</li>
</ul>
<h2>Matériel nécessaire</h2>
<ul>
<li>Un Mac sous macOS 13 ou ultérieur (Intel) ou macOS 14 ou ultérieur (Apple Silicon), avec Safari.</li>
<li>Un focuser <b>myFocuserPro2</b> (version avec pilote DRV8825) ou <b>Ardufocus</b> (carte rev1 avec DRV8825),
  connecté par son câble USB et alimenté (12 V).</li>
<li>Un appareil photo Nikon, Canon ou Sony avec son câble USB. Dans ce guide, l'exemple est un <b>Nikon D5600</b>.</li>
<li>Un adaptateur qui projette l'image du microscope sur le capteur (phototube, bague T2 ou similaire).</li>
</ul>
<div class="box warn"><span class="t">Focusers pris en charge</span>Focus Stack fonctionne avec les cartes
<b>myFocuserPro2</b> et <b>Ardufocus</b>, avec le firmware fourni avec l'app. Un myFocuserPro2 avec son firmware d'origine
se connecte tout de suite et l'app propose de le mettre à jour en un clic. Un Ardufocus avec son firmware d'origine
(protocole Moonlite) n'est en revanche pas reconnu : la première fois, le firmware de Focus Stack doit être chargé à la
main (instructions dans le README sur github.com/teoteo/focus-stack) ; ensuite, l'Ardufocus se met lui aussi à jour
depuis l'app.</div>
<div class="box tip"><span class="t">Sans matériel</span>Les cartes Focuser et Appareil photo comportent la case
<span class="ui">{ui("Simulatore")}</span> : elle permet d'essayer toute l'app sans rien connecter. Les captures
d'écran de ce guide ont été réalisées ainsi.</div>
""")

# 2
add(f"""
<h1><span class="n">2</span>Installation, lancement et mises à jour</h1>
<h2>Première installation</h2>
<ol class="steps">
<li>Téléchargez <code>FocusStack-&lt;version&gt;.zip</code> depuis la page
  <b>github.com/teoteo/focus-stack/releases</b> et ouvrez-le : l'app <b>Focus Stack</b> apparaît.</li>
<li>Faites glisser Focus Stack dans le dossier <b>Applications</b> avant de l'ouvrir.</li>
<li>Ouvrez-la. macOS signale qu'il ne peut pas vérifier le développeur, car l'app n'est pas signée par Apple.
  Ouvrez <b>Réglages Système › Confidentialité et sécurité</b>, faites défiler vers le bas et cliquez sur
  <b>Ouvrir quand même</b>. Ce n'est nécessaire que la première fois.</li>
</ol>
<p>L'app contient déjà tout ce dont elle a besoin : il n'y a rien d'autre à installer.</p>
<h2>Lancement et fermeture</h2>
<ul>
<li>Au lancement, Focus Stack ouvre sa page dans Safari et reste dans le Dock. Un clic sur l'icône du Dock
  ramène la page au premier plan.</li>
<li>Pour quitter : <kbd>⌘Q</kbd> dans l'app, ou <span class="ui">Quitter</span> dans le menu de l'icône du Dock.
  Si une séquence est en cours, l'app demande confirmation, l'interrompt et arrête le moteur.</li>
<li>Fermer Safari ne quitte <b>pas</b> l'app. Si la page reste ouverte, elle affiche « {ui("Focus Stack è chiuso")} »
  et se recharge toute seule quand vous rouvrez l'app.</li>
</ul>
<h2>Mises à jour</h2>
<p>Au lancement, puis toutes les 6 heures, l'app vérifie s'il existe une nouvelle version. Si c'est le cas, une
barre avec <span class="ui">{ui("Aggiorna e riavvia")}</span> apparaît en haut : l'app télécharge la nouvelle version,
se ferme et se rouvre toute seule. La même vérification peut se faire à la main dans
<span class="ui">{ui("Configurazione")} › {ui("Aggiornamenti")} › {ui("Controlla ora")}</span>.</p>
<p>Le <b>firmware du focuser</b> se met lui aussi à jour depuis l'app (chapitre 12) : quand celui de la carte est
plus ancien que celui fourni avec l'app, la même barre le signale.</p>
<h2>Langue</h2>
<p>L'app parle italien, anglais, français, allemand et espagnol. Avec <span class="ui">{ui("Automatica (lingua del sistema)")}</span>
elle suit la langue de macOS, et utilise l'anglais pour les autres langues ; dans
<span class="ui">{ui("Configurazione")} › {ui("Lingua")}</span> vous pouvez choisir une langue fixe. Le choix s'applique à
l'interface, aux messages et au journal, et ce guide existe dans les mêmes langues.</p>
""")

# 3
add(f"""
<h1><span class="n">3</span>L'interface en bref</h1>
<p>La page comporte trois onglets, que l'on choisit en haut :</p>
<ul>
<li><b>{ui("Sessione")}</b> : le travail au microscope. Focuser, séquence, appareil photo et dernière photo.</li>
<li><b>{ui("Configurazione")}</b> : limites, mécanique, commandes manuelles, moteur, mises à jour, température et
  calcul de la profondeur de champ. On le règle une fois, puis on y touche rarement.</li>
<li><b>{ui("Registro")}</b> : la liste horodatée de tout ce qui s'est passé pendant la session. C'est le premier
  endroit à consulter en cas de problème.</li>
</ul>
{fig("sessione", layout="full", caption="L'onglet Session : à gauche le focuser, au centre la séquence, à droite l'appareil photo et la dernière photo.")}
<h2>Barre supérieure</h2>
{fig("barra-superiore", [
    f"<b>Onglets</b> {ui('Sessione')}, {ui('Configurazione')} et {ui('Registro')}.",
    f"<b>État des connexions</b> : {ui('Server')}, {ui('Focheggiatore')} et {ui('Fotocamera')}. Vert = connecté, gris = déconnecté, rouge = erreur.",
    "<b>Température</b> lue par la sonde du focuser.",
    "<b>Thème</b> sombre ou clair. Le thème sombre fatigue moins les yeux pendant les longues sessions au microscope.",
], layout="full below-marks", anchors={1: "b", 2: "b", 3: "b", 4: "b"})}
<p>Sous la barre, deux bandeaux peuvent apparaître : le bleu des <b>mises à jour</b> et le rouge d'<b>alarme</b>,
par exemple quand les boutons physiques amènent le focuser au-delà d'une limite.</p>
""")

# 4
add(f"""
<h1><span class="n">4</span>Connecter le focuser et l'appareil photo</h1>
<h2>Focuser</h2>
{fig("connessione-focheggiatore", [
    "<b>Port série</b> du focuser. Il s'appelle en général <code>/dev/cu.usbserial-…</code> ou <code>/dev/cu.wchusbserial…</code> ; le nom change si vous utilisez une autre prise USB du Mac.",
    "<b>Actualiser la liste</b> des ports, après avoir branché le câble.",
    f"<b>{ui('Simulatore')}</b> : un faux focuser, pour essayer l'app.",
    f"<b>{ui('Connetti')}</b>. À l'ouverture du port, l'Arduino redémarre : la connexion prend 2 à 3 secondes.",
], layout="side narrow")}
<h2>Appareil photo</h2>
{fig("connessione-fotocamera", [
    f"<b>Appareil photo</b> : laissez <i>{ui('Rilevamento automatico')}</i> ou choisissez le modèle trouvé.",
    "<b>Détecter</b> les appareils photo connectés.",
    f"<b>{ui('Simulatore')}</b> : un faux appareil photo qui génère des images de test.",
    f"<b>{ui('Connetti')}</b>. Avant de se connecter, l'app ferme les services de macOS qui s'approprient l'appareil photo.",
], layout="side narrow")}
<h3>Réglages sur l'appareil photo</h3>
{table(["Appareil photo", "Que régler"], [
    ["<b>Nikon D5600</b> et autres Nikon", "Molette de sélection du mode sur <b>M</b> (manuel). Dans le menu Visualisation, désactivez l'<b>affichage des images</b>. Désactivez SnapBridge/Wi-Fi et Bluetooth, qui peuvent occuper la connexion. Gardez une carte mémoire insérée et la batterie chargée (ou l'adaptateur secteur EH-5/EP-5A)."],
    ["Canon", f"Mode <b>M</b>. La photo va dans la mémoire de l'appareil ou sur la carte selon <i>{ui('Destinazione')}</i>. Pour la temporisation du miroir, activez le <b>verrouillage du miroir</b> dans le menu."],
    ["Sony", "Menu USB › <b>PC Remote</b> ; mode <b>M</b>. Pour la visée en direct, l'appareil doit l'autoriser en mode PC Remote."],
])}
<div class="box warn"><span class="t">Si l'appareil photo ne se connecte pas</span>macOS essaie de s'approprier
l'appareil photo dès que vous le branchez. L'app ferme ce service toute seule ; si cela ne suffit pas, quittez
<b>Photos</b>, <b>Aperçu</b>, <b>Transfert d'images</b>, NX Studio et EOS Utility, puis réessayez. Débrancher et
rebrancher le câble avec l'appareil allumé aide souvent.</div>
""")

# 5
add(f"""
<h1><span class="n">5</span>Le focuser : position, déplacements, STOP</h1>
{fig("focheggiatore", [
    f"<b>État</b> : {ui('Fermo')}, {ui('In movimento')}, {ui('Disconnesso')}.",
    f"<b>Connexion</b> : port, version du firmware et maximum du firmware (la position la plus haute autorisée). <span class='ui'>{ui('Disconnetti')}</span> libère le port.",
    "<b>Position</b> en pas moteur et, en dessous, en millimètres ou en micromètres (si la mécanique est configurée).",
    "<b>Limites</b> définies et distance restante, vers l'échantillon, avant la limite.",
    "<b>Barre de course</b> : voir la figure ci-dessous.",
    f"<b>Taille du pas</b> des boutons {ui('Allontana')}/{ui('Avvicina')} : 1, 10, 100… pas. Les tailles disponibles se choisissent dans {ui('Configurazione')} › {ui('Comandi manuali')}.",
    "Le même déplacement <b>en micromètres</b>.",
    f"<b>{ui('Allontana')} / {ui('Avvicina')}</b> : un clic déplace de la taille choisie. En maintenant le bouton enfoncé, le moteur avance sans s'arrêter, puis ralentit jusqu'à l'arrêt quand vous le relâchez.",
    f"<b>{ui('Vai alla posizione…')}</b> : saisissez un nombre de pas et cliquez sur {ui('Vai')}.",
    "<b>STOP</b> : arrête immédiatement le moteur et la séquence éventuelle. Au clavier : <kbd>Esc</kbd>.",
])}
<h2>La barre de course</h2>
{fig("binario", [
    "<b>Zones hachurées rouges</b> : hors des limites, interdites.",
    "<b>Bande bleue</b> : l'intervalle de la séquence, avec un trait pour chaque photo.",
    "<b>Ligne blanche</b> : la position actuelle.",
], layout="side narrow")}
<p>Sous la barre : la limite inférieure, la flèche qui indique <b>de quel côté se trouve l'échantillon</b> et la
limite supérieure. « {ui('Avvicina')} » déplace toujours vers l'échantillon, quel que soit le sens des nombres :
cela se règle dans {ui('Configurazione')} › {ui('Fine corsa')} (chapitre 9).</p>
<div class="box tip"><span class="t">Clavier</span><kbd>↑</kbd> éloigne, <kbd>↓</kbd> rapproche,
<kbd>⇧</kbd> avec une flèche multiplie le pas par 10, les touches numériques <kbd>1</kbd> <kbd>2</kbd>
<kbd>3</kbd>… choisissent la taille du pas, <kbd>Esc</kbd> correspond au STOP. Ces touches fonctionnent dans l'onglet
{ui('Sessione')}, même pendant la visée en direct.</div>
<div class="box warn"><span class="t">Boutons physiques</span>Les boutons du focuser actionnent le moteur sans passer
par l'app. L'app les surveille et, si la position sort des limites, envoie STOP et affiche une alarme ; pour une
protection complète, lisez le chapitre 9. Si vous les actionnez pendant une séquence, la séquence se met en
pause.</div>
""")

# 6
add(f"""
<h1><span class="n">6</span>Appareil photo, photo test et visée en direct</h1>
{fig("fotocamera", [
    f"<b>État</b> : {ui('Pronta')}, {ui('Scatto…')}, {ui('Disconnessa')}.",
    f"<b>Modèle</b> connecté et <span class='ui'>{ui('Disconnetti')}</span>.",
    f"<b>{ui('Tempo di posa')}</b> et <b>ISO</b>.",
    f"<b>{ui('Diaframma')}</b> et <b>{ui('Formato')}</b> (RAW, JPEG…). Au microscope, sans objectif sur l'appareil photo, il n'y a généralement pas d'ouverture.",
    f"<b>{ui('Destinazione')}</b> : mémoire de l'appareil photo ou carte.",
    f"<b>{ui('Posa B (secondi)')}</b> : 0 utilise le temps de pose ; une valeur supérieure à 0 fait une pose B pilotée par le Mac, pour les poses de plus de 30 s.",
    f"<b>{ui('Ritardo specchio (reflex)')}</b>, de 0,5 à 2,5 s : attente entre la levée du miroir et le déclenchement, pour laisser les vibrations s'amortir. Sur le Nikon D5600, l'app utilise la <i>temporisation de l'exposition</i> de l'appareil.",
    f"<b>{ui('Rileggi')}</b> les réglages de l'appareil photo. Après chaque modification, l'app relit la valeur que l'appareil a réellement acceptée.",
    f"<b>{ui('◉ Scatto di prova')}</b> : une photo à la position actuelle, qui s'affiche dans {ui('Ultimo scatto')} et dans la visionneuse.",
])}
<h2>Dernière photo et visée en direct</h2>
<div class="two">
{fig("ultimo-scatto", [
    f"<b>{ui('● Live')}</b> : affiche l'image en direct de l'appareil photo.",
    f"<b>{ui('Apri visualizzatore ↗')}</b> dans une fenêtre séparée (chapitre 8).",
    f"<b>{ui('Ultimo scatto')}</b> : un clic l'ouvre dans la visionneuse.",
    "Nom du fichier, position et température au moment de la photo.",
], layout="stack")}
{fig("live", [
    f"<b>{ui('■ Ferma live')}</b> coupe la visée en direct.",
    f"État : <b>{ui('LIVE')}</b>, <b>{ui('SCATTO…')}</b> pendant une photo test, <b>{ui('IN PAUSA')}</b> pendant la séquence.",
    "Modèle de l'appareil photo. Double-clic sur l'image : plein écran.",
], layout="stack")}
</div>
<p>La visée en direct atteint 15 images par seconde : c'est le moyen le plus pratique de trouver le début et la fin
de la séquence tout en déplaçant le focuser au clavier. Elle est coupée pendant la séquence (le miroir doit
redescendre et l'appareil doit déclencher normalement) et reprend toute seule à la fin. Sur les reflex, le miroir
reste levé tant que la visée en direct est active.</p>
<div class="box tip"><span class="t">Pour une mise au point précise</span>Ouvrez la visée en direct dans la
<b>visionneuse</b> : vous pouvez zoomer à 100 % et au-delà et vous déplacer sur le détail qui vous intéresse
(chapitre 8).</div>
""")

# 7
TORNA = ui("Torna all'inizio a fine sequenza")
add(f"""
<h1><span class="n">7</span>La séquence de stacking</h1>
{fig("sequenza", [
    f"<b>État</b> : {ui('Pronta')}, {ui('In corso')}, {ui('In pausa')}, {ui('Completata')}, {ui('Errore')}.",
    f"<b>{ui('Inizio')}</b> et <b>{ui('Fine')}</b> en pas. <span class='ui'>{ui('⌖ qui')}</span> copie la position actuelle.",
    "<b>Pas</b> entre deux photos, en pas moteur (chapitre 11).",
    f"<b>{ui('Numero di scatti')}</b>, lié au pas : modifier l'un recalcule l'autre.",
    "<b>Récapitulatif</b> : photos, course en pas et en µm, pas en µm, durée estimée. Si la séquence sort des limites, un avertissement rouge apparaît et elle ne démarre pas.",
    f"<b>{ui('Salva in')}</b> : le dossier des photos. <span class='ui'>{ui('Scegli…')}</span> ouvre le Finder, <span class='ui'>{ui('Apri')}</span> y affiche le dossier.",
    "<b>Attente après le mouvement</b> : laisse les vibrations s'amortir avant la photo (1 à 3 s au microscope). <b>Pause après la photo</b> : écriture sur la carte, recharge du flash.",
    "<b>Compensation du jeu</b> : avant la première photo, le moteur recule de ce nombre de pas puis avance ; chaque photo est ainsi atteinte dans le même sens.",
    f"<b>{ui('Modalità di scatto')}</b> : <i>{ui('Scarica sul Mac')}</i> (recommandé), <i>{ui('Solo sulla scheda')}</i>, <i>{ui('Solo trigger (veloce)')}</i> (destination : carte).",
    "<b>Nom de la session</b> : sous-dossier <code>nom_date-heure</code>, fichiers <code>nom_0001</code>, <code>nom_0002</code>…",
    f"<b>{TORNA}</b>.",
    "<b>Préréglages</b> : enregistrent et rappellent les réglages de la séquence, par exemple un par objectif.",
    "<b>Progression</b> : photos prises, temps restant, position.",
    f"<b>{ui('▶ Avvia sequenza')}</b>, <b>{ui('Pausa')}</b>/<b>{ui('Riprendi')}</b>, <b>{ui('■ Interrompi')}</b>.",
    f"<b>{ui('Apri in Helicon Focus')}</b> : en fin de séquence, y charge toutes les photos.",
])}
<p>Les réglages de temps et de jeu se trouvent dans la section repliable <span class="ui">{ui('Tempi, gioco e nome della sessione')}</span>.
Dans le dossier des photos, l'app enregistre aussi <code>sequence.json</code>, avec les paramètres utilisés ainsi que
la position et la température de chaque photo.</p>
<h2>Pendant la séquence</h2>
{fig("sequenza-in-corso", [
    f"L'état passe à <b>{ui('In corso')}</b> (orange).",
    "Photos prises sur le total, temps restant estimé et position actuelle. Sur la barre de course, les traits des photos déjà prises changent de couleur.",
    f"<b>{ui('Pausa')}</b> suspend après la photo en cours ; <b>{ui('■ Interrompi')}</b> termine la séquence. Le <b>STOP</b> du focuser arrête aussi immédiatement le moteur.",
], layout="side narrow")}
<ul>
<li>Si vous actionnez les <b>boutons physiques</b> du focuser, la séquence se met en pause ; à la reprise, elle revient
  à la bonne position et refait la photo.</li>
<li>Les champs de la séquence sont verrouillés tant que la séquence est en cours.</li>
<li>Chaque nouvelle photo s'affiche dans {ui('Ultimo scatto')} et dans la visionneuse.</li>
</ul>
""")

# 8
add(f"""
<h1><span class="n">8</span>La visionneuse</h1>
<p>Elle s'ouvre avec <span class="ui">{ui('Apri visualizzatore ↗')}</span> ou d'un clic sur la dernière photo, dans une
fenêtre séparée que vous pouvez placer sur un second écran. Elle affiche les photos en pleine résolution (y compris
les RAW, convertis à la volée) avec zoom et déplacement, ainsi que la visée en direct de l'appareil photo.</p>
{fig("visualizzatore", [
    "<b>◀ ▶</b> photo précédente et suivante (flèches <kbd>←</kbd> <kbd>→</kbd>).",
    "Nom du fichier ; numéro de la photo, type, position, température et heure.",
    f"<b>{ui('● Live')}</b> (<kbd>L</kbd>) : la visée en direct dans la même fenêtre, avec zoom et déplacement.",
    "<b>Zoom</b> − et + (<kbd>−</kbd> <kbd>+</kbd>) et niveau d'agrandissement.",
    f"<b>{ui('Adatta')}</b> (<kbd>0</kbd>), <b>100%</b> (<kbd>1</kbd> : un pixel du capteur = un pixel de l'écran), <b>{ui('Reset')}</b> (<kbd>R</kbd>).",
    f"<b>{ui('Segui ultimo')}</b> (<kbd>U</kbd>) : affiche automatiquement chaque nouvelle photo.",
    f"<b>{ui('Blocca vista')}</b> (<kbd>K</kbd>) : conserve le zoom et la position quand vous changez de photo, pour comparer la mise au point au même endroit.",
    f"<b>{ui('Finder')}</b> : affiche le fichier dans le Finder.",
    "<b>Plein écran</b> (<kbd>F</kbd>).",
    f"<b>Vignettes</b> : un clic ouvre la photo. <i>{ui('P')}</i> = photo test, les numéros sont les photos de la séquence.",
], layout="full", anchors={n: "b" for n in range(1, 10)})}
<p>À la souris : faites glisser pour déplacer l'image, molette (ou pincement sur le trackpad) pour zoomer autour du
pointeur, double-clic pour passer de « ajuster » à 100 % et inversement. Au-delà de 150 %, les pixels restent nets,
sans flou.</p>
{fig("visualizzatore-live", [
    f"<b>{ui('■ Ferma live')}</b> revient aux photos ; ◀ ▶ ou un clic sur une vignette quittent aussi la visée en direct.",
    f"État de la visée en direct : {ui('LIVE')}, {ui('SCATTO…')}, {ui('IN PAUSA')} pendant la séquence.",
], layout="full", anchors={1: "b"}, caption="La visée en direct dans la visionneuse, ici avec le simulateur au point (le damier est net). À 100 %, la visée en direct a la résolution de l'aperçu de l'appareil photo, inférieure à celle des photos.")}
""")

# 9
add(f"""
<h1><span class="n">9</span>Limites de sécurité</h1>
<p class="lead">Les limites empêchent l'objectif de toucher la lame et la mécanique d'arriver en butée. Il faut
les définir avant tout, sans se presser.</p>
{fig("fine-corsa", [
    f"<b>{ui('Fine corsa inferiore')}</b> en pas ; <span class='ui'>{ui('⌖ Usa posizione attuale')}</span> la reprend de la position du focuser.",
    f"<b>{ui('Fine corsa superiore')}</b>. Vide = le maximum du firmware.",
    f"<b>Vers l'échantillon</b> : si, en se rapprochant de l'échantillon, le nombre de pas diminue ou augmente. Sert à étiqueter correctement {ui('Avvicina')}/{ui('Allontana')}.",
    f"<b>{ui('Salva fine corsa')}</b>.",
    f"<b>{ui('Imposta qui lo zero')}</b> : la position actuelle devient 0 ; les limites et la séquence sont décalées en conséquence.",
    f"<b>{ui('Scrivi il massimo nel firmware')}</b> : la limite supérieure devient la limite du firmware.",
], layout="full")}
<h2>Qu'est-ce qui protège quoi</h2>
<ul>
<li><b>Mouvements commandés par l'app</b> (aller à, {ui('Allontana')}/{ui('Avvicina')}, séquence, compensation du jeu) :
  l'app les vérifie <i>avant</i> de déplacer le moteur. Le mouvement continu s'arrête à la limite ; une séquence qui
  sortirait des limites ne démarre pas.</li>
<li><b>Boutons physiques</b> : l'app lit la position toutes les 0,2 à 0,5 s ; si elle sort des limites, elle envoie
  STOP et affiche l'alarme. Entre deux lectures, le moteur peut toutefois dépasser la limite de quelques dizaines de
  pas.</li>
</ul>
<h2>Protection recommandée : limites dans le firmware</h2>
<p>Le firmware applique ses limites aussi aux boutons physiques : il ne descend jamais sous 0 et ne monte jamais
au-delà de son maximum.</p>
<ol class="steps">
<li>Avec un objectif à sec et sans lame, ou avec une grande prudence, amenez la platine à la position <b>la plus
  proche de l'échantillon qui soit encore sûre</b> et cliquez sur <span class="ui">{ui('Imposta qui lo zero')}</span>.</li>
<li>Amenez la platine à la position utile la plus éloignée, cliquez sur <span class="ui">{ui('⌖ Usa posizione attuale')}</span>
  pour la limite supérieure, puis sur <span class="ui">{ui('Salva fine corsa')}</span> et sur <span class="ui">{ui('Scrivi il massimo nel firmware')}</span>.</li>
<li>Vérifiez une fois, à la main et lentement avec les boutons physiques, que le focuser s'arrête vraiment à 0 et au
  maximum.</li>
</ol>
<div class="box danger"><span class="t">Attention</span>La limite « vers l'échantillon » dépend de l'objectif et de
l'épaisseur de la lame : avec un objectif à courte distance de travail (40×, 100×), la marge est de quelques dixièmes
de millimètre. Vérifiez à nouveau les limites quand vous changez d'objectif, et après avoir changé le
<b>micropas</b>, qui modifie l'échelle des positions.</div>
""")

# 10 — mécanique
add(f"""
<h1><span class="n">10</span>Configuration mécanique : les calculs</h1>
<p class="lead">L'app raisonne en <b>pas moteur</b>. Pour vous montrer les déplacements, les courses et les pas de la
séquence en <b>micromètres</b>, et pour calculer le bon pas à partir de la profondeur de champ, elle doit savoir
combien de micromètres vaut un pas. Ce nombre s'appelle la <b>résolution</b> (µm/pas) et dépend de la façon dont le
moteur est couplé à la vis micrométrique.</p>
{fig("meccanica", [
    f"<b>Mode</b> : <i>{ui('Calcola dalla meccanica')}</i> (à partir des données ci-dessous) ou <i>{ui('Inserisci µm/passo')}</i> (une valeur mesurée).",
    f"<b>{ui('Passi motore per giro')}</b> : 200 pour un moteur de 1,8°, 400 pour un moteur de 0,9°.",
    f"<b>{ui('Microstep')}</b> : lu dans le firmware, il ne se modifie pas ici (voir {ui('Motore (firmware)')}).",
    f"<b>{ui('Rapporto di riduzione')}</b> : combien de tours fait le moteur pour un tour de molette.",
    f"<b>{ui('Corsa per giro manopola (µm)')}</b> : de combien de µm la platine se déplace à chaque tour de la molette micrométrique.",
    "<b>Résultat</b> : µm par pas, pas par µm, µm pour 1000 pas.",
    f"<b>{ui('Salva meccanica')}</b>.",
])}
<h2>10.1 La chaîne de transmission</h2>
<p>Du moteur à la platine, le mouvement passe par plusieurs étages, et chacun multiplie ou divise :</p>
{diagram(DIAGRAM_LABELS)}
<div class="formula">
  résolution (µm/pas) = {frac("course par tour de molette (µm)", "pas par tour × micropas × rapport de réduction")}
  <span class="lbl">C'est exactement le calcul que fait l'app en mode « {ui('Calcola dalla meccanica')} ».</span>
</div>
<h2>10.2 Les quatre nombres, un par un</h2>
<h3>Pas moteur par tour</h3>
<p>Il se déduit de l'angle de pas indiqué sur l'étiquette ou la fiche technique du moteur :</p>
<div class="formula">pas par tour = {frac("360°", "angle de pas")}
<span class="lbl">1,8° → 200 pas · 0,9° → 400 pas · 7,5° → 48 pas</span></div>
<p>Le NEMA 14 OMC 14HM11-0404S du focuser myFocuserPro2 est un moteur de 0,9° : <b>400</b>. Le NEMA 17
17HS13-0404S-PG27 avec réducteur est un moteur de 1,8° : <b>200</b>, et le réducteur entre dans le rapport
(ci-dessous), pas ici.</p>
<h3>Micropas</h3>
<p>Le driver peut diviser chaque pas en 2, 4, 8, 16 ou 32 micropas. En micropas 1/8, un tour du moteur demande 8 fois
plus de pas et la résolution devient 8 fois plus fine (mais le couple par micropas diminue et la vitesse maximale en
µm/s est divisée par 8).</p>
<ul>
<li><b>myFocuserPro2</b> : le micropas est défini par le firmware et se change dans {ui('Configurazione')} ›
  {ui('Motore (firmware)')}. L'app le lit et l'utilise toute seule dans le calcul.</li>
<li><b>Ardufocus</b> : le micropas est fixé sur la carte (cavaliers ou câblage du driver) et le firmware ne le
  commande pas. Indiquez dans {ui('Configurazione')} › {ui('Motore (firmware)')} <b>la même valeur que sur la carte</b>,
  sinon le calcul est faux du même facteur. Si vous ne la connaissez pas, mesurez-la (10.4).</li>
</ul>
<h3>Rapport de réduction</h3>
<p>C'est le nombre de tours du moteur pour <b>un</b> tour de la molette. Tous les étages se multiplient entre eux :</p>
<div class="formula">rapport = réducteur × {frac("dents de la poulie sur la molette", "dents de la poulie sur le moteur")}
<span class="lbl">avec des roues à friction ou des joints toriques : les diamètres à la place des dents</span></div>
<ul>
<li><b>Couplage direct</b> (moteur sur l'axe de la molette, sans réducteur) : rapport 1.</li>
<li><b>Courroie crantée</b> d'une poulie GT2 de 20 dents sur le moteur à une poulie de 60 dents sur la molette :
  60 ÷ 20 = <b>3</b>.</li>
<li><b>Réducteur planétaire</b> : le rapport indiqué sur le moteur. Le PG27 du 17HS13 vaut 26 103/121 = 26 + 103 ÷ 121
  = <b>26,851</b> (pas exactement 27 : utilisez la valeur précise). En couplage direct, le rapport est 26,851 ; avec
  une courroie 20 → 40 dents, il devient 26,851 × 2 = 53,70.</li>
</ul>
<h3>Course par tour de molette</h3>
<p>De combien se déplace la platine (ou le tube, sur les microscopes qui déplacent l'objectif) à chaque tour de la
molette entraînée par le moteur, en général la <b>vis micrométrique</b>. Beaucoup de microscopes font 100 µm par
tour, certains 200 µm ou d'autres valeurs. Le plus sûr pour le savoir est de compter les graduations de la molette :</p>
<div class="formula">course par tour = nombre de graduations sur la molette × µm par graduation
<span class="lbl">exemple : 100 graduations de 1 µm = 100 µm par tour · 50 graduations de 2 µm = 100 µm par tour</span></div>
<p>La valeur d'une graduation est souvent gravée sur la molette ou sur le statif du microscope (« 1 µm », « 2 µm »)
ou indiquée dans le manuel. Si le moteur entraîne la <b>vis macrométrique</b> au lieu de la vis micrométrique, la
course par tour est de plusieurs millimètres : la résolution est beaucoup plus grossière et doit être vérifiée
avec soin.</p>

<h2>10.3 Exemples détaillés</h2>
<h3>Exemple A : myFocuserPro2 avec NEMA 14 et courroie</h3>
<div class="calc">moteur 0,9°              → pas par tour = 360 ÷ 0,9 = 400
micropas                 → 1 (pas entier)
poulies 20 → 60 dents    → rapport = 60 ÷ 20 = 3
vis micrométrique        → 100 µm par tour

pas par tour de molette = 400 × 1 × 3 = 1 200
résolution = 100 ÷ 1 200 = <b>{num(UA, 4)} µm/pas</b>   (12 pas = 1 µm ; 1000 pas = {num(UA * 1000, 1)} µm)</div>
<p>C'est la configuration utilisée pour les captures d'écran de ce guide. En micropas 1/8, le même focuser donnerait
100 ÷ (400 × 8 × 3) = <b>{num(um_step(100, 400, 8, 3), 4)} µm/pas</b>.</p>
<h3>Exemple B : Ardufocus avec NEMA 17 et réducteur PG27</h3>
<div class="calc">moteur 1,8°              → pas par tour = 200
micropas (sur la carte)  → 1
réducteur 26 103/121     → 26,851, couplage direct à la molette
vis micrométrique        → 100 µm par tour

pas par tour de molette = 200 × 1 × 26,851 = {num(200 * GEAR17, 0)}
résolution = 100 ÷ {num(200 * GEAR17, 0)} = <b>{num(UB, 4)} µm/pas</b>   (1 µm = {num(1 / UB, 1)} pas)</div>
<p>Le réducteur rend la résolution environ 4,5 fois plus fine que dans l'exemple A et donne beaucoup plus de couple,
mais il faut beaucoup plus de pas pour le même déplacement : c'est pourquoi l'app permet des tailles de pas jusqu'à
100 000 pas (chapitre 12).</p>

<h2>10.4 Vérifier par une mesure</h2>
<p>Le calcul est valable si toutes les données sont justes et si rien ne patine (courroie détendue, poulie qui tourne
sur son axe). Une vérification est toujours utile, et indispensable si vous ne connaissez pas l'un des nombres.</p>
<h3>Avec les graduations de la vis micrométrique</h3>
<ol class="steps">
<li>Approchez toujours depuis la même direction (pour éliminer le jeu) : faites quelques centaines de pas dans un
  sens, puis notez la graduation de la molette alignée sur le repère.</li>
<li>Avec <span class="ui">{ui('Vai alla posizione…')}</span>, déplacez d'un grand nombre de pas <b>N</b>, dans le même
  sens, de sorte que la molette fasse au moins un demi-tour (exemple A : N = 1000 ; exemple B : N = 5000).</li>
<li>Comptez les graduations parcourues <b>T</b> et multipliez par les µm par graduation.</li>
</ol>
<div class="formula">résolution mesurée = {frac("T × µm par graduation", "N")}</div>
<div class="calc">Exemple A : N = 1000 pas, la molette avance de 83 graduations de 1 µm
résolution = 83 × 1 ÷ 1000 = <b>0,083 µm/pas</b>   (le calcul donnait {num(UA, 4)} : cela concorde)</div>
<h3>Avec un comparateur</h3>
<p>Un comparateur au 1/100 ou au 1/1000 de mm posé sur la platine mesure directement le déplacement. Déplacez de
N pas (toujours depuis la même direction) et divisez le déplacement en µm par N. Plus N est grand, plus la mesure
est précise.</p>
<h3>Si la mesure ne concorde pas</h3>
<ul>
<li>Écart d'un facteur 2, 4, 8, 16 : le <b>micropas</b> n'est pas celui que vous croyez (typique de l'Ardufocus).</li>
<li>Écart d'un facteur 2 exactement : moteur de 0,9° pris pour un 1,8° ou inversement.</li>
<li>Écart irrégulier, qui change d'une mesure à l'autre : quelque chose <b>patine</b> (courroie, vis de blocage de la
  poulie) ou le moteur <b>perd des pas</b> (vitesse trop élevée, courant trop faible).</li>
<li>Si les données mécaniques sont incertaines mais que la mesure est reproductible, choisissez
  <span class="ui">{ui('Inserisci µm/passo')}</span> et saisissez la valeur mesurée.</li>
</ul>
{fig("meccanica-manuale", [
    f"<b>{ui('Inserisci µm/passo')}</b> : pour utiliser une valeur mesurée.",
    f"<b>{ui('µm per passo')}</b> mesurés.",
    "Le résultat se met à jour pendant la saisie.",
], layout="side narrow")}

<h2>10.5 Autres calculs utiles</h2>
<h3>Course utile en millimètres</h3>
<div class="calc">course (µm) = (limite supérieure − limite inférieure) × résolution
exemple A : (45 000 − 2 000) × {num(UA, 4)} = <b>{num(43000 * UA, 0)} µm ≈ {num(43000 * UA / 1000, 2)} mm</b></div>
<h3>Vitesse en µm par seconde</h3>
<div class="calc">vitesse (µm/s) = pas par seconde × résolution
exemple A, firmware à 400 pas/s :   400 × {num(UA, 4)} ≈ <b>{num(400 * UA, 0)} µm/s</b>
exemple B, firmware à 2000 pas/s : 2000 × {num(UB, 4)} ≈ <b>{num(2000 * UB, 0)} µm/s</b></div>
<p>Cela permet d'estimer la durée d'un long déplacement : 1 mm dans l'exemple A demande environ
{num(1000 / (400 * UA), 0)} secondes.</p>
<h3>Le jeu (backlash) en pas</h3>
<p>Quand le moteur inverse le sens, la molette ne bouge pas pendant quelques pas : c'est le <b>jeu</b> de la
transmission (courroie, dents, réducteur, filetage de la vis micrométrique). Il se compense en pas, il vaut donc
mieux le mesurer en pas :</p>
<ol class="steps">
<li>Ouvrez la visée en direct dans la visionneuse à 100 % ou plus, sur un détail petit et bien contrasté.</li>
<li>Déplacez de quelques centaines de pas dans un sens, puis inversez avec une taille de pas de 1 ou 10.</li>
<li>Comptez les pas après l'inversion avant que l'image commence à bouger : c'est le jeu. Répétez quelques fois et
  retenez la valeur la plus élevée, avec une petite marge.</li>
</ol>
<p>Le jeu angulaire annoncé donne un ordre de grandeur. Le réducteur PG27 annonce au maximum 1° de jeu en sortie,
soit 1/360 de tour de molette :</p>
<div class="calc">jeu en pas = (1° ÷ 360°) × pas par tour de molette = {num(200 * GEAR17, 0)} ÷ 360 ≈ <b>{num(200 * GEAR17 / 360, 0)} pas</b>
jeu en µm  = (1° ÷ 360°) × 100 µm ≈ <b>{num(100 / 360, 2)} µm</b></div>
<p>Le jeu de la courroie et de la vis micrométrique s'y ajoute : la mesure en visée en direct reste la donnée fiable.
La valeur va ensuite à <b>un seul</b> des deux endroits : la <b>compensation de la séquence</b> (chapitre 7) ou le
<b>jeu IN/OUT du firmware</b> (chapitre 12, 255 pas au maximum), pas les deux.</p>
<h3>Quelle finesse de résolution faut-il</h3>
<p>Le pas de la séquence (chapitre 11) devrait valoir au moins une dizaine de pas moteur, pour que les arrondis au pas
entier comptent peu. Avec l'exemple A et un objectif 60×, le pas conseillé est d'environ 7 pas : c'est faisable,
mais pour les objectifs très puissants, une résolution plus fine (micropas ou réduction plus forte) est
préférable.</p>
""")

# 11 — pas de la séquence
add(f"""
<h1><span class="n">11</span>Choisir le pas de la séquence</h1>
<p class="lead">Chaque photo n'est nette que dans une fine tranche de l'échantillon, la <b>profondeur de champ</b>.
Pour que tout soit net après le stacking, la mise au point ne doit pas se déplacer de plus que cette tranche entre une
photo et la suivante, avec un peu de chevauchement.</p>
{fig("profondita", [
    f"<b>{ui('Apertura numerica (NA)')}</b> : le second nombre gravé sur l'objectif (10×/<b>0,25</b>).",
    f"<b>{ui('Ingrandimento sul sensore')}</b> : grossissement de l'objectif × facteur de l'adaptateur de l'appareil photo.",
    f"<b>{ui('Pixel del sensore (µm)')}</b>. Nikon D5600 : <b>3,9 µm</b> (23,5 mm ÷ 6000 pixels).",
    f"<b>{ui('Sovrapposizione (%)')}</b> entre une tranche nette et la suivante ; 20 à 30 % est une bonne valeur.",
    "<b>Résultat</b> : profondeur de champ, pas conseillé en µm et en pas moteur.",
    f"<b>{ui('Usa come passo della sequenza')}</b> : copie la valeur en pas dans le champ Pas de la séquence.",
])}
<h2>11.1 La formule</h2>
<p>L'app utilise la formule de Berek, la plus utilisée en microscopie :</p>
<div class="formula">profondeur de champ (µm) = {frac("λ · n", "ON²")} + {frac("n · e", "M · ON")}
<span class="lbl">λ = longueur d'onde = 0,55 µm (lumière verte) · n = indice du milieu entre objectif et lame = 1 (air) ·
e = taille du pixel du capteur (µm) · M = grossissement sur le capteur · ON = ouverture numérique</span></div>
<p>Le premier terme est la limite de l'optique (diffraction), le second celle du capteur. Ensuite :</p>
<div class="formula">pas (µm) = profondeur de champ × (1 − chevauchement) &nbsp;&nbsp;&nbsp; pas (pas moteur) = {frac("pas (µm)", "résolution (µm/pas)")}</div>
<h3>Exemple détaillé : objectif 10×/0,25, Nikon D5600, adaptateur 1×</h3>
<div class="calc">premier terme  = 0,55 × 1 ÷ 0,25²       = 0,55 ÷ 0,0625 = 8,80 µm
second terme   = 1 × 3,9 ÷ (10 × 0,25)  = 3,9 ÷ 2,5     = 1,56 µm
profondeur de champ = 8,80 + 1,56 = <b>10,36 µm</b>
pas avec 30 % de chevauchement = 10,36 × 0,70 = <b>7,25 µm</b>
en pas, exemple A : 7,25 ÷ {num(UA, 4)} = 87,0 → <b>87 pas</b>   exemple B : 7,25 ÷ {num(UB, 4)} → <b>{max(1, round(dof(.25, 10, 3.9) * .7 / UB))} pas</b></div>
<h3>Valeurs typiques (D5600, adaptateur 1×, chevauchement 30 %)</h3>
{table(["Objectif", "Profondeur de champ (µm)", "Pas (µm)", "Pas moteur, exemple A", "Pas moteur, exemple B"], dof_rows, right=(1, 2, 3, 4))}
<p style="font-size:9pt;color:#5a6b80">Exemple A = {num(UA, 4)} µm/pas ; exemple B = {num(UB, 4)} µm/pas (section 10.3). Remarque : {dof_note}</p>
<div class="box tip"><span class="t">L'adaptateur de l'appareil photo</span>Si l'adaptateur a un facteur différent de 1
(par exemple 0,5× ou 2,5×), multipliez le grossissement de l'objectif par ce facteur : 10× avec un adaptateur 0,5×
= 5 sur le capteur. Seul le second terme de la formule change, et il compte davantage avec les objectifs faibles.</div>

<h2>11.2 Début, fin et nombre de photos</h2>
<ol class="steps">
<li>Activez la visée en direct (de préférence dans la visionneuse, zoomée) et amenez la mise au point <b>juste
  au-dessus</b> de la partie la plus haute du sujet que vous voulez net : cliquez sur <span class="ui">{ui('⌖ qui')}</span>
  à côté de <b>{ui('Inizio')}</b>.</li>
<li>Descendez <b>juste en dessous</b> de la partie la plus basse et cliquez sur <span class="ui">{ui('⌖ qui')}</span> à côté
  de <b>{ui('Fine')}</b>.</li>
<li>Saisissez le pas (ou utilisez <span class="ui">{ui('Usa come passo della sequenza')}</span>) : l'app calcule le nombre de photos.</li>
</ol>
<div class="formula">nombre de photos = {frac("|fin − début|", "pas")} + 1
<span class="lbl">arrondi à l'entier inférieur, plus une photo finale exactement sur la fin si la division ne tombe pas juste</span></div>
<div class="calc">exemple : début 24 000, fin 26 000, pas 87
2000 ÷ 87 = 22,99 → 22 + 1 = 23, plus la photo finale à 26 000 = <b>24 photos</b>
course = 2000 × {num(UA, 4)} = <b>{num(2000 * UA, 1)} µm</b></div>
<p>À l'inverse, si vous saisissez le <b>nombre de photos</b>, l'app recalcule le pas : pas = course ÷ (photos − 1),
arrondi au pas entier.</p>
<h2>11.3 Durée estimée</h2>
<p>Pour chaque photo, l'app additionne :</p>
<div class="formula">attente après le mouvement + pause après la photo + temporisation miroir + temps de pose + 1,5 s + {frac("pas", "400")} s</div>
<p>où 1,5 s est une estimation du temps de déclenchement et de transfert, et pas ÷ 400 le temps de déplacement. Avec
l'exemple (1,5 s + 0,5 s + 0 + 1/60 s + 1,5 s + 0,22 s ≈ 3,7 s par photo × 24 photos), la durée est d'environ
<b>une minute et demie</b>, comme sur la capture d'écran du chapitre 7. Pendant la séquence, l'estimation est mise à
jour avec les temps réels.</p>
<div class="box warn"><span class="t">L'attente après le mouvement compte</span>Un microscope vibre un moment après
chaque déplacement. Si les photos sont floues ou « doublées », augmentez l'attente (2 à 3 s) et, sur les reflex, la
temporisation du miroir, avant de chercher d'autres causes.</div>
""")

# 12
add(f"""
<h1><span class="n">12</span>Moteur, commandes manuelles, mises à jour, température</h1>
<h2>{ui('Motore (firmware)')}</h2>
{fig("motore", [
    f"<b>{ui('Microstep')}</b> : {ui('passo intero')}, 1/2 … 1/32 (voir 10.2). Le modifier change l'échelle des positions : vérifiez ensuite à nouveau les limites.",
    f"<b>{ui('Velocità')}</b> du firmware : {ui('Lenta').lower()}, {ui('Media').lower()}, {ui('Veloce').lower()}.",
    f"<b>{ui('Bobine alimentate a motore fermo')}</b> : le moteur maintient sa position, mais chauffe.",
    f"<b>{ui('Inverti verso di rotazione')}</b>.",
    f"<b>{ui('Compensa il gioco IN')} / OUT</b> : à chaque inversion vers des positions plus basses (IN) ou plus hautes (OUT), le firmware ajoute des pas sans les compter, y compris avec les boutons physiques.",
    "<b>Jeu IN / OUT</b> en pas, de 0 à 255 (voir 10.5).",
    f"<b>{ui('Rileggi')}</b> les valeurs du firmware.",
])}
<h2>{ui('Comandi manuali')}</h2>
{fig("comandi-manuali", [
    f"<b>Tailles de pas</b> des boutons {ui('Allontana')}/{ui('Avvicina')} : par puissances de dix jusqu'à 1000, 10 000 ou 100 000 pas. Avec un réducteur, il faut de grandes tailles de pas.",
    f"<b>{ui('Tieni premuto per muovere senza fermarti')}</b> : au relâchement, le moteur ralentit et s'arrête ; il s'arrête de toute façon à la limite et, si la page ne répond plus, après environ une seconde.",
], layout="side")}
<h2>{ui('Aggiornamenti')}</h2>
{fig("aggiornamenti", [
    "Version de l'<b>app</b> et résultat de la dernière vérification.",
    "Version du <b>firmware</b> sur le focuser.",
    f"<b>{ui('Aggiorna firmware')}</b> : environ 20 secondes, les réglages du focuser sont conservés. Ne débranchez pas le câble ; en cas de problème, il suffit de recommencer.",
    f"<b>{ui('Controlla ora')}</b> s'il existe des mises à jour de l'app.",
], layout="side")}
<p>L'app choisit toute seule le firmware adapté à la carte (myFocuserPro2 ou Ardufocus). L'<b>Ardufocus</b> ne
redémarre pas par le câble USB : pendant la mise à jour, l'app vous demande d'appuyer sur le <b>bouton reset</b> de la
carte.</p>
<h2>{ui('Temperatura')}</h2>
{fig("temperatura", [
    "Température actuelle de la sonde.",
    "Évolution sur les 60 dernières minutes. La température de chaque photo est enregistrée dans <code>sequence.json</code> : utile, car la mise au point dérive avec la dilatation thermique.",
], layout="side")}
""")

# 13
add(f"""
<h1><span class="n">13</span>Une session type, étape par étape</h1>
<h2>Une seule fois (ou quand la mécanique change)</h2>
<ol class="steps">
<li><b>Mécanique</b> : saisissez les données et vérifiez la résolution par une mesure (chapitre 10).</li>
<li><b>Sens de l'échantillon</b> et <b>limites</b>, avec les limites écrites dans le firmware (chapitre 9).</li>
<li><b>Jeu</b> : mesurez-le avec la visée en direct et choisissez où le compenser (séquence ou firmware).</li>
<li><b>Préréglages</b> : pour chaque objectif, calculez le pas à partir de la profondeur de champ et enregistrez un préréglage.</li>
</ol>
<h2>À chaque session</h2>
<ol class="steps">
<li>Allumez le focuser et l'appareil photo (mode M), branchez les câbles et ouvrez Focus Stack.</li>
<li>Connectez le focuser et l'appareil photo depuis l'onglet {ui('Sessione')}.</li>
<li>Réglez le temps de pose, l'ISO et le format ; faites une <b>photo test</b> et contrôlez-la dans la visionneuse à 100 %.</li>
<li>Choisissez le <b>préréglage</b> de l'objectif (ou le pas).</li>
<li>Avec la <b>visée en direct</b> et le clavier, trouvez la <b>fin</b> et le <b>début</b> de la séquence et cliquez sur {ui('⌖ qui')}.</li>
<li>Contrôlez le récapitulatif : nombre de photos, course, durée, aucun avertissement rouge.</li>
<li><b>{ui('▶ Avvia sequenza')}</b>. Ne touchez pas le microscope : les vibrations gâchent les photos.</li>
<li>En fin de séquence, cliquez sur <b>{ui('Apri in Helicon Focus')}</b>.</li>
</ol>
""")

# 14
add(f"""<h1><span class="n">14</span>En cas de problème</h1>
<p>Le <b>{ui('Registro')}</b> (troisième onglet) liste avec l'heure chaque connexion, déplacement, photo et erreur : en
cas de problème, lisez-le en premier.</p>
""")
add(table(["Problème", "Que faire"], [
    ["L'appareil photo ne se connecte pas", "Quittez Photos, Aperçu, Transfert d'images, NX Studio, EOS Utility ; débranchez et rebranchez le câble avec l'appareil allumé ; vérifiez qu'il est en mode M et que le Wi-Fi/SnapBridge est désactivé."],
    ["La visée en direct ne démarre pas (Nikon D5600)", f"Molette sur <b>M</b> (avec les modes scène, la visée en direct par USB peut être bloquée), carte insérée, batterie chargée, affichage des images désactivé. Le message exact apparaît en bas et dans le <b>{ui('Registro')}</b> (« Visée en direct interrompue : … ») : c'est la première chose à regarder. Vérifiez aussi que vous avez la dernière version de l'app."],
    ["La visée en direct est lente avec deux fenêtres ouvertes", "Mettez l'app à jour : depuis la version 1.0.6, la fenêtre principale et la visionneuse reçoivent toutes les images."],
    ["Le focuser n'apparaît pas dans la liste des ports", "Cliquez sur ⟳ après avoir branché le câble ; essayez une autre prise USB ou un autre câble (certains câbles servent uniquement à la recharge)."],
    ["Le moteur vibre mais ne tourne pas, ou perd des pas", "Vitesse trop élevée pour la charge ou courant du driver trop faible ; vérifiez aussi que la poulie ne patine pas sur son axe."],
    ["Les distances en µm ne concordent pas", "Refaites la mesure de la section 10.4 ; pour l'Ardufocus, vérifiez le micropas."],
    ["Alarme rouge « hors des limites »", f"Un bouton physique a amené le focuser au-delà d'une limite. Ramenez la position dans les limites avec {ui('Allontana')}/{ui('Avvicina')} ; pour l'éviter, écrivez les limites dans le firmware (chapitre 9)."],
    ["La séquence ne démarre pas", "Lisez l'avertissement rouge dans le récapitulatif : en général, la séquence, compensation du jeu comprise, sort des limites."],
    ["Photos floues ou doublées", "Augmentez l'attente après le mouvement et la temporisation du miroir ; utilisez la pose B ou le déclenchement silencieux si l'appareil le permet."],
    [f"« {ui('Focus Stack è chiuso')} » dans la page", "L'app a été fermée : rouvrez-la et la page se recharge toute seule."],
]))

# 15
add(f"""<h1><span class="n">15</span>Raccourcis clavier</h1>
<div class="two">
<div class="keep"><h2 style="margin-top:0">Onglet {ui('Sessione')}</h2>
<table><tbody>
<tr><td><kbd>↑</kbd></td><td>éloigner l'objectif de l'échantillon</td></tr>
<tr><td><kbd>↓</kbd></td><td>rapprocher l'objectif de l'échantillon</td></tr>
<tr><td><kbd>⇧</kbd> + <kbd>↑</kbd>/<kbd>↓</kbd></td><td>pas × 10</td></tr>
<tr><td><kbd>1</kbd> <kbd>2</kbd> <kbd>3</kbd> …</td><td>taille du pas : 1, 10, 100 …</td></tr>
<tr><td><kbd>Esc</kbd></td><td>STOP</td></tr>
</tbody></table></div>
<div class="keep"><h2 style="margin-top:0">{ui('Visualizzatore')}</h2>
<table><tbody>
<tr><td><kbd>←</kbd> <kbd>→</kbd></td><td>photo précédente / suivante</td></tr>
<tr><td><kbd>L</kbd></td><td>visée en direct activée / désactivée</td></tr>
<tr><td><kbd>−</kbd> <kbd>+</kbd></td><td>zoom</td></tr>
<tr><td><kbd>0</kbd> ou <kbd>R</kbd></td><td>ajuster à la fenêtre</td></tr>
<tr><td><kbd>1</kbd></td><td>100 %</td></tr>
<tr><td><kbd>U</kbd></td><td>suivre la dernière photo</td></tr>
<tr><td><kbd>K</kbd></td><td>figer la vue</td></tr>
<tr><td><kbd>F</kbd></td><td>plein écran</td></tr>
</tbody></table></div>
</div>
<p style="margin-top:8mm;color:#5a6b80;font-size:9pt">Focus Stack est un logiciel libre (licence MIT) ·
github.com/teoteo/focus-stack · Le firmware est dérivé de myFocuserPro2 de Robert Brown (licence MIT).</p>
""")
