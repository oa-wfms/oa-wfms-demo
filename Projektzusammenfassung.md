# Projektzusammenfassung

Entwicklung eines Demonstrators für ein Open-Access-Workflow-Management-System (OA-WFMS) mit Integration zwischen Wekan-Board-System und OJS (Open Journal Systems). Das Projekt stellt eine umfassende Machbarkeitsstudie für die Integration von Workflow-Management-Systemen in den Open-Access-Publikationsprozess dar, mit besonderem Fokus auf praktische Umsetzbarkeit und Skalierbarkeit für verschiedene Verlagsszenarien.

## Projektrahmen und Zeitplan

- Laufzeit von 4 Monaten (September bis Dezember 2025)
- Workshop-Präsentation geplant im November
- Aktueller Fokus auf Vorbereitung des Demonstrators für Workshop-Demonstration

## Technische Implementierungsdetails

In Anbetracht der kurzen Projektlaufzeit wurde auf die Implementierung eines vollständigen Middleware-Servers (mit eigenem OJS-Wekan-Datenmapping über Objekt-IDs) verzichtet. Der Fokus lag auf der Durchführung einer grundlegenden Machbarkeitsstudie und die Implementierung eines einfachen Demonstrator-Skriptes mit folgenden Funktionen:

- Mapping von OJS-Workflow-Stages auf Wekan-Listen
- Mapping von Ausgaben und Artikeln auf Karten
- Verwendung benutzerdefinierter Felder für Metadaten
- Automatische Aktualisierung bestehender Karten bei Änderungen
- Konfiguration über .env-Dateien mit Board-, Listen- und Swimlane-Definitionen
- Herausforderung der textuellen Synchronisation (exakte Namensübereinstimmung erforderlich)

## Board-Struktur und Konzept

Die für den Demonstrator vereinbarte Board-Struktur umfasst die folgenden Elemente:

- **Wekan-Listen** werden verwendet für: Prozessgruppen (Vorlauf, Prüfung, Lektorat, Satz/Produktion, Post-Produktion, Kontrolle)
- **Wekan-Swimlanes** werden verwendet für: Produktgruppen (Zeitschriften, Schriftenreihen, Sammelbände, Monographien)
- **Wekan-Karten** werden verwendet für: Je Zeitschriftenausgabe, (Sammelband) oder Einzelpublikation
- **Teilaufgaben**: Einzelartikel als Unteraufgaben mit Verlinkung zur Hauptkarte der Zeitschriftenausgabe
- **Template-System**: Vorlagen für verschiedene Publikationstypen mit spezifischen Checklisten, konfigurierbar über .env-Datei

## Gewünschte zukünftuge erweiterte Funktionalitäten 

- **Checklisten-Management**: Automatisches Kopieren von Vorlagen bei Kartenerstellung
- **Bidirektionale Kommunikation**: Möglichkeiten für Wekan→OJS-Aktionen
- **Workflow-Synchronisation**: Automatische Listenverschiebung bei Statusänderungen
- **Metadaten-Integration**: Übertragung von Titel, Autorschaft und anderen Feldern
- **Link-Generierung**: Direkte Verlinkung zu spezifischen OJS-Workflow-Bereichen

## Bekannte technische Limitierungen

- REST-API-Beschränkungen in beiden Systemen
- Notwendigkeit zusätzlicher OJS-Plugins für die Implementierung erweiterter Funktionen
- Komplexität der Personenzuordnung und Aufgabenverwaltung
- Herausforderungen bei mehrsprachigen Metadaten
- Unterschiedliche Implementierungsansätze für verschiedene OJS-Versionen

## Aktueller Projektstand

- Einrichtung einer Wekan-Testinstallation bei externem Dienstleister
- Entwicklung von Python-Skripten für die Datensynchronisation
    - Erfolgreiche Implementierung der Grundfunktionen für OJS→Wekan-Synchronisation
    - Konfigurierbare Synchronisation über Kommandozeilen-Tools
    - Automatische Erstellung bzw. Aktualisierung von Karten für neue Einreichungen und Ausgaben

