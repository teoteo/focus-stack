"use strict";
// Ponte con l'app per Mac (packaging/mac): esiste solo dentro la sua finestra. In un browser, su Linux o
// sul telefono window.FSNative è null e l'interfaccia fa tutto da sola, come prima.
// Ogni messaggio va a WKScriptMessageHandlerWithReply "focusstack": postMessage restituisce una Promise.
// Barra nel Dock e notifiche di fine pila le gestisce l'app da sola, dallo stato del server (Bridge.track).
window.FSNative = (() => {
  const h = window.webkit && window.webkit.messageHandlers && window.webkit.messageHandlers.focusstack;
  if (!h) return null;
  const send = (cmd, data = {}) => h.postMessage({ cmd, ...data });
  return {
    // finestra "Scegli cartella" nativa: il percorso scelto, oppure null se annullata
    chooseFolder: (start, prompt) => send("chooseFolder", { start, prompt }),
    // tema della pagina → aspetto della barra del titolo
    theme: (theme) => send("theme", { theme }),
    // preferenze dell'app per Mac (le tiene l'app): viewerOtherScreen
    getPref: (key) => send("getPref", { key }),
    setPref: (key, value) => send("setPref", { key, value }),
  };
})();
