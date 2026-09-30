"""Záhradka – databáza plodín.

Každá plodina:
  nazov, rodina (pre striedanie), naroky (silne / stredne / slabo), typ
  trvalka  – rastie viac rokov (úlohy platia, kým ju neukončíš)
  prezimuje – sadí sa na jeseň, zberá sa budúci rok (cesnak, raž)
  kal      – kalendár pre graf: mesiace predpestovania, sejby/výsadby von, zberu
  ulohy    – úlohy v kalendári (od/do = 'MM-DD')
             sposob: pre ktoré spôsoby pestovania platí (None = všetky)
             stav:   pre ktoré stavy výsadby platí (None = všetky okrem ukončených)
             opak:   'raz' / 'tyzden' / '14dni'
             nastav: po odškrtnutí sa výsadba prepne do tohto stavu
  rel      – úlohy odvodené od dátumu sejby / výsadby (dni od, do)

Spôsoby: priama_sejba, predpestovanie (vlastné sadenice), sadenice (kúpené),
         sadba (cibuľky, strúčiky, hľuzy), ker (kríky, trvalky)
Stavy:   plan, zasiate, vysadene, ukoncene
"""

SEM = ["priama_sejba"]
PRED = ["predpestovanie"]
SAD = ["sadenice"]
SADBA = ["sadba"]
KER = ["ker", "sadenice"]
PLAN = ["plan"]
PLAN_Z = ["plan", "zasiate"]

SPOSOBY = {
    "priama_sejba": "priama sejba von",
    "predpestovanie": "vlastné predpestovanie",
    "sadenice": "kúpené sadenice",
    "sadba": "sadba (cibuľky, strúčiky, hľuzy)",
    "ker": "ker / trvalka",
}
STAVY = {
    "plan": "plánujem",
    "zasiate": "zasiate",
    "vysadene": "rastie vonku",
    "ukoncene": "ukončené",
}
NAROKY = {
    "silne": "silne náročné (veľa živín)",
    "stredne": "stredne náročné",
    "slabo": "slabo náročné",
}


def U(id, od, do, text, typ, opak="raz", sposob=None, stav=None, potrebujes=None, nastav=None):
    return dict(id=id, od=od, do=do, text=text, typ=typ, opak=opak, sposob=sposob,
                stav=stav, potrebujes=potrebujes or [], nastav=nastav)


def R(od, do, text, opak="raz", sposob=None):
    return dict(od=od, do=do, text=text, opak=opak, sposob=sposob)


PLODINY = {}


def plodina(id, **kw):
    kw.setdefault("trvalka", False)
    kw.setdefault("prezimuje", False)
    kw.setdefault("tipy", [])
    kw.setdefault("problemy", [])
    kw.setdefault("dobri", [])
    kw.setdefault("zli", [])
    kw.setdefault("rel", [])
    kw.setdefault("sposoby", ["priama_sejba"])
    kw["id"] = id
    PLODINY[id] = kw


# ---------------------------------------------------------------- ZELENINA
plodina("paradajky", nazov="Paradajky", rodina="Ľuľkovité", naroky="silne", typ="zelenina",
        sposoby=["predpestovanie", "sadenice"],
        kal=dict(pred=[3, 4], von=[5, 6], zber=[7, 8, 9, 10]),
        spon="kolíkové 50 × 70 cm, kríčkové 40 × 60 cm",
        hlbka="semeno 0,5–1 cm; sadenicu sadiť hlbšie, až po prvé pravé listy",
        tipy=["Sadenicu zasaď hlbšie (až po prvé pravé listy) – na stonke narastú ďalšie korene.",
              "Kolík daj do jamky hneď pri sadení, neskôr by si poškodil korene.",
              "Polievaj ku koreňom, nie na listy – mokré listy podporujú pleseň.",
              "Na piesku polievaj pravidelne a mulčuj – nepravidelná vlaha spôsobuje hnilobu spodku plodov.",
              "Najteplejšie a najslnečnejšie miesto na parcele."],
        problemy=[("Pleseň zemiaková (plesň rajčete)", "hnedé škvrny na listoch, stonkách aj plodoch, hlavne po daždivom počasí. Napadnuté listy hneď odstrániť, nepolievať na listy, spodné listy odstrániť."),
                  ("Suchá hniloba vrcholu plodu", "tmavá vpadnutá škvrna na spodku plodu. Príčina: nepravidelná zálievka, nedostatok vápnika. Pravidelne polievať, mulčovať.")],
        dobri=["bazalka", "mrkva", "petrzlen", "cibula"], zli=["zemiaky"],
        ulohy=[
            U("sejba", "03-10", "04-05", "Paradajky: zasej na predpestovanie – miska na južnom parapete, 20–25 °C, zeminu drž vlhkú", "sejba", sposob=PRED, stav=PLAN, potrebujes=["semená paradajok", "výsevný substrát", "misky / kvetináčiky"], nastav="zasiate"),
            U("pik", "03-25", "04-25", "Paradajky: pikíruj – pri 2 pravých listoch presaď každú do vlastného kvetináča (hlbšie, po klíčne listy)", "sejba", sposob=PRED, stav=PLAN_Z, potrebujes=["kvetináče 8–10 cm", "substrát"]),
            U("otuz", "05-01", "05-15", "Paradajky: otužuj sadenice – cez deň von (najprv do tieňa), na noc dnu", "priprava", sposob=PRED, stav=PLAN_Z),
            U("kup", "05-01", "05-20", "Paradajky: kúp sadenice – zavalité, tmavozelené, bez škvŕn", "nakup", sposob=SAD, stav=PLAN, potrebujes=["sadenice paradajok"]),
            U("vys", "05-15", "06-05", "Paradajky: vysaď von (po 15. 5.) – do jamky kompost, kolík hneď pri sadení, sadenicu hlbšie, zaliať", "vysadba", stav=PLAN_Z, potrebujes=["kolíky 150–180 cm", "viazací materiál", "kompost"], nastav="vysadene"),
            U("zalist", "06-01", "08-31", "Paradajky: vyštipuj zálistky (výhony v pazuchách listov) a priväzuj ku kolíku (kolíkové odrody)", "starostlivost", opak="tyzden"),
            U("hnoj", "06-15", "08-31", "Paradajky: prihnoj hnojivom na paradajky (s draslíkom) – od prvých plodov každé 2 týždne", "hnojenie", opak="14dni", potrebujes=["hnojivo na paradajky"]),
            U("list", "07-10", "08-31", "Paradajky: odstráň spodné listy pri zemi, kontroluj hnedé škvrny (pleseň) – napadnuté listy hneď preč", "ochrana", opak="tyzden"),
            U("vrch", "08-20", "09-05", "Paradajky: zaštipni vrcholy – nové kvety už nedozrejú, sila pôjde do plodov", "starostlivost"),
            U("zber", "07-15", "10-10", "Paradajky: zber zrelých plodov", "zber", opak="tyzden"),
            U("mraz", "09-25", "10-15", "Paradajky: pred prvým mrazom obrať všetky plody, zelené nechať dozrieť doma", "zber"),
            U("koniec", "10-01", "10-31", "Paradajky: vytrhať rastliny; s plesňou nedávať na kompost", "priprava"),
        ],
        rel=[R(0, 0, "Paradajky: po výsadbe dôkladne zaliať"),
             R(1, 14, "Paradajky: prvé 2 týždne polievať pri suchu každé 2–3 dni", "tyzden")])

plodina("papriky", nazov="Papriky", rodina="Ľuľkovité", naroky="silne", typ="zelenina",
        sposoby=["predpestovanie", "sadenice"],
        kal=dict(pred=[2, 3, 4], von=[5, 6], zber=[7, 8, 9, 10]),
        spon="40 × 50 cm", hlbka="semeno 0,5–1 cm; sadenicu v rovnakej hĺbke ako v kvetináči",
        tipy=["Paprika potrebuje najviac tepla zo všetkej bežnej zeleniny – najslnečnejšie a závetrné miesto.",
              "Klíči pomaly a len v teple (25 °C) – sej skôr ako paradajky.",
              "Na piesku pravidelne polievať a mulčovať."],
        problemy=[("Opadávanie kvetov", "príliš horúco alebo sucho, alebo chladné noci. Pravidelne polievať, mulčovať.")],
        dobri=["bazalka", "mrkva"], zli=[],
        ulohy=[
            U("sejba", "02-15", "03-15", "Papriky: zasej na predpestovanie (teplo 25 °C, svetlý parapet)", "sejba", sposob=PRED, stav=PLAN, potrebujes=["semená papriky", "výsevný substrát", "misky"], nastav="zasiate"),
            U("pik", "03-15", "04-15", "Papriky: pikíruj do samostatných kvetináčov", "sejba", sposob=PRED, stav=PLAN_Z, potrebujes=["kvetináče 8–10 cm"]),
            U("kup", "05-05", "05-25", "Papriky: kúp sadenice", "nakup", sposob=SAD, stav=PLAN, potrebujes=["sadenice papriky"]),
            U("vys", "05-20", "06-10", "Papriky: vysaď von na najteplejšie miesto (až keď sú noci teplé), zaliať", "vysadba", stav=PLAN_Z, potrebujes=["kompost", "malé kolíky"], nastav="vysadene"),
            U("hnoj", "06-15", "08-31", "Papriky: prihnoj (hnojivo na plodovú zeleninu) každé 2 týždne", "hnojenie", opak="14dni", potrebujes=["hnojivo na plodovú zeleninu"]),
            U("zber", "07-20", "10-10", "Papriky: zber plodov (aj zelené sú jedlé; oberanie podporí ďalšie)", "zber", opak="tyzden"),
            U("mraz", "09-25", "10-10", "Papriky: pred mrazom obrať všetko", "zber"),
        ],
        rel=[R(0, 0, "Papriky: po výsadbe dôkladne zaliať")])

