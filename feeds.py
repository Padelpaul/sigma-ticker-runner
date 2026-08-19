# -*- coding: utf-8 -*-
"""
Eine einzige gueltige Quellenliste fuer den Distressed-Ticker (Stufe 2: Presse/Fach).

Herkunft: Zusammenfuehrung der beiden zuvor getrennten Listen
(./feeds_verified.py, verifiziert 2026-07-21, und ./ticker-system/feeds_verified.py,
verifiziert 2026-07-06). Uebernommen wurden nur URLs, die in einer der beiden
Verifikationen tatsaechlich abgerufen und mit mehreren <item>/<entry> bestaetigt wurden.
Keine geratenen URLs.

Compliance (verbindlich): Der wiederkehrende Abruf laeuft ueber diese lokalen Skripte
mit eigenem User-Agent, NICHT ueber einen Claude-Agenten. Mehrere Verlagsdomains sperren
AI-Crawler per robots.txt fuer die gesamte Domain (u.a. Funke, Madsack, FAZ, Frankfurter
Rundschau, Saarbruecker Zeitung, Trierischer Volksfreund, Der Treasurer). Das Modell ruft
diese Domains nicht selbst ab; es arbeitet nur mit den hier gesammelten Feed-Metadaten.
Vor einer Ausweitung des automatisierten Abrufs Compliance einbinden.

GNEWS_QUERIES sind Metafeeds auf news.google.com (gleicher, verifizierter Endpunkt wie die
zwei bereits produktiv genutzten Google-News-Feeds, nur andere Suchbegriffe). Beim ersten
Lauf mit  python sammeln.py --feedcheck  bestaetigen.
"""

