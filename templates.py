"""
Email Templates — Backlink Outreach (Multilingual)
====================================================
7 languages x 9 variants each, with random selection.
Variables available in every template:
  {domain}     — cleaned site name (e.g. GiveMeSport)
  {sender_name}   — name of the sending account
  {topic}         — the niche/topic of the target site

Language is auto-detected from the domain TLD.
Edit variants freely — keep {variables} exactly as written.
"""

import random


def get_site_name(domain: str) -> str:
    """Convert domain to readable site name. e.g. give-me-sport.com -> Give Me Sport"""
    name = domain.split(".")[0]
    name = name.replace("-", " ").replace("_", " ")
    return name.title()


# ══════════════════════════════════════════════════════════════════════════════
# TLD -> LANGUAGE MAPPING
# ══════════════════════════════════════════════════════════════════════════════

TLD_TO_LANGUAGE = {
    "fi": "fi",
    "no": "no",
    "dk": "dk",
    "se": "se",
    "nl": "nl",
    "ro": "ro",
}

# ══════════════════════════════════════════════════════════════════════════════
# TEMPLATES — 7 languages, 9 variants each
# ══════════════════════════════════════════════════════════════════════════════

OUTREACH_TEMPLATES = {

    # ─────────────────────────── ENGLISH ───────────────────────────
    "en": {
        "subject": "Content Collaboration Inquiry",
        "variants": [
            # Variant 1
            """\
Hi,

I hope you're doing well.

While researching websites within the {topic} niche, {domain} was recommended to us as a potential platform for content collaboration.

My name is {sender_name}, and I handle Media Relations at Link Juice Club, an agency based in Malta. We work with a number of online brands and assist them in expanding their visibility through high-quality, reader-focused editorial contributions.

Before proceeding further, I wanted to check whether you are the right person to speak with regarding partnerships or guest contributions on the site.

If so, I'd appreciate learning more about your editorial guidelines and collaboration process.

Looking forward to your response.

Best regards,
{sender_name}
""",
            # Variant 2
            """\
Hi,

I hope all is well on your end.

During our recent research into websites active in the {topic} space, {domain} came up as a publication that could be a great fit for a potential collaboration.

My name is {sender_name}, and I oversee Media Relations at Link Juice Club, an agency based in Malta. Our team works closely with online brands to support their growth through well-crafted editorial content placed on relevant publications.

Before taking the next step, I wanted to confirm whether you are the person responsible for handling partnerships or editorial collaborations for the site.

If so, I would be grateful to learn more about your content guidelines and editorial process.

Best regards,
{sender_name}
""",
            # Variant 3
            """\
Hi,

I hope you're having a good day.

We recently came across {domain} while reviewing reputable websites in the {topic} niche and were interested in exploring a potential content collaboration.

My name is {sender_name}, and I manage Media Relations at Link Juice Club, a Malta-based agency working with online brands to improve their visibility through informative and well-researched editorial content.

Before moving forward, I wanted to confirm whether you oversee content partnerships or guest contributions for the site.

If that's the case, I'd be happy to learn more about your editorial requirements and collaboration guidelines.

Kind regards,
{sender_name}
""",
            # Variant 4
            """\
Hi,

I hope this message finds you well.

While identifying relevant publications in the {topic} niche, {domain} was recommended to us as a possible platform for editorial collaboration.

My name is {sender_name}, and I work with Link Juice Club, a Malta-based agency that supports online brands in expanding their digital presence through quality content partnerships.

Before proceeding, I wanted to check whether you are the appropriate contact for discussing guest contributions or content partnerships on the site.

If so, I'd appreciate the opportunity to learn more about your editorial guidelines and publishing process.

Best regards,
{sender_name}
""",
            # Variant 5
            """\
Hi,

I hope you're well.

As part of our ongoing research into relevant publications within the {topic} sector, we came across {domain} and thought it might be a good fit for a potential editorial collaboration.

My name is {sender_name}, and I lead Media Relations at Link Juice Club in Malta. We partner with online brands to develop and place high-quality editorial content that offers genuine value to readers.

Before exploring this further, I wanted to confirm whether you manage partnerships or guest content opportunities for the website.

If so, I would appreciate any information you can share regarding your editorial guidelines.

Best regards,
{sender_name}
""",
            # Variant 6
            """\
Hi,

I hope everything is going well.

{domain} was recently suggested to us as a relevant publication while researching websites active in the {topic} niche.

My name is {sender_name}, and I'm responsible for Media Relations at Link Juice Club, an agency based in Malta that collaborates with various online brands to help them grow through meaningful editorial partnerships.

Before proceeding, I wanted to check if you handle partnership inquiries and content collaborations for the site.

If that's the case, I'd be glad to learn more about your editorial process and any contribution guidelines you may have.

Kind regards,
{sender_name}
""",
            # Variant 7
            """\
Hi,

I hope you're doing well today.

While reviewing websites within the {topic} niche, {domain} was recommended to us as a potential platform for editorial collaboration.

My name is {sender_name}, and I manage Media Relations at Link Juice Club, a Malta-based agency that works with online brands to strengthen their visibility through carefully developed content contributions.

Before moving forward, I wanted to confirm whether you are the correct person to speak with regarding partnerships and guest contributions for the site.

If so, I would greatly appreciate learning more about your editorial process and any relevant guidelines.

Best regards,
{sender_name}
""",
            # Variant 8
            """\
Hi,

I hope you're doing well.

While researching reputable websites within the {topic} niche, we came across {domain} and thought it could be a good fit for a potential editorial collaboration.

My name is {sender_name}, and I manage Media Relations at Link Juice Club, an agency based in Malta. We work with a range of online brands and help them expand their visibility through carefully developed content contributions that provide genuine value to readers.

Before moving ahead, I wanted to check whether you are the person responsible for handling content partnerships or guest contributions for the site.

If so, I'd be grateful to learn more about your editorial guidelines and collaboration process.

Looking forward to your response.

Best regards,
{sender_name}
""",
            # Variant 9
            """\
Hi,

I hope everything is going well.

{domain} was recently brought to our attention while we were reviewing publications active in the {topic} space. It looks like a great platform for high-quality content contributions.

My name is {sender_name}, and I handle Media Relations at Link Juice Club in Malta. We collaborate with online brands and support their growth through informative, well-researched articles placed on relevant publications.

Before proceeding further, I wanted to confirm whether you manage editorial collaborations or guest contributions for the website.

If that's the case, I'd be happy to learn more about your publishing guidelines and editorial process.

Best regards,
{sender_name}
""",
        ],
    },

    # ─────────────────────────── FINNISH ───────────────────────────
    "fi": {
        "subject": "Yhteistyotiedustelu",
        "variants": [
            # Variant 1
            """\
Hei,

Toivottavasti voit hyvin.

Tutkiessamme {topic} -aihealueen verkkosivustoja, {domain} nousi esiin mahdollisena alustana sisaltoyhteistyolle.

Nimeni on {sender_name}, ja vastaan Media Relations -toiminnoista Link Juice Clubilla, Maltalla toimivassa toimistossa. Teemme yhteistyota useiden verkkobrändien kanssa ja autamme heita kasvattamaan nakyvyyttaan laadukkaan, lukijalahtoisen sisallon avulla.

Ennen kuin etenemme, halusin varmistaa, oletko oikea henkilo keskustelemaan kumppanuuksista tai vierasjulkaisuista sivustolla.

Jos nain on, kuulisin mielelläni lisaa toimituksellisista ohjeistanne ja yhteistyoprosessista.

Ystavallisin terveisin,
{sender_name}
""",
            # Variant 2
            """\
Hei,

Toivottavasti kaikki on hyvin siella.

Viimeaikaisen tutkimuksemme aikana {topic} -aihealueen verkkosivustoista, {domain} nousi esiin julkaisuna, joka voisi sopia hyvin mahdolliseen yhteistyohon.

Nimeni on {sender_name}, ja vastaan Media Relations -toiminnoista Link Juice Clubilla, Maltalla sijaitsevassa toimistossa. Tiimimme tyoskentelee tiiviisti verkkobrändien kanssa ja tukee niiden kasvua laadukkaan toimituksellisen sisallon avulla relevantteihin julkaisuihin.

Ennen kuin etenemme, halusin varmistaa, oletko oikea henkilo vastaamaan kumppanuuksista tai toimituksellisesta yhteistyosta sivustolla.

Jos nain on, kuulisin mielelläni lisaa sisaltoohjeistanne ja toimituksellisesta prosessistanne.

Ystavallisin terveisin,
{sender_name}
""",
            # Variant 3
            """\
Hei,

Toivottavasti sinulla on hyva paiva.

Loysimme hiljattain {domain} -sivuston kartoittaessamme laadukkaita verkkosivustoja {topic} -aihealueella, ja kiinnostuimme mahdollisesta sisaltoyhteistyosta.

Nimeni on {sender_name}, ja vastaan Media Relations -toiminnoista Link Juice Clubilla, Maltalla toimivassa toimistossa. Tyoskentelemme verkkobrändien kanssa ja autamme niita parantamaan nakyvyyttaan informatiivisen ja hyvin tutkitun sisallon avulla.

Ennen kuin etenemme, halusin varmistaa, vastaatko sisaltoyhteistyosta tai vierasjulkaisuista sivustolla.

Jos nain on, kuulisin mielelläni lisaa toimituksellisista vaatimuksistanne ja yhteistyoohjeistanne.

Ystavallisin terveisin,
{sender_name}
""",
            # Variant 4
            """\
Hei,

Toivottavasti tama viesti tavoittaa sinut hyvin.

Etsiessamme relevantteja julkaisuja {topic} -aihealueella, {domain} suositeltiin meille mahdollisena alustana toimitukselliselle yhteistyolle.

Nimeni on {sender_name}, ja työskentelen Link Juice Clubilla, Maltalla sijaitsevassa toimistossa. Autamme verkkobrändeja kasvattamaan digitaalista nakyvyyttaan laadukkaiden sisaltoyhteistoiden kautta.

Ennen kuin etenemme, halusin varmistaa, oletko oikea henkilo keskustelemaan vierasjulkaisuista tai sisaltoyhteistoista sivustolla.

Jos nain on, arvostaisin mahdollisuutta kuulla lisaa toimituksellisista ohjeistanne ja julkaisuprosessistanne.

Ystavallisin terveisin,
{sender_name}
""",
            # Variant 5
            """\
Hei,

Toivottavasti voit hyvin.

Osana jatkuvaa tutkimustamme {topic} -aihealueen julkaisuista, loysimme {domain} -sivuston ja ajattelimme sen sopivan hyvin mahdolliseen toimitukselliseen yhteistyohon.

Nimeni on {sender_name}, ja vastaan Media Relations -toiminnoista Link Juice Clubilla Maltalla. Teemme yhteistyota verkkobrändien kanssa ja tuotamme laadukasta sisaltoa, joka tarjoaa aitoa arvoa lukijoille.

Ennen kuin etenemme pidemmalle, halusin varmistaa, vastaatko kumppanuuksista tai vierassisallosta sivustolla.

Jos nain on, arvostaisin kaikkea tietoa, jonka voit jakaa toimituksellisista ohjeistanne.

Ystavallisin terveisin,
{sender_name}
""",
            # Variant 6
            """\
Hei,

Toivottavasti kaikki sujuu hyvin.

{domain} suositeltiin meille hiljattain, kun tutkimme {topic} -aihealueella toimivia verkkosivustoja.

Nimeni on {sender_name}, ja vastaan Media Relations -toiminnoista Link Juice Clubilla, Maltalla toimivassa toimistossa. Teemme yhteistyota erilaisten verkkobrändien kanssa ja autamme niita kasvamaan merkityksellisten sisaltoyhteistoiden avulla.

Ennen kuin etenemme, halusin varmistaa, kasitteletko kumppanuuskyselyita ja sisaltoyhteistyota sivustolla.

Jos nain on, kuulisin mielelläni lisaa toimituksellisesta prosessistanne ja mahdollisista ohjeistuksista.

Ystavallisin terveisin,
{sender_name}
""",
            # Variant 7
            """\
Hei,

Toivottavasti paivasi sujuu hyvin.

Tarkastellessamme {topic} -aihealueen verkkosivustoja, {domain} suositeltiin meille mahdollisena alustana toimitukselliselle yhteistyolle.

Nimeni on {sender_name}, ja vastaan Media Relations -toiminnoista Link Juice Clubilla, Maltalla sijaitsevassa toimistossa. Tyoskentelemme verkkobrändien kanssa ja autamme niita vahvistamaan nakyvyyttaan huolellisesti tuotetun sisallon avulla.

Ennen kuin etenemme, halusin varmistaa, oletko oikea henkilo keskustelemaan kumppanuuksista ja vierasjulkaisuista sivustolla.

Jos nain on, arvostaisin suuresti lisatietoa toimituksellisesta prosessistanne ja ohjeistuksistanne.

Ystavallisin terveisin,
{sender_name}
""",
            # Variant 8
            """\
Hei,

Toivottavasti voit hyvin.

Tutkiessamme laadukkaita verkkosivustoja {topic} -aihealueella, loysimme {domain} -sivuston ja ajattelimme sen sopivan hyvin mahdolliseen sisaltoyhteistyohon.

Nimeni on {sender_name}, ja vastaan Media Relations -toiminnoista Link Juice Clubilla, Maltalla toimivassa toimistossa. Teemme yhteistyota monien verkkobrändien kanssa ja autamme niita kasvattamaan nakyvyyttaan laadukkaan sisallon avulla, joka tarjoaa todellista arvoa lukijoille.

Ennen kuin etenemme, halusin varmistaa, oletko oikea henkilo kasittelemaan sisaltoyhteistyota tai vierasjulkaisuja sivustolla.

Jos nain on, kuulisin mielelläni lisaa toimituksellisista ohjeistanne ja yhteistyoprosessista.

Odotan vastaustasi.

Ystavallisin terveisin,
{sender_name}
""",
            # Variant 9
            """\
Hei,

Toivottavasti kaikki sujuu hyvin.

{domain} tuli hiljattain esiin, kun tarkastelimme {topic} -aihealueen julkaisuja. Se vaikuttaa erinomaiselta alustalta laadukkaalle sisallolle.

Nimeni on {sender_name}, ja vastaan Media Relations -toiminnoista Link Juice Clubilla Maltalla. Teemme yhteistyota verkkobrändien kanssa ja tuemme niiden kasvua informatiivisten ja hyvin tutkittujen artikkeleiden avulla relevantteihin julkaisuihin.

Ennen kuin etenemme, halusin varmistaa, vastaatko toimituksellisesta yhteistyosta tai vierasjulkaisuista sivustolla.

Jos nain on, kuulisin mielelläni lisaa julkaisuprosessistanne ja ohjeistuksistanne.

Ystavallisin terveisin,
{sender_name}
""",
        ],
    },

    # ─────────────────────────── NORWEGIAN ───────────────────────────
    "no": {
        "subject": "Samarbeidshenvendelse",
        "variants": [
            # Variant 1
            """\
Hei,

Haper du har det bra.

Mens vi undersokte nettsteder innenfor {topic}-nisjen, ble {domain} anbefalt til oss som en potensiell plattform for innholdssamarbeid.

Mitt navn er {sender_name}, og jeg jobber med Media Relations hos Link Juice Club, et byra basert pa Malta. Vi samarbeider med flere nettbaserte merkevarer og hjelper dem med a oke synligheten gjennom kvalitetsinnhold med fokus pa leseren.

For vi gar videre, onsket jeg a bekrefte om du er riktig person a kontakte angaende samarbeid eller gjesteinnlegg pa siden.

Hvis ja, vil jeg gjerne hore mer om deres redaksjonelle retningslinjer og samarbeidsprosess.

Ser frem til a hore fra deg.

Vennlig hilsen,
{sender_name}
""",
            # Variant 2
            """\
Hei,

Haper alt star bra til hos deg.

Under var nylige research pa nettsteder innen {topic}-omradet, dukket {domain} opp som en publikasjon som kan vaere godt egnet for et samarbeid.

Mitt navn er {sender_name}, og jeg har ansvar for Media Relations hos Link Juice Club, et Malta-basert byra. Teamet vart jobber tett med nettbaserte merkevarer for a stotte deres vekst gjennom godt utformet redaksjonelt innhold pa relevante publiseringer.

For vi tar neste steg, onsket jeg a bekrefte om du er personen som handterer partnerskap eller redaksjonelle samarbeid for nettstedet.

Hvis det stemmer, vil jeg gjerne laere mer om deres innholdsretningslinjer og redaksjonelle prosess.

Vennlig hilsen,
{sender_name}
""",
            # Variant 3
            """\
Hei,

Haper du har en fin dag.

Vi kom nylig over {domain} mens vi gjennomgikk anerkjente nettsteder innen {topic}-nisjen, og ble interessert i a utforske et mulig innholdssamarbeid.

Mitt navn er {sender_name}, og jeg jobber med Media Relations hos Link Juice Club, et byra basert pa Malta som samarbeider med nettbaserte merkevarer for a forbedre deres synlighet gjennom informativt og godt researchbasert innhold.

For vi gar videre, onsket jeg a bekrefte om du handterer innholdssamarbeid eller gjesteinnlegg for nettstedet.

Hvis det er tilfelle, vil jeg gjerne hore mer om deres redaksjonelle krav og retningslinjer.

Vennlig hilsen,
{sender_name}
""",
            # Variant 4
            """\
Hei,

Haper denne meldingen finner deg i god form.

Mens vi identifiserte relevante publiseringer innen {topic}-nisjen, ble {domain} anbefalt som en mulig plattform for redaksjonelt samarbeid.

Mitt navn er {sender_name}, og jeg jobber hos Link Juice Club, et Malta-basert byra som hjelper nettbaserte merkevarer med a utvide sin digitale tilstedevaerelse gjennom kvalitetsinnhold og partnerskap.

For vi gar videre, onsket jeg a bekrefte om du er riktig kontaktperson for gjesteinnlegg eller innholdssamarbeid pa nettstedet.

Hvis ja, setter jeg pris pa muligheten til a laere mer om deres redaksjonelle retningslinjer og publiseringsprosess.

Vennlig hilsen,
{sender_name}
""",
            # Variant 5
            """\
Hei,

Haper du har det bra.

Som en del av var pagaende research pa relevante publiseringer innen {topic}-omradet, kom vi over {domain} og tenkte det kunne vaere en god match for et mulig samarbeid.

Mitt navn er {sender_name}, og jeg leder Media Relations hos Link Juice Club i Malta. Vi samarbeider med nettbaserte merkevarer for a utvikle og plassere kvalitetsinnhold som gir reell verdi for leserne.

For vi gar videre, onsket jeg a bekrefte om du handterer partnerskap eller gjesteinnhold for nettstedet.

Hvis det stemmer, vil jeg sette pris pa all informasjon du kan dele om deres redaksjonelle retningslinjer.

Vennlig hilsen,
{sender_name}
""",
            # Variant 6
            """\
Hei,

Haper alt gar bra.

{domain} ble nylig foreslatt for oss mens vi undersokte nettsteder innen {topic}-nisjen.

Mitt navn er {sender_name}, og jeg er ansvarlig for Media Relations hos Link Juice Club, et byra basert pa Malta som samarbeider med ulike nettbaserte merkevarer for a hjelpe dem med a vokse gjennom meningsfulle redaksjonelle samarbeid.

For vi gar videre, onsket jeg a sjekke om du handterer partnerskapshenvendelser og innholdssamarbeid for nettstedet.

Hvis det er tilfelle, vil jeg gjerne hore mer om deres redaksjonelle prosess og eventuelle retningslinjer for bidrag.

Vennlig hilsen,
{sender_name}
""",
            # Variant 7
            """\
Hei,

Haper du har det bra i dag.

Mens vi gjennomgikk nettsteder innen {topic}-nisjen, ble {domain} anbefalt som en potensiell plattform for redaksjonelt samarbeid.

Mitt navn er {sender_name}, og jeg jobber med Media Relations hos Link Juice Club, et Malta-basert byra som hjelper nettbaserte merkevarer med a styrke sin synlighet gjennom noye utviklet innhold.

For vi gar videre, onsket jeg a bekrefte om du er riktig person a kontakte angaende partnerskap og gjesteinnlegg for nettstedet.

Hvis ja, vil jeg sette stor pris pa a laere mer om deres redaksjonelle prosess og retningslinjer.

Vennlig hilsen,
{sender_name}
""",
            # Variant 8
            """\
Hei,

Haper du har det bra.

Mens vi undersokte anerkjente nettsteder innen {topic}-nisjen, kom vi over {domain} og tenkte det kunne vaere en god match for et mulig samarbeid.

Mitt navn er {sender_name}, og jeg jobber med Media Relations hos Link Juice Club, et byra basert pa Malta. Vi samarbeider med en rekke nettbaserte merkevarer og hjelper dem med a oke synligheten gjennom noye utviklet innhold som gir reell verdi for leserne.

For vi gar videre, onsket jeg a bekrefte om du er ansvarlig for innholdssamarbeid eller gjesteinnlegg pa nettstedet.

Hvis det stemmer, vil jeg gjerne hore mer om deres redaksjonelle retningslinjer og samarbeidsprosess.

Ser frem til a hore fra deg.

Vennlig hilsen,
{sender_name}
""",
            # Variant 9
            """\
Hei,

Haper alt star bra til.

{domain} ble nylig gjort kjent for oss da vi gjennomgikk publiseringer innen {topic}-omradet, og det fremstar som en sterk plattform for kvalitetsinnhold.

Mitt navn er {sender_name}, og jeg jobber med Media Relations hos Link Juice Club i Malta. Vi samarbeider med nettbaserte merkevarer og stotter deres vekst gjennom informativt og godt researchbasert innhold pa relevante publiseringer.

For vi gar videre, onsket jeg a bekrefte om du handterer redaksjonelt samarbeid eller gjesteinnlegg for nettstedet.

Hvis det er tilfelle, vil jeg gjerne laere mer om deres publiseringsprosess og retningslinjer.

Vennlig hilsen,
{sender_name}
""",
        ],
    },

    # ─────────────────────────── DANISH ───────────────────────────
    "dk": {
        "subject": "Samarbejdshenvendelse",
        "variants": [
            # Variant 1
            """\
Hej,

Jeg haber, du har det godt.

Mens vi researchede websites inden for {topic}-nichen, blev {domain} anbefalet til os som en potentiel platform for indholdssamarbejde.

Mit navn er {sender_name}, og jeg star for Media Relations hos Link Juice Club, et bureau baseret pa Malta. Vi arbejder med en raekke online brands og hjaelper dem med at oge deres synlighed gennem kvalitetsindhold med fokus pa laeseren.

Inden vi gar videre, vil jeg gerne bekraefte, om du er den rette person at kontakte vedrorende partnerskaber eller gaesteindlaeg pa siden.

Hvis det er tilfaeldet, vil jeg saette pris pa at hore mere om jeres redaktionelle retningslinjer og samarbejdsproces.

Ser frem til at hore fra dig.

Med venlig hilsen,
{sender_name}
""",
            # Variant 2
            """\
Hej,

Jeg haber, alt er vel hos dig.

Under vores seneste research af websites inden for {topic}-omradet, dukkede {domain} op som en publikation, der kunne vaere et godt match for et samarbejde.

Mit navn er {sender_name}, og jeg er ansvarlig for Media Relations hos Link Juice Club, et Malta-baseret bureau. Vores team arbejder taet sammen med online brands for at understotte deres vaekst gennem veludarbejdet redaktionelt indhold pa relevante publikationer.

Inden vi tager naeste skridt, vil jeg gerne bekraefte, om du er ansvarlig for partnerskaber eller redaktionelle samarbejder pa siden.

Hvis det er tilfaeldet, vil jeg meget gerne hore mere om jeres content guidelines og redaktionelle proces.

Med venlig hilsen,
{sender_name}
""",
            # Variant 3
            """\
Hej,

Jeg haber, du har en god dag.

Vi stodte for nylig pa {domain}, mens vi gennemgik anerkendte websites inden for {topic}-nichen, og blev interesserede i at udforske et muligt indholdssamarbejde.

Mit navn er {sender_name}, og jeg star for Media Relations hos Link Juice Club, et Malta-baseret bureau, der arbejder med online brands for at forbedre deres synlighed gennem informativt og velresearchet indhold.

Inden vi gar videre, vil jeg gerne bekraefte, om du handterer content partnerships eller gaesteindlaeg for siden.

Hvis det er tilfaeldet, vil jeg gerne hore mere om jeres redaktionelle krav og retningslinjer.

Med venlig hilsen,
{sender_name}
""",
            # Variant 4
            """\
Hej,

Jeg haber, denne besked finder dig vel.

Mens vi identificerede relevante publikationer inden for {topic}-nichen, blev {domain} anbefalet til os som en mulig platform for redaktionelt samarbejde.

Mit navn er {sender_name}, og jeg arbejder hos Link Juice Club, et Malta-baseret bureau, der hjaelper online brands med at udvide deres digitale tilstedevaerelse gennem kvalitetsbaserede content partnerships.

Inden vi gar videre, vil jeg gerne bekraefte, om du er den rette kontaktperson for gaesteindlaeg eller indholdssamarbejder pa siden.

Hvis ja, vil jeg saette pris pa muligheden for at hore mere om jeres redaktionelle retningslinjer og publiceringsproces.

Med venlig hilsen,
{sender_name}
""",
            # Variant 5
            """\
Hej,

Jeg haber, du har det godt.

Som en del af vores lobende research af relevante publikationer inden for {topic}-omradet, stodte vi pa {domain} og taenkte, at det kunne vaere et godt match for et muligt samarbejde.

Mit navn er {sender_name}, og jeg leder Media Relations hos Link Juice Club i Malta. Vi samarbejder med online brands om at udvikle og placere kvalitetsindhold, der skaber reel vaerdi for laeserne.

Inden vi gar videre, vil jeg gerne bekraefte, om du handterer partnerskaber eller gaesteindhold pa siden.

Hvis det er tilfaeldet, vil jeg saette pris pa den information, du kan dele om jeres redaktionelle retningslinjer.

Med venlig hilsen,
{sender_name}
""",
            # Variant 6
            """\
Hej,

Jeg haber, alt gar godt.

{domain} blev for nylig foreslaget til os, mens vi undersogte websites inden for {topic}-nichen.

Mit navn er {sender_name}, og jeg er ansvarlig for Media Relations hos Link Juice Club, et bureau baseret pa Malta, som samarbejder med forskellige online brands for at hjaelpe dem med at vokse gennem meningsfulde redaktionelle samarbejder.

Inden vi gar videre, vil jeg gerne hore, om du handterer partnerhenvendelser og indholdssamarbejde for siden.

Hvis det er tilfaeldet, vil jeg gerne hore mere om jeres redaktionelle proces og eventuelle retningslinjer for bidrag.

Med venlig hilsen,
{sender_name}
""",
            # Variant 7
            """\
Hej,

Jeg haber, du har det godt i dag.

Mens vi gennemgik websites inden for {topic}-nichen, blev {domain} anbefalet som en potentiel platform for redaktionelt samarbejde.

Mit navn er {sender_name}, og jeg star for Media Relations hos Link Juice Club, et Malta-baseret bureau, der arbejder med online brands for at styrke deres synlighed gennem noje udviklet indhold.

Inden vi gar videre, vil jeg gerne bekraefte, om du er den rette person at kontakte vedrorende partnerskaber og gaesteindlaeg pa siden.

Hvis ja, vil jeg saette stor pris pa at hore mere om jeres redaktionelle proces og retningslinjer.

Med venlig hilsen,
{sender_name}
""",
            # Variant 8
            """\
Hej,

Jeg haber, du har det godt.

Mens vi researchede anerkendte websites inden for {topic}-nichen, stodte vi pa {domain} og taenkte, at det kunne vaere et godt match for et muligt samarbejde.

Mit navn er {sender_name}, og jeg star for Media Relations hos Link Juice Club, et bureau baseret pa Malta. Vi arbejder med en bred vifte af online brands og hjaelper dem med at oge deres synlighed gennem noje udviklet indhold, der skaber reel vaerdi for laeserne.

Inden vi gar videre, vil jeg gerne bekraefte, om du er ansvarlig for content partnerships eller gaesteindlaeg pa siden.

Hvis det er tilfaeldet, vil jeg meget gerne hore mere om jeres redaktionelle retningslinjer og samarbejdsproces.

Ser frem til at hore fra dig.

Med venlig hilsen,
{sender_name}
""",
            # Variant 9
            """\
Hej,

Jeg haber, alt er vel.

{domain} blev for nylig gjort opmaerksom pa os, mens vi gennemgik publikationer inden for {topic}-omradet, og det fremstar som en staerk platform for kvalitetsindhold.

Mit navn er {sender_name}, og jeg star for Media Relations hos Link Juice Club i Malta. Vi samarbejder med online brands og understotter deres vaekst gennem informativt og velresearchet indhold pa relevante publikationer.

Inden vi gar videre, vil jeg gerne bekraefte, om du handterer redaktionelle samarbejder eller gaesteindlaeg for siden.

Hvis det er tilfaeldet, vil jeg meget gerne hore mere om jeres publiceringsproces og retningslinjer.

Med venlig hilsen,
{sender_name}
""",
        ],
    },

    # ─────────────────────────── SWEDISH ───────────────────────────
    "se": {
        "subject": "Samarbetsforfragan",
        "variants": [
            # Variant 1
            """\
Hej,

Hoppas att du mar bra.

Nar vi undersokte webbplatser inom {topic}-nischen rekommenderades {domain} till oss som en mojlig plattform for innehallssamarbete.

Jag heter {sender_name} och ansvarar for Media Relations pa Link Juice Club, en Malta-baserad byra. Vi arbetar med flera onlinevarumarken och hjalper dem att oka sin synlighet genom kvalitativt och lasarvanligt innehall.

Innan vi gar vidare ville jag bekrafta om du ar ratt person att kontakta gallande samarbeten eller gastinlagg pa sidan.

Om sa ar fallet skulle jag garna vilja veta mer om era redaktionella riktlinjer och samarbetsprocess.

Ser fram emot ditt svar.

Vanliga halsningar,
{sender_name}
""",
            # Variant 2
            """\
Hej,

Hoppas att allt ar bra hos dig.

Under var senaste research kring webbplatser inom {topic}-omradet dok {domain} upp som en publikation som kan vara en bra match for ett samarbete.

Jag heter {sender_name} och ansvarar for Media Relations pa Link Juice Club, en Malta-baserad byra. Vart team arbetar nara onlinevarumarken for att stodja deras tillvaxt genom valskrivet redaktionellt innehall pa relevanta publikationer.

Innan vi tar nasta steg ville jag bekrafta om du ansvarar for partnerskap eller redaktionella samarbeten pa sidan.

Om sa ar fallet skulle jag uppskatta att fa veta mer om era innehallsriktlinjer och redaktionella process.

Vanliga halsningar,
{sender_name}
""",
            # Variant 3
            """\
Hej,

Hoppas att du har en bra dag.

Vi stotte nyligen pa {domain} nar vi gick igenom valrenommerade webbplatser inom {topic}-nischen och blev intresserade av att utforska ett mojligt innehallssamarbete.

Jag heter {sender_name} och arbetar med Media Relations pa Link Juice Club, en Malta-baserad byra som samarbetar med onlinevarumarken for att forbattra deras synlighet genom informativt och valresearchat innehall.

Innan vi gar vidare ville jag bekrafta om du hanterar innehallssamarbeten eller gastinlagg for sidan.

Om det stammer skulle jag garna vilja veta mer om era redaktionella krav och riktlinjer.

Vanliga halsningar,
{sender_name}
""",
            # Variant 4
            """\
Hej,

Hoppas att detta meddelande nar dig val.

Nar vi identifierade relevanta publikationer inom {topic}-nischen rekommenderades {domain} till oss som en mojlig plattform for redaktionellt samarbete.

Jag heter {sender_name} och arbetar pa Link Juice Club, en Malta-baserad byra som hjalper onlinevarumarken att expandera sin digitala narvaro genom kvalitativa innehallssamarbeten.

Innan vi gar vidare ville jag bekrafta om du ar ratt kontaktperson for gastinlagg eller innehallssamarbeten pa sidan.

Om sa ar fallet skulle jag uppskatta mojligheten att fa veta mer om era redaktionella riktlinjer och publiceringsprocess.

Vanliga halsningar,
{sender_name}
""",
            # Variant 5
            """\
Hej,

Hoppas att du mar bra.

Som en del av var pagaende research kring relevanta publikationer inom {topic}-omradet stotte vi pa {domain} och tankte att det kunde vara en bra match for ett mojligt samarbete.

Jag heter {sender_name} och leder Media Relations pa Link Juice Club i Malta. Vi samarbetar med onlinevarumarken for att skapa och placera kvalitativt innehall som ger verkligt varde till lasarna.

Innan vi gar vidare ville jag bekrafta om du hanterar partnerskap eller gastinnehall for webbplatsen.

Om sa ar fallet skulle jag uppskatta all information du kan dela om era redaktionella riktlinjer.

Vanliga halsningar,
{sender_name}
""",
            # Variant 6
            """\
Hej,

Hoppas att allt gar bra.

{domain} rekommenderades nyligen till oss nar vi undersokte webbplatser inom {topic}-nischen.

Jag heter {sender_name} och ansvarar for Media Relations pa Link Juice Club, en Malta-baserad byra som samarbetar med olika onlinevarumarken for att hjalpa dem att vaxa genom meningsfulla redaktionella samarbeten.

Innan vi gar vidare ville jag kontrollera om du hanterar forfragningar om partnerskap och innehallssamarbeten for webbplatsen.

Om sa ar fallet skulle jag garna vilja veta mer om er redaktionella process och eventuella riktlinjer for bidrag.

Vanliga halsningar,
{sender_name}
""",
            # Variant 7
            """\
Hej,

Hoppas att du mar bra idag.

Nar vi gick igenom webbplatser inom {topic}-nischen rekommenderades {domain} som en potentiell plattform for redaktionellt samarbete.

Jag heter {sender_name} och arbetar med Media Relations pa Link Juice Club, en Malta-baserad byra som hjalper onlinevarumarken att starka sin synlighet genom noggrant utvecklat innehall.

Innan vi gar vidare ville jag bekrafta om du ar ratt person att kontakta gallande partnerskap och gastinlagg for webbplatsen.

Om sa ar fallet skulle jag verkligen uppskatta att fa veta mer om er redaktionella process och riktlinjer.

Vanliga halsningar,
{sender_name}
""",
            # Variant 8
            """\
Hej,

Hoppas att du mar bra.

Nar vi undersokte valrenommerade webbplatser inom {topic}-nischen stotte vi pa {domain} och tankte att det kunde vara en bra match for ett mojligt samarbete.

Jag heter {sender_name} och ansvarar for Media Relations pa Link Juice Club, en Malta-baserad byra. Vi arbetar med ett brett utbud av onlinevarumarken och hjalper dem att oka sin synlighet genom noggrant utvecklat innehall som ger verkligt varde till lasarna.

Innan vi gar vidare ville jag bekrafta om du ansvarar for innehallssamarbeten eller gastinlagg pa webbplatsen.

Om sa ar fallet skulle jag garna vilja veta mer om era redaktionella riktlinjer och samarbetsprocess.

Ser fram emot ditt svar.

Vanliga halsningar,
{sender_name}
""",
            # Variant 9
            """\
Hej,

Hoppas att allt ar bra.

{domain} uppmarksammades nyligen av oss nar vi gick igenom publikationer inom {topic}-omradet, och det verkar vara en stark plattform for kvalitativt innehall.

Jag heter {sender_name} och arbetar med Media Relations pa Link Juice Club i Malta. Vi samarbetar med onlinevarumarken och stodjer deras tillvaxt genom informativa och valresearchade artiklar pa relevanta publikationer.

Innan vi gar vidare ville jag bekrafta om du hanterar redaktionella samarbeten eller gastinlagg for webbplatsen.

Om sa ar fallet skulle jag garna vilja veta mer om er publiceringsprocess och riktlinjer.

Vanliga halsningar,
{sender_name}
""",
        ],
    },

    # ─────────────────────────── DUTCH ───────────────────────────
    "nl": {
        "subject": "Samenwerkingsverzoek",
        "variants": [
            # Variant 1
            """\
Hallo,

Ik hoop dat het goed met je gaat.

Tijdens ons onderzoek naar websites binnen de {topic}-niche werd {domain} aan ons aanbevolen als een mogelijk platform voor content samenwerking.

Mijn naam is {sender_name} en ik ben verantwoordelijk voor Media Relations bij Link Juice Club, een bureau gevestigd in Malta. Wij werken met verschillende online merken en helpen hen hun zichtbaarheid te vergroten via hoogwaardige, lezergerichte content.

Voordat we verder gaan, wilde ik graag bevestigen of jij de juiste persoon bent om te spreken over samenwerkingen of gastbijdragen op de website.

Als dat zo is, hoor ik graag meer over jullie redactionele richtlijnen en samenwerkingsproces.

Ik kijk uit naar je reactie.

Met vriendelijke groet,
{sender_name}
""",
            # Variant 2
            """\
Hallo,

Ik hoop dat alles goed gaat aan jouw kant.

Tijdens ons recente onderzoek naar websites binnen de {topic}-sector kwam {domain} naar voren als een publicatie die goed zou kunnen passen bij een mogelijke samenwerking.

Mijn naam is {sender_name} en ik ben verantwoordelijk voor Media Relations bij Link Juice Club, een bureau gevestigd in Malta. Ons team werkt nauw samen met online merken om hun groei te ondersteunen via goed geschreven redactionele content op relevante platforms.

Voordat we de volgende stap zetten, wilde ik graag bevestigen of jij verantwoordelijk bent voor partnerships of redactionele samenwerkingen op de website.

Als dat zo is, hoor ik graag meer over jullie contentrichtlijnen en redactionele proces.

Met vriendelijke groet,
{sender_name}
""",
            # Variant 3
            """\
Hallo,

Ik hoop dat je een fijne dag hebt.

We kwamen onlangs {domain} tegen tijdens het bekijken van gerenommeerde websites binnen de {topic}-niche en waren geinteresseerd in het verkennen van een mogelijke content samenwerking.

Mijn naam is {sender_name} en ik beheer Media Relations bij Link Juice Club, een in Malta gevestigd bureau dat samenwerkt met online merken om hun zichtbaarheid te verbeteren via informatieve en goed onderbouwde content.

Voordat we verder gaan, wilde ik bevestigen of jij verantwoordelijk bent voor content partnerships of gastbijdragen op de website.

Als dat zo is, hoor ik graag meer over jullie redactionele vereisten en richtlijnen.

Met vriendelijke groet,
{sender_name}
""",
            # Variant 4
            """\
Hallo,

Ik hoop dat dit bericht je goed bereikt.

Tijdens het identificeren van relevante publicaties binnen de {topic}-niche werd {domain} aan ons aanbevolen als een mogelijk platform voor redactionele samenwerking.

Mijn naam is {sender_name} en ik werk bij Link Juice Club, een Malta-gebaseerd bureau dat online merken helpt hun digitale aanwezigheid te vergroten via kwalitatieve content partnerships.

Voordat we verder gaan, wilde ik graag bevestigen of jij de juiste contactpersoon bent voor gastbijdragen of content samenwerkingen op de website.

Als dat zo is, hoor ik graag meer over jullie redactionele richtlijnen en publicatieproces.

Met vriendelijke groet,
{sender_name}
""",
            # Variant 5
            """\
Hallo,

Ik hoop dat het goed met je gaat.

Als onderdeel van ons lopende onderzoek naar relevante publicaties binnen de {topic}-sector kwamen we {domain} tegen en dachten we dat het een goede match zou kunnen zijn voor een mogelijke samenwerking.

Mijn naam is {sender_name} en ik leid Media Relations bij Link Juice Club in Malta. Wij werken samen met online merken om kwalitatieve content te ontwikkelen en te plaatsen die echte waarde biedt aan lezers.

Voordat we verder gaan, wilde ik bevestigen of jij verantwoordelijk bent voor partnerships of gastcontent op de website.

Als dat zo is, zou ik het waarderen als je meer kunt delen over jullie redactionele richtlijnen.

Met vriendelijke groet,
{sender_name}
""",
            # Variant 6
            """\
Hallo,

Ik hoop dat alles goed gaat.

{domain} werd onlangs aan ons voorgesteld terwijl we onderzoek deden naar websites binnen de {topic}-niche.

Mijn naam is {sender_name} en ik ben verantwoordelijk voor Media Relations bij Link Juice Club, een bureau gevestigd in Malta dat samenwerkt met verschillende online merken om hun groei te ondersteunen via waardevolle redactionele samenwerkingen.

Voordat we verder gaan, wilde ik graag controleren of jij verantwoordelijk bent voor partnership aanvragen en content samenwerkingen op de website.

Als dat zo is, hoor ik graag meer over jullie redactionele proces en eventuele richtlijnen voor bijdragen.

Met vriendelijke groet,
{sender_name}
""",
            # Variant 7
            """\
Hallo,

Ik hoop dat het goed met je gaat vandaag.

Tijdens het bekijken van websites binnen de {topic}-niche werd {domain} aan ons aanbevolen als een mogelijke partner voor redactionele samenwerking.

Mijn naam is {sender_name} en ik beheer Media Relations bij Link Juice Club, een Malta-gebaseerd bureau dat online merken helpt hun zichtbaarheid te versterken via zorgvuldig ontwikkelde content.

Voordat we verder gaan, wilde ik graag bevestigen of jij de juiste persoon bent om te spreken over partnerships en gastbijdragen op de website.

Als dat zo is, hoor ik graag meer over jullie redactionele proces en richtlijnen.

Met vriendelijke groet,
{sender_name}
""",
            # Variant 8
            """\
Hallo,

Ik hoop dat het goed met je gaat.

Tijdens ons onderzoek naar gerenommeerde websites binnen de {topic}-niche kwamen we {domain} tegen en dachten we dat het een goede match zou kunnen zijn voor een mogelijke samenwerking.

Mijn naam is {sender_name} en ik ben verantwoordelijk voor Media Relations bij Link Juice Club, een bureau gevestigd in Malta. Wij werken met diverse online merken en helpen hen hun zichtbaarheid te vergroten via zorgvuldig ontwikkelde content die echte waarde biedt aan lezers.

Voordat we verder gaan, wilde ik graag bevestigen of jij verantwoordelijk bent voor content partnerships of gastbijdragen op de website.

Als dat zo is, hoor ik graag meer over jullie redactionele richtlijnen en samenwerkingsproces.

Ik kijk uit naar je reactie.

Met vriendelijke groet,
{sender_name}
""",
            # Variant 9
            """\
Hallo,

Ik hoop dat alles goed gaat.

{domain} werd onlangs onder onze aandacht gebracht terwijl we publicaties binnen de {topic}-sector bekeken, en het lijkt een sterk platform voor kwalitatieve content.

Mijn naam is {sender_name} en ik ben verantwoordelijk voor Media Relations bij Link Juice Club in Malta. Wij werken samen met online merken en ondersteunen hun groei via informatieve en goed onderbouwde artikelen op relevante platforms.

Voordat we verder gaan, wilde ik bevestigen of jij verantwoordelijk bent voor redactionele samenwerkingen of gastbijdragen op de website.

Als dat zo is, hoor ik graag meer over jullie publicatieproces en richtlijnen.

Met vriendelijke groet,
{sender_name}
""",
        ],
    },

    # ─────────────────────────── ROMANIAN ───────────────────────────
    "ro": {
        "subject": "Solicitare de colaborare",
        "variants": [
            # Variant 1
            """\
Buna,

Sper ca esti bine.

In timp ce cercetam site-uri din nisa {topic}, {domain} ne-a fost recomandat ca o posibila platforma pentru colaborari de continut.

Numele meu este {sender_name} si ma ocup de Media Relations la Link Juice Club, o agentie cu sediul in Malta. Colaboram cu mai multe branduri online si le ajutam sa isi creasca vizibilitatea prin continut editorial de calitate, orientat catre cititori.

Inainte de a continua, as vrea sa confirm daca tu esti persoana potrivita pentru a discuta despre parteneriate sau contributii tip guest post pe site.

Daca da, mi-ar face placere sa aflu mai multe despre ghidurile voastre editoriale si procesul de colaborare.

Astept cu interes raspunsul tau.

Cu stima,
{sender_name}
""",
            # Variant 2
            """\
Buna,

Sper ca totul este in regula la tine.

In cadrul cercetarii noastre recente asupra site-urilor din domeniul {topic}, {domain} a aparut ca o publicatie care ar putea fi potrivita pentru o posibila colaborare.

Numele meu este {sender_name} si coordonez Media Relations la Link Juice Club, o agentie din Malta. Echipa noastra colaboreaza indeaproape cu branduri online pentru a le sustine cresterea prin continut editorial bine realizat, publicat pe platforme relevante.

Inainte de a face urmatorul pas, as vrea sa confirm daca tu te ocupi de parteneriate sau colaborari editoriale pentru site.

Daca da, as aprecia sa aflu mai multe despre ghidurile voastre de continut si procesul editorial.

Cu stima,
{sender_name}
""",
            # Variant 3
            """\
Buna,

Sper ca ai o zi buna.

Am descoperit recent {domain} in timp ce analizam site-uri de incredere din nisa {topic} si am fost interesati sa exploram o posibila colaborare de continut.

Numele meu este {sender_name} si ma ocup de Media Relations la Link Juice Club, o agentie din Malta care colaboreaza cu branduri online pentru a le imbunatati vizibilitatea prin continut informativ si bine documentat.

Inainte de a continua, as vrea sa confirm daca tu te ocupi de colaborari de continut sau articole guest pentru site.

Daca da, mi-ar face placere sa aflu mai multe despre cerintele si ghidurile voastre editoriale.

Cu stima,
{sender_name}
""",
            # Variant 4
            """\
Buna,

Sper ca acest mesaj te gaseste bine.

In timp ce identificam publicatii relevante din nisa {topic}, {domain} ne-a fost recomandat ca o posibila platforma pentru colaborare editoriala.

Numele meu este {sender_name} si lucrez la Link Juice Club, o agentie din Malta care ajuta brandurile online sa isi extinda prezenta digitala prin parteneriate de continut de calitate.

Inainte de a continua, as vrea sa confirm daca tu esti persoana de contact potrivita pentru a discuta despre guest post-uri sau colaborari de continut pe site.

Daca da, as aprecia oportunitatea de a afla mai multe despre ghidurile voastre editoriale si procesul de publicare.

Cu stima,
{sender_name}
""",
            # Variant 5
            """\
Buna,

Sper ca esti bine.

Ca parte a cercetarii noastre continue asupra publicatiilor relevante din domeniul {topic}, am descoperit {domain} si am considerat ca ar putea fi potrivit pentru o posibila colaborare editoriala.

Numele meu este {sender_name} si coordonez Media Relations la Link Juice Club in Malta. Colaboram cu branduri online pentru a crea si publica continut de calitate care ofera valoare reala cititorilor.

Inainte de a continua, as vrea sa confirm daca tu te ocupi de parteneriate sau continut guest pentru site.

Daca da, as aprecia orice informatie pe care o poti impartasi despre ghidurile voastre editoriale.

Cu stima,
{sender_name}
""",
            # Variant 6
            """\
Buna,

Sper ca totul merge bine.

{domain} ne-a fost recomandat recent in timp ce cercetam site-uri din nisa {topic}.

Numele meu este {sender_name} si sunt responsabil de Media Relations la Link Juice Club, o agentie din Malta care colaboreaza cu diverse branduri online pentru a le ajuta sa creasca prin colaborari editoriale relevante.

Inainte de a continua, as vrea sa verific daca tu te ocupi de solicitarile de parteneriat si colaborarile de continut pentru site.

Daca da, mi-ar face placere sa aflu mai multe despre procesul vostru editorial si eventualele ghiduri pentru contributii.

Cu stima,
{sender_name}
""",
            # Variant 7
            """\
Buna,

Sper ca esti bine astazi.

In timp ce analizam site-uri din nisa {topic}, {domain} ne-a fost recomandat ca o posibila platforma pentru colaborare editoriala.

Numele meu este {sender_name} si ma ocup de Media Relations la Link Juice Club, o agentie din Malta care ajuta brandurile online sa isi consolideze vizibilitatea prin continut atent dezvoltat.

Inainte de a continua, as vrea sa confirm daca tu esti persoana potrivita pentru a discuta despre parteneriate si articole guest pentru site.

Daca da, as aprecia sa aflu mai multe despre procesul vostru editorial si ghiduri.

Cu stima,
{sender_name}
""",
            # Variant 8
            """\
Buna,

Sper ca esti bine.

In timp ce cercetam site-uri de incredere din nisa {topic}, am descoperit {domain} si am considerat ca ar putea fi potrivit pentru o posibila colaborare.

Numele meu este {sender_name} si ma ocup de Media Relations la Link Juice Club, o agentie din Malta. Colaboram cu o gama variata de branduri online si le ajutam sa isi creasca vizibilitatea prin continut atent realizat, care ofera valoare reala cititorilor.

Inainte de a continua, as vrea sa confirm daca tu esti responsabil pentru colaborari de continut sau articole guest pe site.

Daca da, mi-ar face placere sa aflu mai multe despre ghidurile voastre editoriale si procesul de colaborare.

Astept cu interes raspunsul tau.

Cu stima,
{sender_name}
""",
            # Variant 9
            """\
Buna,

Sper ca totul este in regula.

{domain} ne-a fost adus recent in atentie in timp ce analizam publicatii din domeniul {topic} si pare a fi o platforma solida pentru continut de calitate.

Numele meu este {sender_name} si ma ocup de Media Relations la Link Juice Club in Malta. Colaboram cu branduri online si le sustinem cresterea prin articole informative si bine documentate publicate pe platforme relevante.

Inainte de a continua, as vrea sa confirm daca tu te ocupi de colaborari editoriale sau articole guest pentru site.

Daca da, mi-ar face placere sa aflu mai multe despre procesul vostru de publicare si ghiduri.

Cu stima,
{sender_name}
""",
        ],
    },
}