plodina("uhorky", nazov="Uhorky nakladačky", rodina="Tekvicovité", naroky="silne", typ="zelenina",
        sposoby=["priama_sejba", "predpestovanie", "sadenice"],
        kal=dict(pred=[4, 5], von=[5, 6], zber=[7, 8, 9]),
        spon="v riadku 30–40 cm, riadky 100–120 cm; po sieti 30 cm", hlbka="2 cm",
        tipy=["Sej až do teplej pôdy (asi 15 °C) – v studenej zemi semená hnijú.",
              "Pri predpestovaní sej rovno do kvetináčov, uhorky zle znášajú pikírovanie.",
              "Potrebujú veľa vody – na piesku mulč alebo čierna textília.",
              "Oberať často (6–12 cm, každé 2 dni); prerastené uhorky zastavujú tvorbu nových."],
        problemy=[("Pernospora uhorková", "žlté hranaté škvrny na listoch, zospodu sivý povlak, hlavne v auguste. Polievať ráno ku koreňom, napadnuté listy odstrániť.")],
        dobri=["kopor", "fazula", "hrach"], zli=[],
        ulohy=[
            U("pred", "04-20", "05-10", "Uhorky: zasej po 2 semená do kvetináčov na predpestovanie (bez pikírovania)", "sejba", sposob=PRED, stav=PLAN, potrebujes=["semená uhoriek", "kvetináče 8–10 cm"], nastav="zasiate"),
            U("sejba", "05-15", "06-10", "Uhorky: zasej von do teplej pôdy, 2 cm hlboko", "sejba", sposob=SEM, stav=PLAN, potrebujes=["semená uhoriek"], nastav="zasiate"),
            U("vys", "05-20", "06-05", "Uhorky: vysaď sadenice von, zaliať", "vysadba", sposob=PRED + SAD, stav=PLAN_Z, nastav="vysadene"),
            U("opora", "06-01", "06-30", "Uhorky: šplhavým odrodám natiahni sieť alebo oporu", "starostlivost", potrebujes=["sieť na uhorky / opora"]),
            U("hnoj", "06-15", "08-15", "Uhorky: prihnoj (hnojivo na zeleninu) každé 2 týždne", "hnojenie", opak="14dni"),
            U("zber", "07-01", "09-15", "Uhorky nakladačky: zber každé 2 dni (6–12 cm)", "zber", opak="tyzden"),
            U("peron", "07-15", "08-31", "Uhorky: kontroluj žlté hranaté škvrny (pernospora), napadnuté listy odstráň", "ochrana", opak="tyzden"),
        ],
        rel=[R(0, 0, "Uhorky: po sejbe / výsadbe zaliať")])

plodina("cukety", nazov="Cukety", rodina="Tekvicovité", naroky="silne", typ="zelenina",
        sposoby=["priama_sejba", "predpestovanie", "sadenice"],
        kal=dict(pred=[4, 5], von=[5, 6], zber=[7, 8, 9]),
        spon="100 × 100 cm (jedna rastlina zaberie cca 1 m²)", hlbka="3 cm, 2–3 semená do jamky",
        tipy=["Čierna mulčovacia textília = teplo, vlaha, žiadna burina.",
              "Do jamky daj kompost – cukety potrebujú veľa živín.",
              "Oberaj pri dĺžke 15–20 cm, často – rastlina potom rodí ďalej.",
              "Stačia 1–2 rastliny na rodinu."],
        problemy=[("Múčnatka", "biely povlak na listoch, hlavne koncom leta. Ku koncu sezóny je bežná; najviac napadnuté listy odstráň, polievaj ku koreňom."),
                  ("Plody hnijú od konca", "neopelený kvet alebo mokro. Pri daždivom počasí sa to stáva, oberať a čakať.")],
        dobri=["fazula", "kukurica"], zli=[],
        ulohy=[
            U("pred", "04-20", "05-10", "Cukety: zasej po 1–2 semená do kvetináčov na predpestovanie", "sejba", sposob=PRED, stav=PLAN, potrebujes=["semená cukety", "kvetináče 10 cm"], nastav="zasiate"),
            U("sejba", "05-15", "06-05", "Cukety: zasej von, 2–3 semená do jamky s kompostom, 3 cm hlboko", "sejba", sposob=SEM, stav=PLAN, potrebujes=["semená cukety", "kompost"], nastav="zasiate"),
            U("vys", "05-20", "06-05", "Cukety: vysaď do jamky s kompostom (ideálne cez čiernu textíliu), zaliať", "vysadba", sposob=PRED + SAD, stav=PLAN_Z, potrebujes=["kompost"], nastav="vysadene"),
            U("hnoj", "06-15", "08-15", "Cukety: prihnoj (hnojivo na zeleninu) každé 2 týždne", "hnojenie", opak="14dni"),
            U("zber", "07-01", "09-30", "Cukety: oberaj plody 15–20 cm", "zber", opak="tyzden"),
            U("mucn", "08-01", "09-15", "Cukety: najviac napadnuté listy múčnatkou (biely povlak) odstráň", "ochrana", opak="14dni"),
        ],
        rel=[R(0, 0, "Cukety: po sejbe / výsadbe zaliať")])

plodina("tekvica", nazov="Tekvica (hokkaido, maslová…)", rodina="Tekvicovité", naroky="silne", typ="zelenina",
        sposoby=["priama_sejba", "predpestovanie", "sadenice"],
        kal=dict(pred=[4, 5], von=[5, 6], zber=[9, 10]),
        spon="150 × 150 cm (popínavé odrody ešte viac)", hlbka="3 cm",
        tipy=["Veľmi náročná na živiny a vodu – najlepšie na mieste, kde bol kompost.",
              "Čierna textília pod rastlinou = plody neležia v mokre.",
              "Zrelá tekvica: stopka je suchá a zdrevnatená, šupka sa nedá prepichnúť nechtom."],
        problemy=[("Múčnatka", "biely povlak na listoch koncom leta, plodom nevadí.")],
        dobri=["fazula", "kukurica"], zli=["zemiaky"],
        ulohy=[
            U("pred", "04-20", "05-10", "Tekvica: zasej po 1–2 semená do kvetináčov na predpestovanie", "sejba", sposob=PRED, stav=PLAN, potrebujes=["semená tekvice", "kvetináče 10 cm"], nastav="zasiate"),
            U("sejba", "05-15", "06-05", "Tekvica: zasej von do jamky s kompostom", "sejba", sposob=SEM, stav=PLAN, potrebujes=["semená tekvice", "kompost"], nastav="zasiate"),
            U("vys", "05-20", "06-05", "Tekvica: vysaď do jamky s kompostom, zaliať", "vysadba", sposob=PRED + SAD, stav=PLAN_Z, nastav="vysadene"),
            U("hnoj", "06-15", "08-15", "Tekvica: prihnoj každé 2 týždne", "hnojenie", opak="14dni"),
            U("zber", "09-10", "10-15", "Tekvica: zber zrelých plodov so stopkou, pred mrazom; dosušiť na teplom mieste", "zber"),
        ],
        rel=[R(0, 0, "Tekvica: po sejbe / výsadbe zaliať")])

plodina("melon", nazov="Melón vodný", rodina="Tekvicovité", naroky="silne", typ="zelenina",
        sposoby=["predpestovanie", "sadenice"],
        kal=dict(pred=[4, 5], von=[5, 6], zber=[8, 9]),
        spon="100 × 100 cm (1 rastlina na m²)", hlbka="semeno 2 cm; sadenicu v rovnakej hĺbke ako v kvetináči",
        tipy=["Potrebuje najviac tepla z tekvicovitých – najslnečnejšie miesto a čierna textília (zohreje pôdu).",
              "Pre naše podnebie vyber skoré odrody s menšími plodmi.",
              "Predpestuj rovno do kvetináčov, zle znáša presádzanie koreňov.",
              "Pod dozrievajúci plod daj dosku alebo kúsok textílie, aby neležal na mokrej zemi.",
              "Zrelý plod: úponka pri stopke zaschne, miesto, kde leží na zemi, je žlté, pri poklepaní znie duto."],
        problemy=[("Múčnatka", "biely povlak na listoch koncom leta. Polievať ku koreňom, najviac napadnuté listy odstrániť.")],
        dobri=[], zli=["zemiaky"],
        ulohy=[
            U("pred", "04-20", "05-10", "Melón: zasej 1–2 semená do kvetináča (teplo 25 °C, bez pikírovania)", "sejba", sposob=PRED, stav=PLAN, potrebujes=["semená melóna (skorá odroda)", "kvetináče 10 cm"], nastav="zasiate"),
            U("kup", "05-10", "05-31", "Melón: kúp sadenice", "nakup", sposob=SAD, stav=PLAN, potrebujes=["sadenice melóna"]),
            U("vys", "05-25", "06-10", "Melón: vysaď do jamky s kompostom cez čiernu textíliu, až keď sú noci teplé", "vysadba", stav=PLAN_Z, potrebujes=["čierna mulčovacia textília", "kompost"], nastav="vysadene"),
            U("hnoj", "06-15", "07-31", "Melón: prihnoj (hnojivo na plodovú zeleninu) každé 2 týždne", "hnojenie", opak="14dni"),
            U("plody", "07-15", "08-15", "Melón: nechaj 2–3 plody na rastlinu, ďalšie kvety a konce výhonov zaštipni", "starostlivost"),
            U("zber", "08-10", "09-20", "Melón: zber zrelých plodov (suchá úponka, žltá škvrna, dutý zvuk)", "zber", opak="tyzden"),
        ],
        rel=[R(0, 0, "Melón: po výsadbe zaliať"),
             R(1, 14, "Melón: prvé 2 týždne polievať pri suchu", "tyzden")])

