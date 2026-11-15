import json
import urllib.request
import os
from datetime import datetime

ISTAT_URL = "[suspicious link removed]"
VERSION_FILE = "version.json"
OUTPUT_CORE = "comuni_core.json"

def main():
    print("1. Controllo archivio ISTAT...")
    req = urllib.request.Request(
        ISTAT_URL, 
        headers={'User-Agent': 'Mozilla/5.0'}
    )
    
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            csv_bytes = response.read()
            csv_text = csv_bytes.decode('latin-1')
    except Exception as e:
        print(f"Errore download ISTAT: {e}. Salto aggiornamento.")
        return

    lines = csv_text.strip().splitlines()
    if len(lines) < 2:
        print("Tracciato ISTAT vuoto o non conforme.")
        return

    # 2. Carica il database corrente per non perdere curiosità ed etimologie già presenti
    db_esistente = {}
    if os.path.exists(OUTPUT_CORE):
        try:
            with open(OUTPUT_CORE, "r", encoding="utf-8") as f:
                dati_vecchi = json.load(f)
                for item in dati_vecchi:
                    db_esistente[str(item.get("id", ""))] = item
        except Exception as e:
            print(f"Avviso lettura db vecchio: {e}")

    # 3. Parsing del tracciato ISTAT
    # Campi ISTAT standard: Codice Regione; Codice Provincia; Progressivo Comune; Denominazione; Sigla Automobilistica; Ripartizione...
    separatore = ';' if ';' in lines[0] else ','
    header = [h.strip() for h in lines[0].split(separatore)]
    
    comuni_aggiornati = []
    modifiche_rilevate = False

    for line in lines[1:]:
        parts = [p.strip() for p in line.split(separatore)]
        if len(parts) < 15:
            continue
            
        cod_regione = parts[0].zfill(2)
        cod_provincia = parts[1].zfill(3)
        prog_comune = parts[2].zfill(3)
        id_comune = f"{cod_provincia}{prog_comune}"
        nome_comune = parts[6]
        sigla_prov = parts[14]

        # Recupera dati pregressi se presenti
        record_vecchio = db_esistente.get(id_comune, {})
        
        # Popolazione e coordinate
        lat = record_vecchio.get("lat", 0.0)
        lon = record_vecchio.get("lon", 0.0)
        popolazione = record_vecchio.get("pop", 0)
        altitudine = record_vecchio.get("alt", 0)
        difficolta = record_vecchio.get("diff", "Medio")
        stemma = record_vecchio.get("stemma", "")
        regione = record_vecchio.get("regione", "")
        prov_estesa = record_vecchio.get("provEstesa", "")

        comuni_aggiornati.append({
            "id": id_comune,
            "nome": nome_comune,
            "prov": sigla_prov,
            "provEstesa": prov_estesa if prov_estesa else sigla_prov,
            "regione": regione,
            "lat": lat,
            "lon": lon,
            "pop": popolazione,
            "alt": altitudine,
            "diff": difficolta,
            "stemma": stemma
        })

    # Verifica se ci sono state variazioni di numero di comuni
    if len(comuni_aggiornati) != len(db_esistente):
        modifiche_rilevate = True
        print(f"Variazione rilevata: da {len(db_esistente)} a {len(comuni_aggiornati)} comuni.")

    # 4. Se ci sono state modifiche (o primo avvio), genera i file e alza la versione
    if modifiche_rilevate or not os.path.exists(OUTPUT_CORE):
        with open(OUTPUT_CORE, "w", encoding="utf-8") as f:
            json.dump(comuni_aggiornati, f, ensure_ascii=False, separators=(',', ':'))
        
        # Incrementa versione
        versione_nuova = int(datetime.now().strftime("%Y%m%d"))
        nuovo_version_data = {
            "versione": versione_nuova,
            "data_aggiornamento": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        with open(VERSION_FILE, "w", encoding="utf-8") as f:
            json.dump(nuovo_version_data, f, indent=2)
            
        print(f"Database aggiornato con successo alla versione {versione_nuova}!")
    else:
        print("Nessuna variazione territoriale rilevata da ISTAT.")

if __name__ == "__main__":
    main()