FEEDS = {
    # --- Ueberregional / Wirtschaft & Finanzen ---
    "Handelsblatt Unternehmen": "https://feeds.cms.handelsblatt.com/unternehmen",
    "Handelsblatt Finanzen": "https://feeds.cms.handelsblatt.com/finanzen",
    "Manager Magazin": "https://www.manager-magazin.de/unternehmen/index.rss",
    "WirtschaftsWoche Unternehmen": "https://feeds.cms.wiwo.de/rss/unternehmen",
    "WirtschaftsWoche Finanzen": "https://feeds.cms.wiwo.de/rss/finanzen",
    "SZ Wirtschaft": "https://rss.sueddeutsche.de/rss/Wirtschaft",
    "WELT Wirtschaft": "https://www.welt.de/feeds/section/wirtschaft.rss",
    "Zeit Wirtschaft": "https://newsfeed.zeit.de/wirtschaft/index",
    "Tagesschau Wirtschaft": "https://www.tagesschau.de/wirtschaft/index~rss2.xml",
    "ntv Wirtschaft": "https://www.n-tv.de/wirtschaft/rss",
    "Focus (Finanzen)": "https://rss.focus.de/finanzen/",
    "Capital": "https://www.capital.de/rss",
    "Boersen-Zeitung": "https://feeds.purplemanager.com/3bb5104f-f2d6-4138-b889-ac5e5ca06778/alle-news-ohne-agenturmeldungen",
    "FinanzNachrichten": "https://www.finanznachrichten.de/rss-nachrichten-wirtschaft-konjunktur",
    "wallstreet-online": "https://www.wallstreet-online.de/rss/nachrichten-alle.xml",

    # --- Oeffentlich-rechtlich ---
    "WDR Wirtschaft": "https://www1.wdr.de/nachrichten/wirtschaft/index.feed",
    "BR24": "https://www.br.de/nachrichten/meldungen/nachrichten-bayerischer-rundfunk100~newsRss.xml",
    "MDR": "https://www.mdr.de/nachrichten/nachrichten100-rss.xml",
    "SWR": "https://www.swr.de/~rss/swraktuell/swraktuell-100.xml",
    "hessenschau Wirtschaft (HR)": "https://www.hessenschau.de/wirtschaft/index.rss",
    "rbb24 Wirtschaft": "https://www.rbb24.de/wirtschaft/index.xml/feed=rss.xml",
    "Radio Bremen (buten un binnen)": "https://www.butenunbinnen.de/feed/rss/nachrichten/neuste-nachrichten100.xml",

    # --- NRW ---
    "WAZ Wirtschaft": "https://www.waz.de/wirtschaft/rss",
    "Rheinische Post": "https://rp-online.de/feed.rss",
    "Koelner Stadt-Anzeiger Wirtschaft": "https://feed.ksta.de/feed/rss/wirtschaft/index.rss",
    "Westfaelische Nachrichten": "https://www.wn.de/rss/feed/wn_muenster",
    "Neue Westfaelische": "https://www.nw.de/_export/site_rss/nw/index.rss",
    "Ruhr Nachrichten": "https://www.ruhrnachrichten.de/feed/",

    # --- Sued ---
    "Augsburger Allgemeine Wirtschaft": "https://www.augsburger-allgemeine.de/wirtschaft/rss",
    "Muenchner Merkur Wirtschaft": "https://www.merkur.de/wirtschaft/rssfeed.rdf",
    "Merkur Erding (Lokal)": "https://www.merkur.de/lokales/erding/rssfeed.rdf",
    "Rhein-Neckar-Zeitung Wirtschaft": "https://www.rnz.de/feed/160-RL_Wirtschaft_regional_free.xml",

    # --- Nord / Ost ---

    # --- Mitte / West ---
    "Rhein-Zeitung": "https://www.rhein-zeitung.de/feed/37-Rheinland-Pfalz.xml",

    # --- Fach / Restrukturierung ---
    "Creditreform News": "https://www.creditreform.de/rss",
    "Deutscher AnwaltSpiegel": "https://www.deutscheranwaltspiegel.de/feed/",
    "FINANCE Magazin": "https://www.finance-magazin.de/feed/",
    "JUVE": "https://www.juve.de/feed/",

    # --- PR-Wires ---
    "pressebox (PM-Wire)": "https://www.pressebox.de/rss/pressemitteilungen",
    "presseportal Wirtschaft": "https://www.presseportal.de/rss/wirtschaft.rss2",

    # --- Regionale Lokalfeeds (offene Ippen-Netze) ---
    "Merkur Muenchen (Lokal)": "https://www.merkur.de/lokales/muenchen/rssfeed.rdf",
    "Merkur Freising (Lokal)": "https://www.merkur.de/lokales/freising/rssfeed.rdf",
    "Merkur Dachau (Lokal)": "https://www.merkur.de/lokales/dachau/rssfeed.rdf",
    "Merkur Ebersberg (Lokal)": "https://www.merkur.de/lokales/ebersberg/rssfeed.rdf",
    "Merkur Rosenheim (Lokal)": "https://www.merkur.de/lokales/rosenheim/rssfeed.rdf",
    "Merkur Muehldorf (Lokal)": "https://www.merkur.de/lokales/muehldorf/rssfeed.rdf",
    "HNA Kassel/Nordhessen (Lokal)": "https://www.hna.de/rssfeed.rdf",
    "tz Muenchen (Lokal)": "https://www.tz.de/rssfeed.rdf",
    "Offenbach op-online (Lokal)": "https://www.op-online.de/rssfeed.rdf",
    "Westf. Anzeiger wa.de (Lokal)": "https://www.wa.de/rssfeed.rdf",
    "Kreiszeitung Niedersachsen (Lokal)": "https://www.kreiszeitung.de/rssfeed.rdf",
    "come-on Maerkischer Kreis (Lokal)": "https://www.come-on.de/rssfeed.rdf",
}


