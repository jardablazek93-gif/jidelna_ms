import urllib.request
import re
import json

URL = "https://app.strava.cz/jidelnicky?jidelna=6724"

def fetch_html():
    req = urllib.request.Request(
        URL, 
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    )
    with urllib.request.urlopen(req) as response:
        return response.read().decode('utf-8')

def extract_meal(text, meal_name):
    pattern = re.compile(re.escape(meal_name) + r'\s*(?:-\s*)?([^\n\r]+)', re.IGNORECASE)
    match = pattern.search(text)
    if not match:
        return "Není uvedeno"
    
    res = match.group(1).strip()
    # Odstranění závorek s alergeny pro čistý vzhled
    res = re.sub(r'\(Alergeny:.*?\)', '', res, flags=re.IGNORECASE).strip()
    return res if res else "Není uvedeno"

def main():
    try:
        html = fetch_html()
        # Odstranění HTML značek pro snazší textovou analýzu
        text_content = re.sub(r'<[^>]+>', '\n', html)
        
        # Regex pro vyhledání dnů
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
            svacina = extract_meal(content, 'Svačina')

            # Přidáme pouze dny, kde je alespoň jedno jídlo vyplněné
            if any(m != "Není uvedeno" for m in [presnidavka, polevka, obed, svacina]):
                all_days.append({
                    "title": f"{day_name} {day_date}",
                    "dateStr": day_date,
                    "presnidavka": presnidavka,
                    "polevka": polevka,
                    "obed": obed,
                    "svacina": svacina
                })

        # Rozdělení na Tento týden a Příští týden (max 5 dnů na týden)
        result_data = {
            "this": all_days[:5],
            "next": all_days[5:10]
        }

        with open("data.json", "w", encoding="utf-8") as f:
            json.dump(result_data, f, ensure_ascii=False, indent=2)

        print("data.json bylo úspěšně aktualizováno.")

    except Exception as e:
        print(f"Chyba při zpracování: {e}")
        # V případě chyby vytvoříme prázdnou strukturu, aby web nespadl
        with open("data.json", "w", encoding="utf-8") as f:
            json.dump({"this": [], "next": []}, f)

if __name__ == "__main__":
    main()