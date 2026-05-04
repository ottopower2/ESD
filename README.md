# ESD Verifikation — ISO 10605 (330 pF / 330 Ω)

> **© 2026 Amouri — Alle Rechte vorbehalten.**
> Diese Software ist vertraulich und proprietär. Weitergabe, Kopie oder
> Nutzung durch Dritte ohne ausdrückliche schriftliche Genehmigung ist untersagt.
> Siehe [LICENSE](LICENSE).

Automatisierte Verifikation von ESD-Generatoren nach **ISO 10605** über ein Rohde & Schwarz Oszilloskop (SCPI/VISA).

---

## Projektstruktur

```
esd_v1/
├── esd_verifikation.py   # Hauptskript: Messung + PASS/FAIL + Bericht
├── esd_report.py         # Modul: Word-Bericht-Generator (.docx)
├── ESD_<timestamp>.png   # Oszilloskop-Screenshot je Messung
├── ESD_<timestamp>.json  # Messdaten je Messung (für Bericht)
└── ESD_Report_<timestamp>.docx  # Automatisch generierter Prüfbericht
```

---

## Voraussetzungen

### Hardware

| Gerät           | Beschreibung                          |
| --------------- | ------------------------------------- |
| R&S Oszilloskop | RTO / RTM / MXO — IP: `192.168.50.91` |
| ESD-Generator   | Prüfling nach ISO 10605               |
| Strommessung    | 2 Ω Shunt + 20 dB Dämpfungsglied      |

### Messaufbau / Signalkette

```
ESD-Generator
     │
   [2 Ω Shunt]
     │
[20 dB Dämpfung ÷10]
     │
[50Ohm Kabel]
     │
[Oszilloskop]
EATTenuation = 1333
```

**Umrechnung Spannung → Strom:**

```
I = V_gemessen × 10 / (ATTENUATION × 2)
  = V_gemessen × 10 / (1333 × 2)
```

### Software

```bash
pip install pyvisa python-docx
```

---

## Konfiguration

In `esd_verifikation.py` oben anpassbar:

```python
OSC_IP              = "192.168.50.91"   # IP des Oszilloskops
CHANNEL             = 1                 # Eingangskanal
ATTENUATION         = 1333              # EATTenuation-Faktor
TRIGGER_SLOPE       = "EITHer"          # POSitive | NEGative | EITHer
ACQ_WAIT_TIMEOUT_MS = 60000             # Max. Wartezeit auf ESD-Puls (ms)
SCOPE_SCREENSHOT_DIR = r"C:\Temp"       # Temp-Pfad auf dem Oszilloskop
```

---

## Ausführung

```bash
python esd_verifikation.py
```

Das Skript fragt interaktiv nach der Entladespannung:

```
Entladespannung eingeben (1,-1,2,-2,4,-4, 6,-6 oder 8,-8 kV):
```

Danach läuft alles automatisch:

1. Verbindung zum Oszilloskop
2. Konfiguration (Kanal, Trigger, Zeitbasis)
3. Warten auf ESD-Puls
4. Waveform auslesen (REAL32 binary)
5. Strom bei 65 ns und 130 ns berechnen
6. Peak-Strom berechnen
7. PASS/FAIL-Auswertung (Konsole)
8. Screenshot speichern
9. JSON-Datei speichern
10. Word-Bericht generieren

---

## Oszilloskop-Einstellungen (automatisch gesetzt)

| Parameter        | Wert       |
| ---------------- | ---------- |
| Eingangsimpedanz | 50 Ω       |
| Kopplung         | DC         |
| Bandbreite       | FULL       |
| Zeitbasis        | 50 ns/div  |
| Referenz         | CENTER     |
| Trigger          | EDGE, NORM |

**Spannungsbereich je Entladespannung:**

| kV  | Triggerlevel (V) | Skala (V/div) | Offset (V) |
| --- | ---------------- | ------------- | ---------- |
| ±1  | ±100             | 200           | 0          |
| ±2  | ±400             | 400           | 0          |
| ±4  | ±800             | 1000          | 0          |
| ±6  | ±1000            | 1100          | 0          |
| ±8  | ±1000            | 1000 / 2000   | ±2000      |

---

## PASS/FAIL-Kriterien — ISO 10605 (330 pF / 330 Ω)

### Strom bei t = 65 ns (Toleranz ±30 %)

