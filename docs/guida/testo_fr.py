"""Texte français du guide. Ce n'est pas un module à importer : genera_guida.py l'exécute avec exec() dans un
espace de noms qui contient déjà les fonctions et les nombres communs (fig, frac, table, num, diagram, VERSION,
ICON, IMG, UA, UB, GEAR17, um_step, dof, OBJ, APP). Le texte remplit la liste H avec les sections HTML.
"""
# ruff: noqa: F821  (les noms viennent de genera_guida.py)

META = {
    "lang": "fr",
    "title": "Focus Stack — Guide d'utilisation",
    "footer": "Guide d'utilisation",
    "pdf": "FR Focus Stack - Guide.pdf",
}


def ui(s):
    """Nom français d'une commande de l'app (le texte italien est la clé) : le même que dans l'app."""
    return APP.get(s, s)


# nome dell'opzione con l'apostrofo: in una costante, perché Python 3.11 non accetta virgolette annidate nelle f-string
COIL_HOLD = "Anche quando viene disconnesso o si spegne l'applicazione"


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

# schema «Come li usa la fusione» (7.6): etichette dello SVG, testo semplice (&lt; per <)
CALIB_LABELS = {
    "col_dark": 'MASTER DARK',
    "col_stack": 'PILE DU SUJET',
    "col_flat": 'MASTER FLAT',
    "dark": 'Darks · N vues',
    "dark1": 'bouchon, mêmes ISO et temps',
    "mean": 'moyenne pixel par pixel',
    "D": 'D : master dark',
    "flat": 'Flats · N vues',
    "flat1": 'champ uniforme, même optique',
    "flat_mean": 'moyenne − darks des flats',
    "norm": '÷ sa propre moyenne',
    "F": 'F : flat normalisé',
    "F1": '&lt; 1 au bord et sur la poussière',
    "frame": 'Chaque image I',
    "frame1": 'RAW, lumière linéaire',
    "fusion": 'alignement et fusion',
    "note1": 'Sans darks, pas de soustraction ;',
    "note2": 'sans flats, pas de division.',
}

