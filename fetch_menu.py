import urllib.request
import urllib.parse
import json
import re

JIDELNA_ID = "6724"
# Přímá adresa webu Strava.cz pro získání dat jídelny
URL = f"https://app.strava.cz/jidelnicky?jidelna={JIDELNA_ID}"

def fetch_data():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'cs-CZ,cs;q=0.9'
    }
    req = urllib.request.Request(URL, headers=headers)
    with urllib.request.urlopen(req) as response:
        return response.read().decode('utf-8')

def extract_meal(text, meal_name):
    # Vyhledá text konkrétního jídla podle názvu
    pattern = re.compile(re.escape(meal_name) + r'\s*(?:-\s*)?([^\n\r]+)', re.IGNORECASE)
    match = pattern.search(text)
    if not match:
        return "Není uvedeno"
    
    res = match.group(1).strip()
    # Odstranění zápisu alergenů např. (Alergeny: ----01, 07)
    res = re.sub(r'\(Alergeny:.*?\)', '', res, flags=re.IGNORECASE).strip()
    return res if res else "Není uvedeno"

def main():
    try:
        html = fetch_data()
        
        # Očistíme HTML značky pro snazší parsování
        text_content = re.sub(r'<[^>]+>', '\n', html)
        
        # Najdeme jednotlivé dny (např. Pondělí 5. 10. 2026)
        day_pattern = re.compile(
            r'(Pondělí|Úterý|Středa|Čtvrtek|Pátek)\s+(\d{1,2}\.\s*\d{1,2}\.\s*\d{4})([\s\S]*?)(?=(Pondělí|Úterý|Středa|Čtvrtek|Pátek|\bVIS Plzeň\b|$))',
            re.IGNORECASE
        )
        
        all_days = []
        for match in day_pattern.finditer(text_content):
            day_name = match.group(1).capitalize()
            day_date = match.group(2).replace(" ", "")
            content = match.group(3)

            presnidavka = extract_meal(content, 'Přesnídávka')
            polevka = extract_meal(content, 'Polévka')
            obed = extract_meal(content, 'Oběd MŠ')
            if obed == "Není uvedeno":
                # Záložní vyhledání obecného Obědu 1, pokud chybí specifické označení "Oběd MŠ"
                obed = extract_meal(content, 'Oběd 1')

            svacina = extract_meal(content, 'Svačina')

            # Přidáme pouze platné dny, kde je alespoň jedno jídlo vyplněné
            if any(m != "Není uvedeno" for m in [presnidavka, polevka, obed, svacina]):
                all_days.append({
                    "title": f"{day_name} {day_date}",
                    "dateStr": day_date,
                    "presnidavka": presnidavka,
                    "polevka": polevka,
                    "obed": obed,
                    "svacina": svacina
                })

        # Rozdělení dnů na Tento týden a Příští týden
        result_data = {
            "this": all_days[:5],
            "next": all_days[5:10]
        }

        with open("data.json", "w", encoding="utf-8") as f:
            json.dump(result_data, f, ensure_ascii=False, indent=2)

        print(f"Úspěšně zpracováno {len(all_days)} dnů a zapsáno do data.json.")

    except Exception as e:
        print(f"Chyba při stahování: {e}")
        # V případě výpadku zapíšeme prázdnou strukturu
        with open("data.json", "w", encoding="utf-8") as f:
            json.dump({"this": [], "next": []}, f)

if __name__ == "__main__":
    main()
