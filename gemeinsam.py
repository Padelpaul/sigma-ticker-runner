# -*- coding: utf-8 -*-
"""Gemeinsame Bausteine: Normalisierung, Keyword-Laden, Matching, Firmenschluessel."""
import re, html, unicodedata

# ---------------------------------------------------------------- Normalisierung
UMLAUT = str.maketrans({"ä": "ae", "ö": "oe", "ü": "ue", "Ä": "ae", "Ö": "oe",
                        "Ü": "ue", "ß": "ss", "é": "e", "è": "e", "á": "a", "à": "a"})

def fold(t):
    """Kleinschreibung + Umlaute gefaltet. Beide Seiten des Vergleichs laufen hierdurch,
    deshalb ist 'zahlungsunfaehig' == 'zahlungsunfähig'."""
    if not t:
        return ""
    t = unicodedata.normalize("NFC", t)
    return t.translate(UMLAUT).lower()

def strip_html(s):
    s = re.sub(r"<[^>]+>", " ", s or "")
    return re.sub(r"\s+", " ", html.unescape(s)).strip()

def norm(t):
    """Gefaltete, satzzeichenfreie Form fuer Aehnlichkeitsvergleiche."""
    t = fold(t)
    t = re.sub(r"[^a-z0-9 ]", " ", t)
    return re.sub(r"\s+", " ", t).strip()

STOP = set(("der die das und oder von zu in im mit fuer auf ist wird werden bei nach aus dem den "
            "des ein eine einer wie was warum mehr als auch nicht vor um euro mio mrd millionen "
            "milliarden prozent neue neuer wegen soll sollen droht nun jetzt hat haben sich es "
            "aber doch schon noch nur so dass wenn weil ueber unter gegen ohne durch bis seit").split())

def sig(t):
    return frozenset(w for w in norm(t).split() if len(w) >= 4 and w not in STOP)

def jacc(a, b):
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)

# ---------------------------------------------------------------- Keywords
def load_keywords(pfad):
    stark, schwach, akt = [], [], None
    with open(pfad, encoding="utf-8-sig") as f:
        for line in f:
            s = line.strip()
            if not s or s.startswith("#"):
                continue
            if s == "[STARK]":
                akt = stark; continue
            if s == "[SCHWACH]":
                akt = schwach; continue
            if akt is not None:
                akt.append(s)
    return stark, schwach

def build_matcher(begriffe):
    """Ein kompiliertes Regex je Begriff, auf Wortgrenzen, gefaltet."""
    out = []
    for b in begriffe:
        f = fold(b)
        pat = r"\b" + r"\W+".join(re.escape(w) for w in f.split()) + r"\w{0,3}\b"
        out.append((b, re.compile(pat)))
    return out

def treffer(text_gefaltet, matcher):
    return [b for b, rx in matcher if rx.search(text_gefaltet)]

# ---------------------------------------------------------------- Firmenschluessel
RECHTSFORMEN = (r"gmbh\s*&\s*co\.?\s*kgaa|gmbh\s*&\s*co\.?\s*kg|ag\s*&\s*co\.?\s*kg|"
                r"gmbh|aktiengesellschaft|\bag\b|\bse\b|\bkgaa\b|\bkg\b|\bohg\b|\bug\b|"
                r"\bggmbh\b|\be\.?\s?k\.?\b|\bmbh\b|\bgbr\b")
RX_RF = re.compile(RECHTSFORMEN)

