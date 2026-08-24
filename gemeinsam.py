# -*- coding: utf-8 -*-
"""Gemeinsame Bausteine: Normalisierung, Keyword-Laden, Matching, Firmenschluessel."""

# Eine Kennung fuer ALLE Skripte. Sie laeuft in index.txt und im Blatt "Lauf" mit, damit
# Skilltext und Skriptstand nicht unbemerkt auseinanderlaufen (siehe SKILL.md, Fassung).
VERSION = "2026-08-21h"
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

# Laengenerhaltende Faltung: NUR fuer Faelle, in denen Trefferpositionen aus dem
# gefalteten Text zurueck auf den Originaltext angewandt werden. fold() macht aus "ä"
# zwei Zeichen und verschiebt damit jeden Offset dahinter (fruehere Folge: Kandidaten
# wie "Wärme Süß Gmb H in"). fold_pos() ersetzt zeichenweise, die Offsets bleiben gueltig.
UMLAUT_POS = str.maketrans({"ä": "a", "ö": "o", "ü": "u", "Ä": "a", "Ö": "o",
                            "Ü": "u", "ß": "s", "é": "e", "è": "e", "á": "a", "à": "a"})

def fold_pos(t):
    if not t:
        return ""
    return unicodedata.normalize("NFC", t).translate(UMLAUT_POS).lower()

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

# ---------------------------------------------------------------- Prio
# Fenster fuer Blatt 1: so viele Tage darf der Insolvenzantrag zurueckliegen. Aelteres
# gehoert auf Grenzfaelle, auch wenn der Fall gross ist (Vorgabe Sigma, 21.08.2026).
FENSTER_TAGE = 14
def prio_aus(alter_tage, score, urteil=""):
    """EINE Regel fuer die Prio, benutzt von aufbereiten.py und von render_xlsx.py.

    Aufteilung der Aufgaben (Vorgabe Sigma, 21.08.2026):
    Das Alter des Antrags ist der FILTER fuer Blatt 1, nicht das Rangkriterium. Nur Faelle,
    deren Insolvenzantrag hoechstens 14 Tage zurueckliegt, kommen auf die Liste. Innerhalb der
    Liste entscheidet der Mix aus dem Punkteschema (Groesse, Mandatsfaehigkeit, Werttreiber),
    Groesse ist dabei wichtig, aber nicht allein ausschlaggebend und ohne Obergrenze.
    """
    try:
        sc = float(score)
    except (TypeError, ValueError):
        sc = 0.0
    if urteil in ("verfolgen", "gepitcht"):
        return "hoch"
    if alter_tage is None or alter_tage > FENSTER_TAGE:
        # ausserhalb des Fensters, der Fall steht auf Grenzfaellen
        return "mittel" if sc >= 40 else "beobachten"
    return "hoch" if sc >= 60 else ("mittel" if sc >= 40 else "beobachten")


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
                 "krankenhaus pflegedienst pflegeheim verein fussballclub "
                 # Verfahrensvokabular, das sonst zum Firmenschluessel wird. Belegt im
                 # Lauflog vom 19. und 20.08.2026: zwoelf von zwanzig Neuzugaengen waren
                 # Fragmente wie "investorenprozess pik" oder "insolvenzverwaltung stc".
                 "insolvenzverwaltung insolvenzen insolvent investorenprozess investorenloesung "
                 "investorensuche sanierungsverfahren glaeubiger glaeubigerausschuss sachwalter "
                 "einschraenkungen fortfuehrung uebertragung liquidation zerschlagung "
                 "immobilien riese anleger pruefstand komponenten loesungen beteiligungen "
                 "stellt meldet droht rettet sucht laeuft bleibt kommt geht steht "
                 # Schlagzeilen-Adjektive: benennen keine Firma ("Grosser Kuechenhersteller
                 # meldet Insolvenz an", belegt 21.08.2026).
                 "grosser grosse grosses deutscher deutsche deutsches bekannter bekannte "
                 "bayerischer bayerische schwaebischer schwaebische norddeutscher sueddeutscher "
                 "traditionsreicher traditionsreiche beruehmter beruehmte insolventer insolvente "
                 # Rechtsformen. Ohne sie wird "gmbh" selbst zum Schluesselwort und es
                 # entstehen zwei Schluessel fuer dieselbe Firma ("gmbh thor" und "thor").
                 "gmbh mbh ag kg kgaa ohg gbr se eg ug ek co gmbhco aktiengesellschaft "
                 "kommanditgesellschaft "
                 # Frage- und Mengenwoerter aus Schlagzeilen. Ohne sie wird aus
                 # "Vivanco insolvent: Warum ..." der Kandidat "warum" und der echte
                 # Name verliert die Eindeutigkeitspruefung (Befund 21.08.2026).
                 "warum wieso weshalb wozu wann wohin woher diese dieser dieses jetzt "
                 "erst nur alle alles viele mehrere etliche einige zukunft schicksal "
                 "moeglichkeiten hammer kollaps ausverkauf startpreis dauerkrise").split())

