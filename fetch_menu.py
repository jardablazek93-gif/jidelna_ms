import urllib.request
import json
import re
from datetime import datetime

JIDELNA_ID = "6724"

def fetch_menu_api():
    # Oficiální veřejný API endpoint Strava.cz pro jídelníčky
    url = f"https://app.strava.cz/api/jidelnicky?jidelna={JIDELNA_ID}"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Referer': f'https://app.strava.cz/jidelnicky?jidelna={JIDELNA_ID}'
    }
    
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req) as response:
            data = response.read().decode('utf-8')
            return json.loads(data)
    except Exception as e:
        print(f"API endpoint nezabral ({e}), zkouším záložní parsování webové stránky...")
        return None

def fetch_web_html():
    url = f"https://app.strava.cz/jidelnicky?jidelna={JIDELNA_ID}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
        'Accept-Language': 'cs-CZ,cs;q=0.9'
    }
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req) as response:
        return response.read().decode('utf-8')

def extract_meal_item(text, meal_type):
    pattern = re.compile(re.escape(meal_type) + r'\s*(?:-\s*)?([^\n\r]+)', re.IGNORECASE)
    match = pattern.search(text)
    if not match:
        return "Není uvedeno"
    
    res = match.group(1).strip()
    res = re.sub(r'\(Alergeny:.*?\)', '', res, flags=re.IGNORECASE).strip()
    return res if res else "Není uvedeno"

def parse_html_content(html):
    # Očistění HTML od značek
    clean_text = re.sub(r'<[^>]+>', '\n', html)
    
    day_pattern = re.compile(
        r'(Pondělí|Úterý|Středa|Čtvrtek|Pátek)\s+(\d{1,2}\.\s*\d{1,2}\.\s*\d{4})([\s\S]*?)(?=(Pondělí|Úterý|Středa|Čtvrtek|Pátek|\bVIS Plzeň\b|$))',
        re.IGNORECASE
    )
    
    parsed_days = []
    for match in day_pattern.finditer(clean_text):
        day_name = match.group(1).capitalize()
        day_date = match.group(2).replace(" ", "")
        content = match.group(3)

        presnidavka = extract_meal_item(content, 'Přesnídávka')
        polevka = extract_meal_item(content, 'Polévka')
        obed = extract_meal_item(content, 'Oběd MŠ')
        if obed == "Není uvedeno":
            obed = extract_meal_item(content, 'Oběd 1')

        svacina = extract_meal_item(content, 'Svačina')

        if any(m != "Není uvedeno" for m in [presnidavka, polevka, obed, svacina]):
            parsed_days.append({
                "title": f"{day_name} {day_date}",
                "dateStr": day_date,
                "presnidavka": presnidavka,
                "polevka": polevka,
                "obed": obed,
                "svacina": svacina
            })
    return parsed_days

def main():
    print(f"Stahuji jídelníček pro jídelnu {JIDELNA_ID}...")
    parsed_days = []
    
    # 1. Pokus přes API
    api_data = fetch_menu_api()
    if api_data and isinstance(api_data, list):
        for entry in api_data:
            # Zpracování dat z JSON API
            datum_str = entry.get('datum', '')
            parsed_days.append({
                "title": entry.get('den', '') + ' ' + datum_str,
                "dateStr": datum_str,
                "presnidavka": entry.get('presnidavka', 'Není uvedeno'),
                "polevka": entry.get('polevka', 'Není uvedeno'),
                "obed": entry.get('obed_ms', entry.get('obed1', 'Není uvedeno')),
                "svacina": entry.get('svacina', 'Není uvedeno')
            })

    # 2. Pokud API nevrátilo pole, stáhneme a opatrovně zpracujeme HTML s rozšiřujícími pravidly
    if not parsed_days:
        html = fetch_web_html()
        parsed_days = parse_html_content(html)

    print(f"Nalezeno platných dnů: {len(parsed_days)}")

    result = {
        "this": parsed_days[:5],
        "next": parsed_days[5:10]
    }

    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print("Zápis do data.json byl úspěšně dokončen.")

if __name__ == "__main__":
    main()
