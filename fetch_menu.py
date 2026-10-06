import json
import re
import time
from playwright.sync_api import sync_playwright

JIDELNA_ID = "6724"
URL = f"https://app.strava.cz/jidelnicky?jidelna={JIDELNA_ID}"

def extract_meal(text, meal_type):
    pattern = re.compile(re.escape(meal_type) + r'\s*(?:-\s*)?([^\n\r]+)', re.IGNORECASE)
    match = pattern.search(text)
    if not match:
        return "Není uvedeno"
    
    res = match.group(1).strip()
    res = re.sub(r'\(Alergeny:.*?\)', '', res, flags=re.IGNORECASE).strip()
    return res if res else "Není uvedeno"

def main():
    print(f"Otevírám prohlížeč pro jídelnu {JIDELNA_ID}...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        page.goto(URL, wait_until="networkidle")
        
        # Počkáme 3 sekundy na plné vykreslení dat
        time.sleep(3)
        
        # Získáme kompletní vygenerovaný text ze stránky
        text_content = page.evaluate("() => document.body.innerText")
        browser.close()

    # Vyhledáme dny v textu
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
            obed = extract_meal(content, 'Oběd 1')

        svacina = extract_meal(content, 'Svačina')

        if any(m != "Není uvedeno" for m in [presnidavka, polevka, obed, svacina]):
            all_days.append({
                "title": f"{day_name} {day_date}",
                "dateStr": day_date,
                "presnidavka": presnidavka,
                "polevka": polevka,
                "obed": obed,
                "svacina": svacina
            })

    print(f"Nalezeno platných dnů: {len(all_days)}")

    result = {
        "this": all_days[:5],
        "next": all_days[5:10]
    }

    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print("Zápis do data.json úspěšně dokončen.")

if __name__ == "__main__":
    main()