plodina("uhorky_salat", nazov="Uhorky šalátové (dlhé)", rodina="Tekvicovité", naroky="silne", typ="zelenina",
        sposoby=["predpestovanie", "sadenice"],
        kal=dict(pred=[4, 5], von=[5, 6], zber=[7, 8, 9]),
        spon="po sieti 40–50 cm", hlbka="semeno 2 cm; sadenicu v rovnakej hĺbke ako v kvetináči",
        tipy=["Vonku pestuj len odrody označené na vrecku pre pole / voľnú pôdu. Skleníkové hadovky vonku trpia chladom a vetrom.",
              "Vždy na sieť alebo oporu – plody visia, sú rovné a čisté.",
              "Najteplejšie závetrné miesto, čierna textília, veľa vody (na piesku mulč).",
              "Vonku rodí menej a neskôr ako v skleníku – počítaj s tým."],
        problemy=[("Horké plody", "sucho a veľké výkyvy teplôt. Pravidelne polievať, mulčovať."),
                  ("Pernospora uhorková", "žlté hranaté škvrny na listoch v auguste. Polievať ráno ku koreňom, napadnuté listy odstrániť.")],
        dobri=["kopor", "fazula"], zli=["zemiaky"],
        ulohy=[
            U("pred", "04-20", "05-10", "Uhorky šalátové: zasej po 1–2 semená do kvetináčov (bez pikírovania)", "sejba", sposob=PRED, stav=PLAN, potrebujes=["semená šalátovej uhorky pre pole", "kvetináče 10 cm"], nastav="zasiate"),
            U("kup", "05-10", "05-31", "Uhorky šalátové: kúp sadenice (odroda do voľnej pôdy)", "nakup", sposob=SAD, stav=PLAN, potrebujes=["sadenice šalátovej uhorky"]),
            U("vys", "05-25", "06-10", "Uhorky šalátové: vysaď k sieti cez čiernu textíliu, zaliať", "vysadba", stav=PLAN_Z, potrebujes=["sieť na uhorky + kolíky", "čierna mulčovacia textília"], nastav="vysadene"),
            U("viaz", "06-10", "07-31", "Uhorky šalátové: priväzuj / navádzaj výhony na sieť", "starostlivost", opak="tyzden"),
            U("hnoj", "06-15", "08-15", "Uhorky šalátové: prihnoj každé 2 týždne", "hnojenie", opak="14dni"),
            U("zber", "07-10", "09-20", "Uhorky šalátové: zber (20–30 cm podľa odrody)", "zber", opak="tyzden"),
        ],
        rel=[R(0, 0, "Uhorky šalátové: po výsadbe zaliať")])

plodina("baklazan", nazov="Baklažán", rodina="Ľuľkovité", naroky="silne", typ="zelenina",
        sposoby=["predpestovanie", "sadenice"],
        kal=dict(pred=[2, 3, 4], von=[5, 6], zber=[8, 9]),
        spon="50 × 60 cm", hlbka="semeno 0,5–1 cm; sadenicu v rovnakej hĺbke ako v kvetináči",
        tipy=["Potrebuje ešte viac tepla ako paprika – najslnečnejšie a závetrné miesto, čierna textília.",
              "Vonku je úroda menšia a neskoršia; stačia 2–4 rastliny na skúšku.",
              "Nechaj na rastline 4–6 plodov, ďalšie kvety odstráň – stihnú dozrieť.",
              "Zber, kým je šupka lesklá. Matná šupka = prezretý, semená tvrdnú."],
        problemy=[("Pásavka zemiaková", "baklažán má rada ešte viac ako zemiaky. Kontrolovať listy, chrobáky a vajíčka zbierať."),
                  ("Opadávanie kvetov", "chladné noci alebo sucho. Pravidelne polievať, mulčovať.")],
        dobri=["bazalka", "fazula"], zli=["zemiaky"],
        ulohy=[
            U("sejba", "02-15", "03-15", "Baklažán: zasej na predpestovanie (25 °C, svetlý parapet)", "sejba", sposob=PRED, stav=PLAN, potrebujes=["semená baklažánu", "výsevný substrát", "misky"], nastav="zasiate"),
            U("pik", "03-15", "04-15", "Baklažán: pikíruj do samostatných kvetináčov", "sejba", sposob=PRED, stav=PLAN_Z, potrebujes=["kvetináče 8–10 cm"]),
            U("kup", "05-10", "05-31", "Baklažán: kúp sadenice", "nakup", sposob=SAD, stav=PLAN, potrebujes=["sadenice baklažánu"]),
            U("vys", "05-25", "06-10", "Baklažán: vysaď na najteplejšie miesto cez čiernu textíliu, kolík, zaliať", "vysadba", stav=PLAN_Z, potrebujes=["kolíky", "čierna mulčovacia textília", "kompost"], nastav="vysadene"),
            U("pas", "06-01", "08-15", "Baklažán: kontrola pásavky zemiakovej", "ochrana", opak="tyzden"),
            U("hnoj", "06-15", "08-31", "Baklažán: prihnoj (hnojivo na plodovú zeleninu) každé 2 týždne", "hnojenie", opak="14dni"),
            U("plody", "07-20", "08-10", "Baklažán: nechaj 4–6 plodov, ďalšie kvety odstráň", "starostlivost"),
            U("zber", "08-01", "09-30", "Baklažán: zber lesklých plodov", "zber", opak="tyzden"),
        ],
        rel=[R(0, 0, "Baklažán: po výsadbe zaliať")])

plodina("mangold", nazov="Mangold", rodina="Láskavcovité", naroky="stredne", typ="zelenina",
        kal=dict(pred=[], von=[4, 5, 6], zber=[6, 7, 8, 9, 10]),
        spon="riadky 40 cm, v riadku 30 cm", hlbka="2–3 cm",
        tipy=["Jedna z najmenej náročných zelenín – zberá sa od júna do mrazov.",
              "Strihaj vonkajšie listy, srdce nechaj – dorastá ďalej.",
              "Zo semena (klbka) vyrastie viac rastlín – treba jednotiť."],
        dobri=["salat", "kapusta"], zli=[],
        ulohy=[
            U("sejba", "04-10", "06-30", "Mangold: zasej 2–3 cm hlboko", "sejba", sposob=SEM, stav=PLAN, potrebujes=["semená mangoldu"], nastav="zasiate"),
            U("zber", "06-15", "10-31", "Mangold: strihaj vonkajšie listy", "zber", opak="tyzden"),
        ],
        rel=[R(21, 42, "Mangold: vyjednoť na 30 cm")])

plodina("por", nazov="Pór", rodina="Amarylkovité (cesnakovité)", naroky="stredne", typ="zelenina",
        sposoby=["predpestovanie", "sadenice"],
        kal=dict(pred=[2, 3], von=[5, 6], zber=[9, 10, 11]),
        spon="riadky 30 cm, v riadku 15 cm", hlbka="sadenicu do jamky hlbokej cca 15 cm",
        tipy=["Sadenicu vlož do hlbokej jamky (urobíš ju kolíkom) a len zalej – zem sa do jamky zosype sama.",
              "Postupne prihŕňaj – biela časť bude dlhšia.",
              "Znesie mrazy, zberá sa od septembra aj cez zimu."],
        dobri=["mrkva", "zeler"], zli=["fazula", "hrach"],
        ulohy=[
            U("pred", "02-15", "03-31", "Pór: zasej na predpestovanie", "sejba", sposob=PRED, stav=PLAN, potrebujes=["semená póru"], nastav="zasiate"),
            U("kup", "04-20", "05-31", "Pór: kúp sadenice", "nakup", sposob=SAD, stav=PLAN, potrebujes=["sadenice póru"]),
            U("vys", "05-01", "06-15", "Pór: vysaď do jamiek hlbokých 15 cm (kolíkom), len zaliať", "vysadba", stav=PLAN_Z, nastav="vysadene"),
            U("prihr", "07-01", "09-15", "Pór: prihrň zeminu k stonkám", "starostlivost", opak="14dni"),
            U("zber", "09-01", "11-30", "Pór: zber podľa potreby", "zber", opak="14dni"),
        ])

plodina("kukurica", nazov="Kukurica cukrová", rodina="Lipnicovité (trávy)", naroky="silne", typ="zelenina",
        kal=dict(pred=[], von=[5, 6], zber=[8, 9]),
        spon="v riadku 30 cm, riadky 60 cm; sej do bloku (aspoň 3 × 3 rastliny), nie do jedného riadku",
        hlbka="3–5 cm",
        tipy=["Opeľuje ju vietor – v bloku sa opelí, v jednom riadku sú klasy poloprázdne.",
              "Sej do teplej pôdy (po 10. 5.).",
              "Počas kvitnutia potrebuje vodu – na piesku mulč.",
              "Zrelá: vlákna (bliznu) sú hnedé a suché, zrno pri stlačení pustí mliečnu šťavu."],
        dobri=["fazula", "cukety", "tekvica"], zli=[],
        ulohy=[
            U("sejba", "05-10", "06-05", "Kukurica: zasej do bloku 3–5 cm hlboko", "sejba", sposob=SEM, stav=PLAN, potrebujes=["semená cukrovej kukurice"], nastav="zasiate"),
            U("prihr", "06-15", "07-10", "Kukurica: prihrň zeminu k rastlinám (lepšie stoja vo vetre)", "starostlivost"),
            U("zber", "08-01", "09-15", "Kukurica: zber klasov (hnedé vlákna, mliečne zrno)", "zber", opak="tyzden"),
        ],
        rel=[R(0, 0, "Kukurica: po sejbe zaliať")])

