# -*- coding: utf-8 -*-
"""
sammeln.py - Stufe 2 des Distressed-Tickers: Presse- und Fachfeeds einsammeln.

  python sammeln.py --tage 2                 # Standard-Tageslauf (Fenster 2 Tage)
  python sammeln.py --tage 4 --montag        # Montagslauf mit Wochenend-Nachlauf
  python sammeln.py --feedcheck              # nur Feed-Gesundheit pruefen, nichts schreiben

Schreibt rohtreffer.json (unveraendertes Rohmaterial) und feed_health.json.
Kein Modell, keine Bewertung - nur Abruf, Zeitfenster und Keyword-Vorfilter.
"""
import argparse, json, os, sys, urllib.parse, urllib.request
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
import gemeinsam as g
import feeds as F

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/125.0 Safari/537.36 (Sigma Distressed-Ticker)")
ATOM = "{http://www.w3.org/2005/Atom}"


def hole(url, timeout=25):
    req = urllib.request.Request(url, headers={"User-Agent": UA,
                                              "Accept": "application/rss+xml, application/xml, text/xml, */*"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def datum(item):
    for tag in ("pubDate", "published", "updated", ATOM + "updated", ATOM + "published",
                "{http://purl.org/dc/elements/1.1/}date"):
        d = item.findtext(tag)
        if not d:
            continue
        try:
            dt = parsedate_to_datetime(d)
            return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
        except Exception:
            try:
                dt = datetime.fromisoformat(d.strip().replace("Z", "+00:00"))
                return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
            except Exception:
                continue
    return None


def linkof(item):
    l = (item.findtext("link") or "").strip()
    if l:
        return l
    for a in item.iter(ATOM + "link"):
        if a.get("rel") in (None, "alternate") and a.get("href"):
            return a.get("href").strip()
    return (item.findtext("guid") or "").strip()


def quellen(tage, mit_gesperrten=False):
    q = dict(F.FEEDS)
    if mit_gesperrten:
        q.update(F.GESPERRT_AI_CRAWLER)
    for name, query in F.GNEWS_QUERIES.items():
        q[name] = F.GNEWS_TEMPLATE.format(q=urllib.parse.quote(query), tage=max(1, tage))
    return q


def ein_feed(name, url, grenze, ms, mw):
    out, status = [], "ok:0"
    try:
        root = ET.fromstring(hole(url))
        items = list(root.iter("item")) + list(root.iter(ATOM + "entry"))
        status = f"ok:{len(items)}" if items else "leer"
        for it in items:
            titel = g.strip_html(it.findtext("title") or it.findtext(ATOM + "title") or "")
            besch = g.strip_html(it.findtext("description") or it.findtext(ATOM + "summary")
                                 or it.findtext("{http://purl.org/rss/1.0/modules/content/}encoded") or "")
            if not titel:
                continue
            dt = datum(it)
            if dt and dt < grenze:
                continue
            gef = g.fold(titel + " " + besch)
            ts, tw = g.treffer(gef, ms), g.treffer(gef, mw)
            if not ts and not tw:
                continue
            src = it.findtext("source") or ""
            out.append({"quelle": name, "titel": titel, "beschreibung": besch[:600],
                        "link": linkof(it), "source": g.strip_html(src),
                        "datum": dt.strftime("%Y-%m-%d") if dt else "unbekannt",
                        "datum_iso": dt.isoformat() if dt else "",
                        "signal": "stark" if ts else "schwach",
                        "keywords": (ts + tw)[:6]})
    except Exception as e:
        status = f"FAIL:{type(e).__name__}"
    return name, status, out


def schreibe_digest(ordner, payload, pro_datei=25):
    """Zeilenweiser Digest in Haeppchen. Grund: der Abruf per URL laeuft ueber ein
    Sprachmodell, das lange Dateien kuerzt. 25 Zeilen pro Datei kommen verlustfrei an,
    und index.txt macht eine Kuerzung erkennbar."""
    os.makedirs(ordner, exist_ok=True)
    t = payload["treffer"]
    zeilen = []
    for i, x in enumerate(t, 1):
        titel = x["titel"].replace("|", "/")[:150]
        besch = x["beschreibung"].replace("|", "/")[:220]
        zeilen.append(f"{i}|{x['datum']}|{x['signal']}|{x['quelle'][:28]}|{titel}|{besch}|{x['link']}")
    teile = [zeilen[i:i + pro_datei] for i in range(0, len(zeilen), pro_datei)] or [[]]
    for n, teil in enumerate(teile, 1):
        with open(os.path.join(ordner, f"treffer_{n:02d}.txt"), "w", encoding="utf-8") as f:
            f.write("\n".join(teil) + "\n")
    m = payload["meta"]
    with open(os.path.join(ordner, "index.txt"), "w", encoding="utf-8") as f:
        f.write(f"lauf={m['lauf']}\nfenster_tage={m['fenster_tage']}\n"
                f"feeds_ok={m['feeds_ok']}/{m['feeds_gesamt']}\n"
                f"treffer={len(zeilen)}\nstark={m['n_stark']}\n"
                f"dateien={len(teile)}\npro_datei={pro_datei}\n"
                f"format=nr|datum|signal|quelle|titel|beschreibung|link\n")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tage", type=int, default=2, help="Zeitfenster in Tagen (Standard 2)")
    ap.add_argument("--montag", action="store_true", help="Wochenend-Nachlauf: Fenster auf 4 Tage")
    ap.add_argument("--out", default=os.path.join(os.getcwd(), "rohtreffer.json"))
    ap.add_argument("--feedcheck", action="store_true")
    ap.add_argument("--mit-gesperrten", action="store_true",
                    help="auch die 11 Domains mit AI-Crawler-Sperre abrufen (nur nach Compliance-Freigabe "
                         "und nur auf eigener Infrastruktur)")
    ap.add_argument("--digest", metavar="ORDNER",
                    help="zusaetzlich zeilenweise Digest-Dateien schreiben (fuer den Abruf per URL)")
    a = ap.parse_args()

    tage = 4 if a.montag else a.tage
    grenze = datetime.now(timezone.utc) - timedelta(days=tage)
    ms = g.build_matcher(g.load_keywords(os.path.join(HIER, "keywords.txt"))[0])
    mw = g.build_matcher(g.load_keywords(os.path.join(HIER, "keywords.txt"))[1])
    Q = quellen(tage, a.mit_gesperrten)

    with ThreadPoolExecutor(max_workers=12) as ex:
        res = list(ex.map(lambda kv: ein_feed(kv[0], kv[1], grenze, ms, mw), Q.items()))

    health = {n: s for n, s, _ in res}
    treffer = [t for _, _, lst in res for t in lst]
    problem = [f"{n}({s})" for n, s in health.items() if s == "leer" or s.startswith("FAIL")]

    if a.feedcheck:
        for n, s in sorted(health.items(), key=lambda x: (not x[1].startswith("ok"), x[0])):
            print(f"{s:14} {n}")
        print(f"\n{len(Q)-len(problem)}/{len(Q)} Feeds ok. Problem: {', '.join(problem) or 'keine'}")
        return

    payload = {"meta": {"lauf": datetime.now().isoformat(timespec="seconds"),
                        "fenster_tage": tage, "feeds_gesamt": len(Q),
                        "feeds_ok": len(Q) - len(problem), "n_roh": len(treffer),
                        "n_stark": sum(1 for t in treffer if t["signal"] == "stark")},
               "health": health, "treffer": treffer}
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=1)
    hp = os.path.join(os.path.dirname(a.out) or ".", "feed_health.json")
    with open(hp, "w", encoding="utf-8") as f:
        json.dump({"lauf": payload["meta"]["lauf"], "health": health, "problem": problem}, f,
                  ensure_ascii=False, indent=1)
    if a.digest:
        schreibe_digest(a.digest, payload)
    print(f"{len(treffer)} Treffer (Fenster {tage}d, davon {payload['meta']['n_stark']} stark) "
          f"aus {len(Q)-len(problem)}/{len(Q)} Feeds -> {a.out}"
          + (f" | Feed-Warnung: {', '.join(problem)}" if problem else ""))


if __name__ == "__main__":
    main()
