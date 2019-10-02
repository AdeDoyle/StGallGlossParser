"""Level 2."""

from OpenXlsx import list_xlsx
from functools import lru_cache
import re
from Pickle import save_obj


testlist = list()


@lru_cache(maxsize=3500)
def clean_gloss(gloss, lowercase=False):
    """Takes a gloss and removes all instances of tags or undesirable characters within the gloss"""
    # removes all unnecessary tags and tag content
    if lowercase:
        gloss = gloss.lower()
    tagset = ("term", "gloss", "del", "ex", "add", "supplied", "i", "g")
    for tag in tagset:
        optag = "<{}>".format(tag)
        cltag = "</{}>".format(tag)
        if tag == "term":
            if optag in gloss:
                for i in range(gloss.count(optag)):
                    startpos = gloss.find(optag)
                    endpos = gloss.find(cltag) + len(cltag)
                    gloss = gloss[:startpos] + gloss[endpos:]
        if tag == "gloss":
            if optag in gloss:
                for i in range(gloss.count(optag)):
                    startpos = gloss.find(optag) + len(optag)
                    endpos = gloss.find(cltag)
                    gloss = gloss[startpos:endpos]
        if tag == "del":
            if optag in gloss:
                for i in range(gloss.count(optag)):
                    startpos = gloss.find(optag)
                    endpos = gloss.find(cltag) + len(cltag)
                    gloss = gloss[:startpos] + gloss[endpos:]
        if tag == "g":
            if optag in gloss:
                for i in range(gloss.count(optag)):
                    startpos = gloss.find(optag)
                    endpos = gloss.find(cltag) + len(cltag)
                    gloss = gloss[:startpos] + gloss[endpos:]
        if tag not in ("term", "gloss", "del", "g"):
            gloss = "".join(gloss.split(optag))
            gloss = "".join(gloss.split(cltag))
    if "<" in gloss:
        for i in range(gloss.count("<")):
            startpos = gloss.find("<")
            endpos = gloss.find(">") + 1
            gloss = gloss[:startpos] + gloss[endpos:]
    # remove all characters/strings not necessary in gloss
    remset = ("/", "·", ":", "*", "+", "--", ",.", ".,", ",", "..-", ".-", "?", '"', "|", "┼", "↑", "↓", "┤", "├", "¹",
              "Û", "(m.d.)", "(m.i.)", "(m.l.)", "(m. l.)", "(subs.)")
    if lowercase:
        remset = ("/", "·", ":", "*", "+", "--", ",.", ".,", ",", "..-", ".-", "?", '"', "|", "┼", "↑", "↓", "┤", "├",
                  "¹", "û", "(m.d.)", "(m.i.)", "(m.l.)", "(m. l.)", "(subs.)")
    for rem in remset:
        if rem in gloss:
            gloss = "".join(gloss.split(rem))
    # if "-" in gloss:
    #     gloss = " ".join(gloss.split("-"))
    # greekpat = re.compile(r'\.?[αιλμοπρςστυω]+\.?')
    # greekpatitir = greekpat.finditer(gloss)
    # for i in greekpatitir:
    #     gloss = "".join(gloss.split(i.group()))
    bracpat = re.compile(r'\(cf\. .*\)')
    bracpatitir = bracpat.finditer(gloss)
    for i in bracpatitir:
        gloss = "".join(gloss.split(i.group()))
    bracpat = re.compile(r'^\(.*\)')
    bracpatitir = bracpat.finditer(gloss.strip())
    for i in bracpatitir:
        gloss = "".join(gloss.split(i.group()))
    bracpat = re.compile(r'\(.*\)$')
    bracpatitir = bracpat.finditer(gloss.strip())
    for i in bracpatitir:
        gloss = "".join(gloss.split(i.group()))
    bracpat = re.compile(r'\(.*\)')
    bracpatitir = bracpat.finditer(gloss)
    for i in bracpatitir:
        gloss = gloss[i.end():]
    bracpat = re.compile(r'[\[\{]{1,2}[\d ]*[\]\}]{1,2}')
    bracpatitir = bracpat.finditer(gloss)
    for i in bracpatitir:
        gloss = "".join(gloss.split(i.group()))
    alt_bracks = ["[", "]", "{", "}"]
    for i in alt_bracks:
        if i in gloss:
            gloss = "".join(gloss.split(i))
    numpat = re.compile(r'\d{2,10}')
    numpatitir = numpat.finditer(gloss)
    for i in numpatitir:
        gloss = "".join(gloss.split(i.group()))
    # removes unwanted full stops
    abbrevlist = [".i.", " .i.", ".i. ", " .i. "]
    abbrevpat = re.compile(r' \.[a-záéíóúA-ZÁÉÍÓÚαιλμοπρςστυω]+\. ')
    # abbrevpat = re.compile(r' \.[a-záéíóúA-ZÁÉÍÓÚ]+\. ')
    abbrevpatitir = abbrevpat.finditer(gloss)
    for i in abbrevpatitir:
        abbrev = i.group()
        if abbrev not in abbrevlist:
            abbrev = "".join(abbrev.split("."))
            abbrev = abbrev.strip()
            gloss = abbrev.join(gloss.split(".{}.".format(abbrev)))
    # must be run twice for instances like " .is. .m. " in gloss 136a27 (10025-10040, in SG. Combined Data)
    abbrevpatitir = abbrevpat.finditer(gloss)
    for i in abbrevpatitir:
        abbrev = i.group()
        if abbrev not in abbrevlist:
            abbrev = "".join(abbrev.split("."))
            abbrev = abbrev.strip()
            gloss = abbrev.join(gloss.split(".{}.".format(abbrev)))
    abbrevpat = re.compile(r' \.[a-záéíóúA-ZÁÉÍÓÚ]+\.$')
    abbrevpatitir = abbrevpat.finditer(gloss)
    for i in abbrevpatitir:
        abbrev = i.group()
        if abbrev not in abbrevlist:
            abbrev = "".join(abbrev.split("."))
            abbrev = abbrev.strip()
            gloss = abbrev.join(gloss.split(".{}.".format(abbrev)))
    abbrevpat = re.compile(r'^\.[a-záéíóúA-ZÁÉÍÓÚ]+\. ')
    abbrevpatitir = abbrevpat.finditer(gloss)
    for i in abbrevpatitir:
        abbrev = i.group()
        if abbrev not in abbrevlist:
            abbrev = "".join(abbrev.split("."))
            abbrev = abbrev.strip()
            gloss = abbrev.join(gloss.split(".{}.".format(abbrev)))
    fspat = re.compile(r'.{0,5}[^.][^i]\.+$')
    fspatitir = fspat.finditer(gloss.strip())
    for i in fspatitir:
        stopstring = i.group()
        nostopstring = "".join(stopstring.split("."))
        gloss = nostopstring.join(gloss.split(stopstring))
    fspat = re.compile(r'^\.+[^i][^.].{0,5}')
    fspatitir = fspat.finditer(gloss.strip())
    for _ in fspatitir:
        gloss = gloss[:gloss.find(".")] + gloss[gloss.find(".") + 1:]
    # replace incorrect characters with appropriate alternatives
    if "7" in gloss:
        gloss = "⁊".join(gloss.split("7"))
    dotdict = {"m": "ṁ", "t": "ṫ", "ä": "a", "ü": "u"}
    overdotpat = re.compile(r'\ẇ')
    overdotpatitir = overdotpat.finditer(gloss)
    for i in overdotpatitir:
        replet = i.group()
        let = replet[0]
        replacement = dotdict.get(let)
        gloss = replacement.join(gloss.split(replet))
    overdotpat = re.compile(r'[äü]')
    overdotpatitir = overdotpat.finditer(gloss)
    for i in overdotpatitir:
        replet = i.group()
        let = replet[0]
        replacement = dotdict.get(let)
        gloss = replacement.join(gloss.split(replet))
    # remove all double spacing and spacing at gloss beginning/end
    if "  " in gloss:
        while "  " in gloss:
            gloss = " ".join(gloss.split("  "))
    gloss = gloss.strip()
    return gloss


