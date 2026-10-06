import json
import re
import time
from datetime import datetime, timedelta
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

def get_week_dates(now_dt):
    # Určí pondělí aktuálního týdne
    monday_this = now_dt - timedelta(days=now_dt.weekday())
    monday_next = monday_this + timedelta(days=7)
    
    this_week = [(monday_this + timedelta(days=i)).strftime("%d.%m.%Y") for i in range(5)]
    next_week = [(monday_next + timedelta(days=i)).strftime("%d.%m.%Y") for i in range(5)]
    
    return this_week, next_week

def main():
    print(f"Otevírám prohlížeč pro jídelnu {JIDELNA_ID}...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        page.goto(URL, wait_until="networkidle")
        time.sleep(3)
        text_content = page.evaluate("() => document.body.innerText")
        browser.close()

    day_pattern = re.compile(
        r'(Pondělí|Úterý|Středa|Čtvrtek|Pátek)\s+(\d{1,2}\.\s*\d{1,2}\.\s*\d{4})([\s\S]*?)(?=(Pondělí|Úterý|Středa|Čtvrtek|Pátek|\bVIS Plzeň\b|$))',
        re.IGNORECASE
    )
    
    found_days = {}
    for match in day_pattern.finditer(text_content):
        day_name = match.group(1).capitalize()
        # Normalizace data na DD.MM.YYYY
        raw_date = match.group(2).replace(" ", "")
        parts = raw_date.split('.')
        if len(parts) >= 3:
            day_num = parts[0].zfill(2)
            month_num = parts[1].zfill(2)
            year_num = parts[2]
            formatted_date = f"{day_num}.{month_num}.{year_num}"
        else:
            formatted_date = raw_date

        content = match.group(3)

        presnidavka = extract_meal(content, 'Přesnídávka')
        polevka = extract_meal(content, 'Polévka')
        obed = extract_meal(content, 'Oběd MŠ')
        if obed == "Není uvedeno":
            obed = extract_meal(content, 'Oběd 1')
        svacina = extract_meal(content, 'Svačina')

        found_days[formatted_date] = {
            "title": f"{day_name} {raw_date}",
            "dateStr": formatted_date,
            "presnidavka": presnidavka,
            "polevka": polevka,
            "obed": obed,
            "svacina": svacina
        }

    now = datetime.now()
    this_week_dates, next_week_dates = get_week_dates(now)

    day_names = ["Pondělí", "Úterý", "Středa", "Čtvrtek", "Pátek"]

    def build_week_list(dates_list):
        result = []
        for idx, d_str in enumerate(dates_list):
            if d_str in found_days:
                result.append(found_days[d_str])
            else:
                # Pokud pro daný den jídelna ještě nezveřejnila jídelníček
                display_date = f"{int(d_str.split('.')[0])}. {int(d_str.split('.')[1])}. {d_str.split('.')[2]}"
                result.append({
                    "title": f"{day_names[idx]} {display_date}",
                    "dateStr": d_str,
                    "presnidavka": "Není zadané",
                    "polevka": "Není zadané",
                    "obed": "Není zadané",
                    "svacina": "Není zadané"
                })
        return result

    result = {
        "this": build_week_list(this_week_dates),
        "next": build_week_list(next_week_dates)
    }

    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print("Data úspěšně uspořádána (Po–Pá) a zapsána do data.json.")

if __name__ == "__main__":
    main()
