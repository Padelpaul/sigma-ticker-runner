# Distressed-Ticker Feed-Runner

Holt die Presse- und Fachfeeds inklusive der Google-News-Metafeeds und legt das Ergebnis so ab,
dass der Cowork-Skill `distressed-ticker` es lesen kann.

## Warum dieser Runner existiert

Cowork laeuft in einer Cloud-Umgebung, die Verlagsdomains nicht direkt abrufen darf, und
Google News RSS verbietet automatisierte Agenten per robots.txt. Der Feedabruf gehoert deshalb
auf eigene Infrastruktur, mit eigenem User-Agent. Genau das macht dieser Runner. Cowork liest
danach nur noch die fertige Trefferliste.

Abgerufen werden 51 verifizierte Feeds plus fuenf Google-News-Metafeeds mit den Stichwoertern
aus `lib/keywords.txt`. Elf Verlagsdomains mit AI-Crawler-Sperre sind bewusst ausgenommen; mit
`--mit-gesperrten` lassen sie sich zuschalten, sobald die Compliance-Frage geklaert ist.

## Variante A: GitHub Actions, empfohlen

Laeuft ohne eingeschalteten Rechner, kostet nichts.

1. Neues Repository anlegen, zum Beispiel `sigma-ticker-runner`. Es muss oeffentlich sein,
   damit Cowork die Ergebnisdatei lesen kann. Im Repo liegen nur generische
   Insolvenz-Stichwoerter und oeffentliche Pressetitel, keine Mandats- oder Kundendaten.
2. Diesen Ordner komplett hochladen (`.github/workflows/ticker.yml`, `lib/`, `README.md`).
3. Unter Settings, Actions, General, Workflow permissions auf "Read and write permissions"
   stellen, damit der Lauf das Ergebnis committen darf.
4. Einmal manuell starten: Actions, "Distressed-Ticker Feed-Runner", Run workflow.
5. Danach die Roh-URL notieren und dem Skill mitteilen, Muster:
   `https://raw.githubusercontent.com/<konto>/<repo>/main/digest/index.txt`

Der Lauf schreibt:

| Datei | Inhalt |
|---|---|
| `digest/index.txt` | Kopfzeilen: Lauf, Fenster, Feeds ok, Anzahl Treffer, Anzahl Digest-Dateien |
| `digest/treffer_01.txt` bis `treffer_NN.txt` | je 25 Treffer, eine Zeile pro Treffer |
| `digest/feedcheck.txt` | Feed-Gesundheit, welcher Feed leer oder fehlerhaft war |
| `rohtreffer.json` | vollstaendige Rohdaten, fuer Nachvollziehbarkeit und lokale Auswertung |

Zeilenformat: `nr|datum|signal|quelle|titel|beschreibung|link`

## Variante B: eigener Rechner

`run_lokal.bat` in die Windows-Aufgabenplanung legen, taeglich 09:40. Das Skript schreibt nach
`Desktop\claude code\Insolvenzen\runner\`. Cowork liest den Ordner ueber die Desktop-Bruecke
byte-genau, also ohne jeden Uebertragungsverlust. Nachteil: der Rechner muss laufen.

Beide Varianten koennen parallel laufen. Der Skill nimmt zuerst den Ordner, wenn er erreichbar
ist, sonst die URL.

## Voraussetzungen

Python 3.9 oder neuer, keine Fremdbibliotheken. Der Abruf dauert rund 30 bis 60 Sekunden.
