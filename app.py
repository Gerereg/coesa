import streamlit as st
import folium
from streamlit_folium import folium_static
import requests
import googlemaps
from dotenv import load_dotenv
import os
import math
import pandas as pd
import io
import csv
import concurrent.futures
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

# Carica le variabili d'ambiente
load_dotenv()

# Verifica la presenza della chiave API
if not os.getenv('GOOGLE_MAPS_API_KEY'):
    st.error("🔑 Chiave API di Google Maps non trovata. Assicurati di averla configurata nel file .env")
    st.stop()

# Inizializza il client Google Maps
try:
    gmaps = googlemaps.Client(key=os.getenv('GOOGLE_MAPS_API_KEY'))
except Exception as e:
    st.error(f"❌ Errore nell'inizializzazione del client Google Maps: {str(e)}")
    st.stop()

# Inizializza lo stato della sessione se non esiste
if 'selected_row' not in st.session_state:
    st.session_state.selected_row = None

# Inizializza lo stato per l'indice della mappa selezionata
if 'mappa_selezionata' not in st.session_state:
    st.session_state.mappa_selezionata = 0

if 'risultati_df' not in st.session_state:
    st.session_state.risultati_df = None

if 'mappe' not in st.session_state:
    st.session_state.mappe = []

def handle_click(row):
    """Gestisce il click su una riga della tabella."""
    st.session_state.selected_row = row

def cambia_mappa(direzione):
    """Cambia l'indice della mappa selezionata."""
    nuovo_indice = st.session_state.mappa_selezionata + direzione
    if 0 <= nuovo_indice < len(st.session_state.mappe):
        st.session_state.mappa_selezionata = nuovo_indice

def ottieni_coordinate(indirizzo):
    """Converte un indirizzo in coordinate geografiche usando Google Maps API."""
    try:
        # Aggiungi "Italia" all'indirizzo se non specificato
        if "italia" not in indirizzo.lower():
            indirizzo += ", Italia"
            
        # Geocoding con Google Maps
        result = gmaps.geocode(indirizzo)
        
        if result and len(result) > 0:
            location = result[0]
            lat = location['geometry']['location']['lat']
            lon = location['geometry']['location']['lng']
            indirizzo_completo = location['formatted_address']
            return lat, lon, indirizzo_completo
        return None, None, None
    except Exception as e:
        st.error(f"Errore nel geocoding per l'indirizzo {indirizzo}: {str(e)}")
        return None, None, None

def calcola_superficie_edificio(lat, lon):
    """Calcola la superficie esatta di un edificio utilizzando OpenStreetMap Buildings."""
    try:
        # Cache per le risposte dell'API
        if not hasattr(st.session_state, 'building_cache'):
            st.session_state.building_cache = {}
        
        # Arrotonda le coordinate per la cache
        cache_key = f"{round(lat, 6)},{round(lon, 6)}"
        
        if cache_key in st.session_state.building_cache:
            return st.session_state.building_cache[cache_key]

        # Definisci il raggio di ricerca (in gradi)
        radius = 0.001  # circa 100 metri

        # Query Overpass API ottimizzata
        overpass_url = "http://overpass-api.de/api/interpreter"
        overpass_query = f"""
        [out:json][timeout:10];
        way(around:{int(radius * 111319.9)},{lat},{lon})[building];
        out geom qt;
        """
        
        response = requests.post(overpass_url, data=overpass_query)
        data = response.json()
        
        if not data.get('elements'):
            result = (None, None, "Nessun edificio trovato a questo indirizzo.")
            st.session_state.building_cache[cache_key] = result
            return result
        
        # Trova l'edificio più vicino alle coordinate date
        closest_building = None
        min_distance = float('inf')
        
        for element in data['elements']:
            if element.get('type') == 'way' and element.get('geometry'):
                # Calcola il centro dell'edificio usando la media delle coordinate
                coords = element['geometry']
                center_lat = sum(node['lat'] for node in coords) / len(coords)
                center_lon = sum(node['lon'] for node in coords) / len(coords)
                
                # Calcola la distanza euclidea (più veloce della distanza geodetica per confronti)
                distance = (center_lat - lat)**2 + (center_lon - lon)**2
                
                if distance < min_distance:
                    min_distance = distance
                    closest_building = element
        
        if not closest_building:
            result = (None, None, "Impossibile calcolare l'area dell'edificio.")
            st.session_state.building_cache[cache_key] = result
            return result
        
        # Estrai le coordinate dell'edificio
        coordinates = [[node['lat'], node['lon']] for node in closest_building['geometry']]
        
        # Assicurati che il poligono sia chiuso
        if coordinates[0] != coordinates[-1]:
            coordinates.append(coordinates[0])
        
        def calculate_area(coords):
            """Calcola l'area di un poligono usando la formula di Gauss."""
            def haversine_distance(lat1, lon1, lat2, lon2):
                R = 6371000  # Raggio della Terra in metri
                
                # Converti in radianti
                lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
                
                # Differenze
                dlat = lat2 - lat1
                dlon = lon2 - lon1
                
                # Formula di Haversine
                a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
                c = 2 * math.asin(math.sqrt(a))
                
                return R * c
            
            area = 0
            for i in range(len(coords) - 1):
                # Calcola la base e l'altezza del triangolo
                base = haversine_distance(coords[i][0], coords[i][1], 
                                       coords[i][0], coords[i+1][1])
                height = haversine_distance(coords[i][0], coords[i+1][1], 
                                         coords[i+1][0], coords[i+1][1])
                
                # Area del triangolo = (base * altezza) / 2
                triangle_area = (base * height) / 2
                area += triangle_area
            
            return area

        area = calculate_area(coordinates)
        
        # Se l'edificio ha un nome in OSM, usalo
        nome_edificio = closest_building.get('tags', {}).get('name', 'Edificio')
        tipo_edificio = closest_building.get('tags', {}).get('building', '')
        
        # Aggiungi il tipo di edificio al messaggio se disponibile
        if tipo_edificio:
            messaggio = f"Superficie calcolata con successo per: {nome_edificio} (Tipo: {tipo_edificio})"
        else:
            messaggio = f"Superficie calcolata con successo per: {nome_edificio}"
        
        result = (area, coordinates, messaggio)
        st.session_state.building_cache[cache_key] = result
        return result
        
    except Exception as e:
        st.error(f"Errore durante il calcolo della superficie: {str(e)}")
        return None, None, f"Errore durante il calcolo della superficie: {str(e)}"

