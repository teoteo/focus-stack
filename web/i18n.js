"use strict";
// Traduzioni dell'interfaccia. La lingua e le stringhe arrivano dal server con /lang.js (caricato prima
// di questo file): window.FS_LANG ("it", "en"…) e window.FS_STRINGS {testo italiano: traduzione}.
// Le chiavi sono il testo italiano, quindi senza traduzione resta l'italiano.
const LANG = window.FS_LANG || "it";
const STRINGS = window.FS_STRINGS || {};
const LOCALE = { it: "it-IT", en: "en-GB", fr: "fr-FR", de: "de-DE", es: "es-ES" }[LANG] || LANG;

// t(testo italiano) oppure t(testo con {nome}, { nome: valore }): traduzione con segnaposto
function t(key, params) {
  let s = Object.prototype.hasOwnProperty.call(STRINGS, key) ? STRINGS[key] : key;
  if (params) s = s.replace(/\{(\w+)\}/g, (m, k) => (k in params ? String(params[k]) : m));
  return s;
}

// numeri secondo la lingua: separatore decimale e delle migliaia
const fmtNum = (x, digits = 0, grouping = true) =>
  Number(x).toLocaleString(LOCALE, { minimumFractionDigits: digits, maximumFractionDigits: digits, useGrouping: grouping });

// Traduce i testi fissi dell'HTML: nodi di testo e attributi title/placeholder/aria-label/alt.
// Un elemento con data-i18n-html si traduce tutto insieme (il suo innerHTML è la chiave), per le frasi
// con grassetti o link dentro; data-i18n-skip esclude un elemento e i suoi discendenti.
const I18N_ATTRS = ["title", "placeholder", "aria-label", "alt"];
const squash = (s) => s.replace(/\s+/g, " ").trim();

function translateDom(root = document.body) {
  if (LANG === "it") return;
  const walk = (el) => {
    if (el.nodeType !== 1 || el.hasAttribute("data-i18n-skip") || ["SCRIPT", "STYLE"].includes(el.tagName)) return;
    for (const a of I18N_ATTRS) {
      const v = el.getAttribute(a);
      if (v && /\p{L}/u.test(v)) el.setAttribute(a, t(squash(v)));
    }
    if (el.hasAttribute("data-i18n-html")) { el.innerHTML = t(squash(el.innerHTML)); return; }
    for (const n of el.childNodes) {
      if (n.nodeType === 3) {
        const key = squash(n.nodeValue);
        if (key && /\p{L}/u.test(key)) {
          const lead = n.nodeValue.match(/^\s*/)[0], trail = n.nodeValue.match(/\s*$/)[0];
          n.nodeValue = lead + t(key) + trail;
        }
      } else walk(n);
    }
  };
  walk(root);
  document.title = t(document.title);
}

document.documentElement.lang = LANG;
document.addEventListener("DOMContentLoaded", () => translateDom());
