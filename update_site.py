"""
Descarca toata arhiva de extrageri Loto 6/49 de pe ponturi.ro si
regenereaza index.html (site-ul) cu datele proaspete, gata de publicat.

Ruleaza local sau automat prin GitHub Actions (vezi .github/workflows/update.yml).

INSTALARE (o singura data):
    python -m pip install requests beautifulsoup4

RULARE:
    python update_site.py

Rezultatul: fisierul index.html din acelasi folder este suprascris cu
datele actualizate. Acesta e fisierul care trebuie publicat (Netlify /
GitHub Pages).
"""

import json
import time
import requests
from bs4 import BeautifulSoup

BASE_URL = "https://ponturi.ro/loto/loteria-romana/6-49/arhiva/"
AN_START = 1993
AN_FINAL = 2027  # se opreste cand arhiva nu mai are date pt anul curent+1

TEMPLATE_FILE = "template.html"
OUTPUT_FILE = "index.html"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
}


def extrage_extrageri_din_pagina(html):
    soup = BeautifulSoup(html, "html.parser")
    rezultate = []
    carduri = soup.find_all("div", class_="lr-card")
    for card in carduri:
        span_data = card.find("span", style=lambda s: s and "font-weight:600" in s)
        if not span_data:
            continue
        data_extragere = span_data.get_text(strip=True)
        bile = card.find_all("span", class_="lr-ball")
        numere = [int(b.get_text(strip=True)) for b in bile if b.get_text(strip=True).isdigit()]
        if data_extragere and len(numere) == 6:
            rezultate.append((data_extragere, numere))
    return rezultate


def descarca_toate_extragerile():
    toate = []
    an = AN_START
    ani_goi_consecutivi = 0

    while an <= AN_FINAL:
        url = f"{BASE_URL}?year={an}"
        print(f"Descarc: {url}")
        try:
            resp = requests.get(url, headers=HEADERS, timeout=20)
            resp.raise_for_status()
        except requests.RequestException as e:
            print(f"  Eroare pentru anul {an}: {e}")
            an += 1
            continue

        extrageri = extrage_extrageri_din_pagina(resp.text)
        print(f"  Gasite {len(extrageri)} extrageri pentru {an}")

        if len(extrageri) == 0:
            ani_goi_consecutivi += 1
        else:
            ani_goi_consecutivi = 0
            for data_extragere, numere in extrageri:
                toate.append((data_extragere, numere))

        # daca 2 ani la rand nu au date (ex: am depasit anul curent), ne oprim
        if ani_goi_consecutivi >= 2 and an > 2020:
            print("Doi ani consecutivi fara date, ma opresc.")
            break

        an += 1
        time.sleep(1)

    return toate


def sorteaza_cronologic(extrageri):
    def cheie(item):
        data_str = item[0]
        zi, luna, an = data_str.split(".")
        return (int(an), int(luna), int(zi))
    return sorted(extrageri, key=cheie)


def construieste_json(extrageri):
    randuri = [[data] + numere for data, numere in extrageri]
    return json.dumps(randuri, ensure_ascii=False)


def main():
    extrageri = descarca_toate_extragerile()
    if not extrageri:
        print("Nu am gasit nicio extragere. Nu ating fisierul index.html existent.")
        return

    extrageri = sorteaza_cronologic(extrageri)
    data_json = construieste_json(extrageri)

    with open(TEMPLATE_FILE, encoding="utf-8") as f:
        template = f.read()

    html_final = template.replace("__LOTO_DATA__", data_json)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(html_final)

    print(f"\nGata! {len(extrageri)} extrageri scrise in {OUTPUT_FILE}")
    print(f"Ultima extragere: {extrageri[-1]}")


if __name__ == "__main__":
    main()