# grafico d'esempio dell'analisi del sensore (7.6)
SENSOR_LABELS = {
    "title_dr": 'Plage dynamique (IL)',
    "title_rn": 'Bruit de lecture (électrons)',
    "unreliable": 'pas fiable',
    "stops": 'IL',
    "dcg1": 'double gain :',
    "dcg2": 'de 3,0 à 1,2 e-',
    "dec": ',',
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
  <div class="shot-c"><img src="{IMG}/sessione.jpg" alt=""></div>
  <div class="meta"><span>Version de l'app {VERSION}</span><span>Novembre 2026</span></div>
</section>
""")

add("""
<h1 style="break-before:auto">Sommaire</h1>
<div class="toc"><ol>
<li><span>1</span>Qu'est-ce que Focus Stack<em>principe de fonctionnement, matériel nécessaire</em></li>
<li><span>2</span>Installation, lancement et mises à jour</li>
<li><span>3</span>L'interface en bref<em>les cinq onglets, la barre supérieure et le guide</em></li>
<li><span>4</span>Connecter le focuser et l'appareil photo<em>réglages du Nikon D5600 et des autres appareils</em></li>
<li><span>5</span>Le focuser : position, déplacements, STOP<em>mouvement continu par tronçons, la glissière qui n'avance pas</em></li>
<li><span>6</span>Appareil photo, photo test et visée en direct</li>
<li><span>7</span>La séquence de stacking<em>profils optiques, macro photographique, plusieurs prises par position, les fichiers de la pile,
calibration (darks, flats, exposition), suivi sur smartphone</em></li>
<li><span>8</span>La visionneuse<em>zoom, visée en direct, autofocus sur un point, Inspecteur</em></li>
<li><span>9</span>Limites de sécurité</li>
<li><span>10</span>Configuration mécanique : les calculs<em>résolution en µm par pas, mesure de contrôle, course, vitesse, jeu</em></li>
<li><span>11</span>Choisir le pas de la séquence<em>profondeur de champ, nombre de photos, durée</em></li>
<li><span>12</span>Moteur, commandes manuelles, autofocus, mises à jour, température</li>
<li><span>13</span>Une session type, étape par étape</li>
<li><span>14</span>En cas de problème</li>
<li><span>15</span>Raccourcis clavier</li>
</ol></div>
""")

# 1
add(f"""
<h1><span class="n">1</span>Qu'est-ce que Focus Stack</h1>
<p class="lead">Focus Stack pilote depuis le Mac un focuser motorisé, monté sur la vis micrométrique du microscope
ou sur une glissière macro, et un appareil photo connecté en USB. Il exécute automatiquement des séquences <b>déplacer → attendre →
déclencher</b> : des dizaines de photos à des mises au point différentes, prêtes à être fusionnées en une seule
image entièrement nette avec <b>Helicon Focus</b> (ou un programme similaire).</p>
<h2>Principe de fonctionnement</h2>
<p>L'app Focus Stack lance sur le Mac un petit programme (le <i>serveur</i>) qui dialogue avec le focuser (une
carte Arduino équipée du firmware myFocuserPro2) et avec l'appareil photo. L'interface s'ouvre dans la
<b>fenêtre de l'app</b> : c'est une page web servie à l'adresse <code>http://localhost:8765</code>, accessible
uniquement depuis ce Mac (on peut aussi l'ouvrir dans un navigateur).</p>
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
<li>Un Mac sous macOS 13 ou ultérieur (Intel) ou macOS 14 ou ultérieur (Apple Silicon).</li>
<li>Un focuser <b>myFocuserPro2</b> (version avec pilote DRV8825) ou <b>Ardufocus</b> (carte rev1 avec DRV8825),
  connecté par son câble USB et alimenté (12 V).</li>
<li>Un appareil photo Nikon, Canon ou Sony avec son câble USB. Dans ce guide, l'exemple est un <b>Nikon D5600</b>.</li>
<li>Au microscope, un adaptateur qui projette l'image sur le capteur (phototube, bague T2 ou similaire). En
  <b>macro photographique</b>, un objectif macro (avec d'éventuels tubes ou bonnettes) et une glissière déplacée par
  le focuser.</li>
</ul>
<div class="box warn"><span class="t">Focusers pris en charge</span>Focus Stack fonctionne avec les cartes
<b>myFocuserPro2</b> et <b>Ardufocus</b>, avec le firmware fourni avec l'app. Un myFocuserPro2 avec son firmware d'origine
se connecte tout de suite et l'app propose de le mettre à jour en un clic. Un Ardufocus avec son firmware d'origine
(protocole Moonlite) n'est en revanche pas reconnu : la première fois, le firmware de Focus Stack doit être chargé à la
main (instructions dans le README sur github.com/teoteo/focus-stack) ; ensuite, l'Ardufocus se met lui aussi à jour
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
<li>Au lancement, Focus Stack ouvre sa fenêtre et reste dans le Dock. Fermer la fenêtre (<kbd>⌘W</kbd>) ne fait
  que la masquer : l'app reste ouverte et un clic sur l'icône du Dock la ramène. Le visualiseur et le guide
  s'ouvrent dans des fenêtres séparées ; les liens vers des sites externes s'ouvrent dans le navigateur.</li>
<li>Pour quitter : <kbd>⌘Q</kbd> dans l'app, ou <span class="ui">Quitter</span> dans le menu de l'icône du Dock.
  Si une séquence est en cours, l'app demande confirmation, l'interrompt et arrête le moteur.</li>
<li>Pendant une pile ou une série de calibration, l'icône du Dock affiche une <b>barre de progression</b>. Quand
  elle se termine, ou s'arrête sur une erreur, pendant que vous utilisez une autre app, une <b>notification</b>
  arrive : la première fois, macOS demande l'autorisation.</li>
</ul>
<h2>Mises à jour</h2>
<p>Au lancement, puis toutes les 6 heures, l'app vérifie s'il existe une nouvelle version. Si c'est le cas, une
barre avec <span class="ui">{ui("Aggiorna e riavvia")}</span> apparaît en haut : l'app télécharge la nouvelle version,
se ferme et se rouvre toute seule. La même vérification peut se faire à la main dans
<span class="ui">{ui("Configurazione")} › {ui("Aggiornamenti")} › {ui("Controlla ora")}</span>.</p>
<p>Le <b>firmware du focuser</b> se met lui aussi à jour depuis l'app (chapitre 12) : quand celui de la carte est
plus ancien que celui fourni avec l'app, la même barre le signale. Il vaut la peine de l'installer : la build 5, par
exemple, rend le mouvement continu sans arrêts et arrête toute seule le moteur si le Mac cesse de communiquer (chapitre 12).</p>
<h2>Langue</h2>
<p>L'app parle italien, anglais, français, allemand et espagnol. Avec <span class="ui">{ui("Automatica (lingua del sistema)")}</span>
elle suit la langue de macOS, et utilise l'anglais pour les autres langues ; dans
<span class="ui">{ui("Configurazione")} › {ui("Lingua")}</span> vous pouvez choisir une langue fixe. Le choix s'applique à
l'interface, aux messages et au journal, et ce guide existe dans les mêmes langues.</p>
""")

# 3
add(f"""
<h1><span class="n">3</span>L'interface en bref</h1>
<p>La page comporte cinq onglets, que l'on choisit en haut :</p>
<ul>
<li><b>{ui("Sessione")}</b> : le travail au microscope. Focuser, séquence, appareil photo et dernière photo.</li>
<li><b>{ui("Ottica")}</b> : les <b>profils</b> d'objectif, de filtre et d'éclairage, pour le microscope ou pour la macro
  photographique, qui sont enregistrés dans les données de chaque pile, et le calcul de la profondeur de champ
  (chapitres 7.2, 7.3 et 11).</li>
<li><b>{ui("Calibrazione")}</b> : l'exposition des lights et les images de calibration (darks, flats, darks des flats) pour
  le logiciel de fusion (chapitre 7.6).</li>
<li><b>{ui("Configurazione")}</b> : limites, mécanique, commandes manuelles, moteur, suivi sur smartphone, langue,
  mises à jour et température. On le règle une fois, puis on y touche rarement.</li>
<li><b>{ui("Registro")}</b> : la liste horodatée de tout ce qui s'est passé pendant la session. C'est le premier
  endroit à consulter en cas de problème.</li>
</ul>
{fig("sessione", layout="full", caption="L'onglet Session : à gauche le focuser, au centre la séquence, à droite l'appareil photo et la dernière photo.")}
<h2>Barre supérieure</h2>
{fig("barra-superiore", [
    f"<b>Onglets</b> {ui('Sessione')}, {ui('Ottica')}, {ui('Calibrazione')}, {ui('Configurazione')} et {ui('Registro')}.",
    f"<b>État des connexions</b> : {ui('Server')}, {ui('Focheggiatore')} et {ui('Fotocamera')}. Vert = connecté, gris = déconnecté, rouge = erreur.",
    "<b>Température</b> lue par la sonde du focuser.",
    "<b>?</b> ouvre ce <b>guide</b> au chapitre de l'onglet ouvert.",
    "<b>Thème</b> sombre ou clair. Le thème sombre fatigue moins les yeux pendant les longues sessions au microscope.",
], layout="full below-marks", anchors={1: "b", 2: "b", 3: "b", 4: "b", 5: "b"})}
<p>Sous la barre, deux bandeaux peuvent apparaître : le bleu des <b>mises à jour</b> et le rouge d'<b>alarme</b>,
par exemple quand les boutons physiques amènent le focuser au-delà d'une limite.</p>
<div class="box tip"><span class="t">Le guide dans l'app</span>En plus du <b>?</b> en haut, presque chaque carte a un petit
<b>?</b> à côté de son titre : il ouvre ce guide directement à la partie qui explique cette carte. Le guide a un sommaire
et une recherche (touche <kbd>/</kbd>) et s'ouvre toujours dans la même fenêtre.</div>
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
<p>À l'ouverture, l'app <b>se reconnecte toute seule</b> au focuser et à l'appareil photo utilisés la dernière fois,
s'ils sont branchés au Mac : il suffit de les avoir connectés une fois avec <b>{ui('Connetti')}</b>. Le focuser ne se
reconnecte que s'il s'agit du même adaptateur USB (un autre appareil ayant le même nom de port n'est pas touché), et la
connexion ne fait pas bouger le moteur. Si une connexion échoue, une ligne reste dans le journal, et
<b>{ui('Connetti')}</b> fonctionne comme d'habitude.</p>
<h3>Réglages sur l'appareil photo</h3>
{table(["Appareil photo", "Que régler"], [
    ["<b>Nikon D5600</b> et autres Nikon", "Molette de sélection du mode sur <b>M</b> (manuel). Dans le menu Visualisation, désactivez l'<b>affichage des images</b>. Désactivez SnapBridge/Wi-Fi et Bluetooth, qui peuvent occuper la connexion. Gardez une carte mémoire insérée et la batterie chargée (ou l'adaptateur secteur EH-5/EP-5A)."],
    ["Canon", f"Mode <b>M</b>. La photo va dans la mémoire de l'appareil ou sur la carte selon <i>{ui('Destinazione')}</i>. Pour la temporisation du miroir, activez le <b>verrouillage du miroir</b> dans le menu."],
    ["Sony", "Menu USB › <b>PC Remote</b> ; mode <b>M</b>. Pour télécharger les photos sur le Mac, réglez la destination sur <b>PC uniquement</b> (MENU › Réglage › Réglages PC distant › Destination d'enregistrement des images fixes). Pour la visée en direct, l'appareil doit l'autoriser en mode PC Remote."],
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
    f"<b>{ui('Allontana')} / {ui('Avvicina')}</b> : un clic déplace de la taille choisie. En maintenant le bouton enfoncé, le moteur continue d'avancer, par tronçons (chapitre 12), et au relâchement il ralentit jusqu'à l'arrêt.",
    f"<b>{ui('Vai alla posizione…')}</b> : saisissez un nombre de pas et cliquez sur {ui('Vai')}.",
    "<b>STOP</b> : arrête immédiatement le moteur et la séquence éventuelle. Au clavier : <kbd>Esc</kbd>. Après le STOP, le moteur reste arrêté jusqu'à ce que vous appuyiez de nouveau sur un bouton.",
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
<div class="box tip"><span class="t">Clavier</span><kbd>↑</kbd> éloigne, <kbd>↓</kbd> rapproche : un appui bref fait un
pas, la touche maintenue enfoncée déplace en continu jusqu'au relâchement (comme les boutons). <kbd>⇧</kbd> avec une flèche multiplie le pas par 10, les touches numériques <kbd>1</kbd> <kbd>2</kbd>
<kbd>3</kbd>… choisissent la taille du pas, <kbd>Esc</kbd> correspond au STOP. Ces touches fonctionnent dans l'onglet
{ui('Sessione')}, même pendant la visée en direct.</div>
<div class="box warn"><span class="t">Boutons physiques</span>Les boutons du focuser actionnent le moteur sans passer
par l'app. L'app les surveille et, si la position sort des limites, envoie STOP et affiche une alarme ; pour une
protection complète, lisez le chapitre 9. Si vous les actionnez pendant une séquence, la séquence se met en
pause.</div>
<div class="box warn"><span class="t">Si la glissière n'avance pas avec les petits pas</span>Avec <span class="ui">{ui('Alimentazione bobine motore › Sempre quando connesso')}</span>
désactivé ({ui('Configurazione')} › {ui('Motore (firmware)')}), le moteur perd, à chaque arrêt, la force qui le maintient
en position : la charge (poids de l'appareil photo, un ressort, la courroie) peut le faire reculer. Le compteur de pas
avance, mais la glissière reste où elle est et toute la pile se retrouve sur le même plan. Pendant la séquence, l'app
alimente les bobines toute seule (chapitre 12) ; pour les déplacements manuels de quelques pas, activez-les, ou vérifiez
dans la visée en direct que l'image se déplace vraiment.</div>
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
<p>Avec les <b>Sony</b>, le temps de pose et l'ISO changent par crans, comme en tournant la molette : une valeur
éloignée peut demander quelques secondes. Pour l'<b>A6400</b>, le menu ISO va jusqu'à 102400, le maximum qu'il accepte.
Si l'appareil n'accepte pas une valeur en 12 secondes, l'app le signale : débranchez et rebranchez le câble USB, ou
éteignez et rallumez l'appareil.</p>
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
    f"État : <b>{ui('LIVE')}</b>, ou <b>{ui('SCATTO…')}</b> pendant une photo test.",
    "Modèle de l'appareil photo. Double-clic sur l'image : plein écran.",
], layout="stack")}
</div>
<p>La visée en direct atteint 15 images par seconde : c'est le moyen le plus pratique de trouver le début et la fin
de la séquence tout en déplaçant le focuser au clavier. Quand la séquence démarre, la visée en direct reste
allumée pendant que le focuser revient au point de départ, pour que vous puissiez le surveiller ; une fois arrivé, elle
se met en pause (le miroir doit redescendre et l'appareil doit déclencher normalement) et elle se ferme à la première
photo : le cadre affiche de nouveau la dernière photo, dans la visionneuse aussi. Une fois la pile terminée, rallumez-la
avec <span class="ui">{ui('● Live')}</span>. Sur les reflex, le miroir reste levé tant que la visée en direct est
active. La visée en direct allumée depuis la fenêtre principale démarre aussi dans la visionneuse, si elle est
ouverte ; <span class="ui">{ui('■ Ferma live')}</span> l'éteint dans les deux fenêtres. Avec <span class="ui">{ui('◉ Scatto di prova')}</span>
pendant la visée en direct, le cadre montre la photo et la visée en direct reprend toute seule dès que vous déplacez le
focuser, depuis l'app ou avec ses boutons.</p>
<div class="box tip"><span class="t">Pour une mise au point précise</span>Ouvrez la visée en direct dans la
<b>visionneuse</b> : vous pouvez zoomer à 100 % et au-delà et vous déplacer sur le détail qui vous intéresse
(chapitre 8).</div>
""")

# 7
TORNA = ui("Torna all'inizio a fine sequenza")
OBJ_MAG = ui("Ingrandimento dell'obiettivo")
CAMBIO = ui("Cambio d'ingrandimento intermedio")
FOCALE = ui("Focale (mm)").split(" (")[0]
APERTO = ui("Diaframma più aperto (f/)").split(" (")[0]
RAPPORTO = ui("Rapporto di riproduzione dell'obiettivo (×)").split(" (")[0]
DIAF = ui("Diaframma impostato (f/)").split(" (")[0]
TUBI = ui("Tubi di prolunga / soffietto (mm)").split(" (")[0]
MOSTRA_AV = ui("Mostra l'avanzamento sulla rete locale")
ULT_M = ui("Mostra l'ultimo scatto")
ULT_A = ui("Aggiorna l'ultimo scatto")
add(f"""
<h1><span class="n">7</span>La séquence de stacking</h1>
<h2 style="margin-top:0">7.1 Régler la séquence</h2>
{fig("sequenza", [
    f"<b>État</b> : {ui('Pronta')}, {ui('In corso')}, {ui('In pausa')}, {ui('Completata')}, {ui('Errore')}.",
    f"<b>{ui('Nome della pila')}</b> : les photos vont dans un sous-dossier <code>nom_date-heure</code>, avec les noms <code>nom_0001</code>, <code>nom_0002</code>…",
    f"<b>{ui('＋ Nuova pila')}</b> : une fois une pile terminée, prépare la suivante (l'état redevient {ui('Pronta')}). Même avec le même nom, chaque pile va dans un nouveau dossier.",
    f"<b>{ui('Inizio')}</b> et <b>{ui('Fine')}</b> en pas. <span class='ui'>⌖ {ui('qui')}</span> copie la position actuelle.",
    "<b>Pas</b> entre deux photos, en pas moteur (chapitre 11).",
    f"<b>{ui('Numero di scatti')}</b>. Si vous modifiez {ui('Inizio')}, {ui('Fine')} ou Pas, le nombre de photos est recalculé ; si vous modifiez le nombre de photos, c'est le pas qui est recalculé. Quand le pas change tout seul, il devient orange et affiche <span class='ui'>↺ était …</span> : un clic annule la modification.",
    "<b>Attente après le mouvement</b> : laisse les vibrations s'amortir avant la photo (1 à 3 s au microscope).",
    f"<b>{ui('Ottica e filtro (profilo)')}</b> : le profil d'objectif, de filtre et d'éclairage à écrire dans les données de la pile (7.2). <span class='ui'>{ui('Modifica')}</span> l'ouvre dans l'onglet {ui('Ottica')}. Sans profil, la pile est notée « aucun filtre ».",
    "<b>Récapitulatif</b> : photos, course en pas et en µm, pas en µm et durée estimée. Un clic sur le récapitulatif (▶ à droite) affiche aussi le profil optique utilisé et la calibration qui sera associée à la pile. Si la séquence sort des limites, un avertissement rouge apparaît et elle ne démarre pas.",
    f"<b>{ui('Salva in')}</b> : le dossier des photos. <span class='ui'>{ui('Scegli…')}</span> ouvre le Finder, <span class='ui'>{ui('Apri')}</span> y affiche le dossier.",
    f"<b>{ui('Scatti per posizione')}</b> : combien de photos prendre à chaque position (1 par défaut). Avec plusieurs prises, le logiciel de fusion peut en faire la moyenne et réduire le bruit (7.4).",
    "<b>Pause après la photo</b> : écriture sur la carte, recharge du flash.",
    "<b>Compensation du jeu</b> : avant la première photo, le moteur recule de ce nombre de pas puis avance ; chaque photo est ainsi atteinte dans le même sens.",
    f"<b>{ui('Modalità di scatto')}</b> : <i>{ui('Scarica sul Mac')}</i> (recommandé), <i>{ui('Solo sulla scheda')}</i>, <i>{ui('Solo trigger (veloce)')}</i> (destination : carte).",
    f"<b>{TORNA}</b>.",
    f"<b>{ui('Suono sul Mac a fine sequenza')}</b> : un son clair si la pile est terminée, un son grave si elle s'est arrêtée sur une erreur ou s'est mise en pause toute seule.",
    "<b>Préréglages</b> : enregistrent et rappellent les réglages de la séquence, par exemple un par objectif.",
    "<b>Progression</b> : photos prises, temps restant, position.",
    f"<b>{ui('▶ Avvia sequenza')}</b>, <b>{ui('Pausa')}</b>/<b>{ui('Riprendi')}</b>, <b>{ui('■ Interrompi')}</b>.",
    f"<b>{ui('Apri nel Finder')}</b> : en fin de séquence, ouvre le dossier de la pile, avec les photos, <code>sequence.json</code> et <code>sequence.txt</code> (7.5).",
])}
<p>Les prises par position, la pause après la photo, le jeu, le mode, le retour au début et le son se trouvent dans la
section repliable <span class="ui">{ui('Tempi, gioco e scatti per posizione')}</span>. Si les bobines du moteur sont
éteintes et que l'app ne les alimente pas pendant la séquence, un avertissement orange apparaît en dessous
(chapitre 12).</p>
<h2>Pendant la séquence</h2>
{fig("sequenza-in-corso", [
    f"L'état passe à <b>{ui('In corso')}</b> (orange).",
    "Photos prises sur le total, temps restant estimé et position actuelle. Sur la barre de course, les traits des photos déjà prises changent de couleur.",
    f"<b>{ui('Pausa')}</b> suspend après la photo en cours ; <b>{ui('■ Interrompi')}</b> termine la séquence. Le <b>STOP</b> du focuser arrête aussi immédiatement le moteur.",
], layout="side narrow")}
<ul>
<li>Si vous actionnez les <b>boutons physiques</b> du focuser, la séquence se met en pause ; à la reprise, elle revient
  à la bonne position et refait la photo.</li>
<li><b>Si une photo échoue</b>, l'app réessaie après 3 s ; à la deuxième erreur, elle reconnecte toute seule l'appareil
  photo et réessaie encore. Si cela ne suffit pas, la séquence <b>se met en pause</b> (elle ne s'arrête pas) et le
  message indique quoi vérifier : remettez l'appareil photo en état (batterie, câble, carte) et cliquez sur
  <span class="ui">{ui('Riprendi')}</span>. L'app reconnecte l'appareil photo, revient à la même position et refait la
  photo ; les photos continuent dans le même dossier.</li>
<li><b>Le Mac ne se met pas en veille</b> tant que la séquence est en cours : la veille suspendrait l'USB et l'appareil
  photo disparaîtrait au milieu de la pile. L'écran peut quand même s'éteindre. Attention : si vous fermez l'écran d'un
  portable sans moniteur externe, le Mac se met en veille malgré tout.</li>
<li>Si les bobines du moteur sont éteintes à l'arrêt, l'app les alimente pendant toute la pile et les éteint de nouveau
  après le retour au début (chapitre 12).</li>
<li>Les champs de la séquence sont verrouillés tant que la séquence est en cours.</li>
<li>Chaque nouvelle photo s'affiche dans {ui('Ultimo scatto')} et dans la visionneuse. Pour suivre la pile loin du Mac,
  il y a le suivi sur smartphone (7.7).</li>
</ul>

<h2>7.2 Optique et filtre : les profils</h2>
<p>Le logiciel de fusion travaille mieux s'il sait avec quoi les photos ont été prises : avec le grossissement et le
pixel du capteur, il peut fournir la carte de profondeur et la vue 3D en vrais micromètres. Ces données s'enregistrent
dans l'onglet <b>{ui('Ottica')}</b> sous forme de <b>profils</b> nommés, un pour chaque combinaison d'objectif, de filtre et
d'éclairage (par exemple « 10× GFP », « 4× fond clair »), et se choisissent dans la séquence (repère 8 de la figure
ci-dessus). Chaque profil est de type <b>{ui('Microscopio')}</b> ou <b>{ui('Macro fotografica')}</b> (7.3). Sur la
figure, un profil pour microscope : un objectif 10× avec le changeur de grossissement Optovar 1,6× et l'appareil photo
monté sur une bague T2 sans lentille.</p>
{fig("ottica", [
    f"<b>{ui('Profilo da modificare')}</b> : choisissez-le pour charger ses valeurs ; <i>{ui('— nuovo profilo —')}</i> part d'un formulaire vide.",
    f"<b>{ui('Salva come nuovo profilo…')}</b>, dans la barre qui apparaît en haut : demande un nom et enregistre une copie, sans modifier le profil de départ.",
    f"<b>{ui('Elimina profilo')}</b>, après confirmation. <b>{ui('Rinomina…')}</b> change le nom aussi dans la séquence et dans les flats de la bibliothèque de calibration.",
    f"<b>{ui('Tipo di ottica')}</b>, les deux onglets en haut du panneau {ui('Ottica')}, qui changent les champs en dessous : <i>{ui('Microscopio')}</i> (objectif avec grossissement et ON gravés) ou <i>{ui('Macro fotografica')}</i> (objectif photo, tubes et bonnettes, 7.3).",
    f"<b>{ui('Pixel del sensore (pixel pitch in µm)')}</b>. Nikon D5600 : <b>3,9 µm</b> (23,5 mm ÷ 6000 pixels). On le trouve dans la fiche technique de l’appareil, sur <b>digicamdb.com</b> (appareils photo) ou dans la base de capteurs d’<b>AstroBin</b> (caméras dédiées, en cherchant par exemple IMX571).",
    f"<b>{ui('Adattatore / oculare di proiezione')}</b> entre le microscope et l'appareil photo : nom et facteur, par exemple un adaptateur monture C 0,5× ou 0,63×, un photo-oculaire 2,5×, une bague T2 sans lentille 1×. Vide = 1×.",
    f"<b>{CAMBIO}</b>, si le statif en possède un : nom et facteur, par exemple <i>Optovar</i> 1,25×, 1,6× ou 2×. Vide = 1×.",
    "<b>Objectif</b> : un nom libre, tel qu'il est gravé sur l'objectif.",
    f"<b>{OBJ_MAG}</b> : le premier nombre gravé sur l'objectif (<b>10</b>×/0,25).",
    f"<b>{ui('Apertura numerica (NA)')}</b> : le second nombre gravé sur l'objectif (10×/<b>0,25</b>).",
    f"<b>{ui('Immersione')}</b> : air, eau, huile, glycérine ou silicone.",
    "<b>µm par pixel sur l'échantillon, mesurés</b> avec un micromètre objet : s'il est indiqué, il prime sur le calcul.",
    f"<b>{ui('Ingrandimento sul sensore')}</b> = objectif × changeur intermédiaire × adaptateur (ici 10 × 1,6 × 1 = 16×) et <b>échelle sur l'échantillon</b> : la valeur mesurée, ou bien pixel du capteur ÷ grossissement. Avec une mesure s'affiche aussi le <b>grandissement réel</b> (pixel du capteur ÷ µm par pixel mesurés), qui inclut ce que la chaîne ne dit pas, comme la distance du capteur ou le tube photo ; si l'écart est grand, le facteur <i>suggéré par la mesure</i> apparaît à côté de l'adaptateur : un clic l'inscrit dans le champ.",
    f"<b>{ui('Filtro')}</b> : <i>{ui('Non indicato')}</i> (on ne sait pas), <i>{ui('Nessun filtro')}</i> ou <i>{ui('Filtro montato')}</i>.",
    "<b>Nom</b> et <b>type</b> du filtre : passe-bande, passe-haut (long pass), passe-bas (short pass), densité neutre, polariseur, autre.",
    "<b>Centre</b> et <b>largeur de bande</b> en nm pour un passe-bande ; pour un passe-haut ou un passe-bas, la longueur d'onde de coupure.",
    f"<b>{ui('Illuminazione')}</b> (texte libre, avec suggestions), <b>intensité</b> en % et <b>température de couleur</b> en K (par exemple 4000 K pour une lumière neutre).",
    f"<b>{ui('Note')}</b> libres, qui sont enregistrées dans les données de la pile.",
    f"<b>{ui('Salva profilo')}</b>, dans la barre <i>{ui('Modifiche non salvate')}</i> qui apparaît en haut dès que vous changez une valeur, avec <b>{ui('Annulla')}</b> (retour au profil enregistré) : remplace le profil choisi ; s'il est nouveau, demande un nom.",
    "Le <b>profil</b> ouvert ; en orange s'il y a des modifications non enregistrées.",
    "<b>Index</b> des sections, avec la recherche : un clic mène à la section. Avec Microscope ou Macro, seules les sections de ce type apparaissent.",
    "<b>Récapitulatif</b>, toujours visible pendant la saisie : grandissement sur le capteur, échelle sur l'échantillon (mesurée ou calculée, avec l'écart), profondeur de champ et pas conseillé.",
], layout="full")}
<p>Un champ vide signifie « non indiqué » et n'est pas écrit. Si vous ne choisissez aucun profil dans la séquence, la
pile est notée <b>sans filtre</b> et sans données optiques. Les mêmes valeurs d'ouverture numérique, de grossissement et
de pixel servent aussi au calcul de la profondeur de champ (chapitre 11). Pensez à changer de profil quand vous changez
d'objectif ou de filtre : le récapitulatif de la séquence affiche toujours celui qui sera écrit.</p>

<h2>7.3 Macro photographique</h2>
<p>Avec le type <span class="ui">{ui('Macro fotografica')}</span>, le profil décrit un objectif photo au lieu d'un
objectif de microscope. L'app en déduit le grossissement sur le capteur, l'ouverture effective et une ON équivalente,
qui servent à l'échelle en µm et à la profondeur de champ exactement comme au microscope.</p>
{fig("ottica-macro", [
    f"<b>{ui('Macro fotografica')}</b> : affiche les champs de l'objectif photo à la place de ceux du microscope.",
    f"<b>{ui('Cerca nel database')}</b> : saisissez une partie du nom (par exemple « 90 macro ») et choisissez l'objectif. La base est celle de <b>Lensfun</b> (1162 objectifs), plus quelques objectifs macro spécialisés que Lensfun n'a pas (Canon MP-E 65, Laowa 25/90/100, OM 90) et votre liste personnelle.",
    f"<b>{ui('Marca')}</b> et <b>{ui('Modello').lower()}</b> : remplis par la recherche, ou saisis à la main.",
    f"<b>{FOCALE}</b> et <b>{APERTO.lower()}</b>. Avec un zoom, indiquez la focale utilisée.",
    f"<b>{ui('＋ Aggiungi al mio elenco')}</b> : enregistre un objectif absent de la base, pour le retrouver dans la recherche.",
    f"<b>{RAPPORTO}</b>, lu sur son échelle à la distance de mise au point utilisée : 1 = 1:1, 0,5 = 1:2, 0 = mise au point à l'infini.",
    f"<b>{DIAF}</b> sur l'objectif.",
    f"<b>{TUBI}</b> : la longueur totale ajoutée entre l'objectif et l'appareil photo, en mm.",
    "<b>Bonnettes</b> devant l'objectif (Raynox et similaires), jusqu'à 3, avec leur puissance en dioptries.",
    "<b>Résultat</b> : grossissement sur le capteur, ouverture effective, ON équivalente et échelle sur l'échantillon en µm par pixel.",
], layout="full")}
<p>Les calculs sont ceux de l'optique photographique rapprochée, avec <i>f</i> = focale, <i>m₀</i> = rapport de
l'objectif, <i>e</i> = tubes en mm, <i>D</i> = dioptries des bonnettes et <i>N</i> = ouverture réglée :</p>
<div class="formula">m₁ = m₀ + {frac("e", "f")} &nbsp;&nbsp;&nbsp; grossissement m = m₁ + {frac("ΣD", "1000")} · f · (1 + m₁)
<span class="lbl">ouverture effective = N · (1 + m₁) &nbsp;·&nbsp; ON équivalente = {frac("m", "2 · N · (1 + m₁)")}</span></div>
<div class="calc">Exemple : objectif macro 90 mm à 1:2 (m₀ = 0,5), f/8, sans tube, bonnette de +8 dioptries
m₁ = 0,5 + 0 = 0,5
m  = 0,5 + 8 ÷ 1000 × 90 × (1 + 0,5) = 0,5 + 1,08 = <b>1,58×</b>
ouverture effective = 8 × 1,5 = <b>f/12</b>      ON équivalente = 1,58 ÷ (2 × 8 × 1,5) = <b>0,066</b>
avec un capteur de 3,9 µm : 3,9 ÷ 1,58 = <b>2,47 µm par pixel</b> sur l'échantillon</div>
<p>Comme au microscope, une valeur mesurée avec une règle millimétrée (champ <span class="ui">µm par pixel sur
l'échantillon, mesurés</span>) prime sur le calcul, qui n'est qu'une estimation avec des bonnettes. En macro, la
profondeur de champ est souvent de plusieurs dizaines ou centaines de µm : si un pas de la glissière est plus long que le
pas conseillé, l'onglet {ui('Ottica')} le signale et suggère le micropas adapté (chapitre 10.2).</p>

<h2>7.4 Plusieurs prises par position</h2>
<p>Avec <span class="ui">{ui('Scatti per posizione')}</span> supérieur à 1, l'appareil photo déclenche plusieurs fois à
chaque position, sans déplacer le moteur entre deux prises : l'attente contre les vibrations n'a lieu qu'après le
mouvement, et entre les prises il n'y a que la pause après la photo. Le logiciel de fusion en fait la moyenne : avec
4 prises, le bruit est divisé par deux. Les fichiers s'appellent <code>stack_0001_1</code>, <code>stack_0001_2</code>… ;
avec une seule prise, ils restent <code>stack_0001</code>, <code>stack_0002</code>… Le récapitulatif affiche
positions × prises et la durée correspondante.</p>

<h2>7.5 Les fichiers de la pile</h2>
<p>Dans le dossier de la pile, à côté des photos, l'app écrit deux fichiers. Elle les réécrit après chaque photo : ils
restent donc valables même si la séquence est interrompue. Les photos ne sont jamais modifiées.</p>
<ul>
<li><code>sequence.json</code> : toutes les données pour le <b>logiciel de fusion</b> : position de chaque photo en pas
  et en µm, heure, température, guide, appareil photo, profil optique (microscope ou macro), filtre, éclairage et les
  jeux de calibration adaptés (7.6). Le format est décrit dans <code>docs/sequence-json.md</code> sur GitHub.</li>
<li><code>sequence.txt</code> : un <b>récapitulatif à lire</b>, dans la langue de l'app. Par exemple :</li>
</ul>
<div class="calc long">{SEQ_TXT}</div>

<h2>7.6 Calibration : exposition, darks et flats</h2>
<p>L'onglet <b>{ui('Calibrazione')}</b> prépare ce dont le logiciel de fusion a besoin pour corriger les photos : un temps
de pose juste pour la pile et les <b>images de calibration</b>. Les niveaux se mesurent sur les <b>vrais RAW</b>, sans
conversion des couleurs, avec <i>fs-rawstat</i>, un petit programme fourni avec l'app et basé sur LibRaw ; les pixels
brûlés sont détectés canal par canal. Avec le simulateur, les niveaux ne sont qu'une estimation.</p>
<h3>{ui('Esposizione dei light')}</h3>
{fig("calibrazione-esposizione", [
    f"<b>{ui('Misura su')}</b> : <i>{ui('Luci')}</i> (le 99,5e centile, c'est-à-dire les parties les plus claires) ou <i>{ui('Media (livello medio)')}</i>.",
    "<b>Niveau cible</b> en % de la saturation du capteur, par exemple 85 % sur les hautes lumières.",
    f"<b>{ui('Calcola e imposta il tempo')}</b> : l'app prend quelques photos d'essai, mesure les RAW et règle le temps de pose, en privilégiant les temps sans pixels brûlés. L'ISO et l'ouverture restent ceux qui sont réglés.",
    "<b>Résultat</b> : temps choisi, niveau mesuré et pixels brûlés.",
], layout="side")}
<p>Amenez le focuser au milieu de la pile et allumez l'éclairage comme pour la séquence. L'exposition se calcule
<b>une seule fois, avant la pile</b> : la changer d'un plan à l'autre rendrait la luminosité des images différente.</p>
<h3>{ui('Frame di calibrazione')}</h3>
{fig("calibrazione-frame", [
    f"<b>{ui('Tipo')}</b> : <i>{ui('Dark')}</i> (bouchon sur l'objectif, mêmes ISO et temps de pose que les lights : bruit thermique et pixels chauds), <i>{ui('Flat')}</i> (champ éclairé de façon uniforme, même optique et même ouverture : vignetage et poussières) ou <i>{ui('Dark dei flat')}</i> (bouchon, mêmes ISO et temps de pose que les flats).",
    f"<b>{ui('Fotogrammi')}</b> à prendre, par exemple 16.",
    "<b>Niveau des flats</b> en % de la saturation, par exemple 50 % : l'app trouve elle-même le temps de pose.",
    f"<b>{ui('Avanzamento')}</b> : images prises et niveau mesuré.",
    f"<b>{ui('▶ Scatta i frame')}</b> et <b>{ui('■ Interrompi')}</b>.",
], layout="side")}
<ul>
<li><b>Darks</b> : bouchon sur l'objectif et oculaire du viseur couvert, mêmes ISO et temps de pose (ou pose B) que les
  lights, si possible à la même température.</li>
<li><b>Flats</b> : champ éclairé de façon uniforme (une lame vide, un diffuseur), avec le même profil optique et la même
  ouverture que la pile : ils ne corrigent le vignetage et les poussières que si l'optique est la même.</li>
<li><b>Darks des flats</b> : juste après les flats, avec le bouchon : l'app reprend toute seule l'ISO et le temps de pose
  des flats les plus récents.</li>
</ul>
<h3>Comment la fusion les utilise</h3>
<p>Focus Stack prend les frames et les indique dans le <code>sequence.json</code> de la pile ; la correction est faite
par le logiciel de fusion (par exemple Focus Fusion) sur chaque image, avant de l'aligner. Le dark est
<b>soustrait</b> : il enlève le bruit thermique et les pixels chauds. Le flat <b>divise</b> : il rend la lumière que
le vignetage et les ombres de poussière avaient enlevée.</p>
{calib_diagram(CALIB_LABELS)}
{fig("calibrazione-esempio", [
    '<b>Flat normalisé</b> F, avec un contraste renforcé : les coins reçoivent 70 % de la lumière du centre, et chaque point est un grain de poussière sur le capteur.',
    "<b>Une image de la pile</b> telle quelle : le fond s'assombrit vers les coins (64 % du centre) et la même tache de poussière se voit sur le fond (encadré agrandi 4×).",
    '<b>La même image corrigée</b>, (I − D) ÷ F, avec le même rendu : coins à 94 % du centre et tache disparue.',
], layout="full", caption='Un crayon : Sony A6400 avec le 70-350 mm à 350 mm, lentille additionnelle +8 dioptries, f/20, ISO 400, 1/20 s ; 10 flats, 10 darks et 10 darks des flats.')}
<h3>La {ui('Libreria di calibrazione').lower()}</h3>
{fig("calibrazione-libreria", [
    f"<b>Dossier</b> de la bibliothèque : <code>_calibrazione</code> dans le dossier des piles. <span class='ui'>{ui('Apri nel Finder')}</span> l'affiche.",
    "<b>Jeux adaptés</b> à une pile lancée maintenant, avec l'appareil photo et les réglages actuels.",
    "<b>Tableau des jeux</b> : type, date, appareil photo, ISO, temps de pose, profil optique, images, niveau moyen et température. <span class='ui'>Supprimer</span> place le jeu dans la Corbeille du Mac (récupérable depuis le Finder). Les cases devant le type permettent d'en choisir plusieurs (celle de l'en-tête les sélectionne tous) et de les supprimer ensemble avec <span class='ui'>Supprimer la sélection</span> : par sécurité, il faut taper le mot SUPPRIMER.",
], layout="full")}
<p>Chaque jeu a son dossier avec les images et un fichier <code>calibration.json</code> (format décrit dans
<code>docs/calibration-json.md</code>). Au lancement d'une pile, <code>sequence.json</code> indique les jeux adaptés les
plus récents : pour les darks, même appareil photo, même ISO et même temps de pose ; pour les flats, également le même
profil optique. Les images ne sont pas copiées. C'est la même bibliothèque que celle qu'utilise <b>Focus Fusion</b>, qui y
enregistre ses « masters » à côté.</p>

<p>À droite, le <b>récapitulatif</b> reste visible pendant que vous travaillez dans l'onglet.</p>
{fig("calibrazione-riepilogo", [
    f"<b>{ui('Per la prossima pila')}</b> : pour les darks, les flats et les darks des flats, ✓ avec la date du jeu qui serait utilisé, ou <i>{ui('manca')}</i> en orange. S'il manque un jeu, un point orange apparaît aussi à côté de <i>{ui('Libreria')}</i> dans l'index.",
    "<b>Température</b> actuelle de la sonde.",
    "Évolution sur les <b>60 dernières minutes</b> : comparez-la avec la température des darks dans le tableau.",
    f"<b>{ui('Sensore')}</b> : plage dynamique attendue à l'ISO réglé, avec le graphique (ISO conseillés en vert, l'actuel entouré). Apparaît après l'analyse du capteur.",
], layout="side narrow")}

<h3>{ui('Analisi del sensore')}</h3>
<p>Une fois par appareil, <b>{ui('Calibrazione')} › {ui('Sensore')} › {ui('Analisi del sensore')}</b> mesure comment se
comporte le capteur à chaque ISO : <b>gain</b> (combien d'électrons vaut une unité du RAW), <b>bruit de lecture</b>,
<b>puits plein</b> (quelle quantité de lumière un pixel recueille avant de saturer) et <b>plage dynamique</b> en IL. Pour
19 ISO, il faut environ 20 minutes.</p>
<ol>
<li><b>{ui('Prepara')}</b> : devant l'objectif, le diffuseur éclairé, comme pour les flats ; appareil en RAW et mise au
  point manuelle. Choisissez la plage d'ISO (de 100 à 6400 par tiers d'IL est un bon début) et le nombre de vues par ISO (2 suffisent).</li>
<li><b>Flat</b> : pour chaque ISO, l'app trouve le temps pour un flat à 50 % et déclenche. Les ISO refusés par l'appareil sont barrés.</li>
<li><b>{ui('Tappo')}</b> : l'app s'arrête et demande de mettre le bouchon ; appuyez alors sur <i>{ui('Ho messo il tappo: scatta i dark')}</i>.</li>
<li><b>Dark</b> : mêmes ISO et temps, dans le noir.</li>
<li><b>{ui('Risultato')}</b> : deux graphiques, plage dynamique et bruit de lecture par ISO, et les ISO conseillés.</li>
</ol>
{fig("calibrazione-sensore", [
    'Les <b>étapes</b> de la procédure : celle en cours en bleu, celles terminées cochées.',
    "<b>Graphiques</b> de plage dynamique et de bruit de lecture par ISO : ISO conseillés en vert, l'ISO réglé sur l'appareil entouré, bande grise et ligne pointillée pour les ISO pas fiables.",
    '<b>Conseillé</b>, <b>Conseillé avec peu de lumière</b> et <b>À éviter</b>, chacun avec la raison.',
    '<b>Tableau</b> : pour chaque ISO le temps des flats, la plage, le bruit, le puits plein et le gain.',
    "<b>Exporter en CSV</b> enregistre le tableau dans Téléchargements ; <b>Refaire l'analyse</b> repart de la préparation.",
], layout="full")}
<figure class="shot">{sensor_chart(SENSOR_LABELS)}<figcaption>Analyse du capteur d'un Sony A6400 : 19 ISO de 100 à 102400, 2 flats et 2 darks chacun. ISO 400 entouré.</figcaption></figure>
<p>Comment le lire, avec l'exemple d'un Sony A6400. ISO 100 a la plage la plus large, 13,3 IL, parce qu'il recueille le plus
de lumière. À ISO 400, le capteur passe à un second gain et le bruit de lecture descend de 3 à 1,2 électron : 12,9 IL
avec des temps quatre fois plus courts. Au-delà, le bruit ne baisse plus et chaque doublement de l'ISO coûte un IL : si
la lumière manque, restez à 400 et éclaircissez ensuite. Les ISO de 160 à 320 donnent moins de plage qu'ISO 400 avec des
temps plus longs : mieux vaut les éviter. Au-delà de 3200, l'appareil filtre déjà le bruit dans le RAW, et ces valeurs
sont marquées comme pas fiables.</p>
<p>Le résultat est enregistré comme <b>profil du capteur</b> de l'appareil, dans <code>_calibrazione/_sensore</code>. Le
récapitulatif de la Calibration et celui de la séquence montrent la plage dynamique attendue à l'ISO réglé, avec le point
sur le graphique ; chaque pile écrit dans son <code>sequence.json</code> les valeurs de son ISO (<code>"sensor"</code>),
que Focus Fusion peut utiliser. Les images de l'analyse sont dans le même dossier, hors de la bibliothèque des jeux, et ne
sont jamais choisies pour une pile. Refaites l'analyse si vous changez d'appareil ou en mettez à jour le firmware.</p>

<h2>7.7 Suivi sur smartphone</h2>
<p>Pour suivre une longue pile loin du Mac, <span class="ui">{ui('Configurazione')} › {ui('Avanzamento da smartphone')}</span>
active une page <b>en lecture seule</b> sur le réseau local.</p>
{fig("smartphone", [
    f"<b>{MOSTRA_AV}</b> : active la page (désactivée tant que vous ne l'activez pas).",
    "<b>Code QR</b> : scannez-le avec l'appareil photo du smartphone, qui doit être sur le même réseau Wi-Fi que le Mac.",
    f"<b>{ui('Nuovo link')}</b> : change le code du lien ; l'ancien cesse de fonctionner.",
], layout="side")}
{fig("smartphone-pagina", [
    "Nom de la pile, état, photos prises, temps restant et heure de fin prévue.",
    f"<b>{ui('Avvisami con un suono a fine sequenza')}</b> : le smartphone sonne (et vibre sur Android) quand la pile se termine, s'arrête sur une erreur ou se met en pause toute seule ; tant que le son est activé, l'écran reste allumé.",
    f"<b>{ULT_M} / {ULT_A}</b> : la dernière photo, sur toute la largeur.",
    f"La dernière photo : écartez deux doigts, faites glisser ou touchez deux fois pour agrandir. En agrandissant, un détail en haute résolution se charge ; le zoom est conservé quand on passe à la photo suivante, pour comparer la même zone. <span class='ui'>{ui('Adatta')}</span> revient à l'image entière.",
], layout="side narrow", width="70%")}
<p>Depuis la page, <b>on ne commande rien</b>, et sans le code du lien on ne voit rien. La première fois, macOS demande
s'il faut autoriser les connexions entrantes : répondez <b>Autoriser</b>. Pour le son, gardez la page ouverte au premier
plan : tant que le son est activé, la page garde l'écran allumé. Si le téléphone se verrouille quand même, réglez le
verrouillage automatique sur <b>Jamais</b> pendant l'attente (iPhone : Réglages › Luminosité et affichage › Verrouillage
automatique) : un téléphone verrouillé suspend les pages web et le son n'arrive pas.</p>
""")

# 8
EVID = ui("Evidenzia sull'immagine")
add(f"""
<h1><span class="n">8</span>La visionneuse</h1>
<p>Elle s'ouvre avec <span class="ui">{ui('Apri visualizzatore ↗')}</span> ou d'un clic sur la dernière photo, dans une
fenêtre séparée. Avec deux écrans, elle s'ouvre d'elle-même en plein écran sur l'autre ; on peut le désactiver dans
<span class="ui">{ui('Configurazione')} › {ui('Visualizzatore')}</span>. Elle affiche les photos en pleine résolution (y compris
les RAW, convertis à la volée) avec zoom et déplacement, ainsi que la visée en direct de l'appareil photo.</p>
{fig("visualizzatore", [
    "<b>◀ ▶</b> photo précédente et suivante (flèches <kbd>←</kbd> <kbd>→</kbd>).",
    "<b>Compteur de la pile</b> : pendant la séquence, la dernière photo prise sur le total (par exemple 75/115, <i>en cours</i>), puis <i>terminée</i> ; avec les photos test, leur nombre. À côté, le nom du fichier et, dessous, numéro de la photo, position, température et heure. Pendant la pile, une ligne bleue le long du bord supérieur de la fenêtre montre l'avancement.",
    f"<b>{ui('● Live')}</b> (<kbd>L</kbd>) : la visée en direct dans la même fenêtre, avec zoom et déplacement.",
    "<b>Zoom</b> − et + (<kbd>−</kbd> <kbd>+</kbd>) et niveau d'agrandissement.",
    f"<b>{ui('Adatta')}</b> (<kbd>0</kbd>), <b>100%</b> (<kbd>1</kbd> : un pixel du capteur = un pixel de l'écran), <b>{ui('Reset')}</b> (<kbd>R</kbd>).",
    f"<b>{ui('Segui ultimo')}</b> (<kbd>U</kbd>) : affiche automatiquement chaque nouvelle photo. Comme les deux boutons suivants, c'est une icône, en surbrillance quand elle est active ; il est actif à l'ouverture.",
    f"<b>{ui('Blocca vista')}</b> (<kbd>K</kbd>) : conserve le zoom et la position quand vous changez de photo, pour comparer la mise au point au même endroit. Actif à l'ouverture.",
    "<b>Guides de composition</b> (<kbd>G</kbd>) : à chaque clic, tiers, croix au centre, tiers et centre, aucun. Lignes de 1 pixel qui suivent le zoom et le déplacement ; elles fonctionnent aussi en visée en direct.",
    f"<b>{ui('Ispettore')}</b> (<kbd>I</kbd>) : histogrammes, pixels brûlés et noirs, valeurs sous le pointeur (voir ci-dessous). Ouvert à l'ouverture de la visionneuse.",
    "<b>Plein écran</b> (<kbd>F</kbd>).",
    "<b>?</b> : ce guide, au chapitre de la visionneuse.",
    f"<b>Vignettes</b> : un clic ouvre la photo. <i>{ui('P')}</i> = photo test, <i>{ui('C')}</i> = image de calibration, <i>{ui('E')}</i> = photo pour l'exposition, <i>AF</i> = prises de l'autofocus, les numéros sont les photos de la séquence. La bande montre seulement la séquence en cours ou la dernière : elle se vide au démarrage d'une séquence, et la première photo test prise ensuite en commence une nouvelle. Les fichiers restent dans le dossier.",
    f"<b>{ui('Svuota')}</b>, en bas à droite de la bande des vignettes quand il y a des photos : repart de zéro. Les photos quittent la visionneuse et la séquence redevient {ui('Pronta')} ; les fichiers restent dans le dossier.",
], layout="full", anchors={n: "bb" if n in (7, 9, 11) else "b" for n in range(1, 12)})}
<p>À la souris : faites glisser pour déplacer l'image, molette (ou pincement sur le trackpad) pour zoomer autour du
pointeur, double-clic pour passer de « ajuster » à 100 % et inversement. Au-delà de 150 %, les pixels restent nets,
sans flou.</p>
{fig("visualizzatore-live", [
    f"<b>{ui('■ Ferma live')}</b> revient aux photos ; ◀ ▶ ou un clic sur une vignette quittent aussi la visée en direct.",
    f"État de la visée en direct : {ui('LIVE')}, {ui('SCATTO…')}, {ui('IN PAUSA')} pendant la séquence.",
], layout="full", anchors={1: "b"}, caption="La visée en direct dans la visionneuse, ici avec le simulateur au point (le damier est net). À 100 %, la visée en direct a la résolution de l'aperçu de l'appareil photo, inférieure à celle des photos.")}
<h2>Autofocus sur un point</h2>
<p>L'autofocus trouve tout seul la position du focuser où un détail choisi est le plus net : un repère, un poil, le bord
d'une structure. Il sert par exemple à fixer avec précision le début ou la fin de la pile.</p>
<ol class="steps">
<li>Appuyez sur <span class="ui">⌖ Autofocus</span> (touche <kbd>A</kbd>) et cliquez sur le détail : un carré bleu
  apparaît, la zone mesurée. Son côté se règle avec le curseur <b>Zone</b> ou avec <kbd>[</kbd> <kbd>]</kbd> ; un autre
  clic déplace le carré. Le glissement et le zoom fonctionnent comme d'habitude.</li>
<li>Choisissez le <b>mode</b> (Rapide, Précis ou Vraies prises) et vérifiez la <b>course</b> : la barre et la ligne en
  dessous indiquent de combien le focuser va bouger et jusqu'où il s'approchera de l'échantillon. Puis appuyez sur
  <span class="ui">Démarrer</span> : le focuser se déplace dans le même sens que la pile et la courbe de netteté
  s'allonge d'un point à la fois.</li>
<li>À la fin, le focuser revient à la position la plus nette : il la dépasse d'abord du <b>dépassement</b> et y arrive
  dans le même sens que le balayage, pour que le jeu de la mécanique ne déplace pas la mise au point. Puis il fait une
  <b>prise de vérification</b>, le losange vert du graphique. Dans la ligne en dessous, <span class="ui">Utiliser la mise au point comme</span>
  <span class="ui">début de pile</span> ou <span class="ui">fin de pile</span> écrit la position dans la séquence, dans la fenêtre principale.</li>
</ol>
{fig("visualizzatore-autofocus", [
    "<b>⌖ Autofocus</b> (<kbd>A</kbd>) : ouvre le panneau ; un clic sur l'image choisit la zone. <kbd>Échap</kbd> le ferme.",
    "<b>Zone mesurée</b> : en pointillés pendant l'autofocus. Elle reste au même endroit si l'on change de prise ou si l'on passe à la visée en direct.",
    "<b>Mode</b> : <i>Rapide</i>, <i>Précis</i> (par défaut) ou <i>Vraies prises</i> ; en dessous, ce qu'il va faire. <b>Recherche large</b> l'active quand l'image est entièrement floue. <b>Zone</b> : côté du carré en pixels du capteur. La <b>barre de course</b> va de − à + l'excursion maximale autour du départ : en clair la course prévue, plus foncé le trajet déjà parcouru, le trait est la position actuelle.",
    "<b>Courbe de netteté</b> : un point par mesure, la position du focuser en horizontal ; en dessous, le pas. Les passes précédentes restent plus pâles sous la passe en cours, et le graphique zoome sur la zone de la passe fine. Les carrés orange sont les vraies prises de confirmation, la ligne verte la position choisie, le losange vert la prise de vérification. En survolant un point on lit sa position et sa netteté (en % du maximum).",
    "<b>État</b> : passe, prise en cours et position, puis le résultat avec la vérification et la largeur du pic, ou la raison pour laquelle la mise au point n'a pas été trouvée.",
    "<b>Recommencer</b> et, en dessous, <b>Utiliser la mise au point comme début de pile / fin de pile</b>, tant que le focuser reste sur la position trouvée. <b>Recommencer</b> relance l'autofocus ; un clic sur un autre point déplace la zone sans fermer le panneau. Pendant la mesure il y a <b>Arrêter</b>.",
], layout="full", anchors={6: "r"})}
<p>À chaque prise, l'app mesure la netteté des bords dans la zone (le gradient de luminosité, divisé par la luminosité
moyenne, pour que l'exposition ne compte pas). Loin de la mise au point la courbe est plate ; près d'elle, elle monte en
un pic étroit. L'app ajuste une courbe sur les points autour du maximum : la position trouvée peut donc tomber entre
deux prises. La passe s'arrête toute seule dès que le pic est dépassé ; si le pic est au-delà de la dernière prise elle
continue, s'il est avant la première elle repart plus en arrière. Avec les RAW, elle mesure l'aperçu JPEG contenu dans
le fichier : lors des essais sur de vraies piles, il donne la même mise au point que le RAW développé.</p>
<div class="box tip"><span class="t">Choisir la zone</span>Un détail contrasté, tout à la même profondeur. Si la zone
contient deux éléments à des mises au point différentes (la patte et le corps d'un insecte), la courbe a deux pics et
l'app le signale en orange : réduisez la zone sur le détail qui vous intéresse. Sur un fond uniforme il n'y a rien à
mesurer et l'autofocus s'arrête avec un message.</div>
<h3>Les modes</h3>
<p>La <b>visée en direct</b> est plus rapide, mais son image est petite et compressée, et bruitée en faible lumière ; les
<b>vraies prises</b> mesurent la photo telle qu'elle sera dans la pile, mais demandent quelques secondes chacune. Les
modes combinent les deux :</p>
<ul>
<li><b>Rapide</b> : visée en direct seulement, une passe. Pour chercher la mise au point et pour les essais.</li>
<li><b>Précis</b> (par défaut) : deux passes en visée en direct, puis <b>3 vraies prises de confirmation</b> autour de la
  mise au point trouvée. La mise au point est recalculée sur ces prises (si la plus nette est au bord, une ou deux sont
  ajoutées) et la prise de vérification est aussi une vraie prise. C'est le mode pour fixer le début ou la fin d'une pile.</li>
<li><b>Vraies prises</b> : tout le balayage avec de vraies prises. Le plus sûr et le plus lent.</li>
</ul>
<p>Chaque mode garde ses propres réglages (pas, prises par passe, passes, images, prises de confirmation), qui se
modifient dans <span class="ui">Configuration › Autofocus</span>.</p>
<p>Avec des prises réelles (<i>Précis</i> et <i>Vraies prises</i>), la visée en direct s'éteint avant la
première prise, comme pour une photo test, et reste éteinte jusqu'à la fin de l'autofocus : l'appareil ne passe pas
sans cesse de la visée à la prise de vue. Elle redémarre seule quand vous déplacez le focuser. Si l'appareil se
déconnecte pendant une prise, l'app réessaie et le reconnecte ; si les déconnexions se répètent, vérifiez
l'alimentation : une fausse batterie (<i>dummy battery</i>) qui ne tient pas le pic de la prise de vue déconnecte
l'appareil de l'USB.</p>
<div class="box warn"><span class="t">Excursion maximale : elle protège le sujet</span>L'autofocus ne s'éloigne jamais de
la position de départ de plus que l'<b>excursion maximale</b> (± pas, dans la barre de course). Si la passe devait
s'allonger au-delà, parce que la mise au point est plus loin que prévu, il s'arrête et le signale au lieu de continuer
vers l'échantillon. La valeur calculée couvre la course prévue avec une marge ; diminuez-la si l'échantillon est
proche de l'objectif.</div>
<div class="box warn"><span class="t">Vérification basse : le jeu</span>Si la prise de vérification est bien moins nette
que le maximum de la courbe (moins de 80 %), l'app le signale en orange : en général le jeu de la mécanique est plus
grand que le dépassement. Augmentez-le dans <span class="ui">Configuration › Autofocus</span> ; au départ il vaut la
compensation du jeu de la séquence, mais au moins une largeur du pic.</div>
<p>Toutes les valeurs sont dans <span class="ui">Configuration › Autofocus</span>, chapitre 12.</p>
<h2>{ui('Ispettore')}</h2>
<p>Le panneau <span class="ui">{ui('Ispettore')}</span> (touche <kbd>I</kbd>) contrôle l'exposition d'une photo avec les
mêmes règles que Focus Fusion. Il est en lecture seule : il ne modifie pas les photos. Il fonctionne aussi sur la visée
en direct, mis à jour toutes les demi-secondes.</p>
{fig("ispettore", [
    f"<b>Pixels brûlés et noirs</b> : pourcentage et règles utilisées. <span class='ui'>{EVID}</span> marque en rouge les pixels brûlés et en bleu les noirs ; les deux boutons les affichent ou les masquent séparément.",
    "<b>Histogrammes</b> du rouge, du vert, du bleu et de la luminance. En plaçant le pointeur sur un niveau, on lit combien de pixels il contient.",
    "<b>Sous le pointeur</b> : les valeurs R, G, B et la luminance du pixel sur lequel se trouve la souris.",
], layout="full")}
<p>Avec les photos RAW, l'Inspecteur travaille sur l'aperçu converti ; pour le niveau exact du capteur, utilisez
<span class="ui">{ui('Esposizione dei light')}</span> (7.6), qui mesure les vrais RAW.</p>
""")

# 9
add(f"""
<h1><span class="n">9</span>Limites de sécurité</h1>
<p class="lead">Les limites empêchent l'objectif de toucher la lame et la mécanique d'arriver en butée. Il faut
les définir avant tout, sans se presser.</p>
<p>L'onglet <b>{ui('Configurazione')}</b> est une page unique, divisée en groupes {ui('Focheggiatore')}, {ui('App')} et
{ui('Sistema')}. Les onglets {ui('Ottica')} et {ui('Calibrazione')} sont construits de la même façon.</p>
{fig("configurazione", [
    f"<b>{ui('Cerca')}</b> : tapez une partie d'un nom (par exemple « jeu ») et seules les lignes qui le contiennent restent.",
    "<b>Index</b> : un clic mène à la section ; l'entrée en surbrillance suit le défilement. Un point signale des modifications non enregistrées ou une mise à jour disponible.",
    "<b>Titre de la section</b> ; le <b>?</b> ouvre le guide à cet endroit.",
    f"<b>{ui('Dettagli')}</b> : les explications plus longues, fermées au départ.",
    f"<b>{ui('Riepilogo')}</b>, toujours visible : résolution, course utile, firmware, version de l'app et suivi sur smartphone.",
], layout="full")}
<p>Presque tout s'enregistre dès que vous changez une valeur : les réglages du moteur partent aussitôt au firmware,
la mécanique et les autres options dans les réglages de l'app. Les limites, ci-dessous, font exception.</p>
{fig("fine-corsa", [
    f"<b>{ui('Fine corsa inferiore')}</b> en pas ; <span class='ui'>⌖ {ui('Usa posizione attuale')}</span> la reprend de la position du focuser.",
    f"<b>{ui('Fine corsa superiore')}</b>. Vide = le maximum du firmware.",
    f"<b>Vers l'échantillon</b> : si, en se rapprochant de l'échantillon, le nombre de pas diminue ou augmente. Sert à étiqueter correctement {ui('Avvicina')}/{ui('Allontana')}.",
    f"<b>{ui('Salva fine corsa')}</b>, dans la barre <i>{ui('Modifiche non salvate')}</i> qui apparaît quand vous changez une valeur ; <b>{ui('Annulla')}</b> revient aux valeurs enregistrées. C'est la seule partie de la Configuration qui ne s'enregistre pas toute seule.",
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
<li>Amenez la platine à la position utile la plus éloignée, cliquez sur <span class="ui">⌖ {ui('Usa posizione attuale')}</span>
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
    "<b>Résultat</b> : µm par pas, pas par µm, µm pour 1000 pas. Les modifications sont enregistrées automatiquement.",
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
<p>Le calcul se trouve en bas de l'onglet <b>{ui('Ottica')}</b>, dans le groupe <b>{ui('Strumenti')}</b> (le résultat apparaît aussi dans le récapitulatif à droite), et utilise l'ouverture numérique, le grossissement sur le
capteur (objectif × changeur intermédiaire × adaptateur) et le pixel du capteur du profil ouvert (chapitre 7.2).</p>
{fig("profondita", [
    f"<b>{ui('Sovrapposizione (%)')}</b> entre une tranche nette et la suivante ; 20 à 30 % est une bonne valeur.",
    "<b>Résultat</b> : profondeur de champ, pas conseillé en µm et en pas moteur.",
    f"<b>{ui('Usa come passo della sequenza')}</b> : copie la valeur en pas dans le champ Pas de la séquence.",
], layout="side narrow")}
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
<div class="box tip"><span class="t">Optovar, adaptateurs et oculaires de projection</span>Dans le profil optique
(chapitre 7.2), indiquez le facteur du changeur de grossissement intermédiaire et celui de l'adaptateur ou de l'oculaire
de projection : l'app les multiplie par le grossissement de l'objectif. Par exemple, 10× avec Optovar 1,6× et adaptateur
0,63× = 10 × 1,6 × 0,63 ≈ 10,1× sur le capteur. Seul le second terme de la formule change, et il compte davantage avec
les objectifs faibles. Pour une échelle exacte en µm, mesurez les µm par pixel avec un micromètre objet : les facteurs
inscrits sur les accessoires sont nominaux.</div>

<h2>11.2 Début, fin et nombre de photos</h2>
<ol class="steps">
<li>Activez la visée en direct (de préférence dans la visionneuse, zoomée) et amenez la mise au point <b>juste
  au-dessus</b> de la partie la plus haute du sujet que vous voulez net : cliquez sur <span class="ui">⌖ {ui('qui')}</span>
  à côté de <b>{ui('Inizio')}</b>.</li>
<li>Descendez <b>juste en dessous</b> de la partie la plus basse et cliquez sur <span class="ui">⌖ {ui('qui')}</span> à côté
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
TRATTO = ui("Tratto massimo per comando (passi)").split(" (")[0]
add(f"""
<h1><span class="n">12</span>Moteur, commandes manuelles, autofocus, mises à jour, température</h1>
<h2>{ui('Motore (firmware)')}</h2>
{fig("motore", [
    f"<b>{ui('Microstep')}</b> : {ui('passo intero')}, 1/2 … 1/32 (voir 10.2). Le modifier change l'échelle des positions : vérifiez ensuite à nouveau les limites.",
    f"<b>{ui('Velocità')}</b> du firmware : {ui('Lenta').lower()}, {ui('Media').lower()}, {ui('Veloce').lower()}. Avec le myFocuserPro2 et le firmware build 7, la vitesse maximale des mouvements est de 80, 200 et 400 pas par seconde ; chaque mouvement démarre à 40 pas par seconde et accélère.",
    f"<b>{ui('Alimentazione bobine motore')}</b> : avec <b>{ui('Sempre quando connesso')}</b>, le moteur maintient sa position à l'arrêt, mais chauffe. <b>{ui(COIL_HOLD)}</b> (désactivée au départ ; seulement avec la première activée) : si vous la laissez désactivée, les bobines s'éteignent quand vous déconnectez le focuser ou fermez l'app, et le moteur ne chauffe pas pendant des heures ; le premier mouvement les rallume. Activez-la si le poids peut faire descendre une glissière verticale. Nécessite le firmware build 8.",
    f"<b>{ui('Alimentale comunque durante la sequenza')}</b> (apparaît quand les bobines sont éteintes ; activée par défaut) : les bobines s'allument au lancement de la pile et s'éteignent de nouveau après le retour au début.",
    f"<b>{ui('Inverti verso di rotazione')}</b>.",
    f"<b>{ui('Compensa il gioco IN')} / OUT</b> : à chaque inversion vers des positions plus basses (IN) ou plus hautes (OUT), le firmware ajoute des pas sans les compter, y compris avec les boutons physiques.",
    "<b>Jeu IN / OUT</b> en pas, de 0 à 255 (voir 10.5).",
    f"<b>{ui('Rileggi')}</b> les valeurs du firmware.",
])}
<div class="box warn"><span class="t">Bobines éteintes : la glissière peut ne pas avancer</span>Sans courant à l'arrêt, à
chaque arrêt la charge peut faire reculer la glissière, et en micropas le moteur revient aussi au pas entier le plus
proche : le compteur avance, mais pas la glissière. C'est pourquoi, avec les bobines éteintes, l'app les allume pendant
la séquence (repère 4) et un avertissement orange le rappelle si vous désactivez l'option. Si le moteur chauffe trop,
baissez le courant sur le driver plutôt que d'éteindre les bobines.</div>
<h2>{ui('Comandi manuali')}</h2>
{fig("comandi-manuali", [
    f"<b>Tailles de pas</b> des boutons {ui('Allontana')}/{ui('Avvicina')} : par puissances de dix jusqu'à 1000, 10 000 ou 100 000 pas. Avec un réducteur, il faut de grandes tailles de pas.",
    f"<b>{ui('Tieni premuto per muovere senza fermarti')}</b> : au relâchement, le moteur ralentit et s'arrête ; il s'arrête de toute façon à la limite et, si la page ne répond plus, après environ une seconde.",
    f"<b>{TRATTO}</b> : en maintenant le bouton enfoncé, le moteur ne va jamais plus d'un tronçon (500 pas par défaut) au-delà de la dernière confirmation de la page que le bouton est toujours enfoncé.",
], layout="side")}
<p>Le mouvement continu fonctionne ainsi par sécurité : si la communication s'interrompt (réseau, app bloquée, câble), le
moteur parcourt au plus un tronçon. Avec le <b>firmware build 5</b>, à chaque confirmation la cible est repoussée d'un
tronçon et le moteur ne s'arrête jamais ; avec un firmware plus ancien, il avance d'un tronçon à la fois, avec une brève
pause entre deux tronçons (des tronçons courts sont plus sûrs, mais plus saccadés). Depuis la <b>build 4</b>, il y a une
protection supplémentaire : pendant le mouvement continu, le focuser s'arrête tout seul s'il ne reçoit plus de commandes
du Mac pendant 1,5 s. <span class="ui">{ui('Vai')}</span>, les
boutons en un seul clic et la séquence arrivent en revanche toujours à destination, même si le mouvement dure de
nombreuses secondes.</p>
<h2>Autofocus</h2>
<p>Les réglages de l'autofocus sur un point (chapitre 8) : d'abord le mode et ses réglages, puis ceux communs à tous
les modes. Les champs vides utilisent la valeur par défaut, écrite en gris dans le champ ; pas et prises se calculent
à partir de la <b>largeur du pic</b>, c'est-à-dire l'intervalle de pas où la netteté reste au-dessus de la moitié du
maximum.</p>
{fig("autofocus-config", [
    "<b>Mode</b> utilisé par la visionneuse, avec le résumé de ce qu'il fait. Se choisit aussi dans le panneau.",
    "<b>Réglages du mode</b> : images (visée en direct ou vraies prises), pas et prises de la passe fine, passes. Vide = valeur par défaut du mode ou calculée d'après la largeur du pic. <b>Rétablir le mode</b> revient aux valeurs initiales.",
    "<b>Confirmation par de vraies prises</b> (avec la visée en direct) : combien de vraies prises autour de la mise au point trouvée ; 0 = pas de confirmation.",
    "<b>Recherche large</b> si l'image est entièrement floue, avec son amplitude (± pas) et son pas, une largeur du pic : quelques prises très espacées.",
    "<b>Excursion maximale ±</b> depuis la position de départ : au-delà, l'autofocus s'arrête. En dessous, attente après le mouvement et <b>dépassement pour le jeu</b>.",
    "<b>Largeur du pic</b> utilisée pour les calculs et son origine. <b>Oublier la mesure</b> revient à l'estimation.",
], layout="side", anchors={2: "r", 4: "r"})}
<p>La première fois, la largeur du pic est estimée d'après la profondeur de champ du profil optique choisi dans la
séquence et la mécanique (µm par pas) ; sans profil, d'après la course entre les limites. Après chaque autofocus
réussi, l'app enregistre la largeur mesurée pour ce profil et l'utilise ensuite. La première estimation est
approximative : si le pic est plus large que prévu la passe s'allonge toute seule, s'il est plus étroit elle répète la
mesure avec un pas plus fin. Le <b>dépassement pour le jeu</b> est la distance dont le focuser dépasse une position avant
d'y revenir : il doit être supérieur au jeu de la mécanique. <span class="ui">Rétablir les valeurs calculées</span>
vide les champs communs saisis à la main. Si la recherche large est désactivée et que la mise au point est loin,
l'autofocus s'arrête et propose de l'activer.</p>
<h2>{ui('Aggiornamenti')}</h2>
{fig("aggiornamenti", [
    "Version de l'<b>app</b> et résultat de la dernière vérification.",
    "Version du <b>firmware</b> sur le focuser.",
    f"<b>{ui('Aggiorna firmware')}</b> : environ 20 secondes, les réglages du focuser sont conservés. Ne débranchez pas le câble ; en cas de problème, il suffit de recommencer. La build 5 rend le mouvement continu quand le bouton est maintenu enfoncé ; depuis la build 4, il y a l'arrêt automatique si le Mac cesse de communiquer. La build 7 démarre les mouvements plus doucement (40 pas par seconde) et divise par deux la vitesse lente du myFocuserPro2.",
    f"<b>{ui('Controlla ora')}</b> s'il existe des mises à jour de l'app.",
], layout="side")}
<p>L'app choisit toute seule le firmware adapté à la carte (myFocuserPro2 ou Ardufocus). L'<b>Ardufocus</b> ne
redémarre pas par le câble USB : pendant la mise à jour, l'app vous demande d'appuyer sur le <b>bouton reset</b> de la
carte.</p>
<p>La carte n'enregistre la position et les réglages dans sa mémoire permanente qu'une dizaine de secondes après le
dernier mouvement. Pour ne pas perdre la position, l'app la fait enregistrer immédiatement chaque fois qu'elle ferme la
connexion ({ui('Disconnetti')}, sortie de l'app, mise à jour).</p>
<h2>{ui('Temperatura')}</h2>
<p>La température actuelle de la sonde est dans la barre du haut. Le graphique des 60 dernières minutes se trouve dans
le récapitulatif de l'onglet <b>{ui('Calibrazione')}</b> (chapitre 7.6), à côté des darks. La température de chaque photo
est enregistrée dans <code>sequence.json</code> et résumée dans <code>sequence.txt</code> : utile, car la mise au point
dérive avec la dilatation thermique.</p>
""")

# 13
add(f"""
<h1><span class="n">13</span>Une session type, étape par étape</h1>
<h2>Une seule fois (ou quand la mécanique change)</h2>
<ol class="steps">
<li><b>Mécanique</b> : saisissez les données et vérifiez la résolution par une mesure (chapitre 10).</li>
<li><b>Sens de l'échantillon</b> et <b>limites</b>, avec les limites écrites dans le firmware (chapitre 9).</li>
<li><b>Jeu</b> : mesurez-le avec la visée en direct et choisissez où le compenser (séquence ou firmware).</li>
<li><b>Moteur</b> : vérifiez les bobines (chapitre 12) et, si l'app le propose, mettez à jour le firmware.</li>
<li><b>Profils optiques</b> : dans l'onglet {ui('Ottica')}, enregistrez un profil pour chaque combinaison d'objectif, de
  filtre et d'éclairage, au microscope ou en macro (chapitres 7.2 et 7.3).</li>
<li><b>Préréglages</b> : pour chaque objectif, calculez le pas à partir de la profondeur de champ et enregistrez un
  préréglage ; le préréglage retient aussi le profil optique.</li>
</ol>
<h2>À chaque session</h2>
<ol class="steps">
<li>Allumez le focuser et l'appareil photo (mode M), branchez les câbles et ouvrez Focus Stack.</li>
<li>Le focuser et l'appareil photo se connectent tout seuls ; sinon, appuyez sur <b>{ui('Connetti')}</b> dans l'onglet {ui('Sessione')}.</li>
<li>Réglez le temps de pose, l'ISO et le format ; faites une <b>photo test</b> et contrôlez-la dans la visionneuse à 100 %.</li>
<li>Choisissez le <b>préréglage</b> de l'objectif (ou le pas) et vérifiez le <b>profil optique</b> dans la séquence.</li>
<li>Avec la <b>visée en direct</b> et le clavier, trouvez la <b>fin</b> et le <b>début</b> de la séquence et cliquez sur ⌖ {ui('qui')}.</li>
<li>Si nécessaire, préparez les <b>darks</b> et les <b>flats</b> et calculez l'exposition des lights (chapitre 7.6).</li>
<li>Contrôlez le récapitulatif : nombre de photos, course, durée, aucun avertissement rouge.</li>
<li><b>{ui('▶ Avvia sequenza')}</b>. Ne touchez pas le microscope : les vibrations gâchent les photos. Pour la suivre à
  distance, utilisez le suivi sur smartphone (chapitre 7.7).</li>
<li>En fin de séquence, cliquez sur <b>{ui('Apri nel Finder')}</b> et ouvrez le dossier dans le logiciel de fusion.</li>
</ol>
""")

# 14
add(f"""<h1><span class="n">14</span>En cas de problème</h1>
<p>Le <b>{ui('Registro')}</b> (le dernier onglet) liste avec l'heure chaque connexion, déplacement, photo et erreur : en
cas de problème, lisez-le en premier. En haut, vous pouvez chercher des mots et n'afficher que les avertissements (⚠)
et les erreurs (✖). Si vous signalez un problème, appuyez sur <b>{ui('Esporta')}</b> : le journal est enregistré
dans un fichier texte du dossier Téléchargements, avec les versions de l'app et du firmware et les données du focuser
et de l'appareil photo, sans la clé du lien pour le smartphone ni votre nom d'utilisateur. Joignez ce fichier au signalement.</p>
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
    ["Toute la pile est sur le même plan : la glissière n'avance pas", f"Les bobines du moteur sont éteintes et la charge fait reculer la glissière à chaque arrêt (chapitre 12) : laissez activée l'option <i>{ui('Alimentale comunque durante la sequenza')}</i>. Faites un essai avec un petit déplacement en regardant la visée en direct."],
    ["La séquence s'est mise en pause toute seule", f"La photo a échoué même après la reconnexion de l'appareil photo. Lisez le message, vérifiez la batterie, le câble et la carte, puis cliquez sur <i>{ui('Riprendi')}</i> : la photo est refaite à la même position."],
    ["L'appareil photo disparaît au milieu de la pile", "En général, le Mac s'est mis en veille et a suspendu l'USB. Pendant la séquence, l'app l'en empêche, mais pas si vous fermez l'écran d'un portable sans moniteur externe. Vérifiez aussi la batterie de l'appareil photo."],
    ["Le smartphone n'ouvre pas la page de suivi", f"Le téléphone doit être sur le même réseau Wi-Fi que le Mac ; au premier lancement, macOS demande d'autoriser les connexions entrantes (répondez Autoriser). Après <i>{ui('Nuovo link')}</i>, l'ancien code n'est plus valable."],
]))

# 15
add(f"""<h1><span class="n">15</span>Raccourcis clavier</h1>
<div class="two">
<div class="keep"><h2 style="margin-top:0">Onglet {ui('Sessione')}</h2>
<table><tbody>
<tr><td><kbd>↑</kbd></td><td>éloigner l'objectif de l'échantillon</td></tr>
<tr><td><kbd>↓</kbd></td><td>rapprocher l'objectif de l'échantillon</td></tr>
<tr><td><kbd>↑</kbd>/<kbd>↓</kbd> maintenues enfoncées</td><td>mouvement continu jusqu'au relâchement</td></tr>
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
<tr><td><kbd>I</kbd></td><td>{ui('Ispettore')}</td></tr>
<tr><td><kbd>G</kbd></td><td>guides de composition</td></tr>
<tr><td><kbd>A</kbd></td><td>autofocus : ouvre le panneau, puis clic sur le détail</td></tr>
<tr><td><kbd>[</kbd> <kbd>]</kbd></td><td>zone de l'autofocus plus petite / plus grande</td></tr>
<tr><td><kbd>Échap</kbd></td><td>ferme l'autofocus</td></tr>
<tr><td><kbd>F</kbd></td><td>plein écran</td></tr>
</tbody></table></div>
</div>
<p style="margin-top:8mm;color:#5a6b80;font-size:9pt">Focus Stack est un logiciel libre (licence MIT) ·
github.com/teoteo/focus-stack · Le firmware est dérivé de myFocuserPro2 de Robert Brown (licence MIT).</p>
""")
