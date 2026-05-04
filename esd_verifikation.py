# -*- coding: utf-8 -*-
# =============================================================================
# Copyright (c) 2026  CSA GROUP. Alle Rechte vorbehalten / All rights reserved.
# Vertraulich und proprietär – Weitergabe, Kopie und Nutzung durch Dritte
# ohne ausdrückliche schriftliche Genehmigung des Urhebers untersagt.
# Confidential and proprietary – redistribution and use by third parties
# without explicit written permission of the author is strictly prohibited.
# Siehe / See: LICENSE
# =============================================================================
__author__  = "H.Amouri"
__version__ = "1.0"
__date__    = "2026"

import os
import time
from datetime import datetime

print("=" * 55)
print(f"  ESD Verifikation  |  ISO 10605  |  330pF / 330Ohm")
print(f"  Entwickelt von: {__author__}  |  Version {__version__}  |  {__date__}")
print("=" * 55)
print()

import json
import pyvisa
from pyvisa.errors import VisaIOError




# --------------------------------------------------
# EINSTELLUNGEN
# --------------------------------------------------
OSC_IP               = "192.168.50.91"
CHANNEL              = 1
ATTENUATION          = 1333
TRIGGER_SLOPE        = "EITHer"    # POSitive | NEGative | EITHer
ACQ_WAIT_TIMEOUT_MS  = 60000       # max. Wartezeit auf Trigger (ms)
SCOPE_SCREENSHOT_DIR = r"C:\Temp"
LOCAL_SAVE_DIR       = os.path.dirname(os.path.abspath(__file__))

# --------------------------------------------------
# ENTLADESPANNUNG ABFRAGEN
# --------------------------------------------------
TRIGGER_MAP = {1:100,  -1:-100,    2:  400, -2: -400, 4: 800, -4: -800, 6: 1000, -6: -1000, 8: 1000, -8: -1000}  #+kV/-kV     Triggerlevel in V (Puls soll sicher getriggert werden, aber nicht zu frueh)
SCALE_MAP   = {1: 200, -1:200, 2: 400, -2: 400, 4: 1000, -4: 1000, 6: 1100, -6: 1100, 8: 1000, -8: 1000}
# 8, -8 mit Offset 2kV, da Triggerlevel sonst zu hoch ist und Puls nicht getriggert wird
Offset_Map  = {1: 0, -1:0, 2: 0, -2: 0, 4: 0, -4: 0, 6: 0, -6: 0, 8: 3000, -8: -3000}


# ---------------------------------------------------



while True:
    try:
        entlade_kv = int(input("Entladespannung eingeben (1,-1,2,-2,4,-4, 6,-6 oder 8,-8 kV): "))
        if entlade_kv in TRIGGER_MAP:
            break
        print("  Ungueltige Eingabe. Bitte 1,-1,2,-2,4,-4, 6,-6 oder 8,-8 eingeben.")
    except ValueError:
        print("  Bitte eine Zahl eingeben.")

TRIGGER_LEVEL = TRIGGER_MAP[entlade_kv]
TRIGGER_OFFSET = Offset_Map[entlade_kv]
print(f"  -> Entladespannung: {entlade_kv} kV  |  Triggerlevel: {TRIGGER_LEVEL} V  |  Skala: {SCALE_MAP[entlade_kv]} V/div |  Offset: {TRIGGER_OFFSET} V")


def safe_query(instr, cmd, timeout_ms=3000):
    orig = instr.timeout
    try:
        instr.timeout = timeout_ms
        return instr.query(cmd).strip()
    except VisaIOError as e:
        if e.error_code == -1073807339:
            try:
                instr.clear()
            except Exception:
                pass
            return "<timeout>"
        raise
    finally:
        instr.timeout = orig


# --------------------------------------------------
# VERBINDUNG
# --------------------------------------------------
rm    = pyvisa.ResourceManager()
scope = rm.open_resource(f"TCPIP::{OSC_IP}::INSTR")
scope.timeout          = 10000
scope.write_termination = "\n"
scope.read_termination  = "\n"

print("Verbunden:", scope.query("*IDN?"))
scope.write("*CLS")
scope.write("*RST")          # Werkseinstellungen: deaktiviert HD-Mode, setzt Sample-Modus
scope.query("*OPC?")
time.sleep(1.5)

