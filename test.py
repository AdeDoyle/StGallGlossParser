"""Level 1."""

from functools import lru_cache
from Pickle import open_obj, save_obj
from OpenXlsx import list_xlsx
from Clean_Glosses import clean_gloss, clean_word
import re


glossdict = open_obj("Clean_GlossDict.pkl")
glosslist = open_obj("Gloss_List.pkl")
worddict = open_obj("Clean_WordDict.pkl")
wordslist = open_obj("Words_List.pkl")
analyses = list_xlsx("SG. Combined Data", "Sheet 1")


def clean_analysis():
    pass


noA1 = list()
testA1 = list()
noA2 = list()
testA2 = list()
noA3 = list()
testA3 = list()

POS_list = ["AF", "BR", "CPL", "AID", "FRA", "ALT", "TSP", "DBR", "RFH", "CN", "NOD", "MBR",
            "UMR", "INT", "SNL", "BRS", "PNC"]

lastnum = False
for i in analyses:
    glossnum = i[0]
    word = worddict.get(i[1])
    A1 = i[3]
    A2 = i[4]
    A3 = i[5]
    vb_actpas = i[6]
    vb_rel = i[7]
    if not A1:
        noA1.append(i)
    elif A1.strip() not in testA1:
        testA1.append(A1.strip())
    # output = [word, A1, A2, A3, vb_actpas, vb_actpas]
    # if glossnum == lastnum:
    #     print(output)
    # else:
    #     lastnum = glossnum
    # print(output)

testlist = sorted(list(set(testA1)))
print("Entries, no A1: {}".format(len(noA1)))
print("Unique A1 Types: {}".format(len(testlist)))
for i in testlist:
    print(i)

