# Záhradka – riešenie problémov a tipy

## Kde čo je

| Čo | Windows | Linux |
|---|---|---|
| Aplikácia | `C:\Users\eliasmichal\Dev\Projects\Personal\Zahradka\` | priečinok, kam si ju rozbalil |
| Python (env) | `C:\Users\eliasmichal\Dev\Env\Personal\Scripts\pythonw.exe` | `python3` zo systému |
| Ikona | **Záhradka** na ploche (vytvorí `vytvor_odkaz.py`) | `~/.local/share/applications/zahradka.desktop` + plocha |
| Databáza | `data\zahradka.db` | `data/zahradka.db` |
| Fotky | `data\fotky\RRRR\` | `data/fotky/` |
| Denné zálohy (30 dní) | `data\backups\` | `data/backups/` |
| Log servera | `data\server.log` | `data/server.log` |
| Adresa | `http://127.0.0.1:8768/` | `http://127.0.0.1:8768/` |

Potrebné: Python 3.9+. Žiadne ďalšie balíky.

---

## 1. Riešenie problémov

### Po kliknutí na ikonu sa nič nestane / „Server sa nespustil“
Spúšťač ukáže koniec `data\server.log`.

| Chyba v logu | Príčina | Riešenie |
|---|---|---|
| `Address already in use` / `[WinError 10048]` | na porte 8768 beží iný program | Správca úloh → ukonči `pythonw.exe`, alebo iný port (nižšie) |
| `SyntaxError` + riadok | chyba po ručnej úprave kódu | oprav riadok alebo vráť pôvodný súbor zo zipu |
| `database is locked` | DB má otvorenú iný program na zápis | zavri ho (DB Viewer len číta, nevadí) |

Spustenie s viditeľnými chybami:
```
cd C:\Users\eliasmichal\Dev\Projects\Personal\Zahradka
C:\Users\eliasmichal\Dev\Env\Personal\Scripts\python.exe server.py
```
Iný port: `python.exe server.py --port 8770`; v ikone do Cieľa za `zahradka.pyw"` doplň ` 8770`.

### Červený pruh „Beží iná verzia servera“
Po aktualizácii ostal bežať starý server. Klikni znova na ikonu (vypne starý, spustí nový), potom Ctrl+F5.

### Počasie
| Príznak | Riešenie |
|---|---|
| „Počasie nedostupné“ | PC nemá internet alebo firma blokuje `api.open-meteo.com`. Úlohy fungujú aj bez počasia |
| „Predpoveď sa nepodarilo obnoviť… zobrazujem uloženú“ | ukazuje poslednú stiahnutú predpoveď; skús ↻ obnoviť neskôr |
| počasie z iného miesta | Nastavenia → Miesto → Hľadať → vyber obec → Uložiť |

Predpoveď sa sťahuje najviac raz za hodinu (↻ obnoviť = hneď).

### Úlohy
| Príznak | Príčina / riešenie |
|---|---|
| na nástenke len všeobecné úlohy | nemáš pridané plodiny → Čo pestujem |
| chýba sejba / výsadba | výsadba už nie je v stave „plánujem“, alebo spôsob nesedí (kúpené sadenice nemajú úlohu predpestovania) |
| plodina z minulého roka stále straší | trvalky a cesnak platia, kým ich nedáš do stavu „ukončené“ |
| odškrtol som omylom | odškrtni znova – zmaže sa aj zápis v denníku (stav výsadby ostane, oprav ho v Čo pestujem) |
| úlohy „každý týždeň“ | odškrtnutie platí pre aktuálny týždeň, budúci týždeň sa ukážu znova |

### Diagnostika cez API
| Chyba | Riešenie |
|---|---|
| `API vrátilo chybu 401` | zlý alebo zrušený kľúč → Nastavenia → nový kľúč |
| `API vrátilo chybu 400` + text o kredite | na API účte nie je kredit |
| `API vrátilo chybu 404` + model | model v Nastaveniach neexistuje → oprav názov modelu |
| `Nedá sa pripojiť na api.anthropic.com` | internet / firemný proxy. Použi „Otázka pre chat“ |