def processa_file(file):
    """Processa un file di indirizzi e restituisce i risultati utilizzando parallelizzazione."""
    risultati = []
    mappe = []
    
    try:
        # Leggi il file come DataFrame
        if file.name.endswith('.csv'):
            df = pd.read_csv(file)
        elif file.name.endswith('.xlsx'):
            df = pd.read_excel(file)
        else:  # Assume che sia un file di testo
            df = pd.read_csv(file, header=None, names=['Indirizzo'])
        
        # Assicurati che ci sia una colonna con gli indirizzi
        colonna_indirizzi = None
        for col in df.columns:
            if 'indirizzo' in col.lower() or 'address' in col.lower():
                colonna_indirizzi = col
                break
        
        if not colonna_indirizzi:
            colonna_indirizzi = df.columns[0]
        
        # Inizializza la progress bar e il contatore
        total_rows = len(df)
        progress_bar = st.progress(0)
        status_text = st.empty()
        processed = 0
        
        # Step 1: Estrai tutte le coordinate
        status_text.text("Fase 1: Estrazione coordinate...")
        coordinate_edifici = []
        
        # Processa gli indirizzi in batch per evitare sovraccarichi
        batch_size = 5
        for i in range(0, total_rows, batch_size):
            batch = df.iloc[i:min(i + batch_size, total_rows)]
            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = []
                for _, row in batch.iterrows():
                    futures.append(executor.submit(ottieni_coordinate, str(row[colonna_indirizzi])))
                
                for future in as_completed(futures):
                    try:
                        lat, lon, indirizzo_completo = future.result()
                        coordinate_edifici.append({
                            'indirizzo': str(df.iloc[processed][colonna_indirizzi]),
                            'indirizzo_completo': indirizzo_completo,
                            'lat': lat,
                            'lon': lon
                        })
                        processed += 1
                        progress_bar.progress(processed / (total_rows * 2))
                    except Exception as e:
                        st.warning(f"Errore nel processare un indirizzo: {str(e)}")
                        coordinate_edifici.append({
                            'indirizzo': str(df.iloc[processed][colonna_indirizzi]),
                            'indirizzo_completo': None,
                            'lat': None,
                            'lon': None,
                            'error': str(e)
                        })
                        processed += 1
                        progress_bar.progress(processed / (total_rows * 2))
        
        # Step 2: Calcola le superfici
        status_text.text("Fase 2: Calcolo superfici...")
        processed = 0
        
        # Processa le superfici in batch
        for i in range(0, len(coordinate_edifici), batch_size):
            batch = coordinate_edifici[i:min(i + batch_size, len(coordinate_edifici))]
            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = []
                for coord in batch:
                    if coord['lat'] and coord['lon']:
                        futures.append(executor.submit(calcola_superficie_edificio, coord['lat'], coord['lon']))
                    else:
                        futures.append(None)
                
                for j, future in enumerate(futures):
                    coord = batch[j]
                    try:
                        if future:
                            area, coordinates, messaggio = future.result()
                            
                            if coordinates:
                                mappe.append({
                                    'lat': coord['lat'],
                                    'lon': coord['lon'],
                                    'coordinates': coordinates,
                                    'area': area,
                                    'indirizzo': coord['indirizzo_completo'],
                                    'indirizzo_input': coord['indirizzo']
                                })
                            
                            risultati.append({
                                'Indirizzo_Input': coord['indirizzo'],
                                'Indirizzo_Trovato': coord['indirizzo_completo'],
                                'Latitudine': coord['lat'],
                                'Longitudine': coord['lon'],
                                'Superficie_m2': area if area else None,
                                'Stato': messaggio if area else "Calcolo superficie non riuscito"
                            })
                        else:
                            risultati.append({
                                'Indirizzo_Input': coord['indirizzo'],
                                'Indirizzo_Trovato': None,
                                'Latitudine': None,
                                'Longitudine': None,
                                'Superficie_m2': None,
                                'Stato': 'Indirizzo non trovato' if not coord.get('error') else f"Errore: {coord['error']}"
                            })
                        
                        processed += 1
                        progress_bar.progress(0.5 + processed / (total_rows * 2))
                    except Exception as e:
                        st.warning(f"Errore nel calcolo della superficie: {str(e)}")
                        risultati.append({
                            'Indirizzo_Input': coord['indirizzo'],
                            'Indirizzo_Trovato': coord['indirizzo_completo'],
                            'Latitudine': coord['lat'],
                            'Longitudine': coord['lon'],
                            'Superficie_m2': None,
                            'Stato': f'Errore durante il calcolo: {str(e)}'
                        })
                        processed += 1
                        progress_bar.progress(0.5 + processed / (total_rows * 2))
        
        status_text.text("Elaborazione completata!")
        progress_bar.empty()
        status_text.empty()
        
        if not risultati:
            st.warning("Nessun risultato ottenuto dall'elaborazione del file.")
            return pd.DataFrame(), []
            
        return pd.DataFrame(risultati), mappe
    
    except Exception as e:
        st.error(f"Errore durante l'elaborazione del file: {str(e)}")
        if not risultati:
            return pd.DataFrame(), []
        return pd.DataFrame(risultati), mappe