plodina("fazula", nazov="Fazuľa kríčková", rodina="Bôbovité", naroky="slabo", typ="zelenina",
        kal=dict(pred=[], von=[5, 6, 7], zber=[7, 8, 9]),
        spon="riadky 40 cm, v riadku 5–8 cm", hlbka="3–4 cm",
        tipy=["Nehnojiť dusíkom – fazuľa si ho viaže z ovzdušia sama.",
              "Sej až do teplej pôdy (po 15. 5.), dá sa siať postupne do začiatku júla.",
              "Po zbere odstrihni rastliny pri zemi a korene nechaj v pôde – obohatia ju o dusík.",
              "Oberaj mladé struky pravidelne, rastlina potom tvorí ďalšie."],
        dobri=["uhorky", "cukety", "zemiaky", "mrkva"], zli=["cibula", "cesnak"],
        ulohy=[
            U("sejba", "05-15", "07-05", "Fazuľa: zasej 3–4 cm hlboko, po 5–8 cm (dá sa postupne každé 2–3 týždne)", "sejba", sposob=SEM, stav=PLAN, potrebujes=["semená fazule"], nastav="zasiate"),
            U("prihr", "06-15", "07-20", "Fazuľa: prihrň zeminu k rastlinám (lepšie stoja)", "starostlivost"),
            U("zber", "07-10", "09-20", "Fazuľa: oberaj mladé struky", "zber", opak="tyzden"),
        ],
        rel=[R(0, 0, "Fazuľa: po sejbe zaliať")])

plodina("hrach", nazov="Hrach", rodina="Bôbovité", naroky="slabo", typ="zelenina",
        kal=dict(pred=[], von=[3, 4], zber=[6, 7]),
        spon="riadky 30–40 cm, v riadku 5 cm", hlbka="4–5 cm",
        tipy=["Znesie chlad – sej hneď, ako sa dá pracovať s pôdou.",
              "Vyššie odrody potrebujú oporu (pletivo, konáriky).",
              "Semená radi vyzobávajú vtáky – po sejbe prikry textíliou.",
              "Po zbere nechaj korene v zemi a zasej zelené hnojenie."],
        dobri=["mrkva", "uhorky", "redkovka"], zli=["cibula", "cesnak"],
        ulohy=[
            U("sejba", "03-20", "04-30", "Hrach: zasej 4–5 cm hlboko, prikry textíliou proti vtákom", "sejba", sposob=SEM, stav=PLAN, potrebujes=["semená hrachu", "biela textília"], nastav="zasiate"),
            U("opora", "05-01", "05-31", "Hrach: vyšším odrodám daj oporu", "starostlivost", potrebujes=["pletivo / konáriky"]),
            U("zber", "06-10", "07-15", "Hrach: zber struskov (mladý, sladký)", "zber", opak="tyzden"),
            U("po", "07-01", "07-31", "Hrach: po zbere odstrihni nať pri zemi, korene nechaj, zasej zelené hnojenie", "priprava"),
        ])

plodina("mrkva", nazov="Mrkva", rodina="Mrkvovité", naroky="stredne", typ="zelenina",
        kal=dict(pred=[], von=[3, 4, 5, 6], zber=[6, 7, 8, 9, 10]),
        spon="riadky 25–30 cm, po jednotení 3–5 cm", hlbka="1–2 cm",
        tipy=["Piesočnatá pôda je pre mrkvu ideálna – rovné, dlhé korene.",
              "Nehnojiť čerstvým hnojom – mrkva sa potom rozkonáruje.",
              "Klíči 2–3 týždne, pôda musí byť stále vlhká. Pridaj do riadku zopár semien reďkovky ako značku.",
              "Biela textília po sejbe chráni pred pochmúrnatkou mrkvovou (červivá mrkva)."],
        problemy=[("Pochmúrnatka mrkvová", "hnedé chodbičky v koreni. Prevencia: textília, striedanie, pri jednotení nenechávať vytrhané rastliny na záhone.")],
        dobri=["cibula", "hrach", "paradajky", "salat"], zli=[],
        ulohy=[
            U("sejba", "03-20", "05-31", "Mrkva: zasej do riadkov 1–2 cm hlboko, zaliať, prikryť bielou textíliou", "sejba", sposob=SEM, stav=PLAN, potrebujes=["semená mrkvy", "biela textília"], nastav="zasiate"),
            U("zber", "06-20", "10-31", "Mrkva: zber (skoré odrody od júna, na uskladnenie v októbri pred mrazmi)", "zber", opak="14dni"),
        ],
        rel=[R(0, 21, "Mrkva: udržuj pôdu vlhkú, kým nevzíde (2–3 týždne)", "tyzden"),
             R(21, 45, "Mrkva: vyjednoť na 3–5 cm (vytrhané rastliny odnes preč)")])

plodina("petrzlen", nazov="Petržlen", rodina="Mrkvovité", naroky="stredne", typ="zelenina",
        kal=dict(pred=[], von=[3, 4], zber=[9, 10]),
        spon="riadky 25–30 cm, po jednotení 5–8 cm", hlbka="1–2 cm",
        tipy=["Klíči až 3–4 týždne – pôdu drž vlhkú.",
              "Nehnojiť čerstvým hnojom.",
              "Vňať sa dá strihať priebežne."],
        dobri=["paradajky", "cibula"], zli=[],
        ulohy=[
            U("sejba", "03-15", "04-30", "Petržlen: zasej do riadkov 1–2 cm hlboko, drž vlhko", "sejba", sposob=SEM, stav=PLAN, potrebujes=["semená petržlenu"], nastav="zasiate"),
            U("zber", "09-01", "10-31", "Petržlen: zber koreňov (pred silnými mrazmi)", "zber"),
        ],
        rel=[R(28, 50, "Petržlen: vyjednoť na 5–8 cm")])

plodina("cibula", nazov="Cibuľa (sadzačka)", rodina="Amarylkovité (cesnakovité)", naroky="stredne", typ="zelenina",
        sposoby=["sadba", "priama_sejba"],
        kal=dict(pred=[], von=[3, 4], zber=[7, 8]),
        spon="riadky 20–25 cm, v riadku 8–10 cm", hlbka="sadzačku tak, aby špička trčala zo zeme",
        tipy=["Nehnojiť čerstvým hnojom, stačí kompost.",
              "Cibuľa neznáša burinu – pleť včas.",
              "Keď vňať začne žltnúť, prestaň polievať – cibuľa lepšie vyzrie a vydrží."],
        dobri=["mrkva", "paradajky", "jahody"], zli=["fazula", "hrach"],
        ulohy=[
            U("sadba", "03-20", "04-20", "Cibuľa: vysaď sadzačku (špička nad zemou)", "vysadba", stav=PLAN, potrebujes=["cibuľa sadzačka"], nastav="vysadene"),
            U("plev", "05-01", "06-30", "Cibuľa: pleť a kypri", "starostlivost", opak="14dni"),
            U("stop", "07-01", "07-20", "Cibuľa: keď vňať žltne, prestaň polievať", "starostlivost"),
            U("zber", "07-20", "08-20", "Cibuľa: keď väčšina vňate poľahne, vytiahni a nechaj preschnúť na slnku / pod strieškou", "zber"),
        ])

plodina("cesnak", nazov="Cesnak (ozimný)", rodina="Amarylkovité (cesnakovité)", naroky="stredne", typ="zelenina",
        sposoby=["sadba"], prezimuje=True,
        kal=dict(pred=[], von=[10], zber=[6, 7]),
        spon="riadky 25–30 cm, v riadku 10–15 cm", hlbka="5 cm (strúčik špičkou hore)",
        tipy=["Kúp sadbový cesnak – cesnak z obchodu býva ošetrený a často z teplejších krajín.",
              "Sadí sa na jeseň, zberá budúce leto. Na piesku ľahko zakorení.",
              "Paličák (s kvetným stvolom): stvoly v júni odlom, hlavičky budú väčšie."],
        dobri=["jahody", "mrkva", "paradajky"], zli=["fazula", "hrach"],
        ulohy=[
            U("sadba", "09-25", "10-31", "Cesnak: vysaď strúčiky 5 cm hlboko, špičkou hore, po 10–15 cm", "vysadba", stav=PLAN, potrebujes=["sadbový cesnak"], nastav="vysadene"),
            U("jar", "03-15", "04-15", "Cesnak: okopať, prihnojiť (kompost / granule)", "hnojenie"),
            U("stvol", "06-01", "06-25", "Cesnak: odlom kvetné stvoly (paličák)", "starostlivost"),
            U("zber", "06-25", "07-25", "Cesnak: zber, keď spodná tretina listov zožltne; sušiť v tieni aj so vňaťou", "zber"),
        ])

plodina("redkovka", nazov="Reďkovka", rodina="Kapustovité", naroky="slabo", typ="zelenina",
        kal=dict(pred=[], von=[3, 4, 5, 8, 9], zber=[4, 5, 6, 9, 10]),
        spon="riadky 15–20 cm, v riadku 3–5 cm", hlbka="1 cm",
        tipy=["Rastie 4–6 týždňov. Sej po troške každé 2 týždne.",
              "Potrebuje rovnomernú vlahu – v suchu je drevnatá a pálivá.",
              "V lete (dlhý deň, horúco) vybieha do kvetu – sej na jar a koncom leta.",
              "Je kapustovitá – počíta sa do striedania s kapustou."],
        dobri=["mrkva", "salat", "hrach"], zli=[],
        ulohy=[
            U("sejba1", "03-15", "05-15", "Reďkovka: zasej ďalší riadok (každé 2 týždne)", "sejba", opak="14dni", potrebujes=["semená reďkovky"], nastav="zasiate"),
            U("sejba2", "08-10", "09-15", "Reďkovka: jesenná sejba (každé 2 týždne)", "sejba", opak="14dni", potrebujes=["semená reďkovky"], nastav="zasiate"),
        ],
        rel=[R(25, 45, "Reďkovka: zber (4–6 týždňov po sejbe), neskôr je dutá")])

