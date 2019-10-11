"""Level 2."""

from OpenXlsx import list_xlsx
from functools import lru_cache
import re
from Pickle import save_obj


testlist = list()


@lru_cache(maxsize=3500)
def clean_gloss(gloss, lowercase=False, ellipses=True, rem_hyphen=False, rem_greek=False):
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
    # remove hyphens if explicitly stated as function argument
    if rem_hyphen:
        if "-" in gloss:
            gloss = " ".join(gloss.split("-"))
    # remove greek characters if explicitly stated as function argument
    if rem_greek:
        greekpat = re.compile(r'\.?[αιλμοπρςστυω]+\.?')
        greekpatitir = greekpat.finditer(gloss)
        for i in greekpatitir:
            gloss = "".join(gloss.split(i.group()))
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
    # removes/replaces unwanted full stops with ellipses or blank spaces as required
    ellipat = re.compile(r'(?<!\.i)\.[ \.]*\.(?!i\.)')
    ellipatitir = ellipat.finditer(gloss)
    if ellipses:
        elreplace = "…"
    else:
        elreplace = ""
    for _ in ellipatitir:
        gloss = ellipat.sub(elreplace, gloss)
        break
    stopat = re.compile(r'(?<!\.i)\.(?!i\.)')
    stopatitir = stopat.finditer(gloss)
    for _ in stopatitir:
        gloss = stopat.sub("", gloss)
        break
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


@lru_cache(maxsize=3500)
def clean_word(gloss, lowercase=False, ellipses=True, rem_hyphen=False, rem_greek=False):
    """Takes a word and removes all instances of tags or undesirable characters within the it"""
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
    # remove all characters/strings not necessary in gloss
    remset = ("<", ">", "/", "·", ":", "*", "+", "--", ",.", ".,", ",", "..-", ".-", "?", '"', "|", "┼", "↑", "↓", "┤",
              "├", "¹", "Û", "(m.d.)", "(m.i.)", "(m.l.)", "(m. l.)", "(subs.)")
    if lowercase:
        remset = ("<", ">", "/", "·", ":", "*", "+", "--", ",.", ".,", ",", "..-", ".-", "?", '"', "|", "┼", "↑", "↓",
                  "┤", "├", "¹", "û", "(m.d.)", "(m.i.)", "(m.l.)", "(m. l.)", "(subs.)")
    for rem in remset:
        if rem in gloss:
            gloss = "".join(gloss.split(rem))
    # remove hyphens if explicitly stated as function argument
    if rem_hyphen:
        if "-" in gloss:
            gloss = " ".join(gloss.split("-"))
    # remove greek characters if explicitly stated as function argument
    if rem_greek:
        greekpat = re.compile(r'\.?[αιλμοπρςστυω]+\.?')
        greekpatitir = greekpat.finditer(gloss)
        for i in greekpatitir:
            gloss = "".join(gloss.split(i.group()))
    bracpat = re.compile(r'\(cf\. .*\)')
    bracpatitir = bracpat.finditer(gloss)
    for i in bracpatitir:
        gloss = "".join(gloss.split(i.group()))
    bracpat = re.compile(r'\(.*\)')
    bracpatitir = bracpat.finditer(gloss)
    for _ in bracpatitir:
        gloss = "".join(gloss.split("("))
        gloss = "".join(gloss.split(")"))
        break
    bracpat = re.compile(r' \[leg\..*\]')
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
    # removes/replaces unwanted full stops with ellipses or blank spaces as required
    ellipat = re.compile(r'(?<!\.i)\.[ \.]*\.(?!i\.)')
    ellipatitir = ellipat.finditer(gloss)
    if ellipses:
        elreplace = "…"
    else:
        elreplace = ""
    for _ in ellipatitir:
        gloss = ellipat.sub(elreplace, gloss)
        break
    stopat = re.compile(r'(?<!\.i)\.(?!i\.)')
    stopatitir = stopat.finditer(gloss)
    for _ in stopatitir:
        gloss = stopat.sub("", gloss)
        break
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
# testgloss = sgData[14890]
# print(clean_gloss(testgloss[8]))

# # Clean all glosses in the SG. corpus, print each gloss (original, then clean)
# # Count all unique (cleaned) glosses
# lastgloss = ""
# glcount = 0
# cleaned_glosses = list()
# for i in sgData:
#     # thisgloss = clean_gloss(i[8], lowercase=True, rem_greek=True, rem_hyphen=True)
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


# # Save a dictionary of glosses with: keys = original gloss; and values = cleaned gloss
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
# save_obj("Clean_GlossDict", glossdict)


# # Print a gloss, a given word from it, and that word after cleaning for comparison
# sgData = list_xlsx("SG. Combined Data", "Sheet 1")
# for i in sgData[:]:
#     thisword = i[1]
#     if thisword:
#         cleaned = clean_word(thisword)
#         if thisword != cleaned:
#             # print(i)
#             print(thisword)
#             print(cleaned)
#             print()
#         # print(thisword)
#         # print(clean_word(thisword))
#         # print()


# # Save a dictionary of words with: keys = original word; and values = cleaned word
# sgData = list_xlsx("SG. Combined Data", "Sheet 1")
# wordlist = list()
# for i in sgData:
#     thisword = i[1]
#     if thisword:
#         if thisword not in wordlist:
#             wordlist.append(thisword)
# worddict = {}
# for i in wordlist:
#     worddict[i] = clean_word(i)
# save_obj("Clean_WordDict", worddict)

