"""
Author: Thomas Berends
Date: 2024-12-30
Description: This script retrieves and processes parking permit waiting list information from the Utrecht municipality website.
"""

import os
from bs4 import BeautifulSoup
import requests
import pandas as pd
import urllib3
import time
import re

# Onderdruk SSL-waarschuwingen
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Define the URL
url = 'https://www.utrecht.nl/wonen-en-leven/parkeren/parkeren-bewoner/wachtlijst-parkeervergunning'

# Define the headers
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def haal_website_data():
    """Haalt de website data op met cookie handling"""
    print("Verbinding maken met de website...")
    start_time = time.time()
    
    try:
        # Eerste request om de cookie te verkrijgen
        response = requests.get(url, headers=headers, timeout=30, verify=False)
        
        # Controleer of we de beveiligingspagina hebben gekregen
        if 'JavaScript must be enabled' in response.text:
            print("Beveiligingspagina gedetecteerd, cookie extraheren...")
            
            # Extraheer de cookie uit de response
            cookie_match = re.search(r'document\.cookie="([^"]+)"', response.text)
            
            if cookie_match:
                cookie_str = cookie_match.group(1)
                cookie_name = cookie_str.split('=')[0]
                cookie_value = cookie_str.split('=')[1].split(';')[0]
                
                # Haal de redirect URL
                url_match = re.search(r'location\.href="([^"]+)"', response.text)
                if url_match:
                    redirect_url = url_match.group(1)
                    
                    # Maak nieuwe headers met de cookie
                    new_headers = headers.copy()
                    new_headers['Cookie'] = f"{cookie_name}={cookie_value}"
                    
                    # Doe een nieuwe request met de cookie
                    response = requests.get(redirect_url, headers=new_headers, timeout=30, verify=False)
        
        response_time = time.time() - start_time
        
        if response.status_code == 200 and 'parkeervergunning' in response.text.lower():
            print(f"✅ Verbinding succesvol! Responstijd: {response_time:.2f}s")
            return response.text
        else:
            print(f"❌ Verbinding kreeg een response, maar de inhoud was niet correct.")
            return None
            
    except Exception as e:
        print(f"❌ Verbinding werkt niet: {str(e)}")
        return None

def scrape_alle_wijken_data(soup):
    """Scrapet data voor alle wijken uit de tabel"""
    alle_data = []
    
    # Zoek naar tabellen in de HTML
    tabellen = soup.find_all('table')
    
    for tabel in tabellen:
        # Zoek naar alle rijen in de tabel
        rijen = tabel.find_all('tr')
        
        for rij in rijen:
            # Zoek naar alle cellen in de rij
            cellen = rij.find_all(['td', 'th'])
            
            if len(cellen) >= 4:  # Een rij moet minimaal 4 kolommen hebben
                # De kolommen zijn: Parkeergebied, Wachtlijst voor, Eerstvolgende wacht sinds, Aantal op wachtlijst
                parkeergebied_cel = cellen[0]
                wachtlijst_voor_cel = cellen[1]
                eerstvolgende_wacht_cel = cellen[2]
                aantal_cel = cellen[3]
                
                if (parkeergebied_cel.text and parkeergebied_cel.text.strip() and
                    parkeergebied_cel.text.lower() not in ['parkeergebied (met rayonnummer)', 'parkeergebied', 'wijk']):
                    
                    parkeergebied = parkeergebied_cel.text.strip()
                    wijk_naam = parkeergebied.split('(')[0].strip()
                    wachtlijst_voor = wachtlijst_voor_cel.text.strip()
                    eerstvolgende_wacht = eerstvolgende_wacht_cel.text.strip()
                    aantal = aantal_cel.text.strip()
                    
                    # Alle records meenemen
                    alle_data.append({
                        'wijk': wijk_naam,
                        'wachtlijst_voor': wachtlijst_voor,
                        'eerstvolgende_wacht': eerstvolgende_wacht,
                        'aantal': aantal
                    })
    
    return alle_data


# Haal website data op
html = haal_website_data()
if not html:
    print("Geen data opgehaald. Het script wordt gestopt.")
    exit(1)

# Parse HTML
soup = BeautifulSoup(html, 'html.parser')

# Scrape data voor alle wijken
alle_wijken_data = scrape_alle_wijken_data(soup)