plodina("salat", nazov="Šalát hlávkový", rodina="Astrovité", naroky="slabo", typ="zelenina",
        sposoby=["priama_sejba", "predpestovanie", "sadenice"],
        kal=dict(pred=[2, 3], von=[4, 5, 6, 7, 8], zber=[5, 6, 7, 8, 9, 10]),
        spon="25–30 cm", hlbka="semeno 0,5 cm; sadenicu plytko, srdiečko nad zemou",
        tipy=["Sadenicu sadiť plytko – keď zasypeš srdiečko, hnije.",
              "V horúčave vybieha do kvetu – v lete sej letné odrody, stačí aj polotieň.",
              "Sej / saď po troške každé 3 týždne, aby neprišlo všetko naraz."],
        problemy=[("Slimáky", "ohryzené listy, slizké stopy. Večer zbierať, pasce, granule proti slimákom (povolené v bio).")],
        dobri=["mrkva", "redkovka", "jahody"], zli=[],
        ulohy=[
            U("pred", "02-20", "03-31", "Šalát: zasej na predpestovanie", "sejba", sposob=PRED, stav=PLAN, potrebujes=["semená šalátu", "misky"], nastav="zasiate"),
            U("sejba", "03-20", "07-31", "Šalát: zasej / vysaď ďalšiu várku (každé 3 týždne)", "sejba", opak="14dni", sposob=SEM + SAD, potrebujes=["semená / sadenice šalátu"], nastav="vysadene"),
            U("vys", "04-01", "05-15", "Šalát: vysaď predpestované sadenice (plytko)", "vysadba", sposob=PRED, stav=PLAN_Z, nastav="vysadene"),
            U("zber", "05-01", "10-15", "Šalát: zber hláv (pred vybehnutím do kvetu)", "zber", opak="tyzden"),
        ])

plodina("spenat", nazov="Špenát", rodina="Láskavcovité", naroky="stredne", typ="zelenina",
        kal=dict(pred=[], von=[3, 4, 8, 9], zber=[4, 5, 6, 9, 10]),
        spon="riadky 20–25 cm", hlbka="2 cm",
        tipy=["Rastie v chlade – na jar a na jeseň. V lete (dlhý deň) hneď vybehne do kvetu.",
              "Zbieraj listy skôr, ako rastlina vytvorí kvetný stvol."],
        dobri=["redkovka", "jahody"], zli=[],
        ulohy=[
            U("sejba1", "03-10", "04-20", "Špenát: jarná sejba 2 cm hlboko", "sejba", sposob=SEM, potrebujes=["semená špenátu"], nastav="zasiate"),
            U("sejba2", "08-15", "09-15", "Špenát: jesenná sejba", "sejba", sposob=SEM, potrebujes=["semená špenátu"], nastav="zasiate"),
        ],
        rel=[R(40, 70, "Špenát: zber listov (skôr, ako vybehne do kvetu)", "tyzden")])

plodina("cvikla", nazov="Cvikla", rodina="Láskavcovité", naroky="stredne", typ="zelenina",
        kal=dict(pred=[], von=[4, 5, 6], zber=[7, 8, 9, 10]),
        spon="riadky 30 cm, v riadku 8–10 cm", hlbka="2–3 cm",
        tipy=["Zo semena (klbka) vyrastie viac rastlín – treba jednotiť.",
              "Na piesku pravidelne polievať, inak je drevnatá."],
        dobri=["cibula", "salat", "kalerab"], zli=[],
        ulohy=[
            U("sejba", "04-20", "06-15", "Cvikla: zasej 2–3 cm hlboko", "sejba", sposob=SEM, stav=PLAN, potrebujes=["semená cvikly"], nastav="zasiate"),
            U("zber", "07-15", "10-20", "Cvikla: zber bulvičiek (pred silnými mrazmi všetko)", "zber", opak="14dni"),
        ],
        rel=[R(21, 42, "Cvikla: vyjednoť na 8–10 cm")])

plodina("kalerab", nazov="Kaleráb", rodina="Kapustovité", naroky="stredne", typ="zelenina",
        sposoby=["predpestovanie", "sadenice", "priama_sejba"],
        kal=dict(pred=[2, 3, 5, 6], von=[4, 5, 6, 7], zber=[5, 6, 7, 8, 9, 10]),
        spon="25–30 cm", hlbka="sadenicu plytko – bulva musí byť nad zemou",
        tipy=["Pravidelná vlaha – v suchu drevnatie a praská.",
              "Sadiť plytko, bulva sa tvorí nad zemou.",
              "Kapustovitý – v striedaní ako kapusta (pauza 4 roky)."],
        problemy=[("Skočky", "drobné dierky v listoch v suchom teple. Polievať, textília."),
                  ("Kýla kapustová", "zdurené korene, rastlina vädne. Ochorenie pôdy – dlhá pauza v striedaní, nezaťahovať ho sadenicami.")],
        dobri=["salat", "cvikla", "zeler"], zli=[],
        ulohy=[
            U("pred", "02-15", "03-31", "Kaleráb: zasej na predpestovanie", "sejba", sposob=PRED, stav=PLAN, potrebujes=["semená kalerábu"], nastav="zasiate"),
            U("vys", "04-01", "05-15", "Kaleráb: vysaď sadenice plytko, po 25–30 cm", "vysadba", sposob=PRED + SAD, stav=PLAN_Z, potrebujes=["sadenice kalerábu"], nastav="vysadene"),
            U("leto", "05-15", "07-15", "Kaleráb: letná sejba / výsadba ďalšej várky", "sejba", opak="14dni"),
            U("zber", "05-20", "10-31", "Kaleráb: zber (kým je mladý a šťavnatý)", "zber", opak="tyzden"),
        ])

plodina("kapusta", nazov="Kapusta, kel", rodina="Kapustovité", naroky="silne", typ="zelenina",
        sposoby=["predpestovanie", "sadenice"],
        kal=dict(pred=[3, 4], von=[4, 5, 6], zber=[7, 8, 9, 10, 11]),
        spon="50 × 50 cm, neskoré odrody 60 × 60 cm", hlbka="sadenicu po prvé listy",
        tipy=["Veľa živín – kompost pri výsadbe, v lete prihnojiť.",
              "Kapustovité na rovnaké miesto najskôr po 4 rokoch (kýla kapustová). Horčica aj reďkovka sú tiež kapustovité!",
              "Proti mlynárikom a skočkám pomáha jemná sieťka alebo textília."],
        problemy=[("Mlynárik kapustový", "zelené húsenice, ohryzené listy. Kontrolovať spodnú stranu listov (žlté vajíčka), odstrániť."),
                  ("Kýla kapustová", "zdurené korene. Dlhá pauza v striedaní.")],
        dobri=["salat", "zeler", "kopor"], zli=["jahody"],
        ulohy=[
            U("pred", "03-15", "04-30", "Kapusta: zasej na predpestovanie", "sejba", sposob=PRED, stav=PLAN, potrebujes=["semená kapusty"], nastav="zasiate"),
            U("vys", "04-20", "06-15", "Kapusta: vysaď sadenice s kompostom, zaliať", "vysadba", stav=PLAN_Z, potrebujes=["sadenice kapusty", "kompost"], nastav="vysadene"),
            U("hus", "05-15", "09-15", "Kapusta: kontrola húseníc a vajíčok mlynárika (spodná strana listov)", "ochrana", opak="tyzden", potrebujes=["ochranná sieťka"]),
            U("hnoj", "06-01", "07-31", "Kapusta: prihnoj (hnojivo na zeleninu)", "hnojenie", opak="14dni"),
            U("zber", "07-01", "11-15", "Kapusta: zber pevných hláv", "zber", opak="14dni"),
        ])

plodina("brokolica", nazov="Brokolica", rodina="Kapustovité", naroky="silne", typ="zelenina",
        sposoby=["predpestovanie", "sadenice"],
        kal=dict(pred=[3, 4, 6], von=[4, 5, 7], zber=[6, 7, 8, 9, 10]),
        spon="40 × 50 cm", hlbka="sadenicu po prvé listy",
        tipy=["Hlavnú ružicu odrež, kým sú púčiky zatvorené – potom dorastú bočné.",
              "V horúčave rýchlo rozkvitá – lepšia je jarná a jesenná výsadba.",
              "Kapustovitá – pauza 4 roky na rovnakom mieste."],
        problemy=[("Mlynárik, skočky", "ako pri kapuste – sieťka / textília, kontrola listov.")],
        dobri=["salat", "zeler"], zli=["jahody"],
        ulohy=[
            U("pred", "03-15", "04-30", "Brokolica: zasej na predpestovanie", "sejba", sposob=PRED, stav=PLAN, potrebujes=["semená brokolice"], nastav="zasiate"),
            U("vys", "04-20", "05-31", "Brokolica: vysaď sadenice s kompostom", "vysadba", stav=PLAN_Z, potrebujes=["sadenice brokolice", "kompost"], nastav="vysadene"),
            U("hus", "05-15", "09-15", "Brokolica: kontrola húseníc mlynárika", "ochrana", opak="tyzden"),
            U("zber", "06-15", "10-31", "Brokolica: zber ružíc (púčiky zatvorené)", "zber", opak="tyzden"),
        ])

