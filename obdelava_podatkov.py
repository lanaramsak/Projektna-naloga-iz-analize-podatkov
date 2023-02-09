from ast import Break
import re
import orodja
import json
import csv

def zajem_spletne_strani(st_oddelkov):
    for i in range(st_oddelkov):
        url = ("https://www.nepremicnine.net/oglasi-prodaja/slovenija/hisa/{index:}/").format(index = i)
        ime_datoteke = f"imenik/stran_{i}"
        orodja.shrani_spletno_stran(url, ime_datoteke)

vzorec_bloka = re.compile(
    r'<div class="oglas_container oglasbold oglasi\d*"(.*?)</div>',
    flags=re.DOTALL
)

vzorec_oglasa_cena = re.compile(r'<span> ?(?:Izklicna cena: ?|max.|do )?(?:cca )?(?P<cena>(?:\d{0,3}.)?(?:\d{1,3}.)?\d{0,3},\d{2}) .(?P<enota>/m2)?')

vzorec_oglasa_lokacija = re.compile(
    r'<div class=\"more_info\">.*?Regija: (?P<regija>.*?) \| '
    r'Upravna enota: (?P<upravna>.*) \| '
    r'Občina: (?P<obcina>.*?)'
    r'</div><div class=\"main-data\">',
    flags=re.DOTALL
)

vzorec_oglasa_podatki = re.compile(
    r'(?P<povrsina>\d{0,3}(?:,\d{0,2})?) m2, (?P<gradnja>samostojna|dvojček|vrstna|dvostanovanjska|trojček|hiša|atrijska),',
    flags=re.DOTALL
)

vzorec_oglasa_podatki_blok = re.compile(
    r'<div class=\"kratek\" itemprop=\"description\">.*?</strong>, (.*?)'
    r'</div>',
    flags=re.DOTALL
)

vzorec_leto_gradnja = re.compile(r'(?:zgrajen[a,o,i,e]?|zgr\.|gradnje) l\. (?P<leto>\d{4})', flags=re.DOTALL)
vzorec_leto_adaptacija = re.compile(r'adaptiran[a,e,i,o,u]? l\. (?P<leto>\d{4})', flags=re.DOTALL)

def preveri_zajem_oglasov(st_oddelkov):
    nisem_nasel = []
    for i in range(st_oddelkov):
        stejem = 0
        ime_datoteke = f"imenik/stran_{i}"
        vsebina = orodja.vsebina_datoteke(ime_datoteke)
        for stevilka, blok in enumerate(vzorec_bloka.finditer(vsebina)):
            stejem += 1
            seznam = re.findall(r"<a class=\"slika\" href=\"(.*?)\"><img class=\"lazyload\"", blok.group(0), flags=re.DOTALL)
            datoteka = f"imenik2/hisa_{i, stevilka}"
            celoten_url = "https://www.nepremicnine.net" + seznam[0]
            orodja.shrani_spletno_stran(celoten_url, datoteka)
            oglas = orodja.vsebina_datoteke(datoteka)
            txt = re.findall(vzorec_oglasa_podatki_blok, oglas)[0]
            seznam2 = re.findall(vzorec_leto_gradnja, txt)
            print(seznam2)
            if seznam2 == []:
                print("")
                print("OJOJ NISEM NAŠEL NEČESAR")
                print("")
                nisem_nasel.append(celoten_url)
        print("")
        print(f"Grem na novo stran, po pregledanih {stejem} oglasov")
        print("")
    print(nisem_nasel)
    print(len(nisem_nasel))



def zajem_oglasov(st_oddelkov):
    hise = []
    for i in range(st_oddelkov):
        ime_datoteke = f"imenik/stran_{i}"
        vsebina = orodja.vsebina_datoteke(ime_datoteke)
        for stevilka, blok in enumerate(vzorec_bloka.finditer(vsebina)):
            url = re.findall(r"<a class=\"slika\" href=\"(.*?)\"><img class=\"lazyload\"", blok.group(0), flags=re.DOTALL)
            datoteka = f"imenik2/hisa_{i, stevilka}"
            celoten_url = "https://www.nepremicnine.net" + url[0]
            orodja.shrani_spletno_stran(celoten_url, datoteka)
            id_hise = url[0][-8:-1]
            hisa = orodja.vsebina_datoteke(datoteka)
            slovar_oglas = zajem_podatkov(hisa)
            slovar_oglas["id"] = int(id_hise)
            hise.append(slovar_oglas)
    return hise

#nekateri oglasi nimajo podanega leta
def iscem_leto(txt, vzorec):
    leto = re.search(vzorec, txt)
    return leto.groupdict()

def zajem_podatkov(stran):
    slovar = {}
    #je bolje imeti tako, kjer lahko najde več zadetkov in se potem povozi, ali spodnja možnost ki vzame le prvo kar najde
    for najdeno in vzorec_oglasa_cena.finditer(stran):
        slovar_cena = najdeno.groupdict()
        slovar.update(slovar_cena)

    for najdeno in re.finditer(vzorec_oglasa_lokacija, stran):
        slovar_lokacije = najdeno.groupdict()
        slovar.update(slovar_lokacije)

    #vzame le del besedila, kjer so zbrani naslednji podatki
    besedilo = re.search(vzorec_oglasa_podatki_blok, stran)[0]
    #zaenkrat sem zajela tako leto adaptacij, kot leto izgradnje, ob obdelav podatkov, bom ugotovila kaj je boljše za obdelavo
    leto_gradnje = vzorec_leto_gradnja.search(besedilo)
    if leto_gradnje:
        slovar["leto_gradnje"] = leto_gradnje["leto"]
    else:
        slovar["leto_gradnje"] = None
    leto_adaptacije = vzorec_leto_adaptacija.search(besedilo)
    if leto_adaptacije:
        slovar["leto_adaptacije"] = leto_adaptacije["leto"]
    else:
        slovar["leto_adaptacije"] = None

    najdeno = vzorec_oglasa_podatki.search(besedilo)
    slovar_podatki = najdeno.groupdict()
    slovar.update(slovar_podatki)    
    print(slovar)
    urejen_slovar = ureditev_podatkov(slovar)
    print(urejen_slovar)
    return urejen_slovar

def ureditev_podatkov(slovar):
    slovar["cena"] = float(slovar["cena"].replace(".", "").replace(",", "."))
    if slovar["leto_gradnje"] != None:
        slovar["leto_gradnje"] = int(slovar["leto_gradnje"])
    if slovar["leto_adaptacije"] != None:
        slovar["leto_adaptacije"] = int(slovar["leto_adaptacije"])
    slovar["povrsina"] = float(slovar["povrsina"].replace(".", "").replace(",", "."))
    if slovar["enota"] != None:
        slovar["cena"] = slovar["povrsina"] * slovar["cena"]
    slovar.pop("enota")
    return slovar


st_oddelkov = 108
hise = zajem_oglasov(st_oddelkov)
with open("hise.json", "w") as dat:
    json.dump(hise, dat, indent=4, ensure_ascii=False)

with open("hise.csv", "w") as dat:
    writer = csv.DictWriter(dat, [
        "id", 
        "cena",
        "regija",
        "upravna",
        "obcina",
        "leto_gradnje",
        "leto_adaptacije",
        "povrsina",
        "gradnja",  
    ])
    writer.writeheader()
    writer.writerows(hise)
