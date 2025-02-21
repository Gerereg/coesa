import requests
import googlemaps
from dotenv import load_dotenv
import os
import math
import webbrowser
import tempfile

# Carica le variabili d'ambiente
load_dotenv()

# Verifica la presenza della chiave API
if not os.getenv('GOOGLE_MAPS_API_KEY'):
    print("❌ Errore: Chiave API di Google Maps non trovata!")
    print("Assicurati di:")
    print("1. Aver creato il file .env nella directory del progetto")
    print("2. Aver inserito la chiave API nel formato: GOOGLE_MAPS_API_KEY=your_api_key_here")
    exit(1)

# Inizializza il client Google Maps
try:
    gmaps = googlemaps.Client(key=os.getenv('GOOGLE_MAPS_API_KEY'))
except Exception as e:
    print(f"❌ Errore nell'inizializzazione del client Google Maps: {str(e)}")
    exit(1)

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
            has_street_number = any(component['types'][0] == 'street_number' 
                                  for component in location['address_components'])
            return lat, lon, indirizzo_completo, has_street_number
        return None, None, None, False
    except Exception as e:
        print(f"❌ Errore nel geocoding per l'indirizzo {indirizzo}: {str(e)}")
        return None, None, None, False

def genera_mappa_html(lat, lon, coordinates, area):
    """Genera una mappa HTML con il poligono dell'edificio usando Google Maps."""
    api_key = os.getenv('GOOGLE_MAPS_API_KEY')
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Mappa Edificio</title>
        <script src="https://maps.googleapis.com/maps/api/js?key={api_key}&libraries=places"></script>
        <style>
            #map {{ height: 600px; width: 100%; }}
            body {{ margin: 0; padding: 20px; font-family: Arial, sans-serif; }}
            .info {{ margin-bottom: 20px; padding: 10px; background-color: #f0f0f0; border-radius: 5px; }}
        </style>
    </head>
    <body>
        <div class="info">
            <h2>Dettagli Edificio</h2>
            <p><strong>Coordinate:</strong> {lat:.6f}, {lon:.6f}</p>
            <p><strong>Area stimata:</strong> {area:.1f} m²</p>
        </div>
        <div id="map"></div>
        <script>
            function initMap() {{
                var map = new google.maps.Map(document.getElementById('map'), {{
                    center: {{ lat: {lat}, lng: {lon} }},
                    zoom: 19,
                    mapTypeId: 'hybrid'
                }});
                
                var buildingCoords = {coordinates};
                
                var building = new google.maps.Polygon({{
                    paths: buildingCoords.map(coord => ({{lat: coord[0], lng: coord[1]}})),
                    strokeColor: '#0000FF',
                    strokeOpacity: 0.8,
                    strokeWeight: 2,
                    fillColor: '#0000FF',
                    fillOpacity: 0.35
                }});
                building.setMap(map);
                
                var marker = new google.maps.Marker({{
                    position: {{ lat: {lat}, lng: {lon} }},
                    map: map,
                    title: 'Posizione cercata'
                }});
                
                var infowindow = new google.maps.InfoWindow({{
                    content: '<div style="padding: 10px;"><h3>Superficie Edificio</h3><p>Area: {area:.1f} m²</p></div>'
                }});
                
                marker.addListener('click', function() {{
                    infowindow.open(map, marker);
                }});
                
                // Apri l'infowindow automaticamente
                infowindow.open(map, marker);
            }}
            
            window.onload = initMap;
        </script>
    </body>
    </html>
    """
    
    fd, path = tempfile.mkstemp(suffix='.html')
    with os.fdopen(fd, 'w', encoding='utf-8') as f:
        f.write(html)
    return path

def calcola_superficie_edificio(lat, lon):
    """Calcola la superficie esatta di un edificio utilizzando OpenStreetMap Buildings."""
    try:
        # Definisci il raggio di ricerca (in gradi)
        radius = 0.001  # circa 100 metri

        # Query Overpass API per ottenere i dati dell'edificio
        overpass_url = "http://overpass-api.de/api/interpreter"
        overpass_query = f"""
        [out:json];
        way(around:{int(radius * 111319.9)},{lat},{lon})[building];
        (._;>;);
        out geom;
        """
        
        response = requests.post(overpass_url, data=overpass_query)
        data = response.json()
        
        if not data.get('elements'):
            return None, None, "Nessun edificio trovato a questo indirizzo."
        
        # Trova l'edificio più vicino alle coordinate date
        closest_building = None
        min_distance = float('inf')
        
        for element in data['elements']:
            if element.get('type') == 'way' and element.get('geometry'):
                # Calcola il centro dell'edificio
                coords = element['geometry']
                center_lat = sum(node['lat'] for node in coords) / len(coords)
                center_lon = sum(node['lon'] for node in coords) / len(coords)
                
                # Calcola la distanza dal punto cercato
                distance = math.sqrt((center_lat - lat)**2 + (center_lon - lon)**2)
                
                if distance < min_distance:
                    min_distance = distance
                    closest_building = element
        
        if not closest_building:
            return None, None, "Impossibile calcolare l'area dell'edificio."
        
        # Estrai le coordinate dell'edificio
        coordinates = [[node['lat'], node['lon']] for node in closest_building['geometry']]
        
        # Assicurati che il poligono sia chiuso
        if coordinates[0] != coordinates[-1]:
            coordinates.append(coordinates[0])
        
        # Calcola l'area usando la formula del poligono irregolare (formula di Gauss)
        def calculate_area(coords):
            def distance_between_points(lat1, lon1, lat2, lon2):
                R = 6371000  # Raggio della Terra in metri
                lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
                dlat = lat2 - lat1
                dlon = lon2 - lon1
                a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
                c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
                return R * c

            area = 0
            for i in range(len(coords) - 1):
                lat1, lon1 = coords[i]
                lat2, lon2 = coords[i + 1]
                
                # Calcola la base e l'altezza del triangolo formato
                base = distance_between_points(lat1, lon1, lat1, lon2)
                height = distance_between_points(lat1, lon2, lat2, lon2)
                
                # Aggiungi l'area del triangolo
                area += base * height / 2

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
        
        return area, coordinates, messaggio
        
    except Exception as e:
        print(f"❌ Errore durante il calcolo della superficie: {str(e)}")
        return None, None, f"Errore durante il calcolo della superficie: {str(e)}"

def main():
    print("\n🏢 Calcolatore di Superficie Edifici")
    print("=" * 40)
    print("\n📌 Suggerimenti per un risultato migliore:")
    print("- Inserisci l'indirizzo completo con il numero civico")
    print("- Includi la città e la provincia")
    print("- Esempio: Via Roma 1, Milano, MI")
    print("=" * 40)
    
    while True:
        indirizzo = input("\n📍 Inserisci l'indirizzo dell'edificio (o 'q' per uscire): ")
        
        if indirizzo.lower() == 'q':
            print("\n👋 Grazie per aver usato il calcolatore!")
            break
            
        lat, lon, indirizzo_completo, numero_civico_trovato = ottieni_coordinate(indirizzo)
        
        if lat and lon:
            print(f"\n✅ Indirizzo trovato: {indirizzo_completo}")
            if not numero_civico_trovato:
                print("\n⚠️  Attenzione: il numero civico non è stato trovato con precisione.")
                print("   L'edificio selezionato potrebbe non essere quello corretto.")
                
            area, coordinates, messaggio = calcola_superficie_edificio(lat, lon)
            
            if area and coordinates:
                print(f"\n📏 Superficie stimata: {area:.1f} m²")
                
                # Genera e apri la mappa
                mappa_path = genera_mappa_html(lat, lon, coordinates, area)
                print("\n🗺️  Apertura mappa nel browser...")
                webbrowser.open('file://' + mappa_path)
            else:
                print(f"\n❌ Errore: {messaggio}")
        else:
            print("\n❌ Impossibile trovare le coordinate per questo indirizzo.")

if __name__ == "__main__":
    main() 