plodina("zemiaky", nazov="Zemiaky", rodina="Ľuľkovité", naroky="silne", typ="zelenina",
        sposoby=["sadba"],
        kal=dict(pred=[3], von=[4], zber=[6, 7, 8, 9]),
        spon="v riadku 30–35 cm, riadky 60–70 cm", hlbka="8–10 cm",
        tipy=["Na piesku sa darí – zemiaky sú čisté, ľahko sa kopú.",
              "Predklíčená sadba = úroda o 2–3 týždne skôr.",
              "Nesaď po paradajkách ani vedľa nich – rovnaká pleseň.",
              "Kúp sadbové zemiaky, nie zemiaky na jedenie."],
        problemy=[("Pásavka zemiaková (mandelinka)", "pruhované chrobáky, oranžové vajíčka pod listami, larvy žerú listy. Zbierať ručne."),
                  ("Pleseň zemiaková", "hnedé škvrny na vňati po daždi. Ak sa rozšíri, vňať odstrániť, hľuzy vykopať o 2 týždne.")],
        dobri=["fazula", "kapusta"], zli=["paradajky", "tekvica"],
        ulohy=[
            U("klic", "03-01", "03-31", "Zemiaky: predkľúčuj sadbu – rozlož na svetlé miesto, 10–15 °C", "priprava", stav=PLAN, potrebujes=["sadbové zemiaky", "prepravky"]),
            U("sadba", "04-01", "04-30", "Zemiaky: vysaď 8–10 cm hlboko, 30–35 cm od seba", "vysadba", stav=PLAN, nastav="vysadene"),
            U("prihr", "05-10", "06-15", "Zemiaky: prihŕňaj zeminu k rastlinám (spolu 2×)", "starostlivost", opak="14dni"),
            U("pas", "05-20", "07-31", "Zemiaky: kontrola pásavky (chrobáky, oranžové vajíčka pod listami)", "ochrana", opak="tyzden"),
            U("zber1", "06-20", "07-20", "Zemiaky: rané – zber podľa potreby", "zber"),
            U("zber2", "08-20", "09-30", "Zemiaky: zber, keď nať zaschne (šupka je pevná asi 2 týždne po zaschnutí)", "zber"),
        ])

# ---------------------------------------------------------------- OVOCIE
plodina("jahody", nazov="Jahody", rodina="Ružovité", naroky="stredne", typ="ovocie", trvalka=True,
        sposoby=["sadenice", "ker"],
        kal=dict(pred=[], von=[4, 7, 8, 9], zber=[5, 6]),
        spon="v riadku 25–30 cm, riadky 50–60 cm",
        hlbka="srdiečko (korunka) presne v úrovni zeme – nezasypať, korene nesmú trčať",
        tipy=["Najlepší čas výsadby je júl až august; do polovice septembra ešte zakorenia pred zimou.",
              "Srdiečko v úrovni zeme: zasypané hnije, vytŕčajúce vysychá.",
              "Prvé 3 týždne po výsadbe polievaj pri suchu každé 2–3 dni – na piesku je to kľúčové.",
              "Čierna textília alebo slama pod rastlinami = čisté plody, menej hniloby a buriny.",
              "Po 3–4 rokoch rodia menej – vysaď nové na iné miesto."],
        problemy=[("Sivá hniloba (pleseň sivá)", "sivý chlpatý povlak na plodoch, hlavne v daždi. Mulč pod plody, nahnité plody hneď odstraňovať, nepolievať zhora."),
                  ("Omrznuté kvety", "kvet má čierny stred – nebude plod. Pri mrazíku počas kvitnutia zakryť na noc textíliou."),
                  ("Vytláčanie mrazom", "jesenné výsadby môže mráz vytlačiť zo zeme. Po zime pritlačiť, na zimu ľahko prikryť čečinou.")],
        dobri=["cesnak", "cibula", "salat", "spenat"], zli=["kapusta", "brokolica"],
        ulohy=[
            U("vys_j", "04-01", "04-30", "Jahody: jarná výsadba (srdiečko v úrovni zeme), dôkladne zaliať", "vysadba", stav=PLAN, potrebujes=["sadenice jahôd", "kompost"], nastav="vysadene"),
            U("vys", "07-20", "09-15", "Jahody: výsadba nových rastlín (srdiečko v úrovni zeme), po 25–30 cm, zaliať", "vysadba", stav=PLAN, potrebujes=["sadenice jahôd", "kompost"], nastav="vysadene"),
            U("jar", "03-15", "04-15", "Jahody: odstráň suché a choré listy, okopať, prihnojiť", "hnojenie", stav=["vysadene"], potrebujes=["hnojivo na jahody"]),
            U("mulc", "04-20", "05-10", "Jahody: pred kvitnutím podstlať slamu (alebo čierna textília) – plody nebudú na zemi", "starostlivost", stav=["vysadene"], potrebujes=["slama"]),
            U("kvet", "04-20", "05-20", "Jahody kvitnú: pri nočnom mrazíku ich zakry textíliou", "ochrana", stav=["vysadene"], potrebujes=["biela textília"]),
            U("zber", "05-20", "06-30", "Jahody: zber každé 2–3 dni, nahnité plody odstraňuj", "zber", opak="tyzden", stav=["vysadene"]),
            U("po", "07-01", "07-31", "Jahody po zbere: odstráň šľahúne (ak nechceš nové rastliny), pokos staré listy nad srdiečkami, prihnoj, polievaj", "starostlivost", stav=["vysadene"]),
            U("zima", "11-15", "12-15", "Jahody: pri mrazoch bez snehu ľahko prikry čečinou alebo slamou", "ochrana", potrebujes=["čečina / slama"]),
            U("jar_kontr", "03-01", "03-31", "Jahody: skontroluj jesenné výsadby – mráz vytlačené rastliny pritlač k zemi", "starostlivost"),
        ],
        rel=[R(0, 0, "Jahody: po výsadbe dôkladne zaliať"),
             R(1, 21, "Jahody: nové rastliny polievaj pri suchu každé 2–3 dni, kým nezakorenia", "tyzden")])

plodina("ribezle", nazov="Ríbezle", rodina="Egrešovité", naroky="stredne", typ="ovocie", trvalka=True,
        sposoby=["ker"],
        kal=dict(pred=[], von=[3, 4, 10, 11], zber=[6, 7]),
        spon="1,5 m medzi kríkmi", hlbka="o 5–10 cm hlbšie, ako rástli v škôlke / kontajneri",
        tipy=["Sadiť hlbšie – vyrastú nové výhony zo zeme.",
              "Plytké korene: na piesku mulčovať a v suchu polievať, inak bobule opadávajú.",
              "Rez: ker má mať 8–12 konárov rôzneho veku; najstaršie (4–5-ročné, tmavé) vyrež pri zemi."],
        problemy=[("Opadávanie bobúľ", "sucho počas dozrievania – polievať, mulč."),
                  ("Múčnatka", "biely povlak na vrcholoch – napadnuté vrcholy vystrihnúť, ker preriediť.")],
        dobri=[], zli=[],
        ulohy=[
            U("vys", "10-01", "11-15", "Ríbezle: výsadba (hlbšie o 5–10 cm), voľnokorenné výhony skrátiť na 3–4 púčiky", "vysadba", stav=PLAN, potrebujes=["kríky ríbezlí", "kompost"], nastav="vysadene"),
            U("vys_j", "03-15", "04-15", "Ríbezle: jarná výsadba", "vysadba", stav=PLAN, potrebujes=["kríky ríbezlí"], nastav="vysadene"),
            U("rez", "02-01", "03-20", "Ríbezle: rez – najstaršie konáre pri zemi, slabé a prekrížené preč", "rez", stav=["vysadene"], potrebujes=["záhradné nožnice"]),
            U("hnoj", "03-15", "04-15", "Ríbezle: kompost / hnojivo s draslíkom okolo kríka, namulčovať", "hnojenie", stav=["vysadene"], potrebujes=["hnojivo na drobné ovocie"]),
            U("voda", "05-15", "07-15", "Ríbezle: pri suchu výdatne poliať (bobule opadávajú zo sucha)", "starostlivost", opak="14dni", stav=["vysadene"]),
            U("zber", "06-20", "07-25", "Ríbezle: zber celých strapcov", "zber", opak="tyzden", stav=["vysadene"]),
        ])

plodina("egrese", nazov="Egreše", rodina="Egrešovité", naroky="stredne", typ="ovocie", trvalka=True,
        sposoby=["ker"],
        kal=dict(pred=[], von=[3, 4, 10, 11], zber=[6, 7]),
        spon="1,5 m medzi kríkmi", hlbka="ako v kontajneri alebo o trochu hlbšie",
        tipy=["Ker udržuj vzdušný (rez), menej múčnatky.",
              "Odolné odrody voči americkej múčnatke sú pre záhradkára najlepšia voľba."],
        problemy=[("Americká múčnatka egreša", "biely, neskôr hnedý plstnatý povlak na bobuliach a vrcholoch. Napadnuté vrcholy vystrihnúť, ker preriediť.")],
        ulohy=[
            U("vys", "10-01", "11-15", "Egreše: výsadba", "vysadba", stav=PLAN, potrebujes=["kríky egrešov"], nastav="vysadene"),
            U("rez", "02-01", "03-20", "Egreše: rez – staré konáre preč, ker preriediť", "rez", stav=["vysadene"]),
            U("mucn", "05-15", "06-30", "Egreše: kontrola múčnatky na vrcholoch, napadnuté vystrihnúť", "ochrana", opak="14dni", stav=["vysadene"]),
            U("zber", "06-20", "07-31", "Egreše: zber", "zber", opak="tyzden", stav=["vysadene"]),
        ])

