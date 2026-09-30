# Záhradka – návod

Kalendár úloh podľa toho, čo pestuješ, počasie, plán záhonov so striedaním plodín, denník, fotky a diagnostika.
Len Python 3 (žiadne ďalšie knižnice), dáta v SQLite (`data/zahradka.db`), beží na Windows aj Linuxe. Port **8768** (Výkaz 8765, Financie 8766, Nákupy 8767).

## 1. Spustenie a ikona na ploche

**Windows** (rovnaký env ako DB Viewer a Nákupy):
1. Rozbaľ do `C:\Users\eliasmichal\Dev\Projects\Personal\Zahradka\`.
2. V cmd/PowerShell raz:
   ```
   C:\Users\eliasmichal\Dev\Env\Personal\Scripts\python.exe C:\Users\eliasmichal\Dev\Projects\Personal\Zahradka\vytvor_odkaz.py
   ```
3. Na ploche je ikona **Záhradka**. Dvojklik = spustí server na pozadí (bez terminálu) a otvorí prehliadač. Ak už beží, len otvorí prehliadač.

Ručne (ak skript zlyhá): pravý klik na plochu → Nový → Odkaz →
`"C:\Users\eliasmichal\Dev\Env\Personal\Scripts\pythonw.exe" "C:\Users\eliasmichal\Dev\Projects\Personal\Zahradka\zahradka.pyw"`, ikona `zahradka.ico`.

**Linux:** `python3 vytvor_odkaz.py` (spúšťač v menu aj na ploche; GNOME: pravý klik → Povoliť spúšťanie).

**Bez ikony:** `zahradka.bat` / `./zahradka.sh`, adresa `http://127.0.0.1:8768/`.
**Vypnutie:** Nastavenia → Vypnúť Záhradku. **Chyby pri štarte:** `data/server.log`.

## 2. Prvé nastavenie (raz, ~15 minút)

| Kde | Čo |
|---|---|
| Nastavenia → Záhrada | miesto (tlačidlo Hľadať → vyber obec, kvôli počasiu), pôda (piesočnatá), rozmery parcely v m, kde je juh |
| Plán | **+ Nakresliť** → typ (záhon, ker, chodník, kompost, chatka…) → ťahaj obdĺžnik myšou. Klik = detail, ťahaním presunieš, presné rozmery v detaile |
| Čo pestujem | **+ Pridať plodinu**: plodina, záhon, spôsob (priama sejba / vlastné predpestovanie / kúpené sadenice / sadba), stav |

Pridaj aj to, čo len **plánuješ** (stav „plánujem“). Nástenka ti potom včas pripomenie predpestovanie, nákup, sejbu aj výsadbu.
Pri pridaní do záhona apka skontroluje **striedanie plodín** (rovnaká čeľaď v posledných 3 rokoch, kapustovité 4 roky).

## 3. Bežné používanie (napr. cez víkend, 5 minút)

1. **Nástenka** – počasie na 7 dní + upozornenia, úlohy na tento týždeň, tento mesiac, čo príde a čo kúpiť.
2. Hotovú úlohu **odškrtni** → zapíše sa do denníka. Pri sejbe/výsadbe sa výsadba sama prepne na „zasiate“ / „rastie vonku“ s dnešným dátumom.
3. Iné práce, pozorovania a **zber (kg / ks)** → Denník → + Zápis.
4. Fotky → nahraj, priraď k záhonu a plodine.
5. Šípky ◀ ▶ na nástenke = pozrieť si iný týždeň (plánovanie dopredu).

### Ako sa vyberajú úlohy
| Zdroj | Príklad |
|---|---|
| kalendár plodiny, filtrovaný podľa spôsobu a stavu | paradajky z vlastných semien → sejba v marci; kúpené sadenice → „kúp sadenice“ v máji |
| dni od sejby / výsadby | jahody: 3 týždne polievať pri suchu; mrkva: jednotiť po 3–6 týždňoch |
| všeobecné úlohy podľa pôdy | piesočnatá: kyprenie na jar, na jeseň neryľovať, mulčovať |
| počasie (Open-Meteo, bez registrácie) | mrazík → zakryť; 3+ dni sucho → polievať; dážď → nestriekať; horúčava; vietor |

„Zmeškané?“ = jednorazová úloha skončila v posledných 2 týždňoch a nie je odškrtnutá.
Trvalky (jahody, ríbezle, maliny, egreše, pažítka) a cesnak / raž (sadia sa na jeseň) platia aj v ďalších rokoch, kým ich neukončíš (stav „ukončené“).

## 4. Plán a striedanie

- V záhone sa zobrazujú plodiny zvoleného roka.
- Detail záhona: čo tam rástlo po rokoch, **návrh na budúci rok** (silne → stredne → slabo náročné, ktorým čeľadiam sa vyhnúť), fotky a denník záhona.
- Zmazaný záhon zmizne z plánu, história ostane.

**Plán na ďalší rok (napr. od októbra):** v Pláne prepni **Rok** na 2027.
- Čo nakreslíš, platí **od 2027** – v pláne 2026 to nie je.
- **Odstrániť** v roku 2027 = objekt zmizne od 2027, v pláne 2026 ostane (napr. starý kompost).
- Plodiny na 2027 pridáš cez klik na záhon → **+ Plodina sem** (stav „plánujem“).
- Posun a rozmery platia vo všetkých rokoch, kde objekt existuje. Ak sa objekt mení (presun kompostu), odstráň ho v novom roku a nakresli nový.
- Roky platnosti sa dajú upraviť aj ručne v detaile objektu (od roku / do roku).

