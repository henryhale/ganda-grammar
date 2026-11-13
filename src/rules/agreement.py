"""Agreement: an adjective or possessive right after a noun takes the noun's class prefix.

Only after the nouns listed here, whose class is certain. A prefix alone isn't enough: eki-/obu-/ama- also start
relative verbs (ekisinga obunene) and ordinary verbs (amanyi = he knows).
"""
from .base import APOSTROPHES, Edit
from .elision import TRIGGERS

SRC = "Sternefeld & Sseguya, A Luganda Grammar (2015)"
RULES = {
    "AGREE_ADJ": ("an adjective takes its noun's class: ebintu ekirungi → ebintu ebirungi", f"{SRC}, §7"),
    "AGREE_POSS": ("a possessive takes its noun's class: ebitabo kyange → ebitabo byange", f"{SRC}, §6"),
}


def _pairs(sg, pl, stems):
    """Nouns of a singular/plural class pair: eki + tabo = ekitabo, eky + alo = ekyalo before a vowel."""
    glide = {"i": "y", "u": "w"}
    return {(pre[:-1] + glide[pre[-1]] if s[0] in "aeiou" else pre) + s: cls
            for s in stems.split() for cls, pre in (sg, pl)}


NOUNS = {
    **_pairs(("7", "eki"), ("8", "ebi"), """ntu fo biina seera tongole tundu gambo buga zibu ragiro rwadde faananyi
        binja gendererwa zimbe rabo wandiiko tabo kopo saawe bonerezo teeso rowoozo senge tone kwekweto rooto buuzo
        banja sanja rungo gere tanda muli bira go nnya kolwa ka alo uma ambalo"""),
    **_pairs(("12", "aka"), ("14", "obu"), """kiiko lulu wuka tale bonero benje tambi tabo baga kodyo faananyi piira
        sente waayiro ti solya yumba ntu papula zannyo goye veera wunga gaali wale sawo tebe buga sozi saale cupa
        pande motoka duuka kebe seera"""),
    **dict.fromkeys("""obulamu obugagga obwakabaka obukulembeze obujulizi obubaka obukuumi obusobozi obwenkanya
        obulwadde obuvunaanyizibwa""".split(), "14"),
    **dict.fromkeys("""olunaku olugendo olusozi olulimi oluggi olubuto olupapula olugoye olutalo oluyimba oluguudo
        olukiiko olusuku olususu olukalala olugero olubiri oluzzi olunyiriri olwazi""".split(), "11"),
    # Not loanwords with e + double consonant (essanduuko, essimu, ebbaluwa, ekkanisa, eggaali): they are class 9
    **dict.fromkeys("""erinnya eriiso ejjinja essomero eddoboozi ettooke eggwanga ekkubo eggye eggi etteeka essaza
        eddagala ettendekero ekkomera essomo eddwaliro""".split(), "5"),
    **dict.fromkeys("""amannya amaaso amayinja amasomero amaloboozi amatooke amawanga amakubo amagye amagi amateeka
        amasaza amalagala amatendekero amakomera amasomo amalwaliro amazzi amata amafuta amaanyi amagezi amawulire
        amaka amaziga amazima""".split(), "6"),
}

# Adjective prefixes with the augment (§7). Class 5 is left out: its forms are irregular (eddene, eddungi, eribi).
ADJ_PREFIX = {"7": "eki", "8": "ebi", "12": "aka", "14": "obu", "11": "olu", "6": "ama"}
ADJ_STEMS = "nene lungi bi kulu tono to nafu siru lalu lamu kadde gezi mpi gazi zito ddugavu myufu kalu bisi tuufu ngi pya"


def adjective(cls, stem):
    pre = ADJ_PREFIX[cls]
    return pre + ("r" + stem[1:] if pre.endswith("i") and stem[0] == "l" else stem)  # ki + lungi = kirungi


# Forms that can be wrong after a noun of another class. Not obu- forms, which are also adverbs (akola obulungi),
# nor forms that are also nouns: akatono 'a little', akabi 'danger', akakadde 'million', amakulu 'meaning',
# amato 'boats', amagezi 'wisdom'.
WRONG_ADJ = {adjective(c, s): (c, s) for c in ADJ_PREFIX for s in ADJ_STEMS.split() if c != "14"}
for w in "akatono akabi akakadde amakulu amato amagezi".split():
    del WRONG_ADJ[w]

# Possessive prefixes before the stem's a (§6). Classes 1 and 2 are left out: wange, bange are also vocatives.
POSS_PREFIX = {"3": "gw", "4": "gy", "5": "ly", "6": "g", "7": "ky", "8": "by", "9": "y", "10": "z", "11": "lw",
               "12": "k", "13": "tw", "14": "bw", "15": "kw"}


def possessive(cls, stem):
    pre = POSS_PREFIX[cls]
    return pre + (stem[1:] if stem == "aabwe" and pre[-1] in "wy" else stem)  # kyabwe but gaabwe (§1.1.6)


POSS = {POSS_PREFIX[c] + s: (c, "aabwe" if s == "abwe" else s)
        for c in POSS_PREFIX for s in ("ange", "affe", "ammwe", "aabwe", "abwe")}


def edits(text, toks):
    out = []
    for prev, a, b in zip([None] + toks, toks, toks[1:]):
        cls = NOUNS.get(a.text[0].lower() + a.text[1:])
        # Skip y'ekibuga ebirungi and bya ekibiina ebirungi: the adjective may belong to an earlier noun.
        if (not cls or a.end == b.start or text[a.end:b.start].strip(" \t")
                or (a.start and text[a.start - 1] in APOSTROPHES + "-")
                or (prev and prev.text.lower() in TRIGGERS)):
            continue
        if (hit := WRONG_ADJ.get(b.text)) and hit[0] != cls and cls in ADJ_PREFIX:
            out.append(Edit("AGREE_ADJ", b.start, b.end, b.text, adjective(cls, hit[1])))
        elif (hit := POSS.get(b.text)) and hit[0] != cls:
            out.append(Edit("AGREE_POSS", b.start, b.end, b.text, possessive(cls, hit[1])))
    return out