plodina("maliny", nazov="Maliny", rodina="Ružovité", naroky="stredne", typ="ovocie", trvalka=True,
        sposoby=["ker"],
        kal=dict(pred=[], von=[3, 4, 10, 11], zber=[6, 7, 8, 9]),
        spon="v riadku 40–50 cm, riadky 1,5–2 m", hlbka="ako rástli, prúty po výsadbe skrátiť na 20–30 cm",
        tipy=["Letné maliny rodia na minuloročných prútoch, stáleplodiace (jesenné) na tohtoročných.",
              "Potrebujú oporu (drôty medzi kolíkmi).",
              "Rozrastajú sa výbežkami – ohranič ich (zapustená fólia / obrubník)."],
        ulohy=[
            U("vys", "10-01", "11-15", "Maliny: výsadba, prúty skrátiť na 20–30 cm", "vysadba", stav=PLAN, potrebujes=["sadenice malín"], nastav="vysadene"),
            U("rezj", "02-01", "03-20", "Maliny stáleplodiace: všetky prúty zrež pri zemi", "rez", stav=["vysadene"]),
            U("opora", "04-01", "04-30", "Maliny: skontroluj / natiahni oporu, priviaž prúty", "starostlivost", stav=["vysadene"], potrebujes=["drôt, kolíky"]),
            U("zber", "06-20", "09-30", "Maliny: zber", "zber", opak="tyzden", stav=["vysadene"]),
            U("rezl", "07-20", "08-31", "Maliny letné: po zbere odrež odrodené prúty pri zemi, nechaj 8–10 silných mladých na meter", "rez", stav=["vysadene"]),
        ])

plodina("cucoriedka", nazov="Čučoriedka kanadská", rodina="Vresovité", naroky="stredne", typ="ovocie", trvalka=True,
        sposoby=["ker"],
        kal=dict(pred=[], von=[3, 4, 10], zber=[7, 8]),
        spon="1–1,5 m medzi kríkmi",
        hlbka="do jamky (aspoň 50 × 50 cm, 40 cm hlboko) s kyslým substrátom, v rovnakej hĺbke ako v kontajneri",
        tipy=["Potrebuje kyslú pôdu (pH 4–5). V bežnej záhradnej pôde živorí – jamka s kyslým substrátom (rašelina / substrát pre čučoriedky a vresoviská). pH overíš lacným pôdnym testerom.",
              "Zalievaj dažďovou vodou. Tvrdá voda z vodovodu postupne zvyšuje pH.",
              "Hnoj len hnojivom pre čučoriedky / rododendróny. Nie popol, nie vápno, nie čerstvý hnoj.",
              "Mulč z ihličia alebo borovicovej kôry drží vlahu aj kyslosť – na piesku dôležité.",
              "Dve rôzne odrody vedľa seba = lepšie opelenie a väčšia úroda.",
              "V roku výsadby je dobré kvety odstrániť, rastlina zosilnie."],
        problemy=[("Žltnúce listy so zelenými žilkami", "chloróza – pôda nie je dosť kyslá, rastlina neprijíma železo. Hnojivo pre čučoriedky, kyslý mulč, dažďová voda."),
                  ("Vtáky", "zobú zrelé plody – sieť cez ker počas dozrievania.")],
        ulohy=[
            U("vys", "10-01", "11-15", "Čučoriedka: výsadba do jamky s kyslým substrátom, zaliať dažďovou vodou, namulčovať ihličím / kôrou", "vysadba", stav=PLAN, potrebujes=["kríky čučoriedky (2 odrody)", "kyslý substrát pre čučoriedky", "borovicová kôra / ihličie"], nastav="vysadene"),
            U("vys_j", "03-15", "04-30", "Čučoriedka: jarná výsadba do kyslého substrátu", "vysadba", stav=PLAN, potrebujes=["kríky čučoriedky", "kyslý substrát pre čučoriedky"], nastav="vysadene"),
            U("rez", "02-15", "03-20", "Čučoriedka: rez (od 4. roku) – najstaršie konáre pri zemi, slabé a prekrížené preč", "rez", stav=["vysadene"]),
            U("hnoj", "04-01", "04-30", "Čučoriedka: prihnoj hnojivom pre čučoriedky, doplň mulč z ihličia / kôry", "hnojenie", stav=["vysadene"], potrebujes=["hnojivo pre čučoriedky / rododendróny", "borovicová kôra / ihličie"]),
            U("voda", "05-15", "08-31", "Čučoriedka: pri suchu poliať dažďovou vodou", "starostlivost", opak="14dni", stav=["vysadene"]),
            U("siet", "06-20", "07-10", "Čučoriedka: prehoď cez ker sieť proti vtákom", "ochrana", stav=["vysadene"], potrebujes=["sieť proti vtákom"]),
            U("zber", "07-01", "08-31", "Čučoriedka: zber (plody dozrievajú postupne, zrelé sú celé modré)", "zber", opak="tyzden", stav=["vysadene"]),
        ])

# ---------------------------------------------------------------- BYLINKY
plodina("bazalka", nazov="Bazalka", rodina="Hluchavkovité", naroky="stredne", typ="bylinka",
        sposoby=["predpestovanie", "sadenice"],
        kal=dict(pred=[4], von=[5, 6], zber=[6, 7, 8, 9]),
        spon="25 cm", hlbka="semeno len pritlačiť (klíči na svetle)",
        tipy=["Veľmi citlivá na chlad – von až keď sú noci teplé.",
              "Obrať vrcholy a kvety, rastlina sa rozkonári."],
        dobri=["paradajky", "papriky"],
        ulohy=[
            U("pred", "04-01", "04-30", "Bazalka: zasej na parapet", "sejba", sposob=PRED, stav=PLAN, potrebujes=["semená bazalky"], nastav="zasiate"),
            U("vys", "05-20", "06-15", "Bazalka: vysaď von (len do tepla)", "vysadba", stav=PLAN_Z, potrebujes=["sadenice bazalky"], nastav="vysadene"),
            U("stip", "06-15", "09-15", "Bazalka: obrať vrcholy, odstrániť kvety", "zber", opak="tyzden"),
        ])

plodina("pazitka", nazov="Pažítka", rodina="Amarylkovité (cesnakovité)", naroky="slabo", typ="bylinka", trvalka=True,
        sposoby=["priama_sejba", "sadenice"],
        kal=dict(pred=[], von=[3, 4], zber=[4, 5, 6, 7, 8, 9, 10]),
        spon="trs 25 cm", hlbka="1 cm",
        tipy=["Strihaj 3–5 cm nad zemou, obrastie.", "Každé 3–4 roky trs rozdeľ."],
        ulohy=[
            U("sejba", "03-20", "04-30", "Pažítka: zasej alebo vysaď trs", "sejba", stav=PLAN, potrebujes=["semená / sadenica pažítky"], nastav="vysadene"),
            U("zber", "04-15", "10-15", "Pažítka: strihaj podľa potreby", "zber", opak="14dni"),
        ])

plodina("kopor", nazov="Kôpor", rodina="Mrkvovité", naroky="slabo", typ="bylinka",
        kal=dict(pred=[], von=[4, 5, 6, 7], zber=[6, 7, 8, 9]),
        spon="riadky 25 cm", hlbka="1 cm",
        tipy=["Sej po troške každé 3 týždne.", "Rád sa sám vysieva."],
        dobri=["uhorky", "kapusta"],
        ulohy=[
            U("sejba", "04-01", "07-15", "Kôpor: zasej ďalšiu várku", "sejba", opak="14dni", sposob=SEM, potrebujes=["semená kôpru"], nastav="zasiate"),
        ])

# ---------------------------------------------------------------- ZELENÉ HNOJENIE
plodina("horcica", nazov="Horčica biela (zelené hnojenie)", rodina="Kapustovité", naroky="slabo", typ="zelene_hnojenie",
        kal=dict(pred=[], von=[4, 5, 8, 9], zber=[]),
        spon="naširoko, asi 2–3 g/m²", hlbka="zahrabať hrabľami, 1–2 cm",
        tipy=["Rastie rýchlo (6–8 týždňov), zakryje pôdu a potlačí burinu.",
              "Pozor: je kapustovitá – nesej ju pred kapustu, kaleráb, brokolicu, reďkovku (kýla kapustová).",
              "Zapraviť pred kvitnutím, alebo nechať na zimu – vymrzne a na jar sa zapraví.",
              "Na piesočnatej pôde dodá organickú hmotu a zadrží živiny cez zimu."],
        ulohy=[
            U("sejba", "08-01", "09-15", "Horčica: rozhoď semeno (2–3 g/m²), zahrabať, zaliať", "sejba", stav=PLAN, potrebujes=["semeno horčice bielej"], nastav="zasiate"),
            U("sejba_j", "04-01", "05-15", "Horčica: jarná sejba na voľný záhon", "sejba", stav=PLAN, potrebujes=["semeno horčice bielej"], nastav="zasiate"),
            U("zapr", "10-01", "11-15", "Horčica: pred kvitnutím pokosiť a zapraviť, alebo nechať vymrznúť", "priprava", stav=["zasiate"]),
        ])

plodina("facelia", nazov="Facélia (zelené hnojenie)", rodina="Facéliovité (nepríbuzná zelenine)", naroky="slabo", typ="zelene_hnojenie",
        kal=dict(pred=[], von=[4, 5, 6, 7, 8], zber=[]),
        spon="naširoko, asi 1–2 g/m²", hlbka="zahrabať hrabľami, 1–2 cm",
        tipy=["Nie je príbuzná žiadnej zelenine – dá sa pred čokoľvek.",
              "Kvitne modro, výborná pre včely.",
              "V zime vymrzne, na jar sa zvyšky zapravia."],
        ulohy=[
            U("sejba", "04-01", "09-05", "Facélia: rozhoď semeno na voľný záhon, zahrabať, zaliať", "sejba", stav=PLAN, potrebujes=["semeno facélie"], nastav="zasiate"),
            U("kos", "06-01", "10-31", "Facélia: pred kvitnutím pokos a zaprav (alebo nechaj kvitnúť pre včely a pokos po odkvitnutí, kým sa nevysemení)", "priprava", stav=["zasiate"]),
        ])

