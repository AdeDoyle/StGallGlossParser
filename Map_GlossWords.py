"""Level ."""

"""
   Clean POS tags from Bernhard's to Standard
   
   Find all consecutive cleaned words in each gloss

   Use above to isolate OI material

   Split glosses into gloss-lists on non-OI material

   Match tokenisation of OI material in gloss-lists to words

   Implement appropriate spacing in gloss-lists based on tokenisation

   Sequence gloss-lists
"""

from functools import lru_cache
from Pickle import open_obj, save_obj
from OpenXlsx import list_xlsx
from Clean_Glosses import clean_gloss, clean_word

# glossdict = open_obj("Clean_GlossDict.pkl")
# glosslist = open_obj("Gloss_List.pkl")
# worddict = open_obj("Clean_WordDict.pkl")
# wordslist = open_obj("Words_List.pkl")
analyses = list_xlsx("SG. Combined Data", "Sheet 1")


def map_glosswords(gloss, wordlist):
    glosstext = clean_gloss(gloss)
    for word in wordlist:
        cleanword = clean_word(word)
    return glosstext


# print(map_glosswords(glosslist[0], wordlist))


gloss_replist = ('æ', 'ɫ', 'ǽ')
# replace_in_gloss = {'ae' :'æ', ['no', 'nó', 'vel', ...?]: 'ɫ', 'áe': 'ǽ'}