# --------------------------------------------------
# KANAL
# --------------------------------------------------
scope.write(f"CHAN{CHANNEL}:STAT ON")
scope.write(f"CHAN{CHANNEL}:IMP 50")                # 50 Ohm Eingangsimpedanz
scope.write(f"CHAN{CHANNEL}:COUP DC")               # DC 50 Ohm
scope.write(f"CHANnel{CHANNEL}:EATScale LIN")
scope.write(f"CHANnel{CHANNEL}:EATTenuation {ATTENUATION}")
scope.write(f"CHAN{CHANNEL}:SCAL {SCALE_MAP[entlade_kv]}")     # V/div je nach Entladespannung
scope.write(f"CHAN{CHANNEL}:OFFS {Offset_Map[entlade_kv]}")  # Offset je nach Entladespannung
scope.write(f"CHAN{CHANNEL}:BAND FULL")

# --------------------------------------------------
# ZEITBASIS
# --------------------------------------------------
scope.write("TIM:SCAL 50E-9")   # 50 ns/div
scope.write("TIM:REF CENTer")   # Referenzpunkt = Bildschirmmitte
scope.write("TIM:POS 0")

# --------------------------------------------------
# TRIGGER
# --------------------------------------------------
scope.write("TRIGger1:MODE NORM")
scope.write(f"TRIGger1:SOURce CHAN{CHANNEL}")
scope.write("TRIGger1:TYPE EDGE")
scope.write(f"TRIGger1:EDGE:SLOPe {TRIGGER_SLOPE}")
scope.write(f"TRIGger1:LEVel1 {TRIGGER_LEVEL}")
scope.write(f"TRIGger1:OFFS {TRIGGER_OFFSET}")
scope.query("*OPC?")

# --------------------------------------------------
# WARTEN AUF TRIGGER
# --------------------------------------------------
scope.write("SING")
print(f"Warte auf ESD-Puls  (Level={TRIGGER_LEVEL} V, Slope={TRIGGER_SLOPE}, Offset={TRIGGER_OFFSET}) ...")

scope.timeout = ACQ_WAIT_TIMEOUT_MS
scope.query("*OPC?")
scope.timeout = 10000
print("Trigger erkannt!")

# --------------------------------------------------
# CURSOR-MESSUNG
# --------------------------------------------------
scope.write("SYST:DISP:UPD ON")
scope.query("*OPC?")

scope.write("CURS1:STAT ON")
scope.write("CURS1:FUNC PAIR")
scope.write("CURS1:SOUR C1W1")
scope.write("CURS1:TRAC ON")
scope.write("CURS1:TRAC:STAT ON")
scope.write("CURS1:XCO OFF")
scope.write("CURS1:X1P 65E-9")
scope.write("CURS1:X2P 130E-9")
scope.query("*OPC?")
time.sleep(0.3)

# Y-Werte aus Waveform-Rohdaten (CURS:Y1POS? scheitert im HD-Mode)
scope.write("FORM REAL,32")
hdr    = safe_query(scope, f"CHAN{CHANNEL}:DATA:HEAD?", timeout_ms=5000)
hparts = hdr.split(",")
x0, x1_end, n = float(hparts[0]), float(hparts[1]), int(hparts[2])
dx = (x1_end - x0) / max(n - 1, 1)

orig_rt = scope.read_termination
scope.read_termination = ""
scope.timeout = 15000
try:
    samples = scope.query_binary_values(
        f"CHAN{CHANNEL}:DATA?", datatype='f', container=list
    )
finally:
    scope.read_termination = orig_rt
    scope.timeout = 10000

def y_at(t):
    i = round((t - x0) / dx)
    return samples[max(0, min(i, len(samples) - 1))]

y_65ns  = y_at(65e-9)
y_130ns = y_at(130e-9)
y_65ns_raw, y_130ns_raw = y_65ns, y_130ns   # vor abs() sichern
print(f"  Y @ 65 ns  = {y_65ns:.2f} V")
print(f"  Y @ 130 ns = {y_130ns:.2f} V")


# --------------------------------------------------
# MESSUNG: PEAK UND PEAK-TO-PEAK (aus Waveform-Daten)
# --------------------------------------------------
vpeak = max(samples)
vpp   = max(samples) - min(samples)
print(f"  Peak:         {vpeak:.2f} V")
print(f"  Peak-to-Peak: {vpp:.2f} V")









# --------------------------------------------------

# --------------------------------------------------
# SCREENSHOT
# --------------------------------------------------
timestamp            = datetime.now().strftime("%Y%m%d_%H%M%S")
filename             = f"ESD_{timestamp}.png"
local_path           = os.path.join(LOCAL_SAVE_DIR, filename)
scope_path           = f"{SCOPE_SCREENSHOT_DIR}\\{filename}"