plodina("raz", nazov="Ozimná raž (zelené hnojenie)", rodina="Lipnicovité (trávy)", naroky="slabo", typ="zelene_hnojenie",
        prezimuje=True,
        kal=dict(pred=[], von=[9, 10], zber=[]),
        spon="naširoko, asi 15–20 g/m²", hlbka="zahrabať 2–3 cm",
        tipy=["Najneskoršie zelené hnojenie – sej ešte v októbri.",
              "Prezimuje, pôda je cez zimu krytá, živiny sa nevyplavia (dôležité na piesku).",
              "Na jar pokosiť a zapraviť; drobné semená (mrkva, šalát) sej až o 3 týždne neskôr."],
        ulohy=[
            U("sejba", "09-15", "10-20", "Ozimná raž: rozhoď semeno, zahrabať 2–3 cm", "sejba", stav=PLAN, potrebujes=["osivo ozimnej raže"], nastav="zasiate"),
            U("zapr", "03-20", "04-20", "Raž: pokosiť a zapraviť; drobné semená sej až o 3 týždne", "priprava"),
        ])


# ---------------------------------------------------------------- VŠEOBECNÉ ÚLOHY
# poda: pre ktoré pôdy (None = všetky); ak_plodiny: len ak pestuješ niektorú z nich
def G(id, od, do, text, typ, opak="raz", poda=None, ak_plodiny=None, ak_sposob=None, potrebujes=None):
    return dict(id=id, od=od, do=do, text=text, typ=typ, opak=opak, poda=poda,
                ak_plodiny=ak_plodiny, ak_sposob=ak_sposob, potrebujes=potrebujes or [])


VSEOBECNE = [
    G("plan", "01-05", "02-15", "Naplánuj záhony na sezónu (Plán → striedanie plodín) a spíš semená", "priprava", potrebujes=["semená podľa plánu"]),
    G("substrat", "02-10", "03-10", "Priprav výsevný substrát, misky a miesto na južnom parapete", "priprava", ak_sposob=["predpestovanie"], potrebujes=["výsevný substrát", "misky / kvetináčiky"]),
    G("zapr_zel", "03-10", "04-15", "Ak máš na záhonoch zelené hnojenie z jesene (facélia, horčica): zvyšky pokos a plytko zaprav 2–3 týždne pred sejbou", "priprava"),
    G("ryl_jar", "03-10", "04-20", "Jarné kyprenie / rýľovanie – na piesočnatej pôde až na jar, keď pôda oschne. Zapracuj kompost alebo granulovaný hnoj.", "priprava", poda=["piesocnata"], potrebujes=["kompost alebo granulovaný hnoj"]),
    G("ryl_jar2", "03-15", "04-20", "Jarné urovnanie záhonov: hrudy po jesennom rýľovaní rozbiť hrabľami, zapraviť kompost", "priprava", poda=["hlinita", "ilovita"], potrebujes=["kompost"]),
    G("hnoj_jar", "03-15", "04-30", "Jarné hnojenie: kompost / granulovaný hnoj na záhony, na silne náročné plodiny viac. Minerálne granule (NPK) tesne pred výsadbou, podľa obalu.", "hnojenie", potrebujes=["granulované hnojivo NPK", "granulovaný hnoj"]),
    G("textil", "03-20", "04-30", "Skoré sejby (mrkva, reďkovka, šalát, hrach, špenát) prikry bielou textíliou – rýchlejšie vzídu, chráni pred mrazíkom a muškami", "ochrana", ak_plodiny=["mrkva", "redkovka", "salat", "hrach", "spenat", "petrzlen"], potrebujes=["biela netkaná textília (17–23 g/m²)", "kamene / kolíky na zaťaženie"]),
    G("kompost", "04-01", "04-30", "Kompost: prehodiť; zrelý (tmavý, drobivý) použiť na záhony", "priprava"),
    G("cierna", "04-15", "05-15", "Pred výsadbou teplomilných rastlín polož na záhon čiernu mulčovaciu textíliu (zohreje pôdu, drží vlahu, bez buriny)", "priprava", ak_plodiny=["cukety", "tekvica", "uhorky", "paradajky", "jahody"], potrebujes=["čierna mulčovacia textília (UV stabilizovaná)", "skoby na textíliu"]),
    G("muzi", "05-08", "05-16", "Zamrznutí muži (12.–14. 5.) a Žofia (15. 5.) – teplomilné sadenice ešte nevysádzaj, sleduj predpoveď", "info"),
    G("plev", "05-01", "08-31", "Okopávanie a pletie – malá burina = 10 minút práce", "starostlivost", opak="tyzden"),
    G("mulc", "05-15", "06-15", "Namulčuj záhony (zavädnutá pokosená tráva, slama) – na piesku ušetrí veľa polievania", "starostlivost", poda=["piesocnata"], potrebujes=["slama / pokosená tráva"]),
    G("zel_leto", "07-15", "09-10", "Záhon po zbere (hrach, rané zemiaky, cibuľa, cesnak) nenechaj holý – zasej facéliu alebo horčicu", "sejba", potrebujes=["semeno facélie alebo horčice"]),
    G("zel_jesen", "09-15", "10-20", "Voľné záhony: ešte stihneš ozimnú raž ako zelené hnojenie", "sejba", potrebujes=["osivo ozimnej raže"]),
    G("jes_piesok", "10-01", "11-15", "Na piesku na jeseň neryľuj (živiny sa cez zimu vyplavia). Voľné záhony zakry: zelené hnojenie, lístie, pokosená tráva alebo kompost.", "priprava", poda=["piesocnata"], potrebujes=["lístie / kompost na nastielku"]),
    G("ryl_jes", "10-15", "11-30", "Jesenné rýľovanie do hrubej brázdy – hrudy nerozbíjaj, mráz ich rozdrobí", "priprava", poda=["hlinita", "ilovita"]),
    G("uprat", "10-10", "11-15", "Upratovanie: zdravé zvyšky rastlín na kompost, choré (pleseň, hniloba) nie na kompost", "priprava"),
    G("voda", "10-20", "11-20", "Vypusti hadice a sudy, ulož náradie, vyper a ulož textílie", "priprava"),
    G("vyhodnot", "11-15", "12-31", "Vyhodnoť sezónu v denníku: čo sa darilo, čo nie, kam čo na budúci rok", "priprava"),
]


# ---------------------------------------------------------------- STRIEDANIE (4 skupiny, každý rok o krok ďalej)
# Každá čeľaď je len v jednej skupine, takže sa na rovnaký záhon vráti až po 4 rokoch.
SKUPINY = [
    dict(id=1, nazov="Plodová (ľuľkovité, tekvicovité)", kratko="Plodová", farba="#e57373", naroky="silne",
         plodiny=["paradajky", "papriky", "baklazan", "zemiaky", "uhorky", "uhorky_salat", "cukety", "tekvica", "melon", "kukurica"],
         jesen="nastiel kompost alebo lístie; ak tu je ozimná raž, nechaj ju rásť",
         jar="zapraviť zelené hnojenie, zapracovať veľa kompostu alebo granulovaného hnoja; pod teplomilné položiť čiernu textíliu",
         po="zasej ozimnú raž alebo zakry kompostom"),
    dict(id=2, nazov="Strukoviny a listová", kratko="Strukoviny", farba="#81c784", naroky="slabo",
         plodiny=["fazula", "hrach", "salat", "kopor", "bazalka"],
         jesen="nehnojiť, len nastielka",
         jar="len nakypriť, nehnojiť – fazuľa a hrach si dusík viažu samy",
         po="korene strukovín nechaj v zemi, zasej facéliu (nie horčicu)"),
    dict(id=3, nazov="Kapustovité", kratko="Kapustovité", farba="#64b5f6", naroky="silne",
         plodiny=["kapusta", "brokolica", "kalerab", "redkovka", "horcica"],
         jesen="facélia po strukovinách môže vymrznúť na záhone",
         jar="zapracovať kompost; dusík po strukovinách kapustoviny využijú",
         po="facélia alebo ozimná raž"),
    dict(id=4, nazov="Koreňová a cibuľová", kratko="Koreňová", farba="#ffb74d", naroky="stredne",
         plodiny=["mrkva", "petrzlen", "cvikla", "mangold", "spenat", "cibula", "cesnak", "por"],
         jesen="v októbri sem môžeš vysadiť cesnak",
         jar="bez čerstvého hnoja, len trochu vyzretého kompostu; hlbšie nakypriť pre mrkvu a petržlen",
         po="ozimná raž – na jar sa zapraví spolu s kompostom pred plodovou zeleninou"),
]


def skupina_plodiny(pid):
    for s in SKUPINY:
        if pid in s["plodiny"]:
            return s["id"]
    return None

# rastliny citlivé na mráz (pre upozornenia počasia)
CITLIVE = ["paradajky", "papriky", "baklazan", "uhorky", "uhorky_salat", "cukety", "tekvica", "melon",
           "fazula", "kukurica", "bazalka"]
CITLIVE_JAR = CITLIVE + ["jahody", "zemiaky"]


def zoznam():
    """Krátky zoznam plodín pre výberové polia."""
    return [dict(id=p["id"], nazov=p["nazov"], typ=p["typ"], rodina=p["rodina"], naroky=p["naroky"],
                 trvalka=p["trvalka"], prezimuje=p["prezimuje"], sposoby=p["sposoby"], kal=p["kal"],
                 spon=p.get("spon", ""), hlbka=p.get("hlbka", ""))
            for p in PLODINY.values()]


def detail(pid):
    p = PLODINY.get(pid)
    if not p:
        return None
    d = dict(p)
    d["problemy"] = [dict(nazov=a, text=b) for a, b in p["problemy"]]
    d["dobri"] = [PLODINY[x]["nazov"] for x in p["dobri"] if x in PLODINY]
    d["zli"] = [PLODINY[x]["nazov"] for x in p["zli"] if x in PLODINY]
    return d
