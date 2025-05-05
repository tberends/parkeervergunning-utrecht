"""
Author: Thomas Berends
Date: 2024-12-30
Description: This script retrieves and processes parking permit waiting list information from the Utrecht municipality website.
"""
#%%
# Import the necessary libraries
import os
from bs4 import BeautifulSoup
import requests
import pandas as pd
import urllib3
import time
from concurrent.futures import ThreadPoolExecutor

# Onderdruk SSL-waarschuwingen
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Define the URL
url = 'https://www.utrecht.nl/wonen-en-leven/parkeren/parkeren-bewoner/wachtlijst-parkeervergunning'
proxy_list_url = 'https://raw.githubusercontent.com/proxifly/free-proxy-list/main/proxies/protocols/http/data.txt'

# Define the headers
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def haal_proxy_lijst_op():
    """Haalt de lijst met proxies op van de gegeven URL"""
    try:
        response = requests.get(proxy_list_url, timeout=10)
        response.raise_for_status()
        # Split de tekst op spaties en haal eventuele lege regels weg
        proxies = [proxy.strip() for proxy in response.text.split() if proxy.strip()]
        print(f"Succesvol {len(proxies)} proxies opgehaald.")
        return proxies
    except requests.RequestException as e:
        print(f"Fout bij het ophalen van de proxy lijst: {e}")
        return []

def test_directe_verbinding():
    """Test directe verbinding met de target URL zonder proxy"""
    print("Testen van directe verbinding zonder proxy...")
    start_time = time.time()
    try:
        # Eerste request om de cookie te verkrijgen
        response = requests.get(
            url, 
            headers=headers, 
            timeout=30, 
            verify=False
        )
        
        # Controleer of we de beveiligingspagina hebben gekregen
        if 'JavaScript must be enabled' in response.text:
            print("Beveiligingspagina gedetecteerd, cookie extraheren...")
            
            # Extraheer de cookie uit de response
            import re
            cookie_match = re.search(r'document\.cookie="([^"]+)"', response.text)
            
            if cookie_match:
                cookie_str = cookie_match.group(1)
                cookie_name = cookie_str.split('=')[0]
                cookie_value = cookie_str.split('=')[1].split(';')[0]
                
                print(f"Cookie gevonden: {cookie_name}={cookie_value}")
                
                # Haal de redirect URL
                url_match = re.search(r'location\.href="([^"]+)"', response.text)
                if url_match:
                    redirect_url = url_match.group(1)
                    print(f"Redirect URL: {redirect_url}")
                    
                    # Maak nieuwe headers met de cookie
                    new_headers = headers.copy()
                    new_headers['Cookie'] = f"{cookie_name}={cookie_value}"
                    
                    # Doe een nieuwe request met de cookie
                    response = requests.get(
                        redirect_url,
                        headers=new_headers,
                        timeout=30,
                        verify=False
                    )
                    
                    response_time = time.time() - start_time
                    
                    if response.status_code == 200 and 'parkeervergunning' in response.text.lower():
                        print(f"✅ Directe verbinding met cookie werkt! Responstijd: {response_time:.2f}s")
                        return {
                            'methode': 'direct',
                            'status_code': response.status_code,
                            'response_time': response_time,
                            'werkt': True,
                            'html': response.text
                        }
        
        # Originele check als we geen beveiligingspagina kregen
        response_time = time.time() - start_time
        if response.status_code == 200 and 'parkeervergunning' in response.text.lower():
            print(f"✅ Directe verbinding werkt! Responstijd: {response_time:.2f}s")
            return {
                'methode': 'direct',
                'status_code': response.status_code,
                'response_time': response_time,
                'werkt': True,
                'html': response.text
            }
        
        print(f"❌ Directe verbinding kreeg een response, maar de inhoud was niet correct.")
        return {
            'methode': 'direct',
            'status_code': response.status_code,
            'response_time': response_time,
            'werkt': False
        }
    except Exception as e:
        print(f"❌ Directe verbinding werkt niet: {str(e)}")
        return {
            'methode': 'direct',
            'status_code': None,
            'response_time': time.time() - start_time,
            'werkt': False,
            'error': str(e)
        }

def test_proxy(proxy, timeout=10):
    """Test of een proxy werkt met de doel-URL"""
    proxies = {
        'http': proxy,
    }
    start_time = time.time()
    try:
        # Eerste request om de cookie te verkrijgen
        response = requests.get(
            url, 
            headers=headers, 
            proxies=proxies,
            timeout=timeout, 
            verify=False
        )
        
        # Controleer of we de beveiligingspagina hebben gekregen
        if 'JavaScript must be enabled' in response.text:
            print(f"Beveiligingspagina gedetecteerd via proxy {proxy}, cookie extraheren...")
            
            # Extraheer de cookie uit de response
            import re
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
                    response = requests.get(
                        redirect_url,
                        headers=new_headers,
                        proxies=proxies,
                        timeout=timeout,
                        verify=False
                    )
                    
                    response_time = time.time() - start_time
                    
                    if response.status_code == 200 and 'parkeervergunning' in response.text.lower():
                        print(f"✅ Proxy {proxy} met cookie werkt! Responstijd: {response_time:.2f}s")
                        return {
                            'proxy': proxy,
                            'status_code': response.status_code,
                            'response_time': response_time,
                            'werkt': True,
                            'html': response.text
                        }
        
        # Originele check als we geen beveiligingspagina kregen
        response_time = time.time() - start_time
        if response.status_code == 200 and 'parkeervergunning' in response.text.lower():
            print(f"✅ Proxy {proxy} werkt! Responstijd: {response_time:.2f}s")
            return {
                'proxy': proxy,
                'status_code': response.status_code,
                'response_time': response_time,
                'werkt': True,
                'html': response.text
            }
        
        print(f"❌ Proxy {proxy} kreeg een response, maar de inhoud was niet correct.")
        return {
            'proxy': proxy,
            'status_code': response.status_code,
            'response_time': response_time,
            'werkt': False
        }
    except Exception as e:
        print(f"❌ Proxy {proxy} werkt niet: {str(e)}")
        return {
            'proxy': proxy,
            'status_code': None,
            'response_time': time.time() - start_time,
            'werkt': False,
            'error': str(e)
        }