# # Pick spreadsheet to draw glosses from (for all testing)
# sgData = list_xlsx("SG. Combined Data", "Sheet 1")

# # Print a single cleaned gloss from the combined data spreadsheet
# testgloss = sgData[10025]
# print(clean_gloss(testgloss[8]))

# # Clean all glosses in the SG. corpus, print each gloss (original, then clean)
# # Count all unique (cleaned) glosses
# lastgloss = ""
# glcount = 0
# cleaned_glosses = list()
# for i in sgData:
#     thisgloss = clean_gloss(i[8])
#     if thisgloss != lastgloss:
#         cleaned_glosses.append(thisgloss)
#         # print(i[8])
#         # print("{}: {}".format(i[0], thisgloss))
#         lastgloss = thisgloss
#         glcount += 1
# print(glcount)

# # Print a sorted list of all characters in the cleaned St. Gall corpus
# all_chars = list(set("".join(cleaned_glosses)))
# print(sorted(all_chars))
# print(len(all_chars))
# # for i in testlist:
# #     print(i)

# # Print a sorted list of all selected sub-strings in the cleaned St. Gall corpus
# print(len(testlist))
# all_subs = sorted(list(set(testlist)))
# # print(all_subs)
# print(len(all_subs))
# list1 = list()
# list2 = list()
# for i in all_subs:
#     print(i)
#     # li = i.split("-")
#     # list1.append(li[0])
#     # list2.append(li[1])
# # print(testlist)
# # allpres = sorted(list(set(list1)))
# # print(len(allpres))
# # for i in allpres:
# #     print(i)
# # allposts = sorted(list(set(list2)))
# # print(len(allposts))
# # for i in allposts:
# #     print(i)


# # Save a dictionary of glosses with keys = original gloss, and values = cleaned gloss
# sgData = list_xlsx("SG. Combined Data", "Sheet 1")
# glosslist = list()
# lastgloss = ""
# for i in sgData:
#     thisgloss = i[8]
#     if thisgloss != lastgloss:
#         glosslist.append(thisgloss)
#         lastgloss = thisgloss
# glossdict = {}
# for i in glosslist:
#     glossdict[i] = clean_gloss(i)
# save_obj("Cleaned_Glosses", glossdict)