# Domains mit AI-Crawler-Sperre per robots.txt. Aus dem Cowork-Lauf ausgeschlossen
# (Entscheidung Sigma, 18.08.2026). Auf eigener Infrastruktur nach Compliance-Freigabe nutzbar.
GESPERRT_AI_CRAWLER = {
    "FAZ Wirtschaft": "https://www.faz.net/rss/aktuell/wirtschaft/",
    "Hamburger Abendblatt Wirtschaft": "https://www.abendblatt.de/wirtschaft/rss",
    "Weser-Kurier": "https://www.weser-kurier.de/?view=rss",
    "Kieler Nachrichten": "https://www.kn-online.de/arc/outboundfeeds/rss/",
    "Saechsische Zeitung": "https://www.saechsische.de/arc/outboundfeeds/rss/",
    "Leipziger Volkszeitung": "https://www.lvz.de/arc/outboundfeeds/rss/",
    "Ostsee-Zeitung": "https://www.ostsee-zeitung.de/arc/outboundfeeds/rss/",
    "Frankfurter Rundschau Wirtschaft": "https://www.fr.de/wirtschaft/rssfeed.rdf",
    "Saarbruecker Zeitung": "https://www.saarbruecker-zeitung.de/feed.rss",
    "Trierischer Volksfreund": "https://www.volksfreund.de/feed.rss",
    "Der Treasurer": "https://www.dertreasurer.de/feed",
}

# Deaktiviert, weil im Lauf-Log seit 2026-07-06 durchgehend leer.
# Reaktivieren nur nach erneuter Verifikation per --feedcheck.
DEAKTIVIERT = {
    "NDR": "https://www.ndr.de/home/index-rss.xml",
}

# Google-News-Metafeeds: erhoehen die Abdeckung regionaler, kleiner und PM-getriebener
# Meldungen erheblich. Suchbegriffe werden von sammeln.py URL-kodiert, {tage} eingesetzt.
GNEWS_QUERIES = {
    "GNews Insolvenzantrag": 'Insolvenzantrag OR "Insolvenz angemeldet" OR "meldet Insolvenz" OR insolvent',
    "GNews Verfahren/Verwalter": 'Insolvenzverwalter OR Sachwalter OR Eigenverwaltung OR Schutzschirmverfahren OR "Insolvenzverfahren eröffnet"',
    "GNews Sanierung/StaRUG": 'StaRUG OR "übertragende Sanierung" OR Restrukturierungsplan OR Sanierungsverfahren OR Gläubigerausschuss',
    "GNews Investorenprozess": 'Investorenprozess OR "sucht Investor" OR "Investor gesucht" OR Bieterprozess OR "sucht Geldgeber"',
    "GNews Fruehsignal": 'Zahlungsunfähigkeit OR Liquiditätsengpass OR Moratorium OR "drohende Zahlungsunfähigkeit" OR Überschuldung',
}

GNEWS_TEMPLATE = "https://news.google.com/rss/search?q={q}+when:{tage}d&hl=de&gl=DE&ceid=DE:de"


# ---------------------------------------------------------------------------
# Betriebsart Cowork: der Container darf Verlagsdomains nicht direkt abrufen
# (Test 18.08.2026: HTTP 403 am Proxy). Deshalb sammelt dort das Modell per
# WebFetch auf diesen Aggregatoren und per WebSearch. Details in
# references/quellen.md.
COWORK_AGGREGATOREN = {
    "INDat Pressemitteilungen": "https://www.indat.info/Meldungen/Pressemitteilungen-Insolvenz-Sanierung",
    "ZRI online": "https://www.zri-online.de/restrukturierungen-insolvenzen/",
    "presseportal Wirtschaft": "https://www.presseportal.de/rss/wirtschaft.rss2",
    "Verlag INDat": "https://www.der-indat.de/",
    "pleiteticker": "https://pleiteticker.info/",
}

# Geprueft, aber nicht nutzbar: insolvenzkarte.de laedt die Tabelle per JavaScript nach,
# WebFetch sieht nur den Platzhalter. Dahinter steht InsolvenzTracker (99 EUR/Monat, CSV-
# und Excel-Export) als weitere Option fuer Etappe 2.