def visualizza_mappa(mappa, indice, totale):
    """Visualizza una singola mappa con i suoi dettagli."""
    m = folium.Map(location=[mappa['lat'], mappa['lon']], zoom_start=19)
    folium.Marker(
        [mappa['lat'], mappa['lon']],
        popup=f"Indirizzo: {mappa['indirizzo']}",
        icon=folium.Icon(color="red", icon="info-sign"),
    ).add_to(m)
    folium.Polygon(
        locations=mappa['coordinates'],
        popup=f"Area: {mappa['area']:.1f} m²",
        color="blue",
        fill=True,
        fill_color="blue",
        fill_opacity=0.4,
    ).add_to(m)
    
    st.write(f"### Mappa {indice + 1}/{totale}")
    st.write(f"**Indirizzo inserito:** {mappa['indirizzo_input']}")
    st.write(f"**Indirizzo trovato:** {mappa['indirizzo']}")
    st.write(f"**Superficie:** {mappa['area']:.1f} m²")
    folium_static(m, width=800)

def main():
    st.set_page_config(page_title="Calcolatore Superficie Edifici", layout="wide")
    
    # Inizializza lo stato della sessione se non esiste
    if 'selected_row' not in st.session_state:
        st.session_state.selected_row = None

    if 'mappa_selezionata' not in st.session_state:
        st.session_state.mappa_selezionata = 0

    if 'risultati_df' not in st.session_state:
        st.session_state.risultati_df = None

    if 'mappe' not in st.session_state:
        st.session_state.mappe = []
    
    st.title("🏢 Calcolatore Superficie Edifici")
    
    # Tab per scegliere la modalità
    tab1, tab2 = st.tabs(["Singolo Indirizzo", "Carica File"])
    
    with tab1:
        col1, col2 = st.columns([2, 3])
        
        with col1:
            indirizzo = st.text_input("Indirizzo dell'edificio", "")
            calcola_button = st.button("Calcola Superficie")
            
            if calcola_button and indirizzo:
                lat, lon, indirizzo_completo = ottieni_coordinate(indirizzo)
                
                if lat and lon:
                    st.success(f"Indirizzo trovato: {indirizzo_completo}")
                    area, coordinates, messaggio = calcola_superficie_edificio(lat, lon)
                    
                    if area and coordinates:
                        st.metric("Superficie", f"{area:.1f} m²")
                        
                        # Crea la mappa
                        m = folium.Map(location=[lat, lon], zoom_start=19)
                        
                        # Aggiungi il marker della posizione cercata
                        folium.Marker(
                            [lat, lon],
                            popup="Posizione cercata",
                            icon=folium.Icon(color="red", icon="info-sign"),
                        ).add_to(m)
                        
                        # Aggiungi il poligono dell'edificio
                        folium.Polygon(
                            locations=coordinates,
                            popup=f"Area: {area:.1f} m²",
                            color="blue",
                            fill=True,
                            fill_color="blue",
                            fill_opacity=0.4,
                        ).add_to(m)
                        
                        with col2:
                            st.write("### Mappa dell'edificio")
                            folium_static(m, width=800)
                    else:
                        st.error(messaggio)
                else:
                    st.error("Impossibile trovare le coordinate per questo indirizzo.")
    
    with tab2:
        st.write("Carica un file CSV, Excel o di testo contenente gli indirizzi")
        file = st.file_uploader("Scegli un file", type=['csv', 'txt', 'xlsx'])
        
        if file:
            # Processa il file solo se non è già stato processato o se è un nuovo file
            if st.session_state.risultati_df is None or file.name != st.session_state.get('ultimo_file', ''):
                st.info("Elaborazione del file in corso...")
                st.session_state.risultati_df, st.session_state.mappe = processa_file(file)
                st.session_state.ultimo_file = file.name
                st.session_state.mappa_selezionata = 0
            
            risultati_df = st.session_state.risultati_df
            mappe = st.session_state.mappe
            
            if risultati_df is not None:
                st.success("Elaborazione completata!")
                
                # Creiamo due colonne per la tabella e la mappa
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    # Mostra i risultati in una tabella
                    st.write("### Risultati")
                    st.dataframe(risultati_df)
                    
                    # Prepara il file CSV per il download
                    csv = risultati_df.to_csv(index=False)
                    st.download_button(
                        label="📥 Scarica risultati CSV",
                        data=csv,
                        file_name="risultati_superfici.csv",
                        mime="text/csv"
                    )
                
                with col2:
                    if mappe:
                        st.write("### Naviga tra le mappe")
                        
                        # Controlli di navigazione in riga
                        cols = st.columns([1, 3, 1])
                        with cols[0]:
                            if cols[0].button("⬅️", key="prev", disabled=st.session_state.mappa_selezionata <= 0):
                                cambia_mappa(-1)
                                st.rerun()
                        
                        with cols[1]:
                            # Usa un select_slider invece di uno slider normale
                            opzioni = [f"Mappa {i+1}/{len(mappe)}" for i in range(len(mappe))]
                            indice_selezionato = st.select_slider(
                                "Seleziona la mappa",
                                options=range(len(mappe)),
                                value=st.session_state.mappa_selezionata,
                                format_func=lambda x: opzioni[x],
                                key="mappa_slider"
                            )
                            
                            if indice_selezionato != st.session_state.mappa_selezionata:
                                st.session_state.mappa_selezionata = indice_selezionato
                                st.rerun()
                        
                        with cols[2]:
                            if cols[2].button("➡️", key="next", disabled=st.session_state.mappa_selezionata >= len(mappe)-1):
                                cambia_mappa(1)
                                st.rerun()
                        
                        # Visualizza la mappa selezionata
                        mappa = mappe[st.session_state.mappa_selezionata]
                        visualizza_mappa(mappa, st.session_state.mappa_selezionata, len(mappe))

    st.markdown("---")
    st.markdown("""
    ### Come utilizzare:
    1. Scegli la modalità:
       - **Singolo Indirizzo**: Inserisci un indirizzo e visualizza il risultato sulla mappa
       - **Carica File**: Carica un file con multiple indirizzi e ottieni i risultati in formato CSV
    
    ### Formati file supportati:
    - CSV (con una colonna contenente gli indirizzi)
    - TXT (un indirizzo per riga)
    - Excel (XLSX)
    
    ### Note:
    - La precisione del calcolo dipende dalla qualità dei dati OpenStreetMap
    - Per risultati migliori, inserisci gli indirizzi nel formato più completo possibile
    - L'area calcolata è approssimativa
    - Clicca su una riga nella tabella dei risultati per visualizzare la mappa corrispondente
    """)

if __name__ == "__main__":
    main() 