
import os.path
from os import path
from Clean_ExcelLists import create_data_combo
from Clean_Glosses import create_clean_glossdict, create_clean_worddict
from OpenXlsx import list_xlsx
from Reassign_POS import save_sorted_tags, sort_tag_levels, list_tag_levels,\
    save_all_pos_combos_list, create_pos_taglist, create_glosslist, create_wordlist
from Match_GlossSets import save_poslist
from CoNLL_U import compile_SGG
from Pickle import open_obj


# #                                             REMOVE OLD FILES


def rem_files():
    resources = ["A1 List.pkl", "A2 List.pkl", "A3 List.pkl",
                 "Active_Passive List.pkl",
                 "All POS Combos Used.pkl",
                 "Clean_GlossDict.pkl", "Clean_WordDict.pkl",
                 "Gloss_List.pkl",
                 "POS_taglist.pkl",
                 "Relative Options List.pkl",
                 "SG. Combined Data.xlsx",
                 "SG POS-tagged combined.pkl", "SG POS-tagged separated.pkl",
                 "sga_dipsgg-ud-test_combined_POS.conllu", "sga_dipsgg-ud-test_split_POS.conllu",
                 "Translations List.pkl",
                 "Words_List.pkl"]
    for filename in resources:
        if path.exists(filename):
            os.remove(filename)
            print(f"Removed file: {filename}")
        else:
            print(f"Could not delete file: {filename}")
    return ""


# print(rem_files())


# #                                             CREATE RESOURCES


def make_files():
    # Set analyses variable for creation of further resources
    # If it does not already exist, it will be created by importing modules from Reassign_POS above
    # If it is deleted by the code above, it will be recreated
    if path.exists("SG. Combined Data.xlsx"):
        analyses = list_xlsx("SG. Combined Data", "Sheet 1")
    else:
        print(create_data_combo())
        analyses = list_xlsx("SG. Combined Data", "Sheet 1")

    # Create 'Clean_GlossDict.pkl' and 'Clean_WordDict.pkl'
    print(create_clean_glossdict())
    print(create_clean_worddict())

    # Create 'A1 List.pkl', 'A2 List.pkl', 'A3 List.pkl', 'Active_Passive List.pkl',
    # 'Relative Options List.pkl', and 'Translations List.pkl'
    print(save_sorted_tags(sort_tag_levels(list_tag_levels(analyses))))

    # Create 'All POS Combos Used.pkl' and 'POS_taglist.pkl'
    print(save_all_pos_combos_list(analyses))
    print(create_pos_taglist())

    # Create 'Gloss_List.pkl' and 'Words_List.pkl'
    print(create_glosslist(analyses))
    print(create_wordlist(analyses))

    # Create 'SG POS-tagged combined.pkl' and 'SG POS-tagged separated.pkl'
    print(save_poslist(True))
    print(save_poslist(False))

    # Create 'sga_dipsgg-ud-test1.conllu' and 'sga_dipsgg-ud-test2.conllu'
    print(compile_SGG(open_obj("SG POS-tagged combined.pkl"), True))
    print(compile_SGG(open_obj("SG POS-tagged separated.pkl"), False))

    return ""


# print(make_files())


# #                                     REMOVE OLD FILES AND CREATE NEW RESOURCES

# print(rem_files())
# print(make_files())