# ══════════════════════════════════════════════════════════════════════════════
# PUBLIC API
# ══════════════════════════════════════════════════════════════════════════════

def get_language(domain: str) -> str:
    """Detect language from TLD. Falls back to English."""
    tld = domain.rsplit(".", 1)[-1].lower()
    return TLD_TO_LANGUAGE.get(tld, "en")


def get_template(topic: str, domain: str = "") -> dict:
    """Return a random {subject, body} for the domain's language."""
    lang = get_language(domain)
    lang_data = OUTREACH_TEMPLATES[lang]
    body = random.choice(lang_data["variants"])
    return {"subject": lang_data["subject"], "body": body}

def _build_signature(name: str, email: str) -> str:
      """Return a plain-text signature block for the given sender."""
      return (
                "--\n"
                f"{name}\n"
                "Account Manager | Link Juice Club\n"
                "Website: https://www.linkjuiceclub.com\n"
                f"Email: {email}"
      )
  
def render(template: dict, domain: str, sender_name: str, sender_email: str, topic: str = "") -> tuple[str, str]:
    """Fill in variables and return (subject, body).
    Note: sender_email is accepted for backward compatibility but not used
    in the body (signature is handled by Outlook)."""
    site_name = get_site_name(domain)
    variables = {
        "domain":       domain,
        "site_name":    site_name,
        "sender_name":  sender_name,
        "sender_email": sender_email,
        "topic":        topic,
    }
    subject = template["subject"].format(**variables)
    body    = template["body"].format(**variables)
      body = body + "\n\n" + _build_signature(sender_name, sender_email)
    return subject, body