scope.write("STOP")
scope.query("*OPC?")
scope.write("*CLS")
scope.write("HCOP:DEST 'MMEM'")
scope.write("HCOP:DEV:LANG PNG")
scope.write(f"MMEM:NAME '{scope_path}'")
scope.write("HCOP:IMM")
scope.query("*OPC?")
time.sleep(2.0)

original_read_term      = scope.read_termination
scope.read_termination  = ""
scope.timeout           = 30000
try:
    png_data = bytes(scope.query_binary_values(
        f"MMEM:DATA? '{scope_path}'",
        datatype='B', container=list,
    ))
finally:
    scope.read_termination = original_read_term
    scope.timeout          = 10000

with open(local_path, "wb") as f:
    f.write(png_data)
print("Screenshot gespeichert:", local_path)

# --------------------------------------------------
scope.close()
rm.close()
print("Fertig.")


# PASS/FAIL-Kriteria 
# --------------------------------------------------
#  t= 65ns
#   bei PASS/FAIL-Kriteria : t= 65ns
# Bei 1KV soll A bei 65ns 2A mit 30% Toleranz sein, bei 2KV 4A mit 30% Toleranz und bei 4KV 8A mit 30% Toleranz, bei 6KV 12A mit 30% Toleranz, Bei 8KV 16A mit 30% Toleranz, bei 10KV 20A mit 30% Toleranz
# --------------------------------------------------
y_65ns= abs(y_65ns)
A_65ns= abs(y_65ns*10/(ATTENUATION*2)) # Umrechnung von gemessener Spannung auf Strom (Skalierung, Attenuation, 2Ohm)
# für kv =1 und KV=-1 , Positive und Negativ

if entlade_kv == 1 or  entlade_kv==-1:      #  A soll 2 amper30% Toleranz sein  das heisst 1.4A <= A <= 2.6A
    lower_limit = 2 * 0.7 
    upper_limit = 2 * 1.3

    if lower_limit <= A_65ns <= upper_limit:
        print(f"PASS: A_65ns = {A_65ns:.2f} A liegt im Bereich [{lower_limit:.2f}, {upper_limit:.2f}] A")
    else:
        print(f"FAIL: A_65ns = {A_65ns:.2f} A liegt außerhalb des Bereichs [{lower_limit:.2f}, {upper_limit:.2f}] A")

elif entlade_kv == 2 or entlade_kv==-2:
    #  A soll 4A mit 30% Toleranz sein
    lower_limit = 4 * 0.7
    upper_limit = 4 * 1.3
    if lower_limit <= A_65ns <= upper_limit:
        print(f"PASS: A_65ns = {A_65ns:.2f} A liegt im Bereich [{lower_limit:.2f}, {upper_limit:.2f}] A")
    else:
        print(f"FAIL: A_65ns = {A_65ns:.2f} A liegt außerhalb des Bereichs [{lower_limit:.2f}, {upper_limit:.2f}] A")
elif entlade_kv == 4 or entlade_kv==-4:
    #  A soll 8A mit 30% Toleranz sein
    lower_limit = 8 * 0.7
    upper_limit = 8 * 1.3
    if lower_limit <= A_65ns <= upper_limit:
        print(f"PASS: A_65ns = {A_65ns:.2f} A liegt im Bereich [{lower_limit:.2f}, {upper_limit:.2f}] A")
    else:
        print(f"FAIL: A_65ns = {A_65ns:.2f} A liegt außerhalb des Bereichs [{lower_limit:.2f}, {upper_limit:.2f}] A")
elif entlade_kv == 6 or entlade_kv==-6:   
    #  A soll 12A mit 30% Toleranz sein
    lower_limit = 12 * 0.7
    upper_limit = 12 * 1.3
    if lower_limit <= A_65ns <= upper_limit:
        print(f"PASS: A_65ns = {A_65ns:.2f} A liegt im Bereich [{lower_limit:.2f}, {upper_limit:.2f}] A")
    else:
        print(f"FAIL: A_65ns = {A_65ns:.2f} A liegt außerhalb des Bereichs [{lower_limit:.2f}, {upper_limit:.2f}] A")
elif entlade_kv == 8 or entlade_kv==-8:   

    #  A soll 16A mit 30% Toleranz sein
    lower_limit = 16 * 0.7
    upper_limit = 16 * 1.3
    if lower_limit <= A_65ns <= upper_limit:
        print(f"PASS: A_65ns = {A_65ns:.2f} A liegt im Bereich [{lower_limit:.2f}, {upper_limit:.2f}] A")
    else:
        print(f"FAIL: A_65ns = {A_65ns:.2f} A liegt außerhalb des Bereichs [{lower_limit:.2f}, {upper_limit:.2f}] A")

        #Finish