| Entladespannung | Sollwert | Untergrenze | Obergrenze |
| --------------- | -------- | ----------- | ---------- |
| ±1 kV           | 2,0 A    | 1,40 A      | 2,60 A     |
| ±2 kV           | 4,0 A    | 2,80 A      | 5,20 A     |
| ±4 kV           | 8,0 A    | 5,60 A      | 10,40 A    |
| ±6 kV           | 12,0 A   | 8,40 A      | 15,60 A    |
| ±8 kV           | 16,0 A   | 11,20 A     | 20,80 A    |

### Strom bei t = 130 ns (Toleranz ±30 %)

| Entladespannung | Sollwert | Untergrenze | Obergrenze |
| --------------- | -------- | ----------- | ---------- |
| ±1 kV           | 1,0 A    | 0,70 A      | 1,30 A     |
| ±2 kV           | 2,0 A    | 1,40 A      | 2,60 A     |
| ±4 kV           | 4,0 A    | 2,80 A      | 5,20 A     |
| ±6 kV           | 6,0 A    | 4,20 A      | 7,80 A     |
| ±8 kV           | 8,0 A    | 5,60 A      | 10,40 A    |

### Peak-Strom (Toleranz ±10 %)

| Entladespannung | Sollwert | Untergrenze | Obergrenze |
| --------------- | -------- | ----------- | ---------- |
| ±1 kV           | 3,75 A   | 3,375 A     | 4,125 A    |
| ±2 kV           | 7,5 A    | 6,75 A      | 8,25 A     |
| ±4 kV           | 15,0 A   | 13,50 A     | 16,50 A    |
| ±6 kV           | 22,5 A   | 20,25 A     | 24,75 A    |
| ±8 kV           | 30,0 A   | 27,00 A     | 33,00 A    |

> **Zeitpunkte:** 65 ns und 130 ns gelten für das 330 pF / 330 Ω Netzwerk (τ ≈ 109 ns).  
> Für das 150 pF / 330 Ω Netzwerk wären es 30 ns und 60 ns (τ ≈ 50 ns).

---

## Ausgabedateien

Pro Messlauf werden drei Dateien im Skript-Verzeichnis gespeichert:

| Datei                         | Inhalt                                                         |
| ----------------------------- | -------------------------------------------------------------- |
| `ESD_<timestamp>.png`         | Oszilloskop-Screenshot des ESD-Pulses                          |
| `ESD_<timestamp>.json`        | Alle Messdaten (Spannungen, Ströme, kV-Stufe, PASS/FAIL-Werte) |
| `ESD_Report_<timestamp>.docx` | Word-Prüfbericht mit allen Messungen und Kriterien             |

**Beispiel JSON-Datei:**

```json
{
  "timestamp": "20260430_143602",
  "entlade_kv": 4,
  "trigger_level": 800,
  "trigger_offset": 0,
  "scale": 1000,
  "attenuation": 1333,
  "v_65ns": 266.6,
  "v_130ns": 133.3,
  "vpeak": 500.0,
  "vpp": 1000.0,
  "A_65ns": 1.0,
  "A_130ns": 0.5,
  "A_peak": 3.75,
  "screenshot_path": "C:\\...\\ESD_20260430_143602.png"
}
```

---

## Word-Bericht (esd_report.py)

Der Bericht enthält:

- Messparameter (Datum, kV, Trigger, Skala, Attenuation)
- Rohwerte (V @ 65 ns, V @ 130 ns, V_peak, V_pp)
- Berechnete Ströme mit Formel
- PASS/FAIL-Tabelle (farbig: grün / rot)
- Gesamtergebnis
- Screenshot der aktuellen Messung
- Alle weiteren ESD\_\*.png im Verzeichnis mit zugehörigen PASS/FAIL-Tabellen (sofern JSON vorhanden)

**Bericht manuell neu generieren (Testmodus):**

```bash
python esd_report.py
```

Erzeugt einen Demo-Bericht mit 4 kV Testdaten.

---

## Bekannte Hinweise

- `CURS:Y1POS?` funktioniert im HD-Mode nicht → Y-Werte werden direkt aus den Waveform-Rohdaten (REAL32 binary) berechnet.
- Bei `query_binary_values` muss `read_termination = ""` gesetzt werden.
- Screenshot wird zuerst auf dem Oszilloskop unter `C:\Temp\` gespeichert und dann per `MMEM:DATA?` auf den PC übertragen.
- Bei ±8 kV wird ein Trigger-Offset von ±2000 V gesetzt, um vorzeitiges Triggern zu verhindern.
- VISA Timeout-Fehler (Error Code `-1073807339`): Instrument wird per `clear()` zurückgesetzt.