### Plán
| Príznak | Riešenie |
|---|---|
| záhon mimo parcely / zlá veľkosť | klik na záhon → prepíš X, Y, šírku, dĺžku v metroch → Uložiť |
| parcela má zlý rozmer | Nastavenia → Šírka / Dĺžka parcely |
| záhon sa neposúva | najprv vypni režim kreslenia (tlačidlo „Ťahaj myšou…“ klikni znova) |

---

## 2. Tipy

- **Plánovanie sezóny (január):** Čo pestujem → prepni rok na nový → pridaj všetko so stavom „plánujem“. Nástenka potom sama povie, kedy siať a čo kúpiť.
- **Striedanie:** pred pridaním plodiny pozri v Pláne detail záhona → „Na rok …“.
- **Úroda:** zber zapisuj do denníka s kg – na konci roka máš súčet po plodinách.
- **Fotky v čase:** fotografuj ten istý záhon z rovnakého miesta, v detaile záhona uvidíš vývoj.
- **Otázka pre chat:** text obsahuje plodinu, pôdu, dátum výsadby a počasie 7 dní pred fotkou – odpoveď je presnejšia ako pri samotnej fotke.
- DB Viewer vie otvoriť `data\zahradka.db` len na čítanie, napr.:
  ```
  SELECT substr(datum,1,4) rok, plodina, SUM(mnozstvo) kg FROM dennik WHERE typ='zber' GROUP BY 1,2;
  ```

---

## 3. Záloha a obnova

- **Automaticky:** pri štarte a potom raz denne vznikne `data\backups\zahradka-RRRR-MM-DD.db`, drží sa 30 dní. **Fotky nie** – `data\fotky\` občas skopíruj inam.
- **Obnova:**
  1. Nastavenia → Vypnúť Záhradku.
  2. `data\zahradka.db` premenuj na `zahradka.db.pokazena`.
  3. Skopíruj zálohu z `data\backups\` ako `data\zahradka.db`.
  4. Spusti ikonou.

---

## 4. Aktualizácia a úprava kódu

**Nová verzia (zip):** rozbaľ cez starý priečinok (`data\` v zipe nie je, neprepíše sa) → klikni na ikonu.
Vlastné úpravy v .py súboroch nová verzia prepíše – odlož si ich.

| Súbor | Po úprave |
|---|---|
| `static\app.js`, `app.css`, `index.html` | Ctrl+F5 v prehliadači |
| `*.py` | Nastavenia → Vypnúť Záhradku → ikona |

Kontrola syntaxe (nič nevypíše = OK): `...\Scripts\python.exe -m py_compile core.py`
Pri zmene .py zvýš `VERZIA` v `core.py` aj `APP_VERZIA` v `static\app.js` (rovnaká hodnota) – ikona potom sama reštartuje server.

| Chcem zmeniť | Kde |
|---|---|
| miesto, pôda, rozmery, API kľúč | Nastavenia (nie kód) |
| termíny a úlohy plodín, nová plodina | `plodiny.py` → `plodina(...)` |
| všeobecné úlohy (rýľovanie, mulč…) | `plodiny.py` → `VSEOBECNE` |
| upozornenia podľa počasia (prahy mrazu, sucha) | `core.py` → `upozornenia()` |
| pravidlá striedania | `core.py` → `kontrola_striedania()`, `navrh_striedania()` |
| text otázky pre diagnostiku | `core.py` → `prompt_diagnostiky()` |
| návody | `navody.py` |

---

## 5. Neskôr na serveri (Linux, ako Výkaz)

```
./make_cert.sh                                   # HTTPS certifikát na IP servera
sudo cp zahradka.service /etc/systemd/system/    # uprav User a WorkingDirectory
sudo systemctl daemon-reload && sudo systemctl enable --now zahradka
sudo journalctl -u zahradka -n 20                # token pre prístup z iného zariadenia
sudo ufw allow 8768/tcp
```
- Z mobilu: `https://<IP>:8768/?token=<token>` – fotky potom nahrávaš priamo z mobilu na záhrade.
- Na serveri sa ikona nepoužíva, server beží ako služba (`systemctl status zahradka`).
- Presun dát: skopíruj celý priečinok aj s `data\`.