# Haal bijgewerkt datum op
bijgewerkt = None
all_divs = soup.find_all('div')
for div in all_divs:
    if div.text and 'bijgewerkt op' in div.text:
        bijgewerkt = div.text.split('bijgewerkt op')[1].split('.')[0].strip()
        break

# Check if file exists and update with new data
file_path = 'data/history.csv'
if os.path.exists(file_path):
    data = pd.read_csv(file_path)
    
    # Controleer per wijk of er nieuwe data is
    nieuwe_records = []
    wijken_met_veranderingen = []
    
    for wijk_data in alle_wijken_data:
        wijk_naam = wijk_data['wijk']
        wachtlijst_voor = wijk_data['wachtlijst_voor']
        
        # Zoek de laatste record voor deze wijk en wachtlijst type
        wijk_records = data[(data['wijk'] == wijk_naam) & (data['wachtlijst_voor'] == wachtlijst_voor)]
        
        if len(wijk_records) > 0:
            # Er zijn al records voor deze wijk en wachtlijst type, vergelijk met de laatste
            laatste_record = wijk_records.iloc[-1]
            
            # Check of er veranderingen zijn in een van de vier items
            verandering_wachtlijst_voor = laatste_record['wachtlijst_voor'] != wachtlijst_voor
            verandering_bijgewerkt = laatste_record['bijgewerkt'] != bijgewerkt
            verandering_aantal = laatste_record['aantal_aanmeldingen'] != int(wijk_data['aantal'])
            verandering_datum = laatste_record['aanmelddatum_eerstvolgende'] != wijk_data['eerstvolgende_wacht']
            
            if verandering_wachtlijst_voor or verandering_bijgewerkt or verandering_aantal or verandering_datum:
                # Er is een verandering, voeg nieuwe record toe
                nieuwe_record = {
                    'wijk': wijk_naam,
                    'wachtlijst_voor': wachtlijst_voor,
                    'bijgewerkt': bijgewerkt,
                    'aantal_aanmeldingen': int(wijk_data['aantal']),
                    'aanmelddatum_eerstvolgende': wijk_data['eerstvolgende_wacht']
                }
                nieuwe_records.append(nieuwe_record)
                wijken_met_veranderingen.append(f"{wijk_naam} ({wachtlijst_voor})")
        else:
            # Eerste keer dat we data voor deze wijk en wachtlijst type hebben
            nieuwe_record = {
                'wijk': wijk_naam,
                'wachtlijst_voor': wachtlijst_voor,
                'bijgewerkt': bijgewerkt,
                'aantal_aanmeldingen': int(wijk_data['aantal']),
                'aanmelddatum_eerstvolgende': wijk_data['eerstvolgende_wacht']
            }
            nieuwe_records.append(nieuwe_record)
            wijken_met_veranderingen.append(f"{wijk_naam} ({wachtlijst_voor})")
    
    if nieuwe_records:
        # Voeg nieuwe records toe
        nieuwe_df = pd.DataFrame(nieuwe_records)
        data = pd.concat([data, nieuwe_df], ignore_index=True)
        
        # Update record nummers
        data['record'] = range(1, len(data) + 1)
        
        # Herordenen van kolommen
        data = data[['record', 'wijk', 'wachtlijst_voor', 'bijgewerkt', 'aantal_aanmeldingen', 'aanmelddatum_eerstvolgende']]
        
        # Sla op
        data.to_csv(file_path, index=False)
        print(f"\nCSV bijgewerkt met nieuwe data voor {len(wijken_met_veranderingen)} records:")
        for wijk in wijken_met_veranderingen:
            print(f"- {wijk}")
    else:
        print(f"\nGeen veranderingen gevonden in de data voor alle wijken")
else:
    # Maak nieuwe CSV met alle wijken
    nieuwe_records = []
    for i, wijk_data in enumerate(alle_wijken_data, 1):
        nieuwe_record = {
            'record': i,
            'wijk': wijk_data['wijk'],
            'wachtlijst_voor': wijk_data['wachtlijst_voor'],
            'bijgewerkt': bijgewerkt,
            'aantal_aanmeldingen': int(wijk_data['aantal']),
            'aanmelddatum_eerstvolgende': wijk_data['eerstvolgende_wacht']
        }
        nieuwe_records.append(nieuwe_record)
    
    df = pd.DataFrame(nieuwe_records)
    df.to_csv(file_path, index=False)
    print(f"\nNieuwe CSV aangemaakt met data voor {len(alle_wijken_data)} records")