# <-------------------------------------------------->
# t= 130ns 
# bei PASS/FAIL-Kriteria : 
# Bei 1KV soll A bei 130ns 1A mit 30% Toleranz sein
#  bei 2KV 2A mit 30% Toleranz 
#  bei 4KV 4A mit 30% Toleranz
#  bei 6KV 6A mit 30% Toleranz
#  Bei 8KV 8A mit 30% Toleranz


A_130ns= abs(y_130ns*10/(ATTENUATION*2)) # Umrechnung von gemessener Spannung auf Strom (Skalierung, Attenuation, Faktor 2 da 2 Ohm Systemaufbau)

if entlade_kv == 1 or  entlade_kv==-1:      #  A soll 1A mit 30% Toleranz sein  das heisst 0.7A <= A <= 1.3A
    lower_limit = 1 * 0.7
    upper_limit = 1 * 1.3

    if lower_limit <= A_130ns <= upper_limit:
        print(f"PASS: A_130ns = {A_130ns:.2f} A liegt im Bereich [{lower_limit:.2f}, {upper_limit:.2f}] A")
    else:
        print(f"FAIL: A_130ns = {A_130ns:.2f} A liegt außerhalb des Bereichs [{lower_limit:.2f}, {upper_limit:.2f}] A")
elif entlade_kv == 2 or entlade_kv==-2:
    #  A soll 2A mit 30% Toleranz sein
    lower_limit = 2 * 0.7
    upper_limit = 2 * 1.3
    if lower_limit <= A_130ns <= upper_limit:
        print(f"PASS: A_130ns = {A_130ns:.2f} A liegt im Bereich [{lower_limit:.2f}, {upper_limit:.2f}] A")
    else:
        print(f"FAIL: A_130ns = {A_130ns:.2f} A liegt außerhalb des Bereichs [{lower_limit:.2f}, {upper_limit:.2f}] A")
elif entlade_kv == 4 or entlade_kv==-4:
    #  A soll 4A mit 30% Toleranz sein
    lower_limit = 4 * 0.7
    upper_limit = 4 * 1.3
    if lower_limit <= A_130ns <= upper_limit:
        print(f"PASS: A_130ns = {A_130ns:.2f} A liegt im Bereich [{lower_limit:.2f}, {upper_limit:.2f}] A")
    else:
        print(f"FAIL: A_130ns = {A_130ns:.2f} A liegt außerhalb des Bereichs [{lower_limit:.2f}, {upper_limit:.2f}] A")
elif entlade_kv == 6 or entlade_kv==-6:   
    #  A soll 6A mit 30% Toleranz sein
    lower_limit = 6 * 0.7
    upper_limit = 6 * 1.3
    if lower_limit <= A_130ns <= upper_limit:
        print(f"PASS: A_130ns = {A_130ns:.2f} A liegt im Bereich [{lower_limit:.2f}, {upper_limit:.2f}] A")
    else:
        print(f"FAIL: A_130ns = {A_130ns:.2f} A liegt außerhalb des Bereichs [{lower_limit:.2f}, {upper_limit:.2f}] A")
elif entlade_kv == 8 or entlade_kv==-8:   

    #  A soll 8A mit 30% Toleranz sein
    lower_limit = 8 * 0.7
    upper_limit = 8 * 1.3
    if lower_limit <= A_130ns <= upper_limit:
        print(f"PASS: A_130ns = {A_130ns:.2f} A liegt im Bereich [{lower_limit:.2f}, {upper_limit:.2f}] A")
    else:
        print(f"FAIL: A_130ns = {A_130ns:.2f} A liegt außerhalb des Bereichs [{lower_limit:.2f}, {upper_limit:.2f}] A")

# <-------------------------------------------------->



# Peak Kriteria

#Bei Peak Kriteria soll bei 1KV ein Strom von 3,75A mit Toleranz von 10%,
#  Bei 2KV 7,5A mit Toleranz von 10% 
#  bei 4KV 15A mit Toleranz von 10%,
#  bei 6KV 22,5A mit Toleranz von 10%
#  bei 8KV 30A mit Toleranz von 10% .