WORT_STOP = set(("insolvenz insolvenzantrag insolvenzverfahren insolvenzverwalter eigenverwaltung "
                 "insolvenzgeld sanierung schutzschirm starug traditionsunternehmen traditionsbetrieb "
                 "unternehmen firma betrieb konzern gruppe hersteller haendler discounter kette "
                 "autozulieferer zulieferer maschinenbauer brauerei baecker baeckerei modehaus "
                 "modemarke verlag krise pleite aus ende jobs stellen mitarbeiter beschaeftigte "
                 "filialen standorte standort werk werke deutschland bayern nrw sachsen hessen "
                 "niedersachsen thueringen brandenburg saarland bremen hamburg berlin "
                 "wieder erneut zweiten dritten nach fast jahren jahre millionen umsatz kunden "
                 "januar februar maerz april mai juni juli august september oktober november "
                 "dezember montag dienstag mittwoch donnerstag freitag samstag sonntag "
                 "schliessung entscheidung zukunft zukunftsperspektive perspektive einzelhandel "
                 "branche handel industrie mittelstand markt marke restrukturierung stellenabbau "
                 "kurzarbeit gericht amtsgericht antrag verfahren eroeffnung uebernahme rettung "
                 "investor investoren geldgeber millionenumsatz jahresumsatz news bericht "
                 "kommentar analyse ueberblick liste zahl zahlen statistik anstieg rueckgang "
                 "kreuzfahrtanbieter manufaktur lokal restaurant gastronomie hotel klinik "
                 "vermoegen geschaeftsbetrieb moebelanbieter moebelanbieters anbieter "
                 "insolvenzverwalters sachwalters tochtergesellschaften gesellschaft "
                 "krankenhaus pflegedienst pflegeheim verein fussballclub").split())

def firmenschluessel(titel, beschreibung=""):
    """Heuristischer Firmenschluessel mit Konfidenz.
    Rueckgabe: (schluessel, kandidat, konfidenz) mit konfidenz in {"hoch","mittel",""}.
    Bewusst konservativ: ein falscher Schluessel wuerde zwei verschiedene Firmen
    zusammenfuehren, deshalb lieber leer lassen und dem Modell ueberlassen."""
    text = re.sub(r"\s+", " ", f"{titel}. {beschreibung}")
    gef = fold(text)
    GROSS = r"[A-Z\u00c4\u00d6\u00dc][\w\u00c4\u00d6\u00dc\u00e4\u00f6\u00fc\u00df.&\-]*"

    def clean(kand):
        toks = [k for k in norm(kand).split() if len(k) >= 3 and k not in WORT_STOP and k not in STOP]
        return [" ".join(toks[:2])] if toks else []

    # 1) Name unmittelbar vor einer Rechtsform -> hoch
    for m in RX_RF.finditer(gef):
        vorher = text[max(0, m.start() - 60):m.start()]
        toks = [t for t in re.findall(GROSS, vorher) if fold(t).strip(".&-") not in WORT_STOP]
        if toks:
            key = clean(" ".join(toks[-3:]))
            if key:
                kand = (" ".join(toks[-3:]) + " " + text[m.start():m.end()]).strip()
                return key[0], kand, "hoch"

    # 2) Marke in Anfuehrungszeichen -> hoch
    m = re.search(r'["\u201e\u00bb\u201c]([A-Z\u00c4\u00d6\u00dc][^"\u201c\u00ab\u201d]{2,40})["\u201c\u00ab\u201d]', text)
    if m:
        key = clean(m.group(1))
        if key:
            return key[0], m.group(1).strip(), "hoch"

    # 3) Erstes Wort des Titels vor Doppelpunkt oder Gedankenstrich -> mittel
    m = re.match(r"^(" + GROSS + r"(?: " + GROSS + r")?)\s*[:\u2013\u2014-]\s", titel)
    if m:
        key = clean(m.group(1))
        if key:
            return key[0], m.group(1).strip(), "mittel"

    # 4) Grosswort, das im Text mehrfach vorkommt -> mittel
    kand = []
    for t in re.findall(r"[A-Z\u00c4\u00d6\u00dc][\w\u00c4\u00d6\u00dc\u00e4\u00f6\u00fc\u00df\-]{3,}", titel):
        k = norm(t)
        if not k or k in WORT_STOP or k in STOP or len(k) < 4:
            continue
        vorkommen = len(re.findall(r"\b" + re.escape(k[:8]), norm(text)))
        kand.append((vorkommen, len(k), k, t))
    if kand:
        kand.sort(reverse=True)
        vor, _, k, t = kand[0]
        if vor >= 2:
            return k, t, "mittel"
    return "", "", ""