# Gattungswoerter, die als EINZIGES Wort keinen Firmenschluessel ergeben duerfen. Zwei
# verschiedene Firmen teilen sie sich sonst ("Verteilte Systeme", "Korte Einrichtungen").
GENERIK = set(("systeme systems technik service handel produktion management investment "
               "precision components einrichtungen anlagenbau elektronik logistik metall "
               "bau baustoffe moebel maschinen automation technologies international "
               "engineering consulting solutions group holding partner werke verteilte").split())

# Gattungssuffixe: ein Wort, das so endet, beschreibt die Firma, es benennt sie nicht.
# Belegt am 21.08.2026: "Koelner Projektentwickler PANDION AG" bekam den Schluessel
# "koelner projektentwickler", "Immobilien-Riese" und "Baumarktkette" wurden zu Firmen.
# Der Filter greift nur in der Schluesselbildung und nur, wenn danach noch ein
# kennzeichnendes Wort uebrig bleibt; sonst bleibt der Schluessel lieber leer.
SUFFIX_GATTUNG = ("hersteller", "entwickler", "zulieferer", "anbieter", "betreiber",
                  "vermieter", "haendler", "bauer", "riese", "gigant", "kette",
                  "konzern", "gruppe", "unternehmen", "betrieb", "firma", "marke",
                  "spezialist", "ausstatter", "dienstleister", "produzent")


def _gattungshaft(tok):
    """True, wenn das Token nur beschreibt statt benennt."""
    return (tok in GENERIK
            or any(tok.endswith(s) and len(tok) > len(s) + 1 for s in SUFFIX_GATTUNG)
            or tok in SUFFIX_GATTUNG)

def gnews_echo(titel, beschreibung):
    """True, wenn die Beschreibung nur der Titel plus Outletname ist. Genau so liefern die
    Google-News-Metafeeds ihre Zeilen, und genau daran ist die Schluesselbildung am
    21.08.2026 gescheitert: die Pruefung "Wort kommt mindestens zweimal vor" war fuer JEDES
    Titelwort und fuer den Outletnamen automatisch erfuellt, deshalb wurden "chip",
    "minuten", "asatunews" oder "aachener" zu Firmenschluesseln."""
    if not titel or not beschreibung:
        return False
    basis = fold(re.sub(r"\s+-\s+[^-]{2,40}$", "", titel)).strip()
    if len(basis) < 20:
        return False
    return fold(beschreibung).strip().startswith(basis[:40])


def outlet_ab(titel):
    """Schneidet das angehaengte " - Outlet" der Google-News-Titel ab."""
    return re.sub(r"\s+-\s+[^-]{2,40}$", "", titel).strip() or titel