# # Test the first and last word of each analysis match the first and last word of their associated gloss
# for i in range(len(wordslist)):
#     clwd = (clean_word(wordslist[i][-1], lowercase=True))
#     clgl = clean_gloss(glosslist[i], lowercase=True)
#     if clwd not in clgl:
#         # if clwd not in ('con', 'ínna', 'cí', 'coibnestai', 'ɫ', 'dobriathra', 'fen', 'fo', 'altoir', 'ecóir',
#         #                 'ind', 'roschaill', 'cia', 'to', 'doṡuidigthi', 'tindrem', 'cuithe', 'clethecháin',
#         #                 'comairmith', 'nephairmith', 'húas', 'nícon', 'cenéle', 'neph-', '⁊', 'iar micniar'):
#         if clwd not in ('n-í', 'n-dule', 'ṅ-guttae', 'doruarthatar', 'n-naue', 'ɫ', 'lethguthaigthi',
#                         'dorochuirsemmar', 'fuit', 'ṅ-digaim', 'aranecatar', 'ṡainriuth', 'ṅdi', 'medóndai',
#                         'coibnestai', 'naci', 'ṅ-etha', 'oíndai', 'ndonaithchuiredar', 'fen', 'n-ai', 'con',
#                         'ṅ-affracdai', 'folad', 'altoir', '-ni', 'n-dechur', 'ṅ-diles', 'folaid', 'n-doacaldmaichi',
#                         'n-dechraiged', 'n-déainmmneichtech', 'n-dílsi', 'nacomlatar', 'huanainmnigter',
#                         'huanainmnichfide', 'ecóir', 'ṅ-dílsi', 'romaini', 'n-deogur', 'ḟochraicc', 'chatarde',
#                         'asrubart', 'n-déde', 'don-ecmaiṅg', 'conrodelgg', 'coneperr', 'naill', 'n-dechrigeddar',
#                         'sa', 'n hetha', 'cuithech', 'ṅ-diis', 'borcc', 'nógai', 'remeperthi', 'totúrgimm',
#                         'fírianach', 'dían', 'ninni', 'dorurgabtha', 'tindrem', 'cuithe', 'netha', 'clethecháin',
#                         'conrothinoll', 'comairmith', 'nephairmith', 'm-bad', 'n-óen', 'n-insci', 'calléic', 'folod',
#                         'n-inni', 'n-etarscarad', 'm-médon', 'n-diull', 'n-aiccendaib', 'sluindess', 'n-dírgi',
#                         'm-bí', 'n-óg', 'n-genitiu', 'condeni', 'n-gné', 'n-ísar', 'n-airdíxa', 'cenéle', '-sa',
#                         'laithe', 'n-atacdai', 'ṅ-díis', 'bocc', 'n-aicniud', 'ṅ-dédenach', 'ṅ-inni',
#                         'fordomchomaither', 'n-óinor', 'ṅ-diuit', 'féiss-', 'arṅdaoasailci', 'ṁ-bias', 'nícinnet',
#                         'níforbanar', 'inthinscann', 'n-intinscann', 'nom-bíth', 'm-biat', 'n-díis', 'inndidit',
#                         'n-i', '-', 'n-ogaib', 'n-aimsir', 'm-medón', 'coirp', 'n-óinur', 'n-immognom', 'n-indib',
#                         'n-déni', 'n-alali', 'frecndairc', 'syllaib', 'm-bé', 'n-aimserad', 'timmorte',
#                         'sechmadachte', 'm-bís', 'dogni', 'conimchláim', 'n-ainm', 'n-aicneta', 'dian-accomoltar',
#                         'n-díruidigthe', 'n-immognam', 'n-aili', 'n-optit', 'uam-biat', 'n-erchre', 'n-éis',
#                         'n-dorórpai', 'manudchinni', 'rocinnius', 'n-engracigedar', 'n-anmae', 'n-adiecht',
#                         'n-othuth', 'n-intliuchta', 'n-aile', 'dobiur', 'n-dechor', 'em', 'n-aimnid', 'n-ainmnid',
#                         'ṁ-biat', 'n-diad', 'chenéul', 'n-ind', 'n-immḟognam', 'n-gnáe', 'n-dliged', 'nífil',
#                         'foirbthiu', 'dian-eprem', 'n-digaim', 'naichṅdeirsed', 'n-accomol', 'n-écóir',
#                         'n-donaidbdem', 'ṅ-aili', 'acomuil', 'n-aiccind', 'ṅ-gréc', 'nom-báad', 'dor-rignis',
#                         'ṅ-etrom', 'iar micniar', 'ṅ-dobriathra', 'n-dub'):
#             if 'ǽ' not in clwd:
#                 if 'æ' not in clwd:
#                     print(clwd)
#                     print(clgl)
#                     # print(wordslist[i])
#                     # print(glosslist[i])
#                     break
#     print("{} out of {} complete".format(i + 1, len(wordslist)))
#     # if i + 1 == len(wordslist):
#     #     print(clwd)
#     #     print(wordslist[i])
#     #     print(clgl)
#     #     print(glosslist[i])


# # Create and save an ordered list of glosses (uncleaned)
# glosslist = list()
# lastgloss = ""
# for i in analyses:
#     thisgloss = i[8]
#     if thisgloss != lastgloss:
#         lastgloss = thisgloss
#         glosslist.append(thisgloss)
# save_obj("Gloss_List", glosslist)

# # Create and save an ordered list of word-lists
# wordslist = list()
# thesewords = list()
# lastgloss = ""
# lastword = False
# for i in analyses:
#     # For each analysis (word)
#     thisgloss = i[8]
#     thisword = i[1]
#     if thisgloss != lastgloss:
#         # if this word is from a new gloss
#         lastgloss = thisgloss
#         # update the current gloss
#         if thesewords:
#             # if there is a word (it isn't blank/false)
#             wordslist.append(thesewords)
#         if thisword:
#             # if there is a word to start the new gloss
#             thesewords = [thisword]
#         else:
#             # if there's a missing word at beginning of the new gloss
#             thesewords = []
#     else:
#         # if this word is from the same gloss as last
#         if thisword:
#             # if there actually is a word/it's not a blank entry
#             thesewords.append(thisword)
#     if i == analyses[-1]:
#         # if this word is the last word
#         wordslist.append(thesewords)
# save_obj("Words_List", wordslist)

