import urllib.request
import urllib.parse
import json
import re

JIDELNA_ID = "6724"

def get_menu_from_api():
    # Oficiální webový/API endpoint Strava.cz
    url = f"https://app.strava.cz/jidelnicky?jidelna={JIDELNA_ID}"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept-Language': 'cs-CZ,cs;q=0.9',
        'Referer': 'https://app.strava.cz/'
    }
    
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req) as response:
        return response.read().decode('utf-8')

def extract_meal_item(text, meal_type):
    # Vyhledá text konkrétního jídla podle typu
    pattern = re.compile(re.escape(meal_type) + r'\s*(?:-\s*)?([^\n\r]+)', re.IGNORECASE)
    match = pattern.search(text)
    if not match:
        return "Není uvedeno"
    
    res = match.group(1).strip()
    # Odstranění záznamů o alergenech (např. Alergeny: 01, 07)
    res = re.sub(r'\(Alergeny:.*?\)', '', res, flags=re.IGNORECASE).strip()
    return res if res else "Není uvedeno"

def main():
    print(f"Stahuji jídelníček pro jídelnu {JIDELNA_ID}...")
    
    try:
        html = get_menu_from_api()
        
        # Očistíme HTML značky pro snazší textové zpracování
        clean_text = re.sub(r'<[^>]+>', '\n', html)
        
        # Hledání bloků dnů (Pondělí až Pátek)
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
            
            # Zjištění obědu MŠ
            obed = extract_meal_item(content, 'Oběd MŠ')
            if obed == "Není uvedeno":
                obed = extract_meal_item(content, 'Oběd 1')

            svacina = extract_meal_item(content, 'Svačina')

            # Přidáme pouze dny, kde existuje alespoň 1 jídlo
            if any(meal != "Není uvedeno" for meal in [presnidavka, polevka, obed, svacina]):
                parsed_days.append({
                    "title": f"{day_name} {day_date}",
                    "dateStr": day_date,
                    "presnidavka": presnidavka,
                    "polevka": polevka,
                    "obed": obed,
                    "svacina": svacina
                })

        print(f"Nalezeno platných dnů: {len(parsed_days)}")

        # Rozdělení na Tento týden a Příští týden
        result = {
            "this": parsed_days[:5],
            "next": parsed_days[5:10]
        }

        # Uložení do data.json
        with open("data.json", "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        print("Zápis do data.json byl úspěšně dokončen.")

    except Exception as e:
        print(f"Chyba při stahování: {e}")
        # Vytvoření souboru se strukturou pro případ výpadku
        with open("data.json", "w", encoding="utf-8") as f:
            json.dump({"this": [], "next": []}, f)

if __name__ == "__main__":
    main()