**Uzamknutie roka** (Plán → 🔒 Uzamknúť 2026): uloží sa snímka plánu (poloha a rozmery objektov). Neskoršie presuny sa roka 2026 už nedotknú.
Výsadby uzamknutého roka sa nedajú pridať, zmazať ani presunúť; stav (napr. „ukončené“), množstvo a poznámka sa meniť dajú. 🔓 Odomknúť vráti všetko späť.
**Porovnanie:** Plán → „porovnať s“ → vedľa seba dva roky.

## 4a. Striedanie (4 skupiny)

| Skupina | Plodiny | Príprava |
|---|---|---|
| 1. Plodová | paradajky, papriky, baklažán, zemiaky, uhorky, cukety, tekvica, melón, kukurica | veľa kompostu / granulovaného hnoja, čierna textília |
| 2. Strukoviny a listová | fazuľa, hrach, šalát, kôpor, bazalka | nehnojiť |
| 3. Kapustovité | kapusta, brokolica, kaleráb, reďkovka | kompost |
| 4. Koreňová a cibuľová | mrkva, petržlen, cvikla, mangold, špenát, cibuľa, cesnak, pór | bez čerstvého hnoja |

Každý rok sa záhon posunie o skupinu (1 → 2 → 3 → 4 → 1), rovnaká čeľaď sa vráti po 4 rokoch.
1. Striedanie → zaškrtni záhony, **Navrhnúť podľa roka 2026** (alebo vyber ručne, každému záhonu inú skupinu) → Uložiť.
2. Tabuľka ukáže roky dopredu: farba = skupina, sivý text = návrh, **+ plodina** = pridá plánovanú výsadbu. ⚠ = plodina nepatrí do skupiny alebo porušuje striedanie.
3. Nástenka pridá úlohy: na jeseň „po zbere … budúci rok tu bude …“, na jar prípravu podľa skupiny.
Trvalky (jahody, kríky) a záhony mimo striedania sa ďalej kontrolujú len podľa čeľadí.

## 5. Fotky a diagnostika

Fotky sa pri nahratí zmenšia na max. 1600 px a uložia do `data/fotky/RRRR/`. Pri fotke:

| Tlačidlo | Čo robí | Cena |
|---|---|---|
| 💬 Otázka pre chat | pripraví text (plodina, pôda, dátum, počasie 7 dní, tvoj popis). Fotku stiahneš, v chate s Claude vložíš fotku + text | v rámci predplatného |
| ✍️ Vložiť odpoveď ručne | odpoveď z chatu uložíš k fotke | – |
| 🤖 Diagnostikovať cez API | apka pošle fotku na api.anthropic.com a odpoveď uloží | platí sa zvlášť podľa tokenov; apka ukladá počet tokenov |

API kľúč: Nastavenia → Fotodiagnostika. Aktuálne ceny sú na stránke cien Claude API. Kľúč je len v lokálnej databáze.
Žiadny Claude klient na PC netreba – je to obyčajná HTTPS požiadavka z Pythonu.

## 6. Záložky

| Záložka | Obsah |
|---|---|
| Nástenka | počasie, upozornenia, úlohy týždňa a mesiaca, čo príde, nákupný zoznam, posledné zápisy |
| Plán | nákres parcely po rokoch, uzamknutie roka, porovnanie dvoch rokov vedľa seba |
| Striedanie | 4 skupiny plodín, ktoré sa každý rok posunú o záhon ďalej; plán na roky dopredu |
| Čo pestujem | výsadby po rokoch, stav sa mení priamo v tabuľke |
| Denník | všetky zápisy, filter rok / záhon / plodina, úroda spolu, export CSV |
| Fotky | nahratie, galéria, diagnostika |
| Plodiny | 36 plodín: kalendár, spon, hĺbka, tipy, problémy, susedia, úlohy |
| Návody | piesočnatá pôda, rýľovanie, zelené hnojenie, hnojenie, biela a čierna textília, polievanie, striedanie, kompost, jahody, zima, predpestovanie |
| Nastavenia | miesto, pôda, parcela, API kľúč, export, vypnutie |

## 7. Súbory

| Čo | Kde |
|---|---|
| Databáza | `data/zahradka.db` |
| Fotky | `data/fotky/RRRR/` |
| Denná záloha (30 dní) | `data/backups/zahradka-RRRR-MM-DD.db` (fotky sa nezálohujú, kopíruj `data/fotky/`) |
| Export denníka | Denník → Export CSV (uloží sa aj do `data/export/`) |
| Log servera | `data/server.log` |

## 8. Server (neskôr)

```
./make_cert.sh                                   # HTTPS certifikát na IP servera
sudo cp zahradka.service /etc/systemd/system/    # uprav User a WorkingDirectory
sudo systemctl daemon-reload && sudo systemctl enable --now zahradka
sudo journalctl -u zahradka -n 20                # tu je token
```
Z mobilu / iného PC: `https://<IP>:8768/?token=<token>` (uloží sa do cookie na rok). Potom sa dajú fotky nahrávať priamo z mobilu.
Zvonku len cez VPN (Tailscale), port na routeri neotváraj.
