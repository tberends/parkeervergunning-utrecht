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

# Define the URL
url = 'https://www.utrecht.nl/wonen-en-leven/parkeren/parkeren-bewoner/wachtlijst-parkeervergunning'

# Define the headers
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# Retrieve the HTML from the website
try:
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    html = response.text
except requests.RequestException as e:
    print(f"Error retrieving the webpage: {e}")
    exit(1)

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
print(f'The waiting list was last updated on {bijgewerkt}. There are {aantal_aanmeldingen} people on the waiting list for the Wittevrouwen district. The first person on the waiting list registered on {aanmelddatum_eerstvolgende}.')

# Check if file exists
file_path = 'data/history.csv'
if os.path.exists(file_path):
    data = pd.read_csv(file_path)
    # Check if the information from the last row matches the new information
    last_row = data.iloc[-1]
    if last_row['bijgewerkt'] != bijgewerkt or last_row['aantal_aanmeldingen'] != int(aantal_aanmeldingen) or last_row['aanmelddatum_eerstvolgende'] != aanmelddatum_eerstvolgende:
        new_data = {'bijgewerkt': bijgewerkt, 'aantal_aanmeldingen': aantal_aanmeldingen, 'aanmelddatum_eerstvolgende': aanmelddatum_eerstvolgende}
        data = pd.concat([data, pd.DataFrame([new_data])], ignore_index=True)
        data['record'] = range(1, len(data) + 1)  # Add record numbers starting from 1
        data = data[['record', 'bijgewerkt', 'aantal_aanmeldingen', 'aanmelddatum_eerstvolgende']]  # Reorder columns
        data.to_csv(file_path, index=False)
else:
    # Write the information to the file
    new_data = {'record': [1], 'bijgewerkt': [bijgewerkt], 'aantal_aanmeldingen': [aantal_aanmeldingen], 'aanmelddatum_eerstvolgende': [aanmelddatum_eerstvolgende]}
    df = pd.DataFrame(new_data)
    df.to_csv(file_path, index=False)
#%%