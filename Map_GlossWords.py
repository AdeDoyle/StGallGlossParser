"""
   Find all consecutive pos-tagged words in each gloss

   Use above to isolate OI material

   Split glosses into gloss-lists on non-OI material

   Match tokenisation of OI material in gloss-lists to words

   Implement appropriate spacing in gloss-lists based on tokenisation

   Sequence gloss-lists
"""

from Clean_ExcelLists import create_data_combo
from Pickle import open_obj
from OpenXlsx import list_xlsx
from Clean_Glosses import clean_gloss, clean_word, clean_lemma
from Reassign_POS import clean_analysis, clean_onetag, create_glosslist, create_wordlist


try:
    analyses = list_xlsx("SG. Combined Data", "Sheet 1")
except FileNotFoundError:
    print(create_data_combo())
    analyses = list_xlsx("SG. Combined Data", "Sheet 1")
# # Run the functions below to create the following .pkl files from spreadsheet, "SG. Combined Data"
try:
    glosslist = open_obj("Gloss_List.pkl")
    wordslist = open_obj("Words_List.pkl")
except FileNotFoundError:
    print(create_glosslist(analyses))
    print(create_wordlist(analyses))
    glosslist = open_obj("Gloss_List.pkl")
    wordslist = open_obj("Words_List.pkl")


# Map a word-separated gloss from the Hofman corpus to a list of POS-tagged words from the Bauer corpus
# gloss = TPH reference, cleaned gloss, translation, word_data_list
# word_data_list = cleaned word, cleaned headword, 5-part analysis and word translation/meaning
def map_glosswords(gloss, word_data_list):
    gloss_ref = gloss[0]
    glosstext = clean_gloss(gloss[1])
    glosstrans = gloss[2]
    glosshand = gloss[3]
    pos_gloss = [gloss_ref, glosstext, glosstrans, glosshand]
    pos_analysis = list()
    for word_data in word_data_list:
        word = clean_word(word_data[0])
        headword = clean_lemma(word_data[1])
        word_analysis = clean_onetag(word_data[2])
        word_pos = clean_analysis(word_analysis)
        pos_analysis.append([word, headword, f"<{word_pos}>"])
    pos_gloss.append(pos_analysis)
    return pos_gloss


# #                                             TEST FUNCTIONS

# print(map_glosswords(glosslist[1], wordslist[1]))

# for i, gloss in enumerate(glosslist[:9]):
#     wordlist = wordslist[i]
#     pos_data = map_glosswords(gloss, wordlist)
#     print(f"{[pos_data[0], pos_data[1], pos_data[2]]}\n{pos_data[3]}")