def rubrik_ab(titel):
    """EIN grossgeschriebenes Wort vor einem Doppelpunkt am Titelanfang ist die Rubrik oder
    der Ort, nicht die Firma. Belegt am 21.08.2026: "Moringen: KOENIG-Gruppe ...",
    "Kuerten: Korte meldet ...", "Ladenbau: Korte beantragt ...". Zwei oder mehr Woerter
    vor dem Doppelpunkt bleiben stehen, das ist meist der Firmenname selbst
    ("Korte Einrichtungen: Insolvenz des Ladenbauers")."""
    m = re.match(r"^([A-Z\u00c4\u00d6\u00dc][\w\u00c4\u00d6\u00dc\u00e4\u00f6\u00fc\u00df]{2,})\s*:\s+(.+)$",
                 titel.strip())
    if not m:
        return titel, False
    rest = m.group(2)
    if not re.search(r"[A-Z\u00c4\u00d6\u00dc]", rest):
        return titel, False
    return rest, True


def firmenschluessel(titel, beschreibung=""):
    """Heuristischer Firmenschluessel mit Konfidenz.
    Rueckgabe: (schluessel, kandidat, konfidenz) mit konfidenz in {"hoch","mittel",""}.
    Bewusst konservativ: ein falscher Schluessel wuerde zwei verschiedene Firmen
    zusammenfuehren, deshalb lieber leer lassen und dem Modell ueberlassen."""
    # EINMAL nach NFC normalisieren und danach nur noch mit diesem Text arbeiten. Sonst
    # verschiebt die Normalisierung in fold_pos die Offsets bei zerlegten Umlauten (NFD)
    # und es entstehen Schrottkandidaten wie "Gru Su Konto r Gm".
    # Google-News-Zeilen wiederholen den Titel in der Beschreibung und haengen den
    # Outletnamen an. Beides muss weg, sonst zaehlt jedes Titelwort doppelt (Befund
    # 21.08.2026, 78 von 102 Digest-Zeilen betroffen).
    echo = gnews_echo(titel, beschreibung)
    if echo:
        titel, beschreibung = outlet_ab(titel), ""
    titel, kopf_ab = rubrik_ab(titel)
    text = unicodedata.normalize("NFC", re.sub(r"\s+", " ", f"{titel}. {beschreibung}"))
    # fold_pos statt fold: die Treffer aus RX_RF werden unten per Offset auf "text"
    # angewandt, deshalb muss die Faltung die Zeichenzahl erhalten.
    gef = fold_pos(text)
    GROSS = r"[A-Z\u00c4\u00d6\u00dc][\w\u00c4\u00d6\u00dc\u00e4\u00f6\u00fc\u00df.&\-]*"

    def clean(kand):
        toks, gesehen = [], set()
        for k in norm(kand).split():
            # Zwei Zeichen sind erlaubt, damit Akronyme wie WK, SB oder OKA nicht
            # verschwinden. Rechtsformen und Gattungswoerter faengt WORT_STOP ab.
            if len(k) < 2 or k in WORT_STOP or k in STOP or k in gesehen:
                continue        # Dubletten im Namen weglassen ("Kiekert. Kiekert AG")
            gesehen.add(k)
            toks.append(k)
        if not toks:
            return []
        # Bleibt nur EIN Wort uebrig und ist es kurz oder gattungshaft, ist der Schluessel
        # schlechter als kein Schluessel: er fuehrt zwei fremde Firmen zusammen. Lieber leer
        # lassen und dem Modell ueberlassen, so steht es auch im Kommentar oben.
        # Mindestens vier Zeichen. Kuerzer waere zu unscharf, laenger wuerde echte kurze
        # Firmennamen wie Thor, Zeta oder Kodi um ihren Schluessel bringen und sie taeglich
        # als NEU zurueckbringen.
        # Gattungshaft heisst jetzt auch: endet auf ein beschreibendes Suffix. Ein
        # Schluessel "baumarktkette" oder "elektronikhersteller" benennt keine Firma
        # (belegt 21.08.2026: dieselbe Firma unter fuenf Beschreibungen).
        if len(toks) == 1 and (len(toks[0]) < 4 or _gattungshaft(toks[0])):
            return []
        return [" ".join(toks[:2])]

    # 1) Name unmittelbar vor einer Rechtsform -> hoch
    for m in RX_RF.finditer(gef):
        vorher = text[max(0, m.start() - 60):m.start()]
        # Schwache Rechtsform "ek" (eingetragener Kaufmann): nur gueltig, wenn direkt
        # davor ein grossgeschriebener Name steht ("Mueller Handel e.K."). Sonst faengt
        # sie Kleinschreibung im Titel ("ek robotics scheitert am Marktdruck") und der
        # Schluessel wird aus irgendeinem Wort der Umgebung gebildet (belegt 21.08.2026:
        # Schluessel "marktdruck" fuer die EK Robotics GmbH).
        rf_wort = gef[m.start():m.end()].strip().strip(".")
        if rf_wort == "ek":
            letztes = vorher.rstrip().split()[-1] if vorher.rstrip().split() else ""
            if not letztes or not letztes[:1].isupper() \
                    or fold(letztes) in STOP or fold(letztes).strip(".&-") in WORT_STOP:
                continue
        # Nur der Satz, in dem die Rechtsform steht: das 60-Zeichen-Fenster reicht sonst
        # in den vorigen Satz hinein und dessen Woerter werden zum Schluessel (belegt
        # 21.08.2026: "marktdruck" aus dem Titel fuer die EK Robotics GmbH).
        satz = re.split(r"[.!?]\s", vorher)[-1]
        toks = [t for t in re.findall(GROSS, satz) if fold(t).strip(".&-") not in WORT_STOP]
        # Versalien-Anker: ein komplett gross geschriebenes Wort (PANDION, WEZEK, EK,
        # SAFTIG) ist mit hoher Sicherheit der Firmenname oder sein Beginn, alles davor
        # ist Beschreibung ("Der Koelner Projektentwickler PANDION AG"). Ab dort schneiden.
        for i, t in enumerate(toks):
            if len(t) >= 2 and t.isupper() and t.isalpha():
                toks = toks[i:]
                break
        if toks:
            # Frueher nur die letzten drei Woerter vor der Rechtsform. Damit fiel der
            # KENNZEICHNENDE Namensanfang heraus: aus "Hellweg Die Profi-Bau- &
            # Gartenmaerkte GmbH & Co. KG" wurde der Schluessel "profi bau", und der
            # Bestandseintrag "hellweg profi" wurde nicht gefunden. Belegt am 21.08.2026,
            # Hellweg stand danach zweimal im Gedaechtnis. clean() nimmt ohnehin nur die
            # ersten zwei brauchbaren Woerter, und die stehen im Deutschen am Namensanfang.
            key = clean(" ".join(toks))
            # Besteht der Schluessel nur aus Gattungswoertern, steht der kennzeichnende Teil
            # des Namens links davon und beginnt klein oder mit Ziffern ("comlet Verteilte
            # Systeme", "12.18. Investment Management"). Dann dieses Wort davorziehen.
            if key and all(t in GENERIK for t in key[0].split()):
                lose = [w.strip(".,;:") for w in re.findall(r"[\wÄÖÜäöüß.\-]{2,}", satz)]
                lose = [w for w in lose if fold(w).strip(".&-") not in WORT_STOP
                        and fold(w) not in STOP and w not in toks]
                if lose:
                    key = [(norm(lose[-1]) + " " + key[0].split()[0]).strip()]
            if key:
                kand = (" ".join(toks[:4]) + " " + text[m.start():m.end()]).strip()
                return key[0], kand, "hoch"

    # 2) Marke in Anfuehrungszeichen -> hoch
    m = re.search(r'["\u201e\u00bb\u201c]([A-Z\u00c4\u00d6\u00dc][^"\u201c\u00ab\u201d]{2,40})["\u201c\u00ab\u201d]', text)
    if m:
        key = clean(m.group(1))
        if key:
            return key[0], m.group(1).strip(), "hoch"

    # 2b) Name vor einem beschreibenden Bindestrichteil: "Hellweg-Zentrale in Dortmund",
    # "KOENIG-Gruppe mit 1000 Mitarbeitern", "Pandion-Insolvenz", "PANDION Aktie".
    # Der Teil hinter dem Bindestrich beschreibt, der Teil davor benennt. Ohne diese Regel
    # wurden am 21.08.2026 "dortmund", "moringen" und "pandion aktie" zu Firmenschluesseln.
    ANHANG = (r"(?:Gruppe|Konzern|Zentrale|Insolvenz|Pleite|Aktie|Anleihe|Filialen|Filiale|"
              r"Werk|Werke|Standort|Standorte|Uebernahme|Verfahren)")
    # Klammerzusaetze ausnehmen: in "Gartencenter Augsburg (Hellweg-Gruppe)" benennt
    # "Hellweg" die MUTTER, nicht den Fall, und der Schluessel wuerde beide vermischen.
    ohne_klammer = re.sub(r"\([^)]*\)", " ", text)
    m = re.search(r"\b([A-Z\u00c4\u00d6\u00dc][\w\u00c4\u00d6\u00dc\u00e4\u00f6\u00fc\u00df]{2,})"
                  r"[-\u2011\s]" + ANHANG + r"\b", ohne_klammer)
    if m:
        key = clean(m.group(1))
        if key:
            return key[0], m.group(1).strip(), "mittel"

    # 3) Erstes Wort des Titels vor Doppelpunkt oder Gedankenstrich -> mittel.
    # NUR wenn dieses Wort auch sonst im Text vorkommt. Sonst ist es die Rubrik oder der
    # Ort, nicht die Firma: "Moringen: Koenig-Gruppe ...", "Ladenbau: Korte beantragt ...",
    # "Kuerten: Korte meldet ..." (alle belegt am 21.08.2026). Ein echter Firmenname wird
    # im Text wiederholt, ein Rubrikkopf nicht.
    m = re.match(r"^(" + GROSS + r"(?: " + GROSS + r")?)\s*[:\u2013\u2014-]\s", titel)
    if m:
        key = clean(m.group(1))
        if key:
            return key[0], m.group(1).strip(), "mittel"

    # 4) Grosswort, das im Text mehrfach vorkommt -> mittel
    kand = []
    for t in re.findall(r"[A-Z\u00c4\u00d6\u00dc][\w\u00c4\u00d6\u00dc\u00e4\u00f6\u00fc\u00df\-]{3,}", titel):
        k = norm(t)
        if not k or k in WORT_STOP or k in STOP or len(k) < 4 or _gattungshaft(k):
            continue
        vorkommen = len(re.findall(r"\b" + re.escape(k[:8]), norm(text)))
        kand.append((vorkommen, len(k), k, t))
    if kand:
        kand.sort(reverse=True)
        vor, _, k, t = kand[0]
        if vor >= 2:
            return k, t, "mittel"
        # Google-News-Zeilen wiederholen nichts, weil ihre Beschreibung nur der Titel ist.
        # Dann traegt die Wiederholungsprobe nicht, und es zaehlt die Eindeutigkeit: genau
        # EIN Kandidat im Titel, oder der erste Kandidat direkt nach einem abgeschnittenen
        # Rubrikkopf. Beides ist belegt am 21.08.2026 (Vivanco, KOENIG, Korte).
        if (echo or kopf_ab) and (len(kand) == 1 or kopf_ab):
            return k, t, "mittel"
    return "", "", ""