# Berechnung des Peaks aus den gemessenen Samples , umrechnen von Spannung auf Strom (Skalierung, Attenuation, Faktor 2 da Peak zu Peak)
# Vpp ist der gemessene Peak-to-Peak Wert, umgerechnet auf Strom
# abs() da je nach Polung der Peak positiv oder negativ sein kann, aber wir wollen den Betrag des Stroms wissen
# A_peak ist der berechnete Peak-Strom, umgerechnet von der gemessenen Spannung (Vpp) unter Berücksichtigung der Skalierung und Attenuation

vpp=  abs(vpp)
# Umrechnung in Betrag der vpeak

A_peak = abs(vpp*10/(ATTENUATION*2))   
print(f"  Berechneter Peak-Strom: {A_peak:.2f} A")


if entlade_kv == 1 or  entlade_kv==-1:      #  A soll 3,75A mit 10% Toleranz sein  das heisst 3.375A <= A <= 4.125A
    lower_limit = 3.75 * 0.9
    upper_limit = 3.75 * 1.1
    if lower_limit <= A_peak <= upper_limit:
        print(f"PASS: Peak = {A_peak:.2f} A liegt im Bereich [{lower_limit:.2f}, {upper_limit:.2f}] A")
    else:
        print(f"FAIL: Peak = {A_peak:.2f} A liegt außerhalb des Bereichs [{lower_limit:.2f}, {upper_limit:.2f}] A")
elif entlade_kv == 2 or entlade_kv==-2:   
    lower_limit = 7.5 * 0.9
    upper_limit = 7.5 * 1.1
    if lower_limit <= A_peak <= upper_limit:
        print(f"PASS: Peak = {A_peak:.2f} A liegt im Bereich [{lower_limit:.2f}, {upper_limit:.2f}] A")
    else:
        print(f"FAIL: Peak = {A_peak:.2f} A liegt außerhalb des Bereichs [{lower_limit:.2f}, {upper_limit:.2f}] A")
elif entlade_kv == 4 or entlade_kv==-4:
    lower_limit = 15 * 0.9
    upper_limit = 15 * 1.1
    if lower_limit <= A_peak <= upper_limit:
        print(f"PASS: Peak = {A_peak:.2f} A liegt im Bereich [{lower_limit:.2f}, {upper_limit:.2f}] A")
    else:
        print(f"FAIL: Peak = {A_peak:.2f} A liegt außerhalb des Bereichs [{lower_limit:.2f}, {upper_limit:.2f}] A")
elif entlade_kv == 6 or entlade_kv==-6:
    lower_limit = 22.5 * 0.9
    upper_limit = 22.5 * 1.1
    if lower_limit <= A_peak <= upper_limit:
        print(f"PASS: Peak = {A_peak:.2f} A liegt im Bereich [{lower_limit:.2f}, {upper_limit:.2f}] A")
    else:
        print(f"FAIL: Peak = {A_peak:.2f} A liegt außerhalb des Bereichs [{lower_limit:.2f}, {upper_limit:.2f}] A")
elif entlade_kv == 8 or entlade_kv==-8:
    lower_limit = 30 * 0.9
    upper_limit = 30 * 1.1
    if lower_limit <= A_peak <= upper_limit:
        print(f"PASS: Peak = {A_peak:.2f} A liegt im Bereich [{lower_limit:.2f}, {upper_limit:.2f}] A")
    else:
        print(f"FAIL: Peak = {A_peak:.2f} A liegt außerhalb des Bereichs [{lower_limit:.2f}, {upper_limit:.2f}] A")

# --------------------------------------------------
# MESSDATEN SPEICHERN
# --------------------------------------------------
report_data = {
    "timestamp":       timestamp,
    "entlade_kv":      entlade_kv,
    "trigger_level":   TRIGGER_LEVEL,
    "trigger_offset":  TRIGGER_OFFSET,
    "scale":           SCALE_MAP[entlade_kv],
    "attenuation":     ATTENUATION,
    "v_65ns":          y_65ns_raw,
    "v_130ns":         y_130ns_raw,
    "vpeak":           vpeak,
    "vpp":             abs(vpp),
    "A_65ns":          A_65ns,
    "A_130ns":         A_130ns,
    "A_peak":          A_peak,
    "screenshot_path": local_path,
}
json_path = os.path.join(LOCAL_SAVE_DIR, f"ESD_{timestamp}.json")
with open(json_path, "w", encoding="utf-8") as f:
    json.dump(report_data, f, indent=2)
print("Messdaten gespeichert:", json_path)
print("-> Starte esd_report.py fuer den Gesamtbericht wenn alle Messungen fertig sind.")