<<<<<<< HEAD
# Calcolatore Superficie Edifici

Questo software permette di calcolare la superficie quadrata di un edificio fornendo semplicemente il suo indirizzo. Utilizza le API di Google Maps per ottenere i dati degli edifici e calcolare la loro superficie.

## Requisiti

- Python 3.7 o superiore
- Connessione internet
- Chiave API di Google Maps con i seguenti servizi abilitati:
  - Geocoding API
  - Maps JavaScript API
  - Places API
- Visual Studio Build Tools (solo per Windows)

## Configurazione

1. Ottieni una chiave API di Google Maps dalla [Google Cloud Console](https://console.cloud.google.com/)
2. Abilita i servizi necessari (Geocoding API, Maps JavaScript API, Places API)
3. Crea un file `.env` nella directory principale del progetto con il seguente contenuto:
   ```
   GOOGLE_MAPS_API_KEY=your_api_key_here
   ```
   Sostituisci `your_api_key_here` con la tua chiave API di Google Maps

## Installazione

### Windows

1. Installa Visual Studio Build Tools:
   - Scarica [Visual Studio Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/)
   - Durante l'installazione, seleziona "C++ build tools" e assicurati che sia selezionato "Windows 10 SDK"
   - Riavvia il computer dopo l'installazione

2. Crea un ambiente virtuale (consigliato):
   ```bash
   python -m venv venv
   .\venv\Scripts\activate
   ```

3. Aggiorna pip:
   ```bash
   python -m pip install --upgrade pip
   ```

4. Installa le dipendenze:
   ```bash
   pip install wheel
   pip install -r requirements.txt
   ```

### Linux/MacOS

1. Crea un ambiente virtuale (consigliato):
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

2. Aggiorna pip:
   ```bash
   pip install --upgrade pip
   ```

3. Installa le dipendenze:
   ```bash
   pip install -r requirements.txt
   ```

## Utilizzo

1. Attiva l'ambiente virtuale se non è già attivo:
   - Windows: `.\venv\Scripts\activate`
   - Linux/MacOS: `source venv/bin/activate`

2. Esegui il programma:
   ```bash
   python calcola_superficie.py
   ```
   oppure per l'interfaccia web:
   ```bash
   streamlit run app.py
   ```

3. Inserisci l'indirizzo completo dell'edificio quando richiesto
4. Il programma calcolerà la superficie approssimativa in metri quadrati

## Risoluzione dei problemi

Se incontri errori durante l'installazione:

1. Assicurati di avere Python 3.7 o superiore:
   ```bash
   python --version
   ```

2. Se sei su Windows, verifica che Visual Studio Build Tools sia installato correttamente:
   ```bash
   where cl
   ```
   Dovrebbe mostrare il percorso del compilatore C++

3. Prova a installare le dipendenze una alla volta:
   ```bash
   pip install numpy==1.24.3
   pip install pandas==2.0.3
   pip install -r requirements.txt
   ```

4. Se continui ad avere problemi, prova a utilizzare una versione precompilata di numpy:
   ```bash
   pip install numpy-1.24.3+mkl-cp39-cp39-win_amd64.whl
   ```
   Scarica il file .whl appropriato da [qui](https://www.lfd.uci.edu/~gohlke/pythonlibs/#numpy)

## Note

- La precisione del calcolo dipende dalla qualità dei dati disponibili su Google Maps
- Per ottenere risultati migliori, inserire l'indirizzo nel formato più completo possibile
- Il calcolo è approssimativo e potrebbe non corrispondere esattamente alla superficie reale dell'edificio

## Limitazioni

- È necessaria una chiave API di Google Maps valida
- Il software funziona solo per edifici mappati su Google Maps
- La precisione può variare in base alla qualità dei dati disponibili
- Alcuni indirizzi potrebbero non essere trovati o potrebbero restituire risultati non accurati
=======
# Calcolatore Superficie Edifici

Questo software permette di calcolare la superficie quadrata di un edificio fornendo semplicemente il suo indirizzo. Utilizza le API di Google Maps per ottenere i dati degli edifici e calcolare la loro superficie.

## Requisiti

- Python 3.7 o superiore
- Connessione internet
- Chiave API di Google Maps con i seguenti servizi abilitati:
  - Geocoding API
  - Maps JavaScript API
  - Places API
- Visual Studio Build Tools (solo per Windows)

## Configurazione

1. Ottieni una chiave API di Google Maps dalla [Google Cloud Console](https://console.cloud.google.com/)
2. Abilita i servizi necessari (Geocoding API, Maps JavaScript API, Places API)
3. Crea un file `.env` nella directory principale del progetto con il seguente contenuto:
   ```
   GOOGLE_MAPS_API_KEY=your_api_key_here
   ```
   Sostituisci `your_api_key_here` con la tua chiave API di Google Maps

## Installazione

### Windows

1. Installa Visual Studio Build Tools:
   - Scarica [Visual Studio Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/)
   - Durante l'installazione, seleziona "C++ build tools" e assicurati che sia selezionato "Windows 10 SDK"
   - Riavvia il computer dopo l'installazione

2. Crea un ambiente virtuale (consigliato):
   ```bash
   python -m venv venv
   .\venv\Scripts\activate
   ```

3. Aggiorna pip:
   ```bash
   python -m pip install --upgrade pip
   ```

4. Installa le dipendenze:
   ```bash
   pip install wheel
   pip install -r requirements.txt
   ```

### Linux/MacOS

1. Crea un ambiente virtuale (consigliato):
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

2. Aggiorna pip:
   ```bash
   pip install --upgrade pip
   ```

3. Installa le dipendenze:
   ```bash
   pip install -r requirements.txt
   ```

## Utilizzo

1. Attiva l'ambiente virtuale se non è già attivo:
   - Windows: `.\venv\Scripts\activate`
   - Linux/MacOS: `source venv/bin/activate`

2. Esegui il programma:
   ```bash
   python calcola_superficie.py
   ```
   oppure per l'interfaccia web:
   ```bash
   streamlit run app.py
   ```

3. Inserisci l'indirizzo completo dell'edificio quando richiesto
4. Il programma calcolerà la superficie approssimativa in metri quadrati

## Risoluzione dei problemi

Se incontri errori durante l'installazione:

1. Assicurati di avere Python 3.7 o superiore:
   ```bash
   python --version
   ```

2. Se sei su Windows, verifica che Visual Studio Build Tools sia installato correttamente:
   ```bash
   where cl
   ```
   Dovrebbe mostrare il percorso del compilatore C++

3. Prova a installare le dipendenze una alla volta:
   ```bash
   pip install numpy==1.24.3
   pip install pandas==2.0.3
   pip install -r requirements.txt
   ```

4. Se continui ad avere problemi, prova a utilizzare una versione precompilata di numpy:
   ```bash
   pip install numpy-1.24.3+mkl-cp39-cp39-win_amd64.whl
   ```
   Scarica il file .whl appropriato da [qui](https://www.lfd.uci.edu/~gohlke/pythonlibs/#numpy)

## Note

- La precisione del calcolo dipende dalla qualità dei dati disponibili su Google Maps
- Per ottenere risultati migliori, inserire l'indirizzo nel formato più completo possibile
- Il calcolo è approssimativo e potrebbe non corrispondere esattamente alla superficie reale dell'edificio

## Limitazioni

- È necessaria una chiave API di Google Maps valida
- Il software funziona solo per edifici mappati su Google Maps
- La precisione può variare in base alla qualità dei dati disponibili
- Alcuni indirizzi potrebbero non essere trovati o potrebbero restituire risultati non accurati
>>>>>>> a2622d63a6b1201a228824d34f75578498cad150
- Le API di Google Maps potrebbero comportare costi in base all'utilizzo 