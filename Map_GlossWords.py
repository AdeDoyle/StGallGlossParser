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
from Clean_Glosses import clean_gloss, clean_word
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


# Test the first and last word of each analysis match the first and last word of their associated gloss
def check_glossmatch(check_word="first"):
    for i in range(len(wordslist)):
        clgl = clean_gloss(glosslist[i], lowercase=True)
        if check_word == "first":
            # if we want to check the first word in each gloss
            clwd = (clean_word(wordslist[i][0][0], lowercase=True))
            check_list = ('con', 'ínna', 'cí', 'coibnestai', 'ɫ', 'dobriathra', 'fen', 'fo', 'altoir', 'ecóir',
                          'ind', 'roschaill', 'cia', 'to', 'doṡuidigthi', 'tindrem', 'cuithe', 'clethecháin',
                          'comairmith', 'nephairmith', 'húas', 'nícon', 'cenéle', 'neph-', '⁊', 'iar micniar')
        elif check_word == "last":
            # if we want to check the last word in each gloss
            clwd = (clean_word(wordslist[i][-1][0], lowercase=True))
            check_list = ('n-í', 'n-dule', 'ṅ-guttae', 'doruarthatar', 'n-naue', 'ɫ', 'lethguthaigthi',
                          'dorochuirsemmar', 'fuit', 'ṅ-digaim', 'aranecatar', 'ṡainriuth', 'ṅdi', 'medóndai',
                          'coibnestai', 'naci', 'ṅ-etha', 'oíndai', 'ndonaithchuiredar', 'fen', 'n-ai', 'con',
                          'ṅ-affracdai', 'folad', 'altoir', '-ni', 'n-dechur', 'ṅ-diles', 'folaid', 'n-doacaldmaichi',
                          'n-dechraiged', 'n-déainmmneichtech', 'n-dílsi', 'nacomlatar', 'huanainmnigter',
                          'huanainmnichfide', 'ecóir', 'ṅ-dílsi', 'romaini', 'n-deogur', 'ḟochraicc', 'chatarde',
                          'asrubart', 'n-déde', 'don-ecmaiṅg', 'conrodelgg', 'coneperr', 'naill', 'n-dechrigeddar',
                          'sa', 'n hetha', 'cuithech', 'ṅ-diis', 'borcc', 'nógai', 'remeperthi', 'totúrgimm',
                          'fírianach', 'dían', 'ninni', 'dorurgabtha', 'tindrem', 'cuithe', 'netha', 'clethecháin',
                          'conrothinoll', 'comairmith', 'nephairmith', 'm-bad', 'n-óen', 'n-insci', 'calléic', 'folod',
                          'n-inni', 'n-etarscarad', 'm-médon', 'n-diull', 'n-aiccendaib', 'sluindess', 'n-dírgi',
                          'm-bí', 'n-óg', 'n-genitiu', 'condeni', 'n-gné', 'n-ísar', 'n-airdíxa', 'cenéle', '-sa',
                          'laithe', 'n-atacdai', 'ṅ-díis', 'bocc', 'n-aicniud', 'ṅ-dédenach', 'ṅ-inni',
                          'fordomchomaither', 'n-óinor', 'ṅ-diuit', 'féiss-', 'arṅdaoasailci', 'ṁ-bias', 'nícinnet',
                          'níforbanar', 'inthinscann', 'n-intinscann', 'nom-bíth', 'm-biat', 'n-díis', 'inndidit',
                          'n-i', '-', 'n-ogaib', 'n-aimsir', 'm-medón', 'coirp', 'n-óinur', 'n-immognom', 'n-indib',
                          'n-déni', 'n-alali', 'frecndairc', 'syllaib', 'm-bé', 'n-aimserad', 'timmorte',
                          'sechmadachte', 'm-bís', 'dogni', 'conimchláim', 'n-ainm', 'n-aicneta', 'dian-accomoltar',
                          'n-díruidigthe', 'n-immognam', 'n-aili', 'n-optit', 'uam-biat', 'n-erchre', 'n-éis',
                          'n-dorórpai', 'manudchinni', 'rocinnius', 'n-engracigedar', 'n-anmae', 'n-adiecht',
                          'n-othuth', 'n-intliuchta', 'n-aile', 'dobiur', 'n-dechor', 'em', 'n-aimnid', 'n-ainmnid',
                          'ṁ-biat', 'n-diad', 'chenéul', 'n-ind', 'n-immḟognam', 'n-gnáe', 'n-dliged', 'nífil',
                          'foirbthiu', 'dian-eprem', 'n-digaim', 'naichṅdeirsed', 'n-accomol', 'n-écóir',
                          'n-donaidbdem', 'ṅ-aili', 'acomuil', 'n-aiccind', 'ṅ-gréc', 'nom-báad', 'dor-rignis',
                          'ṅ-etrom', 'iar micniar', 'ṅ-dobriathra', 'n-dub')
        if clwd not in clgl:
            if clwd not in check_list:
                if 'ǽ' not in clwd:
                    if 'æ' not in clwd:
                        print(clwd)
                        print(clgl)
                        # print(wordslist[i])
                        # print(glosslist[i])
                        return "Process incomplete.\nWord not found in gloss."
        # print("{} out of {} complete".format(i + 1, len(wordslist)))
    return "Process completed, no errors encountered."


# Map a word-separated gloss from the Hofman corpus to a list of POS-tagged words from the Bauer corpus
# gloss = uncleaned gloss, word_data_list = uncleaned list of word, analysis and translation
def map_glosswords(gloss, word_data_list):
    glosstext = clean_gloss(gloss)
    pos_gloss = [glosstext]
    pos_analysis = list()
    for word_data in word_data_list:
        word = clean_word(word_data[0])
        word_analysis = clean_onetag(word_data[1])
        word_pos = clean_analysis(word_analysis)
        pos_analysis.append(["{}".format(word), "<{}>".format(word_pos)])
    pos_gloss.append(pos_analysis)
    return pos_gloss


# #                                             TEST RESOURCES

# # Test first word in wordlist matches first word in each gloss
# print(check_glossmatch())

# # Test last word in wordlist matches last word in each gloss
# print(check_glossmatch("last"))

# #                                             TEST FUNCTIONS

# print(map_glosswords(glosslist[1], wordslist[1]))

# for i, gloss in enumerate(glosslist[:9]):
#     wordlist = wordslist[i]
#     pos_data = map_glosswords(gloss, wordlist)
#     print(pos_data[0], "\n", pos_data[1])

