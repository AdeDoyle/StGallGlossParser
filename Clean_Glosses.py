"""Level 2."""

from OpenXlsx import list_xlsx
from functools import lru_cache
import re
from Pickle import save_obj


@lru_cache(maxsize=3500)
def clean_gloss(gloss):
    """Takes a gloss and removes all instances of tags or undesirable characters within the gloss"""
    # removes all unnecessary tags and tag content
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
    remset = ("/", "·", "(m.d.)", "(m.i.)", "(m.i.:)", "(m.i.m.l.)", "(m.l.)", "(m. l.)", "(m.l.extr.)", "(m.s.)",
              "(subs.)", "(script. ogamica)", "(scriptura ogamica)", "(scriptura oghamica)", ":", "*", "+", "(?)")
    for rem in remset:
        if rem in gloss:
            gloss = "".join(gloss.split(rem))
    bracpat = re.compile(r'\(cf\. .*\)')
    bracpatitir = bracpat.finditer(gloss)
    for i in bracpatitir:
        gloss = "".join(gloss.split(i.group()))
    bracpat = re.compile(r'[\[\{]{1,2}[\d ]*[\]\}]{1,2}')
    bracpatitir = bracpat.finditer(gloss)
    for i in bracpatitir:
        gloss = "".join(gloss.split(i.group()))
    numpat = re.compile(r'\d{2,10}')
    numpatitir = numpat.finditer(gloss)
    for i in numpatitir:
        gloss = "".join(gloss.split(i.group()))
    # remove all double spacing and spacing at gloss beginning/end
    if "  " in gloss:
        while "  " in gloss:
            gloss = " ".join(gloss.split("  "))
    gloss = gloss.strip()
    return gloss


# # Clean all glosses in the SG. corpus, print each gloss (original, then clean)
# # Count all unique (cleaned) glosses
# sgData = list_xlsx("SG. Combined Data", "Sheet 1")
# lastgloss = ""
# glcount = 0
# for i in sgData:
#     thisgloss = clean_gloss(i[8])
#     if thisgloss != lastgloss:
#         print(i[8])
#         print(thisgloss)
#         lastgloss = thisgloss
#         glcount += 1
# print(glcount)


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

