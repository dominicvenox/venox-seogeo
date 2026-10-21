# Validierung des SEO/GEO-Skills

Stand: 21.10.2026. Keine gemessenen Kundenrankings oder Live-KI-Sichtbarkeitswerte sind Teil dieser Validierung.

- Skill-Creator-Validator: `Skill is valid!` für `skills/seo-geo`.
- Python-Laufzeit: Standardbibliothek, Python 3.10+; Syntaxprüfung bestanden. PyYAML wurde ausschließlich für den externen Skill-Creator-Validator in einer temporären virtuellen Umgebung verwendet.
- `python3 -m unittest discover -s tests -v`: **17/17 bestanden**. Geprüft werden Domain-Grenzen, Alias-Erkennung, UI/API-/Kontrollgruppen, unbekannte Zitierabdeckung, Fehler-/No-feature-Nenner, Provider-Parser, Request-Cap/Stop-on-error, Modellversionen, historische Konfiguration, Zeitvergleich und verschwundene Oberflächen.
- Unabhängiger Skill-Anwendungstest: fiktiver Anbieter Acme, zwei abgeschlossene Wochen, 48 ausdrücklich synthetische Rohbelege, UI und API getrennt. 47 erfolgreiche Captures, ein Capturefehler; ein erfolgreicher Capture mit unbekannter Zitierabdeckung. Kein echter Anbieteraufruf. Getestet wurden Einrichtung, Plan, belegter Import, Zusammenfassung, Report, negative Eingaben und ein gemockter HTML-Audit.
- Nach den Korrekturen wurde der Anwendungstest mit dem aktuellen Paket wiederholt: **16/16 Prüfaussagen bestanden**, 17 protokollierte Helper-Aufrufe. Der Test kontrollierte außerdem unveränderte Paketdateien während des Durchlaufs.
- Ein unbezahlter öffentlicher Smoke-Test auf `https://example.com/` lieferte Status 200, HTML-/Header-/robots.txt-Artefakte und null Fetchfehler. Das ist ein Funktionsnachweis des begrenzten Fetchers, kein vollständiger SEO-Audit.

## Beobachtete Probleme und Korrekturen

1. Vollständig fehlende Vorperioden-Oberflächen konnten aus dem neuen Report verschwinden. Der Report führt fehlende oder methodisch veränderte Gruppen jetzt ausdrücklich als Datenlücke auf; Regressionstest vorhanden. Nicht versuchte API-Aufrufe werden zusätzlich aus dem Laufplan ausgewiesen.
2. Die Basisbefehle waren für einen aktuellen Baseline-Lauf geeignet, beschrieben die Zeitraumparameter des Wochenvergleichs aber nicht konkret genug. Die Wochenreferenz enthält jetzt ausführbare `summarize`-/`report`-Beispiele mit abgeschlossenen Fenstern. Fehlende, überlappende, vorläufige oder nicht vergleichbare Perioden erzeugen keinen automatischen Delta.
3. Alte Eval-Erwartungen nannten Sonar, angenommene Runner-Aufrufe und Baselines ohne zwingende Messdaten. Sie wurden auf Agent API, Tool-Discovery und tatsächliche Evidenz/Unbekannt angepasst.

## Grenzen des Nachweises

Die Live-Adapter für OpenAI, Perplexity und Gemini wurden anhand aktueller Primärdokumentation gebaut und mit synthetischen Providerantworten geprüft. Sie wurden **nicht mit echten API-Schlüsseln abgerechnet oder live Ende-zu-Ende bestätigt**. Modellzugang, aktuelle Provideränderungen, reale UI-/SERP-Erfassung und First-Party-Kontozugänge müssen beim jeweiligen Kunden eingerichtet und geprüft werden.

Der Skill ist lokal für Codex und Claude Code verlinkt. Es wurde kein Kundenschedule angelegt; dafür fehlen ein beauftragter Zielkunde, Datenzugänge, Laufzeit/Reportziel und konkreter Änderungsumfang. Es wurde keine Kundenwebsite verändert und kein Bericht an Dritte versendet. Die ursprünglichen Ohne-Skill-Baselines waren unvollständig; es gibt keinen behaupteten A/B-Leistungsgewinn gegenüber einem Agenten ohne Skill.

Reproduzierbare Pakettests liegen in `tests/test_seo_geo.py`. Temporäre Übungsartefakte des abschließenden Wiederholungslaufs: `/tmp/seo-geo-final-replay-20261021/` mit `commands.json`, `checks.json`, zwei belegten Runs und gekennzeichneten Reportentwürfen. Sie sind lokale Testartefakte und keine Voraussetzung für die Installation.