def vind_beste_verbinding():
    """Zoekt de beste verbindingsmethode (direct of via proxy)"""
    
    # Test eerst de directe verbinding
    directe_resultaat = test_directe_verbinding()
    
    # Als directe verbinding werkt, gebruiken we deze
    if directe_resultaat.get('werkt', False):
        print("\nDirecte verbinding werkt goed. We gebruiken deze.")
        return directe_resultaat
    
    # Haal de lijst met proxies op als directe verbinding niet werkt
    print("\nDirecte verbinding werkt niet goed. Testen van proxies...")
    proxies = haal_proxy_lijst_op()
    
    if not proxies:
        print("Geen proxies gevonden om te testen.")
        return None
    
    # Neem maximaal de eerste 5 proxies voor een snelle test
    proxies_to_test = proxies[:100]
    print(f"Testen van de eerste {len(proxies_to_test)} proxies...")
    
    # Test de proxies
    resultaten = []
    
    # Gebruik ThreadPoolExecutor om de tests parallel uit te voeren
    with ThreadPoolExecutor(max_workers=5) as executor:
        proxy_resultaten = list(executor.map(test_proxy, proxies_to_test))
        resultaten = proxy_resultaten
    
    # Toon werkende methoden
    werkende_methoden = [r for r in resultaten if r.get('werkt', False)]
    if werkende_methoden:
        # Sorteer op responstijd
        werkende_methoden.sort(key=lambda x: x.get('response_time', float('inf')))
        beste_methode = werkende_methoden[0]
        print(f"\nDe beste proxy is: {beste_methode['proxy']} met responstijd: {beste_methode['response_time']:.2f}s")
        return beste_methode
    
    print("\nGeen werkende verbindingsmethoden gevonden.")
    return None

# Vind de beste verbindingsmethode
beste_verbinding = vind_beste_verbinding()

# Als geen werkende verbinding is gevonden, stoppen we
if not beste_verbinding:
    print("Geen werkende verbinding gevonden. Het script wordt gestopt.")
    exit(1)

# Gebruik de HTML van de beste verbinding
html = beste_verbinding.get('html')

soup = BeautifulSoup(html, 'html.parser')

# Find the correct information in the HTML
# Date is behind the string "De wachtlijst is bijgewerkt op"
bijgewerkt = None
raw_divs = soup.find_all('div', class_='frame frame-default frame-type-text frame-layout-0 clearfix', id='c453053')
for div in raw_divs:
    if 'bijgewerkt op' in div.text:
        bijgewerkt = div.text.split('bijgewerkt op')[1].split('.')[0].strip()
        break

# Find the correct information in the HTML
# Number of people is behind the string "Wittevrouwen" and date of first applicant
aanmelddatum_eerstvolgende = None
aantal_aanmeldingen = None
raw_tds = soup.find_all('td')
for td in raw_tds:
    if 'Wittevrouwen' in td.text:
        aanmelddatum_eerstvolgende = td.find_next('td').find_next('td').text
        aantal_aanmeldingen = td.find_next('td').find_next('td').find_next('td').text
        break

# Print the found information in one sentence
print(f'De wachtlijst is voor het laatst bijgewerkt op {bijgewerkt}. Er staan {aantal_aanmeldingen} mensen op de wachtlijst voor de wijk Wittevrouwen. De eerste persoon op de wachtlijst heeft zich aangemeld op {aanmelddatum_eerstvolgende}.')

# Check if file exists
file_path = 'data/history.csv'
if os.path.exists(file_path):
    data = pd.read_csv(file_path)
    # Check if the information from the last row matches the new information
    last_row = data.iloc[-1]
    if last_row['bijgewerkt'] != bijgewerkt or last_row['aantal_aanmeldingen'] != int(aantal_aanmeldingen) or last_row['aanmelddatum_eerstvolgende'] != aanmelddatum_eerstvolgende:
        new_data = {'bijgewerkt': bijgewerkt, 'aantal_aanmeldingen': int(aantal_aanmeldingen), 'aanmelddatum_eerstvolgende': aanmelddatum_eerstvolgende}
        data = pd.concat([data, pd.DataFrame([new_data], columns=data.columns)], ignore_index=True)
        data['record'] = range(1, len(data) + 1)  # Add record numbers starting from 1
        data = data[['record', 'bijgewerkt', 'aantal_aanmeldingen', 'aanmelddatum_eerstvolgende']]  # Reorder columns
        data.to_csv(file_path, index=False)
else:
    # Write the information to the file
    new_data = {'record': [1], 'bijgewerkt': [bijgewerkt], 'aantal_aanmeldingen': [aantal_aanmeldingen], 'aanmelddatum_eerstvolgende': [aanmelddatum_eerstvolgende]}
    df = pd.DataFrame(new_data)
    df.to_csv(file_path, index=False)
#%%