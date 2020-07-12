"""Level 1"""

from OpenXlsx import list_xlsx
from Pickle import open_obj, save_obj
import re
from nltk import edit_distance as ed
from Map_GlossWords import map_glosswords
from CoNLL_U import split_pos_feats, add_features, update_feature
from Clean_Glosses import clean_gloss, clean_word


analyses = list_xlsx("SG. Combined Data", "Sheet 1")
glosslist = open_obj("Gloss_List.pkl")
wordslist = open_obj("Words_List.pkl")


# Changes all characters in Hoffman's glosses to a common set
def standardise_glosschars(gloss):
    gloss = gloss.lower()
    chardict = {'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u', 'ḟ': 'f', 'ṁ': 'm', 'ṅ': 'n', 'ṡ': 's', '⁊': 'ocus',
                'ɫ': 'no'}
    for char in gloss:
        if char in chardict:
            replacement = chardict.get(char)
            gloss = gloss.replace(char, replacement)
    return gloss


# Changes all characters in Bauer's glosses to a common set
def standardise_wordchars(word):
    # chars = sorted(list(set(word.lower())))
    word = word.lower()
    chardict = {'á': 'a', 'æ': 'ae', 'ǽ': 'ae', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
                'ċ': 'c', 'ḟ': 'f', 'ṁ': 'm', 'ṅ': 'n', 'ṡ': 's', '⁊': 'ocus', 'ɫ': 'no'}
    for char in word:
        if char in chardict:
            replacement = chardict.get(char)
            word = word.replace(char, replacement)
    return word


# Removes hyphens from Hofman's glosses with respect to the specific reason for hyphenation
def remove_glosshyphens(gloss):
    words = gloss.split(" ")
    word_ending = False
    for word in words:
        if "-" in word:
            word_index = words.index(word)
            reconstruct = False
            # If there's more than one hyphen in a word
            if word.count("-") > 1:
                first_deconstruct = word.split("-")
                if first_deconstruct[0] == "n":
                    nazal_word = first_deconstruct[:2]
                    remaining_words = first_deconstruct[2:]
                    first_reconstruct = "-".join(["".join(nazal_word), "-".join(remaining_words)])
                    if first_reconstruct.count("-") > 1:
                        word = " ".join(first_reconstruct.split("-"))
                        reconstruct = word
                    else:
                        word = first_reconstruct
                elif first_deconstruct[0] == "nisn":
                    first_word_fix = "nis n"
                    remaining_words = first_deconstruct[1:]
                    first_reconstruct = "".join([first_word_fix, "-".join(remaining_words)])
                    word = first_reconstruct
                elif word == "syl-laib-":
                    word = "".join(word.split("-"))
                    reconstruct = word
                else:
                    word = " ".join(word.split("-"))
                    reconstruct = word
            # If there's only one hyphen in a word
            if word.count("-") == 1:
                # Specialty removals (requiring more than hyphen removal and possible spacing)
                # If the word ends in a hyphen, remove without adding a space
                if word[-1] in ["-", "…"]:
                    small_prob_list = ['mael-', 'cua-', 'b-', 'alde-', 'neph-', 'gen-…', 'memr-', 'brig-', 'col-',
                                       'el-', 'incomṡuig-']
                    if word in small_prob_list:
                        reconstruct = "".join(word.split("-"))
                    # If the following word should be conjoined, concatenate the two, removing hyphen and space
                    big_prob_list = ['indfrec-', 'ṡechma-', 'adrodar-', 'in-', 'preter-', 'thech-', 'tim-', 'di-']
                    big_fix_list = ['indfrec- ndairc', 'ṡechma- dachtu', 'adrodar- car', 'in- narómae', 'preter- itum',
                                    'thech- taite', 'tim- morte', 'di- gal']
                    if word in big_prob_list:
                        for wordfix in big_fix_list:
                            if word in wordfix:
                                reconstruct = "".join(wordfix.split("- "))
                                word_ending = True
                if word[0] == "-":
                    reconstruct = word[1:]
                # If the hyphen seems to be misplaced and should be altered
                if not reconstruct:
                    splitpat = re.compile(r'\b(aran|asan|asech|dian|huan|niaisṅdius|niro|nádn)-')
                    splitpatitir = splitpat.finditer(word)
                    if splitpatitir:
                        for patfind in splitpatitir:
                            wrong_prefix = patfind.group()
                            wrong_remainder = "".join(word.split(wrong_prefix))
                            if wrong_prefix == "aran-":
                                word = "ara-n" + wrong_remainder
                            elif wrong_prefix == "asan-":
                                word = "asa-n" + wrong_remainder
                            elif wrong_prefix == "asech-":
                                word = "a sech" + wrong_remainder
                            elif wrong_prefix == "dian-":
                                word = "dia-n" + wrong_remainder
                            elif wrong_prefix == "huan-":
                                word = "hua-n" + wrong_remainder
                            elif wrong_prefix == "niaisṅdius-":
                                word = "niaisṅdiu-s" + wrong_remainder
                            elif wrong_prefix == "niro-":
                                word = "ni-ro" + wrong_remainder
                            elif wrong_prefix == "nádn-":
                                word = "nád-n" + wrong_remainder
                            reconstruct = " ".join(word.split("-"))
                # If the prefix attached to the hyphen occurs more than once and needs to be treated differently
                if not reconstruct:
                    splitpat = re.compile(r'\b(conro|in)-')
                    splitpatitir = splitpat.finditer(word)
                    if splitpatitir:
                        for patfind in splitpatitir:
                            check_prefix = patfind.group()
                            check_remainder = "".join(word.split(check_prefix))
                            if check_prefix == "conro-":
                                if check_remainder == "thinoll":
                                    reconstruct = "con ro" + check_remainder
                            if check_prefix == "in-":
                                if check_remainder in ["chrut", "remṡuidigud", "tan"]:
                                    reconstruct = " ".join(word.split("-"))
                                elif check_remainder == "na":
                                    reconstruct = "".join(word.split("-"))
                                elif check_remainder == "nabet":
                                    reconstruct = "inna bet"
                # Non-specialty removals
                deconstruct = word.split("-")
                # If the hyphen marks nazalisation, remove the hyphen without inserting a space
                if not reconstruct:
                    splitpat = re.compile(r'\b(nn|n|ṅ)-\w')
                    splitpatitir = splitpat.finditer(word)
                    if splitpatitir:
                        for patfind in splitpatitir:
                            nazalisation_marks = ["nn-", "n-", "ṅ-"]
                            if patfind.group()[:-1] in nazalisation_marks:
                                reconstruct = "".join(deconstruct)
                # If the hyphen marks a prefixed noun, remove the hyphen and insert a space
                if not reconstruct:
                    splitpat = re.compile(r'\b(athir|huasal|iar|medón|sethar|tuistid)-\w.*\b')
                    splitpatitir = splitpat.finditer(word)
                    if splitpatitir:
                        for _ in splitpatitir:
                            reconstruct = " ".join(deconstruct)
                # If the hyphen marks a prefix, remove the hyphen and insert a space
                if not reconstruct:
                    splitpat = re.compile(r'\b(ar|bith|cach|con|cosmail|derb|etar|il|lán|llán|leth|mi|mí|neph|ní|nil|'
                                          r'noen|nóen|nue|oen|óen|oin|óin|oín|ṡain|sechta|sen)-\w.*\b')
                    splitpatitir = splitpat.finditer(word)
                    if splitpatitir:
                        for _ in splitpatitir:
                            reconstruct = " ".join(deconstruct)
                # If the hyphen marks a suffix, remove the hyphen and insert a space
                if not reconstruct:
                    splitpat = re.compile(r'\b.*\w-(ni|sa|se|sem|si|sí|ssí|sidi|sin|siu|síu|so|som|son|són)\b')
                    splitpatitir = splitpat.finditer(word)
                    if splitpatitir:
                        for _ in splitpatitir:
                            reconstruct = " ".join(deconstruct)
                # If the hyphen marks the deictic particle, remove the hyphen and insert a space
                if not reconstruct:
                    splitpat = re.compile(r'\b.*\w-(í|hí)\b')
                    splitpatitir = splitpat.finditer(word)
                    if splitpatitir:
                        for _ in splitpatitir:
                            reconstruct = " ".join(deconstruct)
                # If the hyphen marks a pre-verbal particle, remove the hyphen without inserting a space
                if not reconstruct:
                    splitpat = re.compile(r'\b(for)-\w.*\b')
                    splitpatitir = splitpat.finditer(word)
                    if splitpatitir:
                        for _ in splitpatitir:
                            reconstruct = "".join(deconstruct)
                if not reconstruct:
                    word = "".join(word.split("-"))
                    reconstruct = word
            if not reconstruct:
                raise RuntimeError("Expected reconstruction of word could not be determined.")
            elif reconstruct:
                words[word_index] = reconstruct
            if word_ending:
                del words[word_index + 1]
                word_ending = False
    return " ".join(words)


# Takes a mapping of POS to gloss from the map_glosswords function,
# POS tags the Hofman gloss by comparing each tagged word in the Bauer gloss to each word in the Hofman gloss.
# Gives a score for reliability of the cross tagging:
#     0 - perfect
#     1 - changes made to Bauer's analysis of the copula, verbal complex, or other POS with duplicated tokens
#    10 - different number of POS tagged words in Bauer's analysis and tokens in Hofman's gloss
#   100 - some spelling variation in words matched between Bauer's analysis and Hofman's gloss
# THIRD VERSION
def matchword_levdist(gloss_mapping):
    tph_ref = gloss_mapping[0]
    gloss_string = gloss_mapping[1]
    gloss_trans = gloss_mapping[2]
    if "ᚐ" in gloss_string:
        gloss_list = gloss_string.split(" ")
        if gloss_list[0][0] == "᚛":
            gloss_list = ["᚛", gloss_list[0][1:]] + gloss_list[1:]
    else:
        gloss_list = gloss_string.split(" ")
    standard_string = remove_glosshyphens(standardise_glosschars(gloss_string))
    if "ᚐ" in standard_string:
        standard_list = standard_string.split(" ")
        if standard_list[0][0] == "᚛":
            standard_list = ["᚛", standard_list[0][1:]] + standard_list[1:]
    else:
        standard_list = standard_string.split(" ")
    standard_mapping = False
    pos_list = gloss_mapping[3]
    tags_rating = 0
    tagged_gloss = list()

    #                                                 PART 1:
    #
    # Create a list of standardised token forms from Hofman's gloss, and the original token they match.

    # if there are more tokens in Hofman's gloss before standardisation, combine disjointed tokens
    if len(gloss_list) > len(standard_list):
        replace_list = list()
        for i, original_token in enumerate(gloss_list):
            # if the token ends in a suspension stroke, the following token will be the expanded contraction
            # remove the hyphen and combine the two tokens to make one
            if original_token[-1] == "-":
                replacement = original_token[:-1] + gloss_list[i + 1]
                replacement_place = [i, i + 1]
                replace_list.append([replacement, replacement_place])
        # replace the two, originally split tokens of the token with the new combined form
        for replacement in replace_list:
            rep_token = replacement[0]
            rep_place = replacement[1]
            gloss_list = gloss_list[:rep_place[0]] + [rep_token] + gloss_list[rep_place[1] + 1:]
            standard_list = remove_glosshyphens(standardise_glosschars(" ".join(standard_list))).split(" ")
    if len(gloss_list) > len(standard_list):
        raise RuntimeError("Fewer tokens in Hofman's gloss after standardisation.")
    # if there are more tokens in Hofman's gloss after standardisation
    if len(standard_list) > len(gloss_list):
        standlist_copy = standard_list
        standard_mapping = list()
        # try to match each standardised token to its counterpart
        for i, split_token in enumerate(gloss_list):
            for j, standard_form in enumerate(standlist_copy):
                # if a standardised token form can be matched perfectly to a counterpart
                if standard_form == remove_glosshyphens(standardise_glosschars(split_token)):
                    # add the two matched tokens to 'token-to-standardised-token mapping' list as a tuple with indices
                    standard_mapping.append((split_token, standard_form, i))
                    standlist_copy = standlist_copy[1:]
                    break
                # if a standardised token form can't be matched perfectly to one counterpart
                else:
                    # assume that standardisation has split a token into two or more standardised tokens
                    i_sublist = remove_glosshyphens(standardise_glosschars(split_token)).split(" ")
                    for sub_i, sub_split_token in enumerate(i_sublist):
                        for sub_standard_form in standlist_copy:
                            # standardise the one token
                            # match each standard token to the full non-standard form if it matches a part of it
                            # add the two semi-matched tokens to 'token-to-standardised-token mapping' list as a tuple
                            # with their indices
                            if sub_standard_form == remove_glosshyphens(standardise_glosschars(sub_split_token)):
                                standard_mapping.append((split_token, sub_standard_form, [i, sub_i]))
                                standlist_copy = standlist_copy[1:]
                                break
                            # if a standardised token does not seem to match a part of the full non-standard token
                            else:
                                raise RuntimeError("Standard token form could not be matched to original token form"
                                                   " from Hofman.")
                    break
    # if there are the same number of tokens in Hofman's gloss before and after standardisation
    elif len(gloss_list) == len(standard_list):
        # assume a one-to-one match between the same indices in original and standardised token lists
        # match each as a tuple and add all to a 'token-to-standardised-token mapping' list
        gloss_indices = [i for i, _ in enumerate(gloss_list)]
        standard_mapping = list(zip(gloss_list, standard_list, gloss_indices))
        # if a matched pair in the 'token-to-standardised-token mapping' list do not match
        for matched_token in standard_mapping:
            if matched_token[1] != remove_glosshyphens(standardise_glosschars(matched_token[0])):
                raise RuntimeError("A token from Hofman's gloss has been paired with a standardised token form which"
                                   " it does not match.")
    # if no 'token-to-standardised-token mapping' list has been created yet
    if not standard_mapping:
        raise RuntimeError("No mapping of tokens to their standard forms has been created for Hofman's gloss.")
    # if any token in the 'token-to-standardised-token mapping' list is a known triple combination
    # which is not accounted for by Bauer's analysis, split it into parts
    trip_toks = ["airindi", "airindí", "arindi", "arindí", "anisin", "anísin", "anisiu", "anísiu",
                 "dindí", "dindhí", "dondí", "donaib-hí",
                 "Manidecamar", "manubed"]
    mapping_copy = list()
    trips_found = False
    for i, token_match in enumerate(standard_mapping):
        if token_match[0] in trip_toks:
            trips_found = True
            match_original = token_match[0]
            match_standard = token_match[1]
            match_place = token_match[2]
            new_split = False
            if match_standard in ["airindi", "arindi"]:
                new_split = [(match_original[:-4], match_standard[:-4], match_place),
                             (match_original[-4:-1], match_standard[-4:-1], match_place),
                             (match_original[-1:], match_standard[-1:], match_place)]
            elif match_standard in ["anisin", "anisiu"]:
                new_split = [(match_original[:1], match_standard[:1], match_place),
                             (match_original[1:3], match_standard[1:3], match_place),
                             (match_original[3:], match_standard[3:], match_place)]
            elif match_standard in ["dindi", "dondi"]:
                new_split = [(match_original[:2], match_standard[:2], match_place),
                             (match_original[2:4], match_standard[2:4], match_place),
                             (match_original[4:], match_standard[4:], match_place)]
            elif match_original[-3:] == "-hí":
                new_split = [(match_original[:-3], match_standard[:-2], match_place),
                             (match_original[-2:], match_standard[-2:], match_place)]
            elif match_original[-2:] == "hí":
                new_split = [(match_original[:-2], match_standard[:-2], match_place),
                             (match_original[-2:], match_standard[-2:], match_place)]
            elif match_original[-1] == "í":
                new_split = [(match_original[:-1], match_standard[:-1], match_place),
                             (match_original[-1:], match_standard[-1:], match_place)]
            elif match_original[:4] in ["Mani"]:
                new_split = [(match_original[:4], match_standard[:4], match_place),
                             (match_original[4:], match_standard[4:], match_place)]
            elif match_original[:4] in ["manu"]:
                new_split = [(match_original[:2], match_standard[:2], match_place),
                             (match_original[2:], match_standard[2:], match_place)]
            for j in new_split:
                mapping_copy.append(j)
        else:
            mapping_copy.append(token_match)
    if trips_found:
        for i, token_match in enumerate(mapping_copy):
            mapping_copy[i] = (token_match[0], token_match[1], i)
    standard_mapping = mapping_copy

    #                                                 PART 2:
    #
    # Add a standardised form of each word to the original word and POS tag in Bauer's tagged-gloss list.
    # Also remove any hyphens used by Bauer unless they are used as stand-alone zero tokens.
    # Remove any doubled parts-of-speech which can be easily identified.
    for i, tagged_word_data in enumerate(pos_list):
        tagged_word = tagged_word_data[0]
        if "-" in tagged_word and len(tagged_word) > 1:
            tagged_word_data[0] = "".join(tagged_word.split("-"))
        pos_list[i] = [tagged_word_data[0], tagged_word_data[2],
                       standardise_wordchars(tagged_word_data[0]), tagged_word_data[1]]

    #                                                PART 2.1:
    #
    # check standardised pos-tagged words against a list of known duplicates and problem words, remove as necessary
    combine_subtract = False

    #                                               PART 2.1.0:
    #
    #                                                 COPULA
    #
    # remove doubled dependent conjunctions/particles before the copula, or add to the copula if not doubled
    # cf. Thurn 503, 546-563 Stifter 247-249, 386
    # list all enclitic forms of the copula
    enclitic_cops = [['th', '<AUX Polarity=Pos | VerbType=Cop>', 'th'],  # Present (Indic.)
                     ['id', '<AUX Polarity=Pos | VerbType=Cop>', 'id'],
                     ['so', '<AUX Polarity=Pos | VerbType=Cop>', 'so'],
                     ['su', '<AUX Polarity=Pos | VerbType=Cop>', 'su'],
                     ['tu', '<AUX Polarity=Pos | VerbType=Cop>', 'tu'],
                     ['ndid', '<AUX Polarity=Pos | VerbType=Cop>', 'ndid'],
                     ['ndat', '<AUX Polarity=Pos | VerbType=Cop>', 'ndat'],
                     ['d', '<AUX Polarity=Pos | VerbType=Cop>', 'd'],  # (Subj.)
                     ['b', '<AUX Polarity=Pos | VerbType=Cop>', 'b'],
                     ['bo', '<AUX Polarity=Pos | VerbType=Cop>', 'bo'],
                     ['p', '<AUX Polarity=Pos | VerbType=Cop>', 'p'],
                     ['m', '<AUX Polarity=Pos | VerbType=Cop>', 'm'],
                     ['mbé', '<AUX Polarity=Pos | VerbType=Cop>', 'mbe'],
                     ['t', '<AUX Polarity=Pos | VerbType=Cop>', 't'],
                     ['bí', '<AUX Polarity=Pos | VerbType=Cop>', 'bi'],  # Consutudinal Present
                     ['mbí', '<AUX Polarity=Pos | VerbType=Cop>', 'mbi'],
                     ['mtar', '<AUX Polarity=Pos | VerbType=Cop>', 'mtar'],  # Pret.
                     ['bbad', '<AUX Polarity=Pos | VerbType=Cop>', 'bbad'],  # Past (Subj.)
                     ['mbad', '<AUX Polarity=Pos | VerbType=Cop>', 'mbad'],
                     ['bat', '<AUX Polarity=Pos | VerbType=Cop>', 'bat'],  # Future
                     ['-', '<AUX Polarity=Pos | VerbType=Cop>', '-']]
    # list all full forms of the copula (forms which cannot be combined with preceding conjunctions/particles)
    full_cops = [['am', '<AUX Polarity=Pos | VerbType=Cop>', 'am'],  # Present (Indic.)
                 ['is', '<AUX Polarity=Pos | VerbType=Cop>', 'is'],
                 ['iss', '<AUX Polarity=Pos | VerbType=Cop>', 'iss'],
                 ['ins', '<AUX Polarity=Pos | VerbType=Cop>', 'ins'],  # Problematic form (leg. iss)
                 ['it', '<AUX Polarity=Pos | VerbType=Cop>', 'it'],
                 ['hit', '<AUX Polarity=Pos | VerbType=Cop>', 'hit'],
                 ['Hít', '<AUX Polarity=Pos | VerbType=Cop>', 'hit'],
                 ['as', '<AUX Polarity=Pos | VerbType=Cop>', 'as'],  # (Rel.)
                 ['nas', '<AUX Polarity=Pos | VerbType=Cop>', 'nas'],
                 ['ata', '<AUX Polarity=Pos | VerbType=Cop>', 'ata'],
                 ['atá', '<AUX Polarity=Pos | VerbType=Cop>', 'ata'],
                 ['rop', '<AUX Polarity=Pos | VerbType=Cop>', 'rop'],  # (Subj.)
                 ['beit', '<AUX Polarity=Pos | VerbType=Cop>', 'beit'],
                 ['beith', '<AUX Polarity=Pos | VerbType=Cop>', 'beith'],
                 ['bes', '<AUX Polarity=Pos | VerbType=Cop>', 'bes'],  # (Subj. Rel.)
                 ['ṁbes', '<AUX Polarity=Pos | VerbType=Cop>', 'mbes'],
                 ['beta', '<AUX Polarity=Pos | VerbType=Cop>', 'beta'],
                 ['bete', '<AUX Polarity=Pos | VerbType=Cop>', 'bete'],
                 ['rubat', '<AUX Polarity=Pos | VerbType=Cop>', 'rubat'],  # (Cond.)
                 ['ropat', '<AUX Polarity=Pos | VerbType=Cop>', 'ropat'],
                 ['ropad', '<AUX Polarity=Pos | VerbType=Cop>', 'ropad'],
                 ['bad', '<AUX Polarity=Pos | VerbType=Cop>', 'bad'],  # (Impv.)
                 ['ba', '<AUX Polarity=Pos | VerbType=Cop>', 'ba'],  # Pret.
                 ['bá', '<AUX Polarity=Pos | VerbType=Cop>', 'ba'],  # Perf.
                 ['bid', '<AUX Polarity=Pos | VerbType=Cop>', 'bid'],  # Past (Subj.)
                 ['bed', '<AUX Polarity=Pos | VerbType=Cop>', 'bed'],
                 ['mbed', '<AUX Polarity=Pos | VerbType=Cop>', 'mbed'],
                 ['beth', '<AUX Polarity=Pos | VerbType=Cop>', 'beth'],
                 ['betis', '<AUX Polarity=Pos | VerbType=Cop>', 'betis'],
                 ['ṁbad', '<AUX Polarity=Pos | VerbType=Cop>', 'mbad'],  # (Subj. Rel.)
                 ['mbetis', '<AUX Polarity=Pos | VerbType=Cop>', 'mbetis'],
                 ['bith', '<AUX Polarity=Pos | VerbType=Cop>', 'bith'],  # Future
                 ['bit', '<AUX Polarity=Pos | VerbType=Cop>', 'bit'],
                 ['bas', '<AUX Polarity=Pos | VerbType=Cop>', 'bas']]  # (Rel.)
    # list all verbal particles which can be used in conjunction with a copula, but should be separated from them
    verbal_particles = [['no', '<PART PartType=Vb>', 'no', 'no'],
                        ['nu', '<PART PartType=Vb>', 'nu', 'no']]
    # list all preverbal particles which can be used in conjunction with a copula, and should remain attached
    copula_preverbal_parts = [['ro', '<PVP Mood=Sub>', 'ro', 'ro']]
    # list forms of the copula which have been combined with too many preceding parts of speech ((2<=) + copula)
    over_full_cops = [['cenid', '<AUX Polarity=Pos | VerbType=Cop>', 'cenid'],
                      ['cenobed', '<AUX Polarity=Pos | VerbType=Cop>', 'cenobed'],
                      ['corop', '<AUX Polarity=Pos | VerbType=Cop>', 'corop'],
                      ['corob', '<AUX Polarity=Pos | VerbType=Cop>', 'corob'],
                      ['manubed', '<AUX Polarity=Pos | VerbType=Cop>', 'manubed'],
                      ['nobed', '<AUX Polarity=Pos | VerbType=Cop>', 'nobed'],
                      ['nombed', '<AUX Polarity=Pos | VerbType=Cop>', 'nombed'],
                      ['nombetis', '<AUX Polarity=Pos | VerbType=Cop>', 'nombetis']]
    # list forms of the copula pre-combined with conjunctions/pronouns/particles by Bauer
    combined_cop_forms = [['arṅdid', '<AUX Polarity=Pos | VerbType=Cop>', 'arndid'],
                          ['ceto', '<AUX Polarity=Pos | VerbType=Cop>', 'ceto'],
                          ['cheso', '<AUX Polarity=Pos | VerbType=Cop>', 'cheso'],
                          ['ciaso', '<AUX Polarity=Pos | VerbType=Cop>', 'ciaso'],
                          ['cit', '<AUX Polarity=Pos | VerbType=Cop>', 'cit'],
                          ['cith', '<AUX Polarity=Pos | VerbType=Cop>', 'cith'],
                          ['combed', '<AUX Polarity=Pos | VerbType=Cop>', 'combed'],
                          ['conid', '<AUX Polarity=Pos | VerbType=Cop>', 'conid'],
                          ['comtis', '<AUX Polarity=Pos | VerbType=Cop>', 'comtis'],
                          ['condib', '<AUX Polarity=Pos | VerbType=Cop>', 'condib'],
                          ['combad', '<AUX Polarity=Pos | VerbType=Cop>', 'combad'],
                          ['mad', '<AUX Polarity=Pos | VerbType=Cop>', 'mad'],
                          ['robu', '<AUX Polarity=Pos | VerbType=Cop>', 'robu'],
                          ['robbu', '<AUX Polarity=Pos | VerbType=Cop>', 'robbu'],
                          ['rombu', '<AUX Polarity=Pos | VerbType=Cop>', 'rombu'],
                          ['rop', '<AUX Polarity=Pos | VerbType=Cop>', 'rop'],
                          ['roppad', '<AUX Polarity=Pos | VerbType=Cop>', 'roppad']]
    # list forms of the copula pre-combined with negative particles by Bauer but tagged as positive
    neg_cops = [['níbad', '<AUX Polarity=Pos | VerbType=Cop>', 'nibad'],
                ['nirubi', '<AUX Polarity=Pos | VerbType=Cop>', 'nirubi'],
                ['nad', '<AUX Polarity=Pos | VerbType=Cop>', 'nad'],
                ['nadṁbed', '<AUX Polarity=Pos | VerbType=Cop>', 'nadmbed'],
                ['nírbu', '<AUX Polarity=Pos | VerbType=Cop>', 'nirbu'],
                ['níbbad', '<AUX Polarity=Pos | VerbType=Cop>', 'nibbad'],
                ['nitat', '<AUX Polarity=Pos | VerbType=Cop>', 'nitat'],
                ['níbbu', '<AUX Polarity=Pos | VerbType=Cop>', 'nibbu'],
                ['nand', '<AUX Polarity=Pos | VerbType=Cop>', 'nand'],
                ['ní', '<AUX Polarity=Pos | VerbType=Cop>', 'ni'],
                ['nibad', '<AUX Polarity=Pos | VerbType=Cop>', 'nibad']]
    # list enclitic forms of the copula preceded by negative particles but tagged as positive
    neg_cop_enclitics = [['nd', '<AUX Polarity=Pos | VerbType=Cop>', 'nd']]
    # list forms of the copula combined as a result of the processes below (where they cause trouble)
    new_combined_cops = [['cesu', '<AUX Polarity=Pos | VerbType=Cop>', 'cesu'],
                         ['cid', '<AUX Polarity=Pos | VerbType=Cop>', 'cid'],
                         ['mad', '<AUX Polarity=Pos | VerbType=Cop>', 'mad'],
                         ['nud', '<AUX Polarity=Pos | VerbType=Cop>', 'nud'],
                         ['robo', '<AUX Polarity=Pos | VerbType=Cop>', 'robo']]
    # list independent conjunctions (p.247-249) which cannot be combined with enclitic forms of the copula
    indie_conj = [['amal', '<SCONJ>', 'amal'],
                  ['ar', '<SCONJ>', 'ar'],
                  ['arindí', '<SCONJ>', 'arindi'],
                  ['acht', '<SCONJ>', 'acht'],
                  ['dég', '<SCONJ>', 'deg'],
                  ['ore', '<SCONJ>', 'ore']]
    # list conjunctions which can combine with enclitic forms of the copula (not necessarily dependent conjunctions)
    conj_combo_forms = [['a', '<SCONJ>', 'a', 'a'],  # Temporal (independent)
                        ['ara', '<SCONJ>', 'ara', 'ara'],  # Consecutive & Final
                        ['ce', '<SCONJ>', 'ce', 'cía'],  # Adversative (independent)
                        ['che', '<SCONJ>', 'che', 'cía'],
                        ['ci', '<SCONJ>', 'ci', 'cía'],
                        ['cia', '<SCONJ>', 'cia', 'cía'],
                        ['co', '<SCONJ>', 'co', 'co'],  # Consecutive & Final
                        ['con', '<SCONJ>', 'con', 'co'],
                        ['ma', '<SCONJ>', 'ma', 'má']]  # Conditional (independent)
    # list negative conjunctions which can combine with forms of the copula (enclitic or reduced to zero)
    neg_conj_combo_forms = [['na', '<SCONJ Polarity=Neg>', 'na', 'ná'],
                            ['nach', '<SCONJ Polarity=Neg>', 'nach', 'ná'],
                            ['nách', '<SCONJ Polarity=Neg>', 'nach', 'nach'],
                            ['naich', '<SCONJ Polarity=Neg>', 'naich', 'ná']]
    # list particles which can combine with enclitic forms of the copula
    particle_combo_forms = [['i', '<PART PronType=Int>', 'i', 'in'],
                            ['im', '<PART PronType=Int>', 'im', 'in'],
                            ['in', '<PART PronType=Int>', 'in', 'in'],
                            ['a', '<PART PronType=Rel>', 'a', 'a']]
    # list pronouns which can combine with enclitic forms of the copula
    combo_pron_forms = [['c', '<PRON PronType=Int>', 'c', 'cía'],
                        ['ce', '<PRON PronType=Int>', 'ce', 'cía'],
                        ['ci', '<PRON PronType=Int>', 'ci', 'cía'],
                        ['cia', '<PRON PronType=Int>', 'cia', 'cía'],
                        ['Cia', '<PRON PronType=Int>', 'cia', 'cía'],
                        ['cid', '<PRON PronType=Int>', 'cid', 'cía'],
                        ['sechi', '<PRON PronType=Ind>', 'sechi', 'sechi']]
    # count the instances of the compounded copula form(s) in the gloss
    cop_count = 0
    for tagged_word_data in pos_list:
        split_tagged_pos = split_pos_feats(tagged_word_data[1])
        tagged_short_pos = split_tagged_pos[0]
        tagged_feats = split_tagged_pos[1]
        if tagged_short_pos == "AUX" and all(feat in tagged_feats for feat in ["Polarity=Pos", "VerbType=Cop"]):
            tagged_check_word = [tagged_word_data[0], '<AUX Polarity=Pos | VerbType=Cop>', tagged_word_data[2]]
            # identify forms of the copula which have not been accounted for yet
            if tagged_check_word not in full_cops and tagged_check_word not in enclitic_cops and \
                    tagged_check_word not in combined_cop_forms and tagged_check_word not in neg_cops and \
                    tagged_check_word not in neg_cop_enclitics and tagged_check_word not in over_full_cops:
                print(tagged_word_data)
                print([i[0] for i in standard_mapping])
                print([i for i in pos_list])
                raise RuntimeError("Unknown copula form")
            # identify forms of the copula which may require changing
            else:
                cop_count += 1
    for i in range(cop_count):
        # for each word in the POS list
        for j, tagged_word_data in enumerate(pos_list):
            tagged_original, tagged_pos, tagged_standard, tagged_head = \
                tagged_word_data[0], tagged_word_data[1], tagged_word_data[2], tagged_word_data[3]
            split_tagged_pos = split_pos_feats(tagged_pos)
            tagged_short_pos = split_tagged_pos[0]
            tagged_feats = split_tagged_pos[1]
            # if the POS is a positive form of the copula
            if tagged_short_pos == "AUX" and all(feat in tagged_feats for feat in ["Polarity=Pos", "VerbType=Cop"]):
                tagged_check_word = [tagged_original, '<AUX Polarity=Pos | VerbType=Cop>', tagged_standard]
                # if the copula form has been reduced to zero in this position
                if tagged_original == "-":
                    last_pos_place = 1
                    try:
                        if j != 0:
                            last_pos_data = pos_list[j-last_pos_place]
                            # find any preverbal particles used within the copula form
                            split_last_pos = split_pos_feats(last_pos_data[1])
                            if split_last_pos[0] == "PVP":
                                print(tagged_word_data)
                                print([k[0] for k in standard_mapping])
                                print([k[0] for k in pos_list])
                                raise RuntimeError("PVP found before copula form reduced to zero")
                        else:
                            last_pos_data = False
                    except IndexError:
                        last_pos_data = False
                    # there needs to be a preceding POS to attach the zero copula form to
                    if last_pos_data:
                        last_original, last_pos, last_standard, last_head = \
                            last_pos_data[0], last_pos_data[1], last_pos_data[2], last_pos_data[3]
                        split_last_pos = split_pos_feats(last_pos)
                        last_short_pos = split_last_pos[0]
                        last_feats = split_last_pos[1]
                        # if the last POS is an interrogative particle
                        # delete the empty copula as it does not change the form of the preceding POS
                        if last_pos_data in particle_combo_forms:
                            del pos_list[j]
                            combine_subtract = True
                            break
                        # if the last POS is an interrogative pronoun
                        # delete the empty copula as it does not change the form of the preceding POS
                        elif last_pos_data in combo_pron_forms and 'PronType=Int' in last_feats:
                            del pos_list[j]
                            combine_subtract = True
                            break
                        # fix polarity of negative copula forms reduced to zero which are listed as positive by Bauer
                        elif last_short_pos == "SCONJ" and "Polarity=Neg" in last_feats:
                            last_check_form = [last_original, "<SCONJ Polarity=Neg>", last_standard, last_head]
                            if last_check_form in neg_conj_combo_forms:
                                neg_pos = update_feature(tagged_pos, "Polarity=Neg")
                                tagged_word_data = [tagged_original, neg_pos, tagged_standard, tagged_head]
                                pos_list[j] = tagged_word_data
                                combine_subtract = True
                                break
                            else:
                                print(last_check_form)
                                print(last_pos_data)
                                print(tagged_word_data)
                                print([k[0] for k in standard_mapping])
                                print([k[0] for k in pos_list])
                                raise RuntimeError("Unknown negative conjunction preceding copula reduced to zero")
                        else:
                            print(last_pos_data)
                            print(tagged_word_data)
                            print([k[0] for k in standard_mapping])
                            print([k[0] for k in pos_list])
                            raise RuntimeError("Copula reduced to zero, last POS not a known POS")
                    else:
                        print(tagged_word_data)
                        print([k[0] for k in standard_mapping])
                        print([k[0] for k in pos_list])
                        raise RuntimeError("Copula reduced to zero, but no word precedes the copula form")
                # fix polarity of negative copula forms which are listed as positive by Bauer
                if tagged_check_word in neg_cops or tagged_check_word in neg_cop_enclitics:
                    neg_pos = update_feature(tagged_pos, "Polarity=Neg")
                    tagged_word_data = [tagged_original, neg_pos, tagged_standard, tagged_head]
                    pos_list[j] = tagged_word_data
                    combine_subtract = True
                    break
                # if an enclitic or precombined form of the copula is used
                if tagged_check_word not in full_cops:
                    if tagged_check_word in enclitic_cops or tagged_check_word in combined_cop_forms:
                        last_pos_place = 1
                        copula_preverbs = list()
                        try:
                            if j != 0:
                                last_pos_data = pos_list[j-last_pos_place]
                                # find any preverbal particles used within the copula form
                                split_last_pos = split_pos_feats(last_pos_data[1])
                                if split_last_pos[0] == "PVP":
                                    while split_last_pos[0] == "PVP":
                                        copula_preverbs.append(last_pos_data)
                                        last_pos_place += 1
                                        last_pos_data = pos_list[j-last_pos_place]
                                        split_last_pos = split_pos_feats(last_pos_data[1])
                                        if j-last_pos_place == 0 and split_last_pos[0] == "PVP":
                                            print(last_pos_data)
                                            print(tagged_word_data)
                                            print([k[0] for k in standard_mapping])
                                            print([k[0] for k in pos_list])
                                            raise RuntimeError("Copula preverb is the first POS in the gloss")
                            else:
                                last_pos_data = False
                        except IndexError:
                            last_pos_data = False
                        # there should be a POS preceding an enclitic form of the copula but perhaps not if precombined
                        if last_pos_data:
                            last_original, last_pos, last_standard, last_head = last_pos_data[0], last_pos_data[1], \
                                                                                last_pos_data[2], last_pos_data[3]
                            split_last_pos = split_pos_feats(last_pos)
                            last_short_pos = split_last_pos[0]
                            last_feats = split_last_pos[1]
                            # if an enclitic or precombined copula form is preceded by a preverb
                            if copula_preverbs:
                                if len(copula_preverbs) > 1:
                                    print(last_pos_data)
                                    print(copula_preverbs)
                                    print(tagged_word_data)
                                    print([k[0] for k in standard_mapping])
                                    print([k[0] for k in pos_list])
                                    raise RuntimeError("More preverbs preceding copula than expected")
                                elif len(copula_preverbs) == 1:
                                    pvp_pos_data = copula_preverbs[0]
                                    pvp_original = pvp_pos_data[0]
                                    pvp_pos = pvp_pos_data[1]
                                    pvp_standard = pvp_pos_data[2]
                                    split_pvp_pos = split_pos_feats(pvp_pos)
                                    pvp_feats = split_pvp_pos[1]
                                    # if the preverb is not already at the beginning of the copula form
                                    # add the two together, and add the perverb's features to the copula's
                                    if pvp_original not in tagged_original and pvp_standard not in tagged_standard:
                                        cop_combo = [pvp_original + tagged_original,
                                                     add_features(tagged_pos, pvp_feats),
                                                     pvp_standard + tagged_standard,
                                                     tagged_head]
                                        pos_list = pos_list[:j-last_pos_place+1] + [cop_combo] + pos_list[j+1:]
                                        combine_subtract = True
                                        break
                                    # if the preverb is doubled at the begining of the copula form
                                    # add the preverb's features to the copula's and remove the doubled preverb
                                    elif pvp_original == tagged_original[:len(pvp_original)] \
                                            and pvp_standard == tagged_standard[:len(pvp_standard)]:
                                        cop_combo = [tagged_original,
                                                     add_features(tagged_pos, pvp_feats),
                                                     tagged_standard, tagged_head]
                                        pos_list = pos_list[:j-last_pos_place+1] + [cop_combo] + pos_list[j+1:]
                                        combine_subtract = True
                                        break
                                    else:
                                        print(last_pos_data)
                                        print(copula_preverbs)
                                        print(tagged_word_data)
                                        print([k[0] for k in standard_mapping])
                                        print([k[0] for k in pos_list])
                                        raise RuntimeError("Preverb present in copula form")
                            # if an enclitic or precombined copula form is preceded by verbal particles
                            elif last_pos_data in verbal_particles:
                                # if the verbal particle is not already at the beginning of the copula form
                                if last_original not in tagged_original and last_standard not in tagged_standard:
                                    cop_combo = [last_original + tagged_original,
                                                 tagged_pos,
                                                 last_standard + tagged_standard,
                                                 tagged_head]
                                    pos_list = pos_list[:j-last_pos_place] + [cop_combo] + pos_list[j+1:]
                                    combine_subtract = True
                                    break
                                elif last_original == tagged_original[:len(last_original)] \
                                        and last_standard == tagged_standard[:len(last_standard)]:
                                    print(last_pos_data)
                                    print(tagged_word_data)
                                    print([k[0] for k in standard_mapping])
                                    print([k[0] for k in pos_list])
                                    raise RuntimeError("Preverb present at beginning of copula form")
                                else:
                                    print(last_pos_data)
                                    print(tagged_word_data)
                                    print([k[0] for k in standard_mapping])
                                    print([k[0] for k in pos_list])
                                    raise RuntimeError("Preverb present in copula form")
                            # if an enclitic or precombined copula form is preceded by something other than a preverb
                            # which is capable of combining with it, and not negative
                            elif last_pos_data not in indie_conj \
                                    and (last_pos_data in particle_combo_forms or last_pos_data in combo_pron_forms
                                         or (last_short_pos == 'SCONJ' and 'Polarity=Neg' not in last_feats)
                                         or last_short_pos == 'ADP'):
                                # if the preceding POS is a dependent conjunction or a particle
                                if last_pos_data in conj_combo_forms or last_pos_data in particle_combo_forms:
                                    # if the conjunction/particle is repeated in the copula form
                                    # combine the copula's features with those of the conjunction/particle
                                    # keep the full copula form, but use the preceding POS tag
                                    if last_original == tagged_original[:len(last_original)]:
                                        combined_pos = add_features(last_pos, tagged_feats)
                                        cop_combo = [tagged_original, combined_pos, tagged_standard, last_head]
                                        pos_list = pos_list[:j-last_pos_place] + [cop_combo] + pos_list[j+1:]
                                        combine_subtract = True
                                        break
                                    # if the conjunction/particle needs to be combined with an enclitic copula form
                                    # combine the copula's features with those of the conjunction
                                    # combine the conjunction with the copula form and use the conjunction's POS tag
                                    elif tagged_check_word in enclitic_cops:
                                        combined_pos = add_features(last_pos, tagged_feats)
                                        cop_combo = [last_original + tagged_original,
                                                     combined_pos,
                                                     last_standard + tagged_standard,
                                                     last_head]
                                        pos_list = pos_list[:j-last_pos_place] + [cop_combo] + pos_list[j+1:]
                                        combine_subtract = True
                                        break
                                    # if the copula form is not enclitic, or otherwise cannot be combined
                                    else:
                                        print(last_pos_data)
                                        print(tagged_word_data)
                                        raise RuntimeError("Unknown form of copula, cannot combine if not enclitic")
                                # if the preceding POS is a pronoun
                                elif last_pos_data in combo_pron_forms:
                                    combined_pos = add_features(last_pos, tagged_feats)
                                    cop_combo = [last_original + tagged_original,
                                                 combined_pos,
                                                 last_standard + tagged_standard,
                                                 last_head]
                                    pos_list = pos_list[:j-last_pos_place] + [cop_combo] + pos_list[j+1:]
                                    combine_subtract = True
                                    break
                                # if the preceding POS is a preposition
                                elif last_short_pos == "ADP" and tagged_check_word in combined_cop_forms:
                                    combined_pos = add_features(last_pos, tagged_feats)
                                    cop_combo = [tagged_original, combined_pos, tagged_standard, last_head]
                                    pos_list = pos_list[:j-last_pos_place] + [cop_combo] + pos_list[j+1:]
                                    combine_subtract = True
                                    break
                                # if there is an unexpected POS preceding the enclitic copula form
                                else:
                                    print(last_pos_data)
                                    print(tagged_word_data)
                                    print([k[0] for k in standard_mapping])
                                    print([k[0] for k in pos_list])
                                    raise RuntimeError("Unknown conjunction/particle preceding copula\n"
                                                       "              OR independent conjunction not in indie_conj "
                                                       "list")
                            # if an independent conjunction precedes a pre-combined copula form:
                            elif last_short_pos == "SCONJ" and last_pos_data in indie_conj:
                                if tagged_check_word in combined_cop_forms:
                                    continue
                            # if any other POS precedes a pre-combined copula form:
                            elif tagged_check_word in combined_cop_forms:
                                # if the preceding POS is not repeated in the copula form
                                # it is unrelated to the copula, which is already whole, and can be ignored
                                if last_original not in tagged_original and last_standard not in tagged_standard:
                                    continue
                                # if the preceding POS is repeated in the copula form
                                else:
                                    print(last_pos_data)
                                    print(tagged_word_data)
                                    print([k[0] for k in standard_mapping])
                                    print([k for k in pos_list])
                                    raise RuntimeError("Word preceding pre-combined copula contained in copula form")
                            # fix polarity of enclitic copula forms which follow negative particles or conjunctions
                            elif 'Polarity=Neg' in last_feats:
                                tagged_pos = update_feature(tagged_pos, "Polarity=Neg")
                                pos_list[j] = [tagged_original, tagged_pos, tagged_standard, tagged_head]
                                break
                            # if any other unaccounted-for POS precedes the enclitic copula form
                            else:
                                print(last_pos_data)
                                print(tagged_word_data)
                                print([k[0] for k in standard_mapping])
                                print([k for k in pos_list])
                                raise RuntimeError("New POS type preceding copula form")
                        # if preverbs precede an enclitic copula form but there is no preceding POS
                        elif copula_preverbs:
                            print(tagged_word_data)
                            print([k[0] for k in standard_mapping])
                            print([k[0] for k in pos_list])
                            raise RuntimeError("No data for last POS, but preverbs preceding copula form.")
                        # if there is no POS preceding the enclitic form of the copula
                        elif tagged_check_word not in new_combined_cops:
                            print(tagged_word_data)
                            print(pos_list)
                            raise RuntimeError("No POS preceding enclitic or precombined copula form")
                    # if Bauer combined too many conjunctions/preverbs etc. with a copula and some must be removed
                    # from the over-full copula form to meet the word-separation standard
                    elif tagged_check_word in over_full_cops:
                        last_pos_place = 1
                        copula_preverbs = list()
                        try:
                            if j != 0:
                                last_pos_data = pos_list[j-last_pos_place]
                                # find any preverbal particles used within the copula form
                                split_last_pos = split_pos_feats(last_pos_data[1])
                                if split_last_pos[0] == "PVP":
                                    while split_last_pos[0] == "PVP":
                                        copula_preverbs.append(last_pos_data)
                                        last_pos_place += 1
                                        last_pos_data = pos_list[j-last_pos_place]
                                        split_last_pos = split_pos_feats(last_pos_data[1])
                                        if j - last_pos_place == 0 and split_last_pos[0] == "PVP":
                                            print(last_pos_data)
                                            print(tagged_word_data)
                                            print([k[0] for k in standard_mapping])
                                            print([k[0] for k in pos_list])
                                            raise RuntimeError("Copula preverb is the first POS in the gloss")
                            else:
                                last_pos_data = False
                        except IndexError:
                            last_pos_data = False
                        if last_pos_data:
                            last_original, last_pos, last_standard, last_head = last_pos_data[0], last_pos_data[1], \
                                                                                last_pos_data[2], last_pos_data[3]
                            split_last_pos = split_pos_feats(last_pos)
                            last_short_pos = split_last_pos[0]
                            last_feats = split_last_pos[1]
                            # if there are preverb(s) preceding an overfull copula form
                            # they should remain part of the copula, but any preceding POS should be removed
                            if copula_preverbs:
                                # if there are more than one preverb preceding the copula
                                if len(copula_preverbs) > 1:
                                    print(last_pos_data)
                                    print(copula_preverbs)
                                    print(tagged_word_data)
                                    raise RuntimeError("Multiple copula preverbs found")
                                # if the last POS is a combinable conjunction and it is repeated in the copula form
                                # it should be separated from the copula form leaving only the preverb attached
                                if last_pos_data in conj_combo_forms and \
                                        last_original == tagged_original[:len(last_original)]:
                                    reduced_copform = [tagged_original[len(last_original):],
                                                       tagged_pos,
                                                       tagged_standard[len(last_standard):],
                                                       tagged_head]
                                    reduced_original = reduced_copform[0]
                                    reduced_standard = reduced_copform[2]
                                    copula_preverb = copula_preverbs[0]
                                    cop_preverb_original = copula_preverb[0]
                                    cop_preverb_pos = copula_preverb[0]
                                    cop_preverb_standard = copula_preverb[2]
                                    split_cop_preverb_pos = split_pos_feats(cop_preverb_pos)
                                    cop_preverb_feats = split_cop_preverb_pos[1]
                                    # if the preverb is a full (not reduced) variant spelling of an expected preverb
                                    if copula_preverb in copula_preverbal_parts:
                                        # if the preverb is already at the beginning of the reduced copula form
                                        # remove it to isolate the remaining, pure copula form
                                        if cop_preverb_original == reduced_original[:len(last_original)]:
                                            reduced_copform = [reduced_original[len(cop_preverb_original):],
                                                               tagged_pos,
                                                               reduced_standard[len(cop_preverb_standard):],
                                                               tagged_head]
                                            reduced_check_cop = [reduced_copform[0],
                                                                 '<AUX Polarity=Pos | VerbType=Cop>',
                                                                 reduced_copform[2]]
                                            # if the copula form remaining after removing the preverb is an enclitic
                                            # recombine it with the preverb
                                            # combine the preverb's features with those of the copula
                                            if reduced_check_cop in enclitic_cops:
                                                tagged_pos = add_features(tagged_pos, cop_preverb_feats)
                                                final_cop = [cop_preverb_original + reduced_copform[0],
                                                             tagged_pos,
                                                             cop_preverb_standard + reduced_copform[2],
                                                             tagged_head]
                                            # if the copula form remaining after removing the preverb is a full form
                                            elif reduced_check_cop in full_cops:
                                                raise RuntimeError("Full copula form following preverb")
                                            # if the copula form is neither a known enclitic nor full form
                                            else:
                                                print(last_pos_data)
                                                print(copula_preverb)
                                                print(tagged_word_data)
                                                print(reduced_copform)
                                                raise RuntimeError("Undetermined copula form, cannot combine")
                                            pos_list = pos_list[:j-last_pos_place+1] + [final_cop] + pos_list[j+1:]
                                            combine_subtract = True
                                            break
                                        # if the preverb isn't at the beginning of the copula form once the preceding
                                        # combining conjunction has been removed
                                        else:
                                            print(tagged_word_data)
                                            print(copula_preverbs)
                                            print(last_pos_data)
                                            raise RuntimeError("Could not separate over-full copula form")
                                    # if the preverbal particle preceding the copula form is not listed
                                    else:
                                        print(tagged_word_data)
                                        print(copula_preverb)
                                        print(last_pos_data)
                                        raise RuntimeError("Copula preceded by unknown preverb")
                                # if the last POS is not a combining conjunction
                                # or it does not occur at the start of the copula form
                                else:
                                    print(last_pos_data)
                                    print(copula_preverbs)
                                    print(tagged_word_data)
                                    raise RuntimeError("POS preceding over-full copula form not found in copula form")
                            # if there are no preverbs preceding an overfull copula form but the last POS is a verbal
                            # particle which has been attached to the beginning of the over-full copula
                            # remove everything from the copula from, leaving only the base form itself
                            elif last_pos_data in verbal_particles \
                                    and last_original == tagged_original[:len(last_original)]:
                                tagged_original = tagged_original[len(last_original):]
                                tagged_standard = tagged_standard[len(last_standard):]
                                tagged_word_data = [tagged_original, tagged_pos, tagged_standard, tagged_head]
                                pos_list[j] = tagged_word_data
                                combine_subtract = True
                                break
                            # if there are no preverbs preceding an overfull copula form but the last POS is a verbal
                            # particle which is within the over-full copula
                            # check if any combination of preceding POS plus the preverb are at the beginning of the
                            # copula form and, if so, remove them from the form
                            elif last_pos_data in verbal_particles and last_original in tagged_original:
                                combined_prepos_orig = ""
                                combined_prepos_std = ""
                                for backstep in range(j):
                                    start_position = j - 1 - backstep
                                    backword_data = pos_list[start_position]
                                    backstep_orig = backword_data[0]
                                    combined_prepos_orig = backstep_orig + combined_prepos_orig
                                    backstep_std = backword_data[2]
                                    combined_prepos_std = backstep_std + combined_prepos_std
                                    if combined_prepos_orig == tagged_original[:len(combined_prepos_orig)] \
                                            and combined_prepos_std == tagged_standard[:len(combined_prepos_std)]:
                                        tagged_original = tagged_original[len(combined_prepos_orig):]
                                        tagged_standard = tagged_standard[len(combined_prepos_std):]
                                        break
                                tagged_word_data = [tagged_original, tagged_pos, tagged_standard, tagged_head]
                                pos_list[j] = tagged_word_data
                                combine_subtract = True
                                break
                            # if there are no preverbs preceding an overfull copula form but the last POS is a negative
                            # particle which has been attached to the beginning of the over-full copula
                            # remove everything from th copula from, leaving only the base form itself
                            # change the polarity of the copula to negative
                            elif last_short_pos == "PART" and "Polarity=Neg" in last_feats and \
                                    last_original in tagged_original:
                                tagged_pos = update_feature(tagged_pos, "Polarity=Neg")
                                tagged_original = tagged_original[tagged_original.find(last_original) +
                                                                  len(last_original):]
                                tagged_standard = tagged_standard[tagged_standard.find(last_standard) +
                                                                  len(last_standard):]
                                reduced_copform = [tagged_original, tagged_pos, tagged_standard, tagged_head]
                                pos_list[j] = reduced_copform
                                combine_subtract = True
                                break
                            # if there are any unaccounted for over-full copula forms remaining
                            else:
                                print(last_pos_data)
                                print(tagged_word_data)
                                print([k[0] for k in standard_mapping])
                                print([k[0] for k in pos_list])
                                raise RuntimeError("Could not separate over-full copula form")
                        # if there are preverbs but no preceding POS
                        elif copula_preverbs:
                            raise RuntimeError("Preverb(s) preceding over-full copula are first POS in gloss")
                        # if nothing precedes the over-full copula form
                        else:
                            raise RuntimeError("No POS preceding over-full copula form")
                    # if the copula form is not a known enclitic, combined, full, over-full or negative form
                    elif tagged_check_word not in new_combined_cops:
                        print(tagged_word_data)
                        print([k[0] for k in standard_mapping])
                        print([k[0] for k in pos_list])
                        raise RuntimeError("Copula form not could not be found")
                # ensure absolute forms of the copula are not compounded with preceding conjunctions, etc.
                elif tagged_check_word in full_cops:
                    last_pos_place = 1
                    copula_preverbs = list()
                    try:
                        if j != 0:
                            last_pos_data = pos_list[j - last_pos_place]
                            # find any preverbal particles used within the copula form
                            split_last_pos = split_pos_feats(last_pos_data[1])
                            if split_last_pos[0] == "PVP":
                                while split_last_pos[0] == "PVP":
                                    copula_preverbs.append(last_pos_data)
                                    last_pos_place += 1
                                    last_pos_data = pos_list[j - last_pos_place]
                                    split_last_pos = split_pos_feats(last_pos_data[1])
                                    if j - last_pos_place == 0 and split_last_pos[0] == "PVP":
                                        print(last_pos_data)
                                        print(tagged_word_data)
                                        print([k[0] for k in standard_mapping])
                                        print([k[0] for k in pos_list])
                                        raise RuntimeError("Copula preverb is the first POS in the gloss")
                        else:
                            last_pos_data = False
                    except IndexError:
                        last_pos_data = False
                    # there should be no preverbs before an absolute or otherwise full form of the copula
                    if copula_preverbs:
                        reduced_copform = tagged_original
                        for preverb_data in copula_preverbs:
                            preverb_original = preverb_data[0]
                            split_cop_preverb = split_pos_feats(preverb_data[1])
                            preverb_short_pos = split_cop_preverb[0]
                            preverb_feats = split_cop_preverb[1]
                            if preverb_feats:
                                tagged_pos = add_features(tagged_pos, preverb_feats)
                            if preverb_short_pos != "PVP":
                                print(last_pos_data)
                                print(preverb_data)
                                print(reduced_copform)
                                raise RuntimeError("Unexpected affix preceding full copula form")
                            if preverb_original == reduced_copform[:len(preverb_original)]:
                                reduced_copform = reduced_copform[len(preverb_original):]
                            else:
                                print(last_pos_data)
                                print(preverb_data)
                                print(reduced_copform)
                                raise RuntimeError("Could not find preverb in full copula form")
                        tagged_word_data = [tagged_original, tagged_pos, tagged_standard, tagged_head]
                        pos_list = pos_list[:j-last_pos_place+1] + [tagged_word_data] + pos_list[j+1:]
                        combine_subtract = True
                        break
                    # if there is a POS before the full copula form
                    elif last_pos_data:
                        last_original, last_pos, last_standard, last_head = \
                            last_pos_data[0], last_pos_data[1], last_pos_data[2], last_pos_data[3]
                        split_last_pos = split_pos_feats(last_pos)
                        last_short_pos = split_last_pos[0]
                        last_feats = split_last_pos[1]
                        # if the last POS before the full copula form is a conjunction
                        if last_short_pos == "SCONJ":
                            # if the last POS is not an independent conjunction (as would be expected)
                            if last_pos_data in conj_combo_forms or last_pos_data not in indie_conj:
                                if last_original == tagged_original[:len(last_original)]:
                                    print(last_pos_data)
                                    print(tagged_word_data)
                                    print([k[0] for k in standard_mapping])
                                    print([k[0] for k in pos_list])
                                    raise RuntimeError("Unexpected conjunction found repeated in absolute copula form")
                        # if the last POS before the full copula form is a verbal particle (like empty 'ro')
                        elif last_short_pos == "PART" and "PartType=Vb" in last_feats:
                            if last_original == tagged_original[:len(last_original)]:
                                del pos_list[j-last_pos_place]
                                combine_subtract = True
                        # if the last POS before the full copula form is any other combinable type
                        elif last_pos_data in particle_combo_forms or last_pos_data in combo_pron_forms:
                            if last_original == tagged_original[:len(last_original)]:
                                print(last_pos_data)
                                print(tagged_word_data)
                                print([k[0] for k in standard_mapping])
                                print([k[0] for k in pos_list])
                                raise RuntimeError("Unexpected POS found repeated in absolute copula form")
    # remove doubled 'ní' particle before negative form of the copula, also 'ní'
    # list all copula forms which are negative, or can be combined with negative particles
    full_neg_list = [['in', '<AUX Polarity=Neg | VerbType=Cop>', 'in'],  # Typo
                     ['nad', '<AUX Polarity=Neg | VerbType=Cop>', 'nad'],
                     ['nadṁbed', '<AUX Polarity=Neg | VerbType=Cop>', 'nadmbed'],
                     ['nand', '<AUX Polarity=Neg | VerbType=Cop>', 'nand'],
                     ['ni', '<AUX Polarity=Neg | VerbType=Cop>', 'ni'],
                     ['ní', '<AUX Polarity=Neg | VerbType=Cop>', 'ni'],
                     ['Ni', '<AUX Polarity=Neg | VerbType=Cop>', 'ni'],
                     ['Ní', '<AUX Polarity=Neg | VerbType=Cop>', 'ni'],
                     ['nibad', '<AUX Polarity=Neg | VerbType=Cop>', 'nibad'],
                     ['níbad', '<AUX Polarity=Neg | VerbType=Cop>', 'nibad'],
                     ['nibat', '<AUX Polarity=Neg | VerbType=Cop>', 'nibat'],
                     ['nibba', '<AUX Polarity=Neg | VerbType=Cop>', 'nibba'],
                     ['níbbad', '<AUX Polarity=Neg | VerbType=Cop>', 'nibbad'],
                     ['níbbu', '<AUX Polarity=Neg | VerbType=Cop>', 'nibbu'],
                     ['nibu', '<AUX Polarity=Neg | VerbType=Cop>', 'nibu'],
                     ['níbu', '<AUX Polarity=Neg | VerbType=Cop>', 'nibu'],
                     ['niptis', '<AUX Polarity=Neg | VerbType=Cop>', 'niptis'],
                     ['nírbu', '<AUX Polarity=Neg | VerbType=Cop>', 'nirbu'],
                     ['nirubi', '<AUX Polarity=Neg | VerbType=Cop>', 'nirubi'],
                     ['nitat', '<AUX Polarity=Neg | VerbType=Cop>', 'nitat'],
                     ['nítat', '<AUX Polarity=Neg | VerbType=Cop>', 'nitat']]
    enclitic_neg_list = [['-', '<AUX Polarity=Neg | VerbType=Cop>', '-'],
                         ['b', '<AUX Polarity=Neg | VerbType=Cop>', 'b'],
                         ['bba', '<AUX Polarity=Neg | VerbType=Cop>', 'bba'],
                         ['bbad', '<AUX Polarity=Neg | VerbType=Cop>', 'bbad'],
                         ['bed', '<AUX Polarity=Neg | VerbType=Cop>', 'bed'],
                         ['bi', '<AUX Polarity=Neg | VerbType=Cop>', 'bi'],
                         ['bí', '<AUX Polarity=Neg | VerbType=Cop>', 'bi'],
                         ['d', '<AUX Polarity=Neg | VerbType=Cop>', 'd'],
                         ['mba', '<AUX Polarity=Neg | VerbType=Cop>', 'mba'],
                         ['mtar', '<AUX Polarity=Neg | VerbType=Cop>', 'mtar'],
                         ['nd', '<AUX Polarity=Neg | VerbType=Cop>', 'nd'],
                         ['ndat', '<AUX Polarity=Neg | VerbType=Cop>', 'ndat'],
                         ['nip', '<AUX Polarity=Neg | VerbType=Cop>', 'nip'],
                         ['p', '<AUX Polarity=Neg | VerbType=Cop>', 'p'],
                         ['th', '<AUX Polarity=Neg | VerbType=Cop>', 'th']]
    # list all negative particles which can take enclitic copula forms
    neg_parts = [['na', '<PART Polarity=Neg | PronType=Rel>', 'na', 'ná'],
                 ['ni', '<PART Polarity=Neg>', 'ni', 'ní'],
                 ['ṅi', '<PART Polarity=Neg>', 'ni', 'ní'],
                 ['ní', '<PART Polarity=Neg>', 'ni', 'ní']]
    # list all preverbs which can come between a negative particle and a copula form
    neg_preverbs = [['r', '<PVP>', 'r',  'ro'],
                    ['ru', '<PVP>', 'ru', 'ro']]
    # list all parts of speech which are not negative particles and which combine with a following negative copula form
    # (generally a form reduced to zero)
    neg_conjunctions = [['nach',
                         '<SCONJ Polarity=Neg | PronClass=C | PronGend=Neut '
                         '| PronNum=Sing | PronPers=3 | PronType=Prs>',
                         'nach', 'nach'],
                        ['nách',
                         '<SCONJ Polarity=Neg | PronClass=C | PronGend=Neut '
                         '| PronNum=Sing | PronPers=3 | PronType=Prs>',
                         'nach', 'nach'],
                        ['naich',
                         '<SCONJ Polarity=Neg | PronClass=C | PronGend=Neut '
                         '| PronNum=Sing | PronPers=3 | PronType=Prs>',
                         'naich', 'nach'],
                        ['nach', '<SCONJ Polarity=Neg>', 'nach', 'ná'],
                        ['naich', '<SCONJ Polarity=Neg>', 'naich', 'ná']]
    neg_int_pronouns = [['Caní', '<PRON Polarity=Neg | PronType=Int>', 'cani', 'cani']]
    # count the instances of the negative copula form(s) in the gloss
    neg_count = 0
    for tagged_word_data in pos_list:
        split_tagged_pos = split_pos_feats(tagged_word_data[1])
        tagged_short_pos = split_tagged_pos[0]
        tagged_feats = split_tagged_pos[1]
        if tagged_short_pos == "AUX" and all(feat in tagged_feats for feat in ["Polarity=Neg", "VerbType=Cop"]):
            tagged_check_word = [tagged_word_data[0], '<AUX Polarity=Neg | VerbType=Cop>', tagged_word_data[2]]
            if tagged_check_word not in full_neg_list and tagged_check_word not in enclitic_neg_list:
                print(tagged_word_data)
                print([i[0] for i in standard_mapping])
                print([i[0] for i in pos_list])
                print(pos_list)
                raise RuntimeError("New negative copula form")
            # identify forms of the copula which may require changing
            if tagged_check_word in full_neg_list or tagged_check_word in enclitic_neg_list:
                neg_count += 1
    for i in range(neg_count):
        for j, tagged_word_data in enumerate(pos_list):
            tagged_original, tagged_pos, tagged_standard, tagged_head = \
                tagged_word_data[0], tagged_word_data[1], tagged_word_data[2], tagged_word_data[3]
            split_tagged_pos = split_pos_feats(tagged_pos)
            tagged_short_pos = split_tagged_pos[0]
            tagged_feats = split_tagged_pos[1]
            if tagged_short_pos == "AUX" and all(feat in tagged_feats for feat in ["Polarity=Neg", "VerbType=Cop"]):
                tagged_check_word = [tagged_original, '<AUX Polarity=Neg | VerbType=Cop>', tagged_standard]
                if tagged_check_word in full_neg_list or tagged_check_word in enclitic_neg_list:
                    last_pos_place = 1
                    copula_preverbs = list()
                    try:
                        if j != 0:
                            last_pos_data = pos_list[j-last_pos_place]
                            # find any preverbal particles used within the copula form
                            split_last_pos = split_pos_feats(last_pos_data[1])
                            if split_last_pos[0] == "PVP":
                                while split_last_pos[0] == "PVP":
                                    copula_preverbs.append(last_pos_data)
                                    last_pos_place += 1
                                    last_pos_data = pos_list[j-last_pos_place]
                                    split_last_pos = split_pos_feats(last_pos_data[1])
                                    if j-last_pos_place == 0 and split_last_pos[0] == "PVP":
                                        print(last_pos_data)
                                        print(tagged_word_data)
                                        print([k[0] for k in standard_mapping])
                                        print([k[0] for k in pos_list])
                                        raise RuntimeError("Copula preverb is the first POS in the gloss")
                        else:
                            last_pos_data = False
                    except IndexError:
                        last_pos_data = False
                    # if there are preverbs between the negative particle and the copula form
                    if copula_preverbs:
                        # if all preverbs found are in the list of preverbs which can occur within a copula form
                        # join them together into one conjoined preverb
                        check_preverbs = list()
                        for verbal_prefix_data in copula_preverbs:
                            check_preverb = [verbal_prefix_data[0], "<PVP>",
                                             verbal_prefix_data[2], verbal_prefix_data[3]]
                            check_preverbs.append(check_preverb)
                        if all(check_preverb in neg_preverbs for check_preverb in check_preverbs):
                            combined_preverbs = [''.join(pvp[0] for pvp in copula_preverbs),
                                                 ''.join(pvp[2] for pvp in copula_preverbs)]
                            combined_preverb_feats = list()
                            for verbal_prefix_data in copula_preverbs:
                                verbal_prefix_pos = verbal_prefix_data[1]
                                verbal_prefix_feats = split_pos_feats(verbal_prefix_pos)[1]
                                for verbal_prefix_feat in verbal_prefix_feats:
                                    if verbal_prefix_feat not in combined_preverb_feats:
                                        combined_preverb_feats.append(verbal_prefix_feat)
                            # if the combined preverbs occur within the copula form
                            # remove the preverbs from the POS list and leave only the copula form and negative particle
                            # add the features of the combined preverbs to the copula features
                            # do not break out of the loop, the negative particle still needs to be checked
                            if combined_preverbs[0] in tagged_original and combined_preverbs[1] in tagged_standard:
                                tagged_pos = add_features(tagged_pos, combined_preverb_feats)
                                tagged_word_data = [tagged_original, tagged_pos, tagged_standard, tagged_head]
                                pos_list = pos_list[:j-last_pos_place+1] + [tagged_word_data] + pos_list[j+1:]
                            # if the combined preverbs cannot be found within the copula form
                            else:
                                raise RuntimeError("Known preverb(s) not contained in copula form")
                        # if a preverb is found which cannot occur within a copula form
                        else:
                            print(last_pos_data)
                            print(copula_preverbs)
                            print(tagged_word_data)
                            raise RuntimeError("Unknown preverb(s) between negative particle and copula form")
                        # adjust the value of the j variable to accoun for the number of preverbs removed
                        j = j - len(copula_preverbs)
                        last_pos_place = last_pos_place - len(copula_preverbs)
                    # test that removing copula preverbs hasn't affected the placement of the copula form
                    if tagged_word_data != pos_list[j]:
                        print(tagged_word_data)
                        print(pos_list[j])
                        print([k[0] for k in pos_list])
                        raise RuntimeError("Copula placement affected before moving on")
                    if last_pos_data:
                        last_original, last_pos, last_standard, last_head = \
                            last_pos_data[0], last_pos_data[1], last_pos_data[2], last_pos_data[3]
                        split_last_pos = split_pos_feats(last_pos)
                        last_short_pos = split_last_pos[0]
                        last_feats = split_last_pos[1]
                        # if the last POS is a negative particle
                        if last_short_pos == "PART" and "Polarity=Neg" in last_feats:
                            # if the last POS (neg. part.) is the exact same as the following negative copula form
                            # delete the negative particle from the POS list
                            if tagged_original == last_original and tagged_standard == last_standard:
                                del pos_list[j-last_pos_place]
                                combine_subtract = True
                                break
                            # if the last POS is repeated at the beginning of the copula form
                            # delete the negative particle from the POS list
                            elif last_original == tagged_original[:len(last_original)]:
                                del pos_list[j-last_pos_place]
                                combine_subtract = True
                                break
                            # if the last POS (neg. part.) is not at the beginning of the copula form as expected
                            elif last_original in tagged_original and last_standard in tagged_standard:
                                raise RuntimeError("Negative particle not at beginning of copula form")
                            # if the last POS (neg. part.) is not repeated in the following negative form of the copula
                            # join the two forms and update the features of the copula POS tag
                            elif last_pos_data in neg_parts:
                                tagged_pos = add_features(tagged_pos, last_feats)
                                new_neg_cop = [last_original + tagged_original,
                                               tagged_pos,
                                               last_standard + tagged_standard,
                                               tagged_head]
                                pos_list = pos_list[:j-last_pos_place] + [new_neg_cop] + pos_list[j+1:]
                                combine_subtract = True
                                break
                            # if the last POS is not a known negative particle
                            else:
                                print(last_pos_data)
                                print(tagged_word_data)
                                print([k[0] for k in standard_mapping])
                                print([k[0] for k in pos_list])
                                raise RuntimeError("New neg. particle or poss. doubling of particle preceeding copula")
                        # if the last POS is not a negative particle but the copula form is reduced to zero and negative
                        elif tagged_original == "-" and tagged_standard == "-" and tagged_short_pos == 'AUX' \
                                and all(feat in tagged_feats for feat in ["Polarity=Neg", "VerbType=Cop"]):
                            # if the last POS is a known negative conjunction delete the copula form
                            # but combine its features with the preceding conjunction's
                            if last_pos_data in neg_conjunctions:
                                last_pos_data = [last_original,
                                                 add_features(last_pos, tagged_feats, "combine", ["PronType"]),
                                                 last_standard,
                                                 last_head]
                                pos_list[j-last_pos_place] = last_pos_data
                                del pos_list[j]
                                combine_subtract = True
                                break
                            # if the last POS is a known negative interrogative pronoun delete the copula form
                            elif last_pos_data in neg_int_pronouns:
                                del pos_list[j]
                                combine_subtract = True
                                break
                            # if something other than the expected negative parts of speech precede the copula form
                            else:
                                print(last_pos_data)
                                print(tagged_word_data)
                                print([i[0] for i in standard_mapping])
                                raise RuntimeError("Negative form of copula reduced to zero preceded by unknown POS")
                        # if the last POS is not a negative particle but the copula form enclitic and negative
                        elif tagged_check_word in enclitic_neg_list:
                            # if the last POS is a known combining conjunction, other than the negative forms
                            if last_pos_data in conj_combo_forms:
                                print(last_pos_data)
                                print(tagged_word_data)
                                print([k[0] for k in standard_mapping])
                                print([k[0] for k in pos_list])
                                raise RuntimeError("Enclitic negative copula not preceded by negative POS")
                            # if the last POS is a known negative combining conjunction and the copula form is enclitic
                            # combine the copula's features with conjunction's, keeping the conjunction's POS tag
                            # combine the conjunction form with the copula form
                            elif last_pos_data in neg_conj_combo_forms:
                                combined_pos = add_features(last_pos, tagged_feats)
                                new_neg_cop = [last_original + tagged_original,
                                               combined_pos,
                                               last_standard + tagged_standard,
                                               last_head]
                                pos_list = pos_list[:j-last_pos_place] + [new_neg_cop] + pos_list[j+1:]
                                combine_subtract = True
                                break
                            # if any other type of POS precedes the enclitic negative copula form
                            else:
                                print(last_pos_data)
                                print(tagged_word_data)
                                print([k[0] for k in standard_mapping])
                                print([k[0] for k in pos_list])
                                raise RuntimeError("Enclitic negative copula not combined with previous POS")
                        # if the form of the copula is neither in the full nor enclitic negative copula lists
                        elif tagged_check_word not in full_neg_list:
                            print(last_pos_data)
                            print(tagged_word_data)
                            print([k[0] for k in standard_mapping])
                            print([k[0] for k in pos_list])
                            raise RuntimeError("Last POS not negative particle")

    #                                               PART 2.1.1:
    #
    #                                                 VERBS
    #
    # remove doubled particles, etc. before verbs, or add to the verb if not doubled
    # count instances of verbs in the gloss
    verb_independent_POS = ["ADJ", "ADV", "AUX", "DET", "INTJ", "NOUN", "NUM", "PRON", "PROPN", "UNK", "VERB"]
    verb_dependent_POS = ["ADP", "CCONJ", "PART", "SCONJ"]
    # list conjunct and verbal particles which take conjunct forms of the verb (cf. Stifter p.135, 27.7)
    conjunct_particles = [['a', '<PART PronType=Rel>', 'a', 'a'],
                          ['a', '<PART PronType=Dem,Rel>', 'a', 'a'],
                          ['sa', '<PART PronType=Rel>', 'sa', 'a'],
                          ['in', '<PART PronType=Int>', 'in', 'in'],
                          ['na', '<PART Polarity=Neg | PronType=Rel>', 'na', 'ná'],
                          ['ná', '<PART Polarity=Neg | PronType=Rel>', 'na', 'ná'],
                          ['nad', '<PART Polarity=Neg | PronType=Rel>', 'nad', 'nád'],
                          ['nád', '<PART Polarity=Neg | PronType=Rel>', 'nad', 'nád'],
                          ['nnád', '<PART Polarity=Neg | PronType=Rel>', 'nnad', 'nád'],
                          ['ni', '<PART Polarity=Neg>', 'ni', 'ní'],
                          ['ní', '<PART Polarity=Neg>', 'ni', 'ní'],
                          ['Ní', '<PART Polarity=Neg>', 'ni', 'ní'],
                          ['nicon', '<PART Polarity=Neg>', 'nicon', 'nícon'],
                          ['nícon', '<PART Polarity=Neg>', 'nicon', 'nícon'],
                          ['no', '<PART PartType=Vb>', 'no', 'no'],
                          ['nu', '<PART PartType=Vb>', 'nu', 'no']]
    # list preverbs which are sometimes described as verbal particles, but can be compounded within the verbal complex
    verbal_particles = [['ro', '<PVP Aspect=Perf>', 'ro', 'ro']]
    # list conjunctions which take conjunct forms of the verb (cf. Stifter p.248-249, 49.6)
    dependent_conjunctions = [['Ara', '<SCONJ>', 'ara', 'ara'],
                              ['ara', '<SCONJ>', 'ara', 'ara'],
                              ['co', '<SCONJ>', 'co', 'co'],
                              ['con', '<SCONJ>', 'con', 'co'],
                              ['dia', '<SCONJ>', 'dia', 'dia'],
                              ['na', '<SCONJ Polarity=Neg>', 'na', 'ná'],
                              ['nna', '<SCONJ Polarity=Neg>', 'nna', 'ná'],
                              ['nná', '<SCONJ Polarity=Neg>', 'nna', 'ná'],
                              ['nád', '<SCONJ Polarity=Neg>', 'nad', 'nád']]
    # list conjunctions which do not take conjunct forms of the verb (cf. Stifter p.248-249, 49.6)
    independent_conjunctions = [['a', '<SCONJ>', 'a', 'a'],
                                ['abamin', '<CCONJ>', 'abamin', 'afameinn'],
                                ['afamenad', '<CCONJ>', 'afamenad', 'afameinn'],
                                ['acht', '<SCONJ>', 'acht', 'acht'],
                                ['air', '<SCONJ>', 'air', 'ar'],
                                ['Ar', '<SCONJ>', 'ar', 'ar'],
                                ['ar', '<SCONJ>', 'ar', 'ar'],
                                ['airindi', '<SCONJ>', 'airindi', 'arindí'],
                                ['airindí', '<SCONJ>', 'airindi', 'arindí'],
                                ['arindí', '<SCONJ>', 'arindi', 'arindí'],
                                ['amal', '<SCONJ>', 'amal', 'amal'],
                                ['Amal', '<SCONJ>', 'amal', 'amal'],
                                ['bíth', '<SCONJ>', 'bith', 'bíth'],
                                ['cenmitha', '<SCONJ>', 'cenmitha', 'cenmithá'],
                                ['cenmithá', '<SCONJ>', 'cenmitha', 'cenmithá'],
                                ['ce', '<SCONJ>', 'ce', 'cía'],
                                ['ci', '<SCONJ>', 'ci', 'cía'],
                                ['cia', '<SCONJ>', 'cia', 'cía'],
                                ['deg', '<SCONJ>', 'deg', 'deg'],
                                ['immurgu', '<SCONJ>', 'immurgu', 'immurgu'],
                                ['lase', '<SCONJ>', 'lase', 'lase'],
                                ['ma', '<SCONJ>', 'ma', 'má'],
                                ['má', '<SCONJ>', 'ma', 'má'],
                                ['ɫ', '<CCONJ>', 'no', 'nó'],
                                ['⁊', '<CCONJ>', 'ocus', 'ocus'],
                                ['ol', '<SCONJ>', 'ol', 'ol'],
                                ['resiu', '<SCONJ>', 'resiu', 'resíu'],
                                ['sech', '<SCONJ>', 'sech', 'sech'],
                                ['úare', '<SCONJ>', 'uare', 'óre'],
                                ['huare', '<SCONJ>', 'huare', 'óre'],
                                ['húare', '<SCONJ>', 'huare', 'óre']]
    independent_particles = [['i', '<PART PartType=Dct>', 'i', 'í'],
                             ['í', '<PART PartType=Dct>', 'i', 'í'],
                             ['hí', '<PART PartType=Dct>', 'hi', 'í'],
                             ['ní', '<PART PartType=Dct>', 'ni', 'í'],
                             ['neph', '<PART Polarity=Neg | Prefix=Yes>', 'neph', 'neph'],
                             ['ón', '<PART PronType=Dem>', 'on', 'ón'],
                             ['sa', '<PART PronType=Dem>', 'sa', 'so'],
                             ['so', '<PART PronType=Dem>', 'so', 'so'],
                             ['sin', '<PART PronType=Dem>', 'sin', 'sin'],
                             ['ṡin', '<PART PronType=Dem>', 'sin', 'sin'],
                             ['ucut', '<PART PronType=Dem>', 'ucut', 'ucut']]
    # list particles which have previously been compounded by the script below (or above) and need to be passed over
    compounded_particles = [['naṅd', '<PART Polarity=Neg | PronClass=C | PronGend=Neut '
                             '| PronNum=Sing | PronPers=3 | PronType=Prs,Rel>', 'nand', 'ná'],
                            ['nándun', '<PART Polarity=Neg | PronClass=C | PronNum=Plur '
                             '| PronPers=1 | PronType=Prs,Rel>', 'nandun', 'ná'],
                            ['no', '<PART PartType=Vb | PronClass=C | PronGend=Neut '
                             '| PronNum=Sing | PronPers=3 | PronType=Prs>', 'no', 'no'],
                            ['nom', '<PART PartType=Vb | PronClass=A | PronNum=Sing '
                             '| PronPers=1 | PronType=Prs>', 'nom', 'no'],
                            ['nod', '<PART PartType=Vb | PronClass=C | PronGend=Masc '
                             '| PronNum=Sing | PronPers=3 | PronType=Prs>', 'nod', 'no'],
                            ['nod', '<PART PartType=Vb | PronClass=C | PronGend=Neut '
                             '| PronNum=Sing | PronPers=3 | PronType=Prs>', 'nod', 'no'],
                            ['nud', '<PART PartType=Vb | PronClass=C | PronGend=Neut '
                             '| PronNum=Sing | PronPers=3 | PronType=Prs>', 'nud', 'no']]
    # list conjunctions which have previously been compounded by the script above (or below) and need to be passed over
    compounded_conjunctions = [['naich', '<SCONJ Polarity=Neg | PronClass=C | PronGend=Masc '
                                '| PronNum=Sing | PronPers=3 | PronType=Prs>', 'naich', 'nach']]
    # list all parts of speech that relative particles can follow and combine with (cf. Thurn p.312)
    separate_rel_combos = [['hua', '<ADP AdpType=Prep | Definite=Ind>', 'hua', 'ó'],
                           ['húa', '<ADP AdpType=Prep | Definite=Ind>', 'hua', 'ó']]
    # list all parts of speech that relative particles can fall into and disappear (cf. Thurn p.312)
    fall_together_rels = [['i', '<ADP AdpType=Prep | Definite=Ind>', 'i', 'i'],
                          ['hi', '<ADP AdpType=Prep | Definite=Ind>', 'hi', 'i'],
                          ['ó', '<ADP AdpType=Prep | Definite=Ind>', 'o', 'ó'],
                          ['ho', '<ADP AdpType=Prep | Definite=Ind>', 'ho', 'ó']]
    verbcount = 0
    for tagged_word_data in pos_list:
        split_tagged_pos = split_pos_feats(tagged_word_data[1])
        tagged_short_pos = split_tagged_pos[0]
        if tagged_short_pos == "VERB":
            verbcount += 1
    for i in range(verbcount):
        for j, tagged_word_data in enumerate(pos_list):
            tagged_original, tagged_pos, tagged_standard, tagged_head = \
                tagged_word_data[0], tagged_word_data[1], tagged_word_data[2], tagged_word_data[3]
            split_tagged_pos = split_pos_feats(tagged_pos)
            tagged_short_pos = split_tagged_pos[0]
            # if the POS is a verb
            if tagged_short_pos == "VERB":
                # find the preceding part-of-speech or parts-of-speech
                last_pos_place = 1
                verbal_affixes = list()
                try:
                    if j != 0:
                        last_pos_data = pos_list[j-last_pos_place]
                        # find any preverbal particles used within the verb form
                        split_last_pos = split_pos_feats(last_pos_data[1])
                        if split_last_pos[0] in ["PVP", "IFP"] and j-last_pos_place > 0:
                            while split_last_pos[0] in ["PVP", "IFP"]:
                                verbal_affixes.append(last_pos_data)
                                last_pos_place += 1
                                last_pos_data = pos_list[j-last_pos_place]
                                split_last_pos = split_pos_feats(last_pos_data[1])
                                if j-last_pos_place == 0 and split_last_pos[0] == "PVP":
                                    verbal_affixes.append(last_pos_data)
                                    break
                                # check if a preverbal particle precedes a conjunct particle or dependent conjunction
                                elif last_pos_data in conjunct_particles or last_pos_data in dependent_conjunctions:
                                    second_last_data = pos_list[j-last_pos_place-1]
                                    split_sl_pos = split_pos_feats(second_last_data[1])
                                    if split_sl_pos[0] in ["PVP", "IFP"]:
                                        verbal_affixes.append(last_pos_data)
                                        last_pos_place += 1
                                        last_pos_data = pos_list[j-last_pos_place]
                                        split_last_pos = split_pos_feats(last_pos_data[1])
                                        if j-last_pos_place == 0 and split_last_pos[0] == "PVP":
                                            verbal_affixes.append(last_pos_data)
                                            break
                        elif split_last_pos[0] in ["PVP", "IFP"] and j-last_pos_place == 0:
                            verbal_affixes.append(last_pos_data)
                    else:
                        last_pos_data = False
                except IndexError:
                    last_pos_data = False
                # put the list of POS which can be prefixed to a verb in order
                if verbal_affixes:
                    verbal_affixes.reverse()
                # if there is no POS preceding a verb, assume the verb is complete already and move on
                if not last_pos_data:
                    continue
                # if there is a POS preceding a verb form
                elif last_pos_data:
                    last_original, last_pos, last_standard, last_head = \
                        last_pos_data[0], last_pos_data[1], last_pos_data[2], last_pos_data[3]
                    split_last_pos = split_pos_feats(last_pos)
                    last_short_pos = split_last_pos[0]
                    last_feats = split_last_pos[1]
                    # if there are only preverbal particles and infixed pronouns preceding a verb form
                    if last_short_pos == "PVP":
                        if not verbal_affixes:
                            raise RuntimeError("Expected verbal affixes preceding verb form, none found")
                        else:
                            # check if every preverbal particle and infixed pronoun is already in the full verb form
                            # collect any features and add them to the following verb
                            reduced_verbform = tagged_original
                            collected_preverb_feats = list()
                            for verb_prefix_data in verbal_affixes:
                                verb_prefix_original = verb_prefix_data[0]
                                verb_prefix_pos = verb_prefix_data[1]
                                verb_prefix_standard = verb_prefix_data[2]
                                split_verb_prefix = split_pos_feats(verb_prefix_pos)
                                verb_prefix_feats = split_verb_prefix[1]
                                # because the first POS is a PVP itself, if any infixed pronouns precede the verb form
                                # they can simply be treated as any other preverb here
                                # make sure any preverbal affix is in the verb form
                                if verb_prefix_original == reduced_verbform[:len(verb_prefix_original)]:
                                    reduced_verbform = reduced_verbform[len(verb_prefix_original):]
                                elif "n" + verb_prefix_original == reduced_verbform[:len(verb_prefix_original) + 1]:
                                    reduced_verbform = reduced_verbform[len(verb_prefix_original) + 1:]
                                # if the last POS is a verbal particle like 'ro', and no other POS precedes it,
                                # and the verbal particle is not at the beginning of the following verb
                                # everything that follows has to be part of the verb form (break out of the loop)
                                # add the verbal particle to the following verb form
                                # combine its features, and features of all other preverbs, with the verb's features
                                elif verb_prefix_data in verbal_particles and last_pos_data == verb_prefix_data:
                                    tagged_original = verb_prefix_original + tagged_original
                                    tagged_standard = verb_prefix_standard + tagged_standard
                                    for sub_verb_prefix_data in verbal_affixes:
                                        sub_verb_prefix_feats = split_pos_feats(sub_verb_prefix_data[1])[1]
                                        tagged_pos = add_features(tagged_pos, sub_verb_prefix_feats)
                                    tagged_word_data = [tagged_original, tagged_pos, tagged_standard, tagged_head]
                                    break
                                # if the preverb is reduced to zero and has no features to be added to the verb,
                                # move past it without reducing the verb form
                                elif verb_prefix_original == "-":
                                    if verb_prefix_feats:
                                        print(verb_prefix_data)
                                        print(tagged_word_data)
                                        print([k[0] for k in standard_mapping])
                                        print([k[0] for k in pos_list])
                                        raise RuntimeError()
                                    else:
                                        continue
                                # if a preverb or infixed pronoun can't be found where expected in the verb form
                                else:
                                    if last_pos_data != verb_prefix_data:
                                        print(last_pos_data)
                                    print(verb_prefix_data)
                                    print(tagged_word_data)
                                    print([k[0] for k in standard_mapping])
                                    print([k[0] for k in pos_list])
                                    raise RuntimeError("Not all preverbs found in following verb form")
                                # for each prefix in this loop, add its features to a list to be added to the verb's
                                if verb_prefix_feats:
                                    for preverbal_feature in verb_prefix_feats:
                                        if preverbal_feature not in collected_preverb_feats:
                                            collected_preverb_feats.append(preverbal_feature)
                            # if features have been added to the verb form, add them to the POS list
                            if collected_preverb_feats:
                                tagged_pos = add_features(tagged_pos, collected_preverb_feats, "combine", ["PronType"])
                                tagged_word_data = [tagged_original, tagged_pos, tagged_standard, tagged_head]
                            # remove the preverbs and infixed pronouns from the POS list
                            pos_list = pos_list[:j-last_pos_place] + [tagged_word_data] + pos_list[j+1:]
                            combine_subtract = True
                            break
                    # if the last POS is not a combinable type of POS
                    elif last_short_pos in verb_independent_POS:
                        # if there are no preverbal affixes between the last POS and the verb form
                        # assume the last POS and verbal complex cannot be combined and move on
                        if not verbal_affixes:
                            continue
                        # if there are preverbal affixes between the last POS (uncombinable) and the verb form
                        else:
                            first_preverb_data = verbal_affixes[0]
                            first_preverb_original = first_preverb_data[0]
                            first_preverb_standard = first_preverb_data[2]
                            split_first_preverb = split_pos_feats(first_preverb_data[1])
                            first_preverb_short_pos = split_first_preverb[0]
                            first_preverb_feats = split_first_preverb[1]
                            # if there is only one preverbal affix and it is a preverb, not an infixed pronoun
                            if len(verbal_affixes) == 1 and first_preverb_short_pos == "PVP":
                                # if the preverb is already present in the following verb form
                                if first_preverb_original == tagged_original[:len(first_preverb_original)]:
                                    if first_preverb_feats:
                                        tagged_pos = add_features(tagged_pos, first_preverb_feats)
                                        tagged_word_data = [tagged_original, tagged_pos, tagged_standard, tagged_head]
                                    pos_list = pos_list[:j-1] + [tagged_word_data] + pos_list[j+1:]
                                    combine_subtract = True
                                    break
                                # if the preverb has been reduced to zero
                                elif first_preverb_original == "-" and first_preverb_standard == "-":
                                    if first_preverb_feats:
                                        tagged_pos = add_features(tagged_pos, first_preverb_feats)
                                    tagged_word_data = [tagged_original, tagged_pos, tagged_standard, tagged_head]
                                    pos_list = pos_list[:j - 1] + [tagged_word_data] + pos_list[j + 1:]
                                    combine_subtract = True
                                    break
                                # if the preverb is not in the following verb form at all, combine them
                                elif first_preverb_original not in tagged_original:
                                    tagged_original = first_preverb_original + tagged_original
                                    tagged_standard = first_preverb_standard + tagged_standard
                                    if first_preverb_feats:
                                        tagged_pos = add_features(tagged_pos, first_preverb_feats)
                                    tagged_word_data = [tagged_original, tagged_pos, tagged_standard, tagged_head]
                                    pos_list = pos_list[:j-1] + [tagged_word_data] + pos_list[j+1:]
                                    combine_subtract = True
                                    break
                                # if the compounding preverb is present in the following verb form
                                elif first_preverb_original in tagged_original and len(first_preverb_original) > 1:
                                    combined_prepos_orig = ""
                                    combined_prepos_std = ""
                                    for backstep in range(j):
                                        start_position = j - 1 - backstep
                                        backword_data = pos_list[start_position]
                                        backstep_orig = backword_data[0]
                                        combined_prepos_orig = backstep_orig + combined_prepos_orig
                                        backstep_std = backword_data[2]
                                        combined_prepos_std = backstep_std + combined_prepos_std
                                        if combined_prepos_orig == tagged_original[:len(combined_prepos_orig)] \
                                                and combined_prepos_std == tagged_standard[:len(combined_prepos_std)]:
                                            reduced_verb_original = tagged_original[len(combined_prepos_orig):]
                                            reduced_verb_standard = tagged_standard[len(combined_prepos_std):]
                                            tagged_original = first_preverb_original + reduced_verb_original
                                            tagged_standard = first_preverb_standard + reduced_verb_standard
                                            break
                                    if tagged_word_data == [tagged_original, tagged_pos, tagged_standard, tagged_head]:
                                        continue
                                    else:
                                        tagged_word_data = [tagged_original, tagged_pos, tagged_standard, tagged_head]
                                        pos_list[j] = tagged_word_data
                                        del pos_list[j - 1]
                                        combine_subtract = True
                                        break
                                else:
                                    print(last_pos_data)
                                    print(first_preverb_data)
                                    print(tagged_word_data)
                                    print([k[0] for k in standard_mapping])
                                    print([k[0] for k in pos_list])
                                    raise RuntimeError("One conjoining preverb immediately preceding verb form, but "
                                                       "preverb not in initial position in verb form")
                            # if there is only one preverbal affix and it is not a preverbal particle, as expexted
                            elif len(verbal_affixes) == 1 and first_preverb_short_pos != "PVP":
                                print(last_pos_data)
                                print(first_preverb_short_pos)
                                print(first_preverb_data)
                                print(tagged_word_data)
                                print([k[0] for k in standard_mapping])
                                print([k[0] for k in pos_list])
                                raise RuntimeError("Unexpected POS found as only preverbal affix")
                            # if there are more than one preverbal affixes preceding a verb form
                            elif len(verbal_affixes) > 1:
                                # check if every preverbal particle and infixed pronoun is already in the full verb form
                                reduced_verbform = tagged_original
                                for verb_prefix_data in verbal_affixes:
                                    verb_prefix = verb_prefix_data[0]
                                    verb_prefix_pos = verb_prefix_data[1]
                                    split_verb_prefix = split_pos_feats(verb_prefix_pos)
                                    verb_prefix_short_pos = split_verb_prefix[0]
                                    verb_prefix_feats = split_verb_prefix[1]
                                    # check if any infixed pronouns precede the verb form
                                    # if so, add their features to the verb's
                                    if verb_prefix_short_pos == "IFP":
                                        tagged_pos = add_features(tagged_pos, verb_prefix_feats,
                                                                  "combine", ['PronType'])
                                        tagged_word_data = [tagged_original, tagged_pos, tagged_standard, tagged_head]
                                        pos_list[j] = tagged_word_data
                                    # add features from any preverb to the verb's features also
                                    elif verb_prefix_short_pos == "PVP":
                                        try:
                                            tagged_pos = add_features(tagged_pos, verb_prefix_feats)
                                        except RuntimeError:
                                            if "Mood=Pot" in verb_prefix_feats:
                                                tagged_pos = add_features(tagged_pos, verb_prefix_feats,
                                                                          "combine", ["Mood"])
                                            else:
                                                tagged_pos = add_features(tagged_pos, verb_prefix_feats)
                                        tagged_word_data = [tagged_original, tagged_pos, tagged_standard, tagged_head]
                                        pos_list[j] = tagged_word_data
                                    # check if the preverbal affix is in the verb form
                                    if verb_prefix == reduced_verbform[:len(verb_prefix)]:
                                        reduced_verbform = reduced_verbform[len(verb_prefix):]
                                    elif "ṅ" + verb_prefix == reduced_verbform[:len(verb_prefix) + 1] \
                                            or "n" + verb_prefix == reduced_verbform[:len(verb_prefix) + 1]:
                                        reduced_verbform = reduced_verbform[len(verb_prefix) + 1:]
                                    # if the preverbal affix begins with an f, check that it's not lenited in the verb
                                    elif verb_prefix[0] == 'f' \
                                            and 'ḟ' + verb_prefix[1:] == reduced_verbform[:len(verb_prefix)]:
                                        reduced_verbform = reduced_verbform[len(verb_prefix):]
                                    # if the preverb is reduced to zero, move past it without reducing the verb form
                                    elif verb_prefix == "-":
                                        continue
                                    # if a preverb or infixed pronoun can't be found where expected in the verb form
                                    else:
                                        print(last_pos_data)
                                        print(verb_prefix)
                                        print(reduced_verbform)
                                        print(tagged_word_data)
                                        print([k[0] for k in standard_mapping])
                                        print([k[0] for k in pos_list])
                                        raise RuntimeError("Not all preverbs found in following verb form")
                                # remove the preverbs and infixed pronouns from the POS list
                                pos_list = pos_list[:j-last_pos_place+1] + pos_list[j:]
                                combine_subtract = True
                                break
                            else:
                                print(last_pos_data)
                                print(first_preverb_data)
                                print(tagged_word_data)
                                print([k[0] for k in standard_mapping])
                                print([k[0] for k in pos_list])
                                raise RuntimeError("Unexpected number of preverbs/infixes preceding verb form")
                    # if the last POS is a combinable type of POS
                    elif last_short_pos in verb_dependent_POS:
                        # if the last POS is a conjunct particle or combining conjunction
                        # separate it from the verbal cluster
                        # treat any infixed pronouns as suffixed pronouns to the conjunct particle
                        if last_pos_data in conjunct_particles or last_pos_data in dependent_conjunctions:
                            # if there are no preverbs or infixed pronouns between the conjunct particle and the verb
                            # ensure the conjunct particle is not represented in the verb form
                            if not verbal_affixes:
                                # if the conjunct particle is at the beginning of the verb form, reduce the verb form
                                if last_original == tagged_original[:len(last_original)] and len(last_original) > 1:
                                    tagged_original = tagged_original[len(last_original):]
                                    tagged_standard = tagged_standard[len(last_standard):]
                                    tagged_word_data = [tagged_original, tagged_pos, tagged_standard, tagged_head]
                                    pos_list[j] = tagged_word_data
                                    combine_subtract = True
                                    break
                                # if the conjunct particle is in the verb form but not at the beginning of it,
                                # see if any combination of preceding words with the conjunct particle are
                                # if so, reduce the verb form
                                elif last_original in tagged_original and len(last_original) > 1:
                                    combined_prepos_orig = ""
                                    combined_prepos_std = ""
                                    for backstep in range(j):
                                        start_position = j - 1 - backstep
                                        backword_data = pos_list[start_position]
                                        backstep_orig = backword_data[0]
                                        combined_prepos_orig = backstep_orig + combined_prepos_orig
                                        backstep_std = backword_data[2]
                                        combined_prepos_std = backstep_std + combined_prepos_std
                                        if combined_prepos_orig == tagged_original[:len(combined_prepos_orig)] \
                                                and combined_prepos_std == tagged_standard[:len(combined_prepos_std)]:
                                            tagged_original = tagged_original[len(combined_prepos_orig):]
                                            tagged_standard = tagged_standard[len(combined_prepos_std):]
                                            break
                                    if tagged_word_data == [tagged_original, tagged_pos, tagged_standard, tagged_head]:
                                        continue
                                    else:
                                        tagged_word_data = [tagged_original, tagged_pos, tagged_standard, tagged_head]
                                        pos_list[j] = tagged_word_data
                                        combine_subtract = True
                                        break
                                # if the conjunct particle is a relative particle which has not been reduced to zero
                                # and the preceding POS is a preposition, combine them and check if the combination
                                # is at the beginning of the following verb form, if so remove it from the verb form
                                elif last_pos == '<PART PronType=Rel>':
                                    backword_data = pos_list[j-last_pos_place-1]
                                    backword_original = backword_data[0]
                                    backword_pos = backword_data[1]
                                    backword_standard = backword_data[2]
                                    if backword_pos == '<ADP AdpType=Prep | Definite=Ind>':
                                        combined_last_original = backword_original + last_original
                                        combined_last_standard = backword_standard + last_standard
                                        if combined_last_original == tagged_original[:len(combined_last_original)]:
                                            tagged_original = tagged_original[len(combined_last_original):]
                                            tagged_standard = tagged_standard[len(combined_last_standard):]
                                            tagged_word_data = [tagged_original, tagged_pos,
                                                                tagged_standard, tagged_head]
                                            pos_list[j] = tagged_word_data
                                            combine_subtract = True
                                            break
                                # if the conjunct particle is not in the verb form
                                else:
                                    continue
                            # if preverbs and/or infixed pronouns follow the conjunct particle
                            elif verbal_affixes:
                                # if the conjunct particle is at the beginning of the verb form, reduce the verb form
                                if last_original == tagged_original[:len(last_original)] and len(last_original) > 1:
                                    tagged_original = tagged_original[len(last_original):]
                                    tagged_standard = tagged_standard[len(last_standard):]
                                    tagged_word_data = [tagged_original, tagged_pos, tagged_standard, tagged_head]
                                    pos_list[j] = tagged_word_data
                                # if the conjunct particle is a relative particle and not reduced to zero
                                elif last_original != "-" and "PronType=Rel" in last_feats:
                                    second_last_data = pos_list[j - last_pos_place - 1]
                                    sl_original = second_last_data[0]
                                    sl_pos = second_last_data[1]
                                    sl_standard = second_last_data[2]
                                    split_sl_pos = split_pos_feats(sl_pos)
                                    sl_short_pos = split_sl_pos[0]
                                    # if the POS before relative particle is a preposition which can combine with it
                                    if sl_short_pos == "ADP":
                                        sl_combo_original = sl_original + last_original
                                        sl_combo_standard = sl_standard + last_standard
                                        # if the combination of preposition and relative particle is at the beginning
                                        # of the following verb form, reduce the verb form
                                        if sl_combo_original == tagged_original[:len(sl_combo_original)]:
                                            tagged_original = tagged_original[len(sl_combo_original):]
                                            tagged_standard = tagged_standard[len(sl_combo_standard):]
                                            tagged_word_data = [tagged_original, tagged_pos,
                                                                tagged_standard, tagged_head]
                                            pos_list[j] = tagged_word_data
                                # find out what the first POS following the conjunct particle is
                                first_affix_data = verbal_affixes[0]
                                first_affix_original = first_affix_data[0]
                                first_affix_pos = first_affix_data[1]
                                first_affix_standard = first_affix_data[2]
                                split_first_affix = split_pos_feats(first_affix_pos)
                                first_affix_short_pos = split_first_affix[0]
                                first_affix_feats = split_first_affix[1]
                                # if the first POS following the conjunct particle is a preverbal particle
                                # separate the conjunct particle and let the verb begin with the preverbal particle
                                if first_affix_short_pos == "PVP":
                                    # check if every preverbal affix is already in the full verb form
                                    reduced_verbform = tagged_original
                                    for verb_prefix_data in verbal_affixes:
                                        verb_prefix = verb_prefix_data[0]
                                        verb_prefix_pos = verb_prefix_data[1]
                                        split_verb_prefix = split_pos_feats(verb_prefix_pos)
                                        verb_prefix_short_pos = split_verb_prefix[0]
                                        verb_prefix_feats = split_verb_prefix[1]
                                        if verb_prefix_short_pos == "IFP":
                                            print(last_pos_data)
                                            print(verb_prefix_data)
                                            print(tagged_word_data)
                                            print([k[0] for k in standard_mapping])
                                            print([k[0] for k in pos_list])
                                            raise RuntimeError("IFP found following initial preverb instead of conjunct"
                                                               " particle, unexpected in this position.")
                                        # if the preverb is at the beginning of the verb form, reduce the verb form
                                        if verb_prefix == reduced_verbform[:len(verb_prefix)]:
                                            reduced_verbform = reduced_verbform[len(verb_prefix):]
                                            if verb_prefix_feats:
                                                try:
                                                    tagged_pos = add_features(tagged_pos, verb_prefix_feats)
                                                except RuntimeError:
                                                    if "Mood=Pot" in verb_prefix_feats:
                                                        tagged_pos = add_features(tagged_pos, verb_prefix_feats,
                                                                                  "combine", ["Mood"])
                                                    else:
                                                        tagged_pos = add_features(tagged_pos, verb_prefix_feats)
                                                tagged_word_data = [tagged_original, tagged_pos,
                                                                    tagged_standard, tagged_head]
                                                pos_list[j] = tagged_word_data
                                        # if the preverb is reduced to zero, move past it without reducing the verb form
                                        elif verb_prefix == "-":
                                            if verb_prefix_feats:
                                                print(verb_prefix_data)
                                                raise RuntimeError("Prefix features must be added to verb")
                                            else:
                                                continue
                                        # if the first preverb following a conjunct particle is in the verb form
                                        # but not in the initial position
                                        # combine preceding particles to see if any combo is in initial position
                                        # if so, remove it from the verb original and standard forms before progressing
                                        elif verb_prefix in reduced_verbform and verb_prefix_data == first_affix_data:
                                            combined_prepos_orig = ""
                                            combined_prepos_std = ""
                                            for backstep in range(j):
                                                start_position = j - 1 - backstep - len(verbal_affixes)
                                                backword_data = pos_list[start_position]
                                                # check to see that no further PVPs precede the conjunct particle
                                                # as part of the same verbal complex
                                                backward_short_pos = split_pos_feats(backword_data[1])[0]
                                                if backward_short_pos in ["IFP", "PVP"]:
                                                    print(backword_data)
                                                    print(last_pos_data)
                                                    print(tagged_word_data)
                                                    print([k[0] for k in standard_mapping])
                                                    print([k[0] for k in pos_list])
                                                    raise RuntimeError(
                                                        "Verbal complex may be extended beyond conjunct particle")
                                                backstep_orig = backword_data[0]
                                                combined_prepos_orig = backstep_orig + combined_prepos_orig
                                                backstep_std = backword_data[2]
                                                combined_prepos_std = backstep_std + combined_prepos_std
                                                backstep_pos = backword_data[1]
                                                # if a relative particle is found,
                                                # assume it is preceded by a preposition and add that too
                                                if backstep_pos == '<PART PronType=Rel>':
                                                    start_position = j-2-backstep-len(verbal_affixes)
                                                    backword_data = pos_list[start_position]
                                                    backstep_orig = backword_data[0]
                                                    combined_prepos_orig = backstep_orig + combined_prepos_orig
                                                    backstep_std = backword_data[2]
                                                    combined_prepos_std = backstep_std + combined_prepos_std
                                                if combined_prepos_orig == tagged_original[:len(
                                                        combined_prepos_orig)] \
                                                        and combined_prepos_std == tagged_standard[:len(
                                                        combined_prepos_std)]:
                                                    tagged_original = tagged_original[len(combined_prepos_orig):]
                                                    reduced_verbform = tagged_original
                                                    tagged_standard = tagged_standard[len(combined_prepos_std):]
                                                    tagged_word_data = [tagged_original, tagged_pos,
                                                                        tagged_standard, tagged_head]
                                                    pos_list[j] = tagged_word_data
                                                    break
                                            if verb_prefix == reduced_verbform[:len(verb_prefix)]:
                                                reduced_verbform = reduced_verbform[len(verb_prefix):]
                                                if verb_prefix_feats:
                                                    try:
                                                        tagged_pos = add_features(tagged_pos, verb_prefix_feats)
                                                    except RuntimeError:
                                                        if "Mood=Pot" in verb_prefix_feats:
                                                            tagged_pos = add_features(tagged_pos, verb_prefix_feats,
                                                                                      "combine", ["Mood"])
                                                        else:
                                                            tagged_pos = add_features(tagged_pos, verb_prefix_feats)
                                                    tagged_word_data = [tagged_original, tagged_pos,
                                                                        tagged_standard, tagged_head]
                                                    pos_list[j] = tagged_word_data
                                            # if Bauer added the preverb to his analysis but not the nasalisation marker
                                            elif "ṅ" + verb_prefix == reduced_verbform[:len(verb_prefix) + 1] \
                                                    or "n" + verb_prefix == reduced_verbform[:len(verb_prefix) + 1]:
                                                reduced_verbform = reduced_verbform[len(verb_prefix) + 1:]
                                                if verb_prefix_feats:
                                                    tagged_pos = add_features(tagged_pos, verb_prefix_feats)
                                                    tagged_word_data = [tagged_original, tagged_pos,
                                                                        tagged_standard, tagged_head]
                                                    pos_list[j] = tagged_word_data
                                            else:
                                                print(reduced_verbform, verb_prefix)
                                                print(last_pos_data)
                                                print(tagged_word_data)
                                                print([k[0] for k in standard_mapping])
                                                print([k[0] for k in pos_list])
                                                raise RuntimeError("Not all preverbs found in following verb form")
                                        # if the first preverb following a conjunct particle is not in the verb form
                                        elif verb_prefix not in reduced_verbform:
                                            print(verb_prefix)
                                            print(reduced_verbform)
                                            print(tagged_word_data)
                                            print([k[0] for k in standard_mapping])
                                            print([k[0] for k in pos_list])
                                            raise RuntimeError("Not all preverbs found in following verb form")
                                        # if a preverb or infixed pronoun can't be found where expected in the verb form
                                        else:
                                            print(verb_prefix)
                                            print(reduced_verbform)
                                            print(tagged_word_data)
                                            print([k[0] for k in standard_mapping])
                                            print([k[0] for k in pos_list])
                                            raise RuntimeError("Not all preverbs found in following verb form")
                                    # remove the preverbs and infixed pronouns from the POS list
                                    pos_list = pos_list[:j-last_pos_place+1] + pos_list[j:]
                                    combine_subtract = True
                                    break
                                # if the first POS following the conjunct particle is an infixed pronoun
                                # suffix it to the conjunct particle and separate both from the verb
                                # then ensure any remaining preverbs aren't repeated in the verb form
                                elif first_affix_short_pos == "IFP":
                                    # if the infixed pronoun is reduced to zero after the conjunct particle
                                    if first_affix_original == "-" and first_affix_standard == "-":
                                        combined_last_original = last_original
                                        combined_last_standard = last_standard
                                    else:
                                        combined_last_original = last_original + first_affix_original
                                        combined_last_standard = last_standard + first_affix_standard
                                    combined_last_pos = add_features(last_pos, first_affix_feats,
                                                                     "combine", ['PronType'])
                                    combined_last_data = [combined_last_original,
                                                          combined_last_pos,
                                                          combined_last_standard,
                                                          last_head]
                                    # if the combined conjunct particle and now-suffixed pronoun were in the verb form
                                    # the conjunct particle will likely have been removed above
                                    # test to make sure their combination is not still at the beginning of the verb form
                                    if combined_last_original == tagged_original[:len(combined_last_original)]:
                                        print(verbal_affixes)
                                        print(combined_last_data)
                                        print(tagged_word_data)
                                        print([k[0] for k in standard_mapping])
                                        print([k[0] for k in pos_list])
                                        raise RuntimeError("Combined conjunct particle and pronoun found in verb form "
                                                           "after conjunct particle should have been removed.")
                                    # if the combined conjunct particle and pronoun are found within the verb form
                                    # remove them, and anything preceding them, at this point
                                    elif combined_last_original in tagged_original:
                                        tagged_original = tagged_original[tagged_original.find(
                                            combined_last_original) + len(combined_last_original):]
                                        tagged_standard = tagged_standard[tagged_standard.find(
                                            combined_last_standard) + len(combined_last_standard):]
                                        tagged_word_data = [tagged_original, tagged_pos, tagged_standard, tagged_head]
                                        pos_list[j] = tagged_word_data
                                    # if the infixed pronoun is at the beginning of the following verb form, remove it
                                    # do not add the pronoun's features to the verb's
                                    if first_affix_original == tagged_original[:len(first_affix_original)]:
                                        # delete the IFP from the verbal affixes
                                        del verbal_affixes[0]
                                        # check that any remaining preverbal affix is a preverb
                                        # add any features to the verb
                                        reduced_verbform = tagged_original[len(first_affix_original):]
                                        for remaining_affix in verbal_affixes:
                                            remaining_affix_original = remaining_affix[0]
                                            remaining_affix_pos = remaining_affix[1]
                                            split_remaining_affix = split_pos_feats(remaining_affix_pos)
                                            remaining_affix_short_pos = split_remaining_affix[0]
                                            remaining_affix_feats = split_remaining_affix[1]
                                            # ensure all following affixes are preverbs
                                            if remaining_affix_short_pos != "PVP":
                                                raise RuntimeError("Unexpected POS among remaining verbal affixes")
                                            elif remaining_affix_original == \
                                                    reduced_verbform[:len(remaining_affix_original)]:
                                                reduced_verbform = reduced_verbform[len(remaining_affix_original):]
                                            elif "n" + remaining_affix_original == \
                                                    reduced_verbform[:len(remaining_affix_original) + 1]:
                                                reduced_verbform = reduced_verbform[len(remaining_affix_original) + 1:]
                                            elif remaining_affix_original == "-":
                                                pass
                                            else:
                                                print(remaining_affix_original)
                                                print(reduced_verbform)
                                                print(tagged_word_data)
                                                print([k[0] for k in standard_mapping])
                                                print([k[0] for k in pos_list])
                                                raise RuntimeError("Prefix not found in following verb form")
                                            # add any preverbs' features to the verb's
                                            if remaining_affix_feats:
                                                tagged_pos = add_features(tagged_pos, remaining_affix_feats)
                                        tagged_original = tagged_original[len(first_affix_original):]
                                        tagged_standard = tagged_standard[len(first_affix_standard):]
                                        tagged_word_data = [tagged_original, tagged_pos, tagged_standard, tagged_head]
                                        pos_list = pos_list[:j-last_pos_place] + [combined_last_data] + \
                                                   [tagged_word_data] + pos_list[j+1:]
                                        combine_subtract = True
                                        break
                                    # if the infixed pronoun can't be found within the following verb form,
                                    # replace the separate particle and pronoun with the combined form
                                    # if there are no further preverbal affixes, leave the verb form alone
                                    else:
                                        # if the only preverbal affix is the infixed pronoun
                                        if len(verbal_affixes) == 1:
                                            pos_list = pos_list[:j-last_pos_place] + [combined_last_data] + pos_list[j:]
                                            combine_subtract = True
                                            break
                                        elif len(verbal_affixes) > 1:
                                            # delete the IFP from the verbal affixes
                                            del verbal_affixes[0]
                                            # check that any remaining preverbal affix is a preverb and add its features
                                            # to the verb
                                            reduced_verbform = tagged_original
                                            for remaining_affix in verbal_affixes:
                                                remaining_affix_original = remaining_affix[0]
                                                remaining_affix_pos = remaining_affix[1]
                                                split_remaining_affix = split_pos_feats(remaining_affix_pos)
                                                remaining_affix_short_pos = split_remaining_affix[0]
                                                remaining_affix_feats = split_remaining_affix[1]
                                                # ensure all following affixes are preverbs
                                                if remaining_affix_short_pos != "PVP":
                                                    raise RuntimeError("Unexpected POS among remaining verbal affixes")
                                                if remaining_affix_original == \
                                                        reduced_verbform[:len(remaining_affix_original)]:
                                                    reduced_verbform = reduced_verbform[len(remaining_affix_original):]
                                                else:
                                                    print(remaining_affix_original)
                                                    print(reduced_verbform)
                                                    print(tagged_word_data)
                                                    print([k[0] for k in standard_mapping])
                                                    print([k[0] for k in pos_list])
                                                    raise RuntimeError("Prefix not found in following verb form")
                                                # add any preverbs' features to the verb's
                                                if remaining_affix_feats:
                                                    tagged_pos = add_features(tagged_pos, remaining_affix_feats)
                                            tagged_word_data = [tagged_original, tagged_pos,
                                                                tagged_standard, tagged_head]
                                            pos_list = pos_list[:j-last_pos_place] + [combined_last_data] + \
                                                       [tagged_word_data] + pos_list[j+1:]
                                            combine_subtract = True
                                            break
                                        else:
                                            print(last_pos_data)
                                            print(combined_last_data)
                                            print(verbal_affixes)
                                            print(tagged_word_data)
                                            print([k[0] for k in standard_mapping])
                                            print([k[0] for k in pos_list])
                                            raise RuntimeError("Could not fix verb form following infixed pronoun")
                                else:
                                    print(last_pos_data)
                                    print(first_affix_data)
                                    print(tagged_word_data)
                                    print([k[0] for k in standard_mapping])
                                    print([k[0] for k in pos_list])
                                    raise RuntimeError("Conjunct particle followed by unexpected POS")
                        # if the last POS preceding a verb form and any preverbal affixes is an independent conjunction
                        # a conjunction with a combined copula form, or a particle which cannot be combined with
                        # dependent verb forms
                        elif last_pos_data in independent_conjunctions or last_pos_data in independent_particles \
                                or last_short_pos == "SCONJ" and "VerbType=Cop" in last_feats:
                            # if there are no preverbs or infixed pronouns between the conjunction and the verb
                            # ensure the conjunction is not represented in the verb form
                            if not verbal_affixes:
                                if last_original != tagged_original[:len(last_original)]:
                                    continue
                                else:
                                    print(last_pos_data)
                                    print(tagged_word_data)
                                    print([k[0] for k in standard_mapping])
                                    print([k[0] for k in pos_list])
                                    raise RuntimeError("Conjunction repeated in verb form")
                            # if there are preverbs or infixed pronouns
                            else:
                                # check if every preverbal particle and infixed pronoun is already in the full verb form
                                reduced_verbform = tagged_original
                                for verb_prefix_data in verbal_affixes:
                                    verb_prefix = verb_prefix_data[0]
                                    verb_prefix_pos = verb_prefix_data[1]
                                    split_verb_prefix = split_pos_feats(verb_prefix_pos)
                                    verb_prefix_short_pos = split_verb_prefix[0]
                                    verb_prefix_feats = split_verb_prefix[1]
                                    # if an infixed pronoun is found not to be following an initial preverb
                                    if verb_prefix_short_pos == "IFP" and verb_prefix_data != verbal_affixes[1]:
                                        print(last_pos_data)
                                        print(verbal_affixes)
                                        print(tagged_word_data)
                                        print([k[0] for k in standard_mapping])
                                        print([k[0] for k in pos_list])
                                        raise RuntimeError("IFP found in unexpected position")
                                    # if the independent conjunction is added to the beginning of the verb form
                                    # remove it, do not break out of the loop
                                    indie_conj_combo = last_original + verb_prefix
                                    if indie_conj_combo == tagged_original[:len(indie_conj_combo)]:
                                        tagged_original = tagged_original[len(last_original):]
                                        tagged_standard = tagged_standard[len(last_standard):]
                                        tagged_word_data = [tagged_original, tagged_pos, tagged_standard, tagged_head]
                                        pos_list[j] = tagged_word_data
                                        reduced_verbform = tagged_original
                                        combine_subtract = True
                                    # because the preceding POS is separate from the verbal complex any infixed pronouns
                                    # will occur after an initial preverb, so they can be treated like any other preverb
                                    # make sure any preverbal affix is in the verb form
                                    if verb_prefix == reduced_verbform[:len(verb_prefix)]:
                                        reduced_verbform = reduced_verbform[len(verb_prefix):]
                                        if verb_prefix_feats:
                                            tagged_pos = add_features(tagged_pos, verb_prefix_feats,
                                                                      "combine", ["PronType"])
                                            tagged_word_data = [tagged_original, tagged_pos,
                                                                tagged_standard, tagged_head]
                                            pos_list[j] = tagged_word_data
                                    # if Bauer added the preverb to his analysis but not the nasalisation marker
                                    elif "n" + verb_prefix == reduced_verbform[:len(verb_prefix) + 1]:
                                        reduced_verbform = reduced_verbform[len(verb_prefix) + 1:]
                                        if verb_prefix_feats:
                                            tagged_pos = add_features(tagged_pos, verb_prefix_feats)
                                            tagged_word_data = [tagged_original, tagged_pos,
                                                                tagged_standard, tagged_head]
                                            pos_list[j] = tagged_word_data
                                    # if the preverbal affix begins with an f, check that it's not lenited in the verb
                                    elif verb_prefix[0] == 'f' \
                                            and 'ḟ' + verb_prefix[1:] == reduced_verbform[:len(verb_prefix)]:
                                        reduced_verbform = reduced_verbform[len(verb_prefix):]
                                        if verb_prefix_feats:
                                            tagged_pos = add_features(tagged_pos, verb_prefix_feats)
                                            tagged_word_data = [tagged_original, tagged_pos,
                                                                tagged_standard, tagged_head]
                                            pos_list[j] = tagged_word_data
                                    # if the preverb is reduced to zero, move past it without reducing the verb form
                                    elif verb_prefix == "-":
                                        if verb_prefix_feats:
                                            tagged_pos = add_features(tagged_pos, verb_prefix_feats)
                                            tagged_word_data = [tagged_original, tagged_pos,
                                                                tagged_standard, tagged_head]
                                            print(pos_list)
                                            pos_list[j] = tagged_word_data
                                            print(pos_list)
                                            raise RuntimeError("Prefix features must be added to verb")
                                        else:
                                            continue
                                    # if a preverb or infixed pronoun can't be found where expected in the verb form
                                    else:
                                        print(verb_prefix)
                                        print(reduced_verbform)
                                        print(tagged_word_data)
                                        print([k[0] for k in standard_mapping])
                                        print([k[0] for k in pos_list])
                                        raise RuntimeError("Not all preverbs found in following verb form")
                                # remove the preverbs and infixed pronouns from the POS list
                                pos_list = pos_list[:j-last_pos_place+1] + pos_list[j:]
                                combine_subtract = True
                                break
                        # if the last POS preceding the verb form is reduced to zero
                        elif last_original == "-" and last_standard == "-":
                            second_last_data = pos_list[j-last_pos_place-1]
                            sl_original = second_last_data[0]
                            sl_pos = second_last_data[1]
                            sl_standard = second_last_data[2]
                            sl_head = second_last_data[3]
                            split_sl_pos = split_pos_feats(sl_pos)
                            sl_short_pos = split_sl_pos[0]
                            # if the second last POS before the verb is a preposition into which the relative particle
                            # can fall and the zero particle is a relative particle, combine the features of the
                            # particle with the preceding POS and delete the zero particle
                            if second_last_data in fall_together_rels and "PronType=Rel" in last_feats:
                                sl_pos = add_features(sl_pos, last_feats)
                                second_last_data = [sl_original, sl_pos, sl_standard, sl_head]
                                # check that the prepositional relative particle is not doubled in the verb form
                                if sl_original == tagged_original[:len(sl_original)] \
                                        and sl_standard == tagged_standard[:len(sl_standard)]:
                                    tagged_original = tagged_original[len(sl_original):]
                                    tagged_standard = tagged_standard[len(sl_standard):]
                                    tagged_word_data = [tagged_original, tagged_pos, tagged_standard, tagged_head]
                                rel_prep_combo = [second_last_data, tagged_word_data]
                                pos_list = pos_list[:j-last_pos_place-1] + rel_prep_combo + pos_list[j+1:]
                                combine_subtract = True
                                break
                            # if the second last POS before the verb is a preposition with which the relative particle
                            # can combine and the zero particle is a relative particle, check if the relative particle
                            # is already attached to the end of the second last POS, if so separate the two
                            elif second_last_data in separate_rel_combos and "PronType=Rel" in last_feats:
                                # check that the prepositional relative particle is not doubled in the verb form
                                if sl_original == tagged_original[:len(sl_original)] \
                                        and sl_standard == tagged_standard[:len(sl_standard)]:
                                    tagged_original = tagged_original[len(sl_original):]
                                    tagged_standard = tagged_standard[len(sl_standard):]
                                    tagged_word_data = [tagged_original, tagged_pos, tagged_standard, tagged_head]
                                if sl_original[-1] == 'a' and sl_standard[-1] == 'a':
                                    sl_original, sl_standard = sl_original[:-1], sl_standard[:-1]
                                    second_last_data = [sl_original, sl_pos, sl_standard, sl_head]
                                    last_pos_data = ['a', last_pos, 'a', last_head]
                                else:
                                    print(second_last_data)
                                    print(last_pos_data)
                                    print(tagged_word_data)
                                    print([k[0] for k in standard_mapping])
                                    print([k[0] for k in pos_list])
                                    raise RuntimeError()
                                rel_prep_combo = [second_last_data, last_pos_data, tagged_word_data]
                                pos_list = pos_list[:j - last_pos_place - 1] + rel_prep_combo + pos_list[j + 1:]
                                combine_subtract = True
                                break
                            # if the second last POS before the verb is a preverbal particle and the zero particle
                            # is a relative particle, combine the relative particle's features with the verb's
                            # remove the relative particle and preceding preverb from the POS list
                            elif sl_short_pos == "PVP" and "PronType=Rel" in last_feats:
                                tagged_pos = add_features(tagged_pos, last_feats)
                                tagged_word_data = [tagged_original, tagged_pos, tagged_standard, tagged_head]
                                pos_list = pos_list[:j-last_pos_place-1] + [tagged_word_data] + pos_list[j+1:]
                                combine_subtract = True
                                break
                            else:
                                print(second_last_data)
                                print(last_pos_data)
                                print(tagged_word_data)
                                print([k[0] for k in standard_mapping])
                                print([k[0] for k in pos_list])
                                raise RuntimeError("Empty relative particle preceded by unknown form, add to list")
                        # if the verb is preceded by a prepositional relative particle
                        # this verb has already been processed (directly above) and should be passed over
                        elif last_short_pos == "ADP" and "PronType=Rel" in last_feats:
                            continue
                        # if the verb is preceded by a preposition without a relative particle
                        elif last_short_pos == "ADP":
                            # if the preposition is repeated at the beginning of the following verb form
                            # remove the doubled preposition from the verb form and leave it stand separately
                            if last_original == tagged_original[:len(last_original)] \
                                    and last_standard == tagged_standard[:len(last_standard)]:
                                tagged_original = tagged_original[len(last_original):]
                                tagged_standard = tagged_standard[len(last_standard):]
                                tagged_word_data = [tagged_original, tagged_pos, tagged_standard, tagged_head]
                                pos_list[j] = tagged_word_data
                                if not verbal_affixes:
                                    pass
                                elif len(verbal_affixes) == 1:
                                    first_preverb_data = verbal_affixes[0]
                                    first_preverb_original = first_preverb_data[0]
                                    split_first_preverb = split_pos_feats(first_preverb_data[1])
                                    first_preverb_short_pos = split_first_preverb[0]
                                    first_preverb_feats = split_first_preverb[1]
                                    if first_preverb_short_pos != "PVP":
                                        raise RuntimeError("first verbal affix following preposition is not a preverb")
                                    if first_preverb_original == tagged_original[:len(first_preverb_original)]:
                                        if first_preverb_feats:
                                            tagged_pos = add_features(tagged_pos, first_preverb_feats)
                                            tagged_word_data = [tagged_original, tagged_pos,
                                                                tagged_standard, tagged_head]
                                        pos_list = pos_list[:j-1] + [tagged_word_data] + pos_list[j+1:]
                                    else:
                                        print(last_pos_data)
                                        print(verbal_affixes)
                                        print(tagged_word_data)
                                        print([k[0] for k in standard_mapping])
                                        print([k[0] for k in pos_list])
                                        raise RuntimeError("Could not find preverb in following verb form")
                                else:

                                    reduced_verbform = tagged_original
                                    for affix_data in verbal_affixes:
                                        affix_original = affix_data[0]
                                        split_affix = split_pos_feats(affix_data[1])
                                        affix_feats = split_affix[1]
                                        if affix_original == reduced_verbform[:len(affix_original)]:
                                            reduced_verbform = reduced_verbform[len(affix_original):]
                                        else:
                                            print(affix_original)
                                            print(reduced_verbform)
                                            print([k[0] for k in standard_mapping])
                                            print([k[0] for k in pos_list])
                                            raise RuntimeError("Could not find preverb in verb form")
                                        if affix_feats:
                                            tagged_pos = add_features(tagged_pos, affix_feats)
                                    tagged_word_data = [tagged_original, tagged_pos, tagged_standard, tagged_head]
                                    pos_list = pos_list[:j-last_pos_place+1] + [tagged_word_data] + pos_list[j+1:]
                                    combine_subtract = True
                                    break
                                combine_subtract = True
                                break
                            # if the preposition is not repeated at the beginning of the following verb form
                            # but does occur within it
                            elif last_original in tagged_original:
                                # if there are no verbal affixes between a preposition and following verb,
                                # assume the preposition would be at the start of the verb only
                                # test for nasalisation before the preposition, otherwise move on
                                if not verbal_affixes:
                                    if last_original == tagged_original[1:len(last_original) + 1] \
                                            and tagged_original[0] in ["n", "ṅ"]:
                                        print(last_pos_data)
                                        print(verbal_affixes)
                                        print(tagged_word_data)
                                        print([k[0] for k in standard_mapping])
                                        print([k[0] for k in pos_list])
                                        raise RuntimeError("Possible nasalisation on preposition preceding verb form")
                                    else:
                                        continue
                                # if there are verbal affixes but there may also be a preposition in the verb form
                                elif last_original == tagged_original[1:len(last_original) + 1] \
                                        and tagged_original[0] in ["n", "ṅ"]:
                                    print(last_pos_data)
                                    print(verbal_affixes)
                                    print(tagged_word_data)
                                    print([k[0] for k in standard_mapping])
                                    print([k[0] for k in pos_list])
                                    raise RuntimeError("Possible nasalisation on preposition preceding verb form")
                                # if there is only one affix between a preposition and following verb
                                elif len(verbal_affixes) == 1:
                                    first_preverb_data = verbal_affixes[0]
                                    first_preverb_original = first_preverb_data[0]
                                    split_first_preverb = split_pos_feats(first_preverb_data[1])
                                    first_preverb_short_pos = split_first_preverb[0]
                                    first_preverb_feats = split_first_preverb[1]
                                    if first_preverb_short_pos != "PVP":
                                        raise RuntimeError("first verbal affix following preposition is not a preverb")
                                    if first_preverb_original == tagged_original[:len(first_preverb_original)]:
                                        if first_preverb_feats:
                                            tagged_pos = add_features(tagged_pos, first_preverb_feats)
                                            tagged_word_data = [tagged_original, tagged_pos,
                                                                tagged_standard, tagged_head]
                                        pos_list = pos_list[:j - 1] + [tagged_word_data] + pos_list[j + 1:]
                                        combine_subtract = True
                                        break
                                    else:
                                        print(last_pos_data)
                                        print(verbal_affixes)
                                        print(tagged_word_data)
                                        print([k[0] for k in standard_mapping])
                                        print([k[0] for k in pos_list])
                                        raise RuntimeError("Could not find preverb in following verb form")
                                # if there are multiple affixes between a preposition and following verb
                                else:
                                    first_preverb_data = verbal_affixes[0]
                                    split_first_preverb = split_pos_feats(first_preverb_data[1])
                                    first_preverb_short_pos = split_first_preverb[0]
                                    if first_preverb_short_pos != "PVP":
                                        raise RuntimeError("first verbal affix following preposition is not a preverb")
                                    reduced_verbform = tagged_original
                                    for affix_data in verbal_affixes:
                                        affix_original = affix_data[0]
                                        split_affix = split_pos_feats(affix_data[1])
                                        affix_feats = split_affix[1]
                                        if affix_original == reduced_verbform[:len(affix_original)]:
                                            reduced_verbform = reduced_verbform[len(affix_original):]
                                        else:
                                            print(affix_original)
                                            print(reduced_verbform)
                                            print([k[0] for k in standard_mapping])
                                            print([k[0] for k in pos_list])
                                            raise RuntimeError("Could not find preverb in verb form")
                                        if affix_feats:
                                            tagged_pos = add_features(tagged_pos, affix_feats)
                                    tagged_word_data = [tagged_original, tagged_pos, tagged_standard, tagged_head]
                                    pos_list = pos_list[:j-last_pos_place+1] + [tagged_word_data] + pos_list[j+1:]
                                    combine_subtract = True
                                    break
                            # if the preposition is not repeated anywhere in the following verb form
                            elif not verbal_affixes:
                                continue
                            elif len(verbal_affixes) == 1:
                                first_preverb_data = verbal_affixes[0]
                                first_preverb_original = first_preverb_data[0]
                                split_first_preverb = split_pos_feats(first_preverb_data[1])
                                first_preverb_short_pos = split_first_preverb[0]
                                first_preverb_feats = split_first_preverb[1]
                                if first_preverb_short_pos != "PVP":
                                    raise RuntimeError("first verbal affix following preposition is not a preverb")
                                if first_preverb_original == tagged_original[:len(first_preverb_original)]:
                                    if first_preverb_feats:
                                        tagged_pos = add_features(tagged_pos, first_preverb_feats)
                                        tagged_word_data = [tagged_original, tagged_pos, tagged_standard, tagged_head]
                                    pos_list = pos_list[:j-1] + [tagged_word_data] + pos_list[j+1:]
                                    combine_subtract = True
                                    break
                                elif first_preverb_original == "-":
                                    if first_preverb_feats:
                                        tagged_pos = add_features(tagged_pos, first_preverb_feats)
                                        tagged_word_data = [tagged_original, tagged_pos, tagged_standard, tagged_head]
                                    pos_list = pos_list[:j - 1] + [tagged_word_data] + pos_list[j + 1:]
                                    combine_subtract = True
                                    break
                                else:
                                    print(last_pos_data)
                                    print(verbal_affixes)
                                    print(tagged_word_data)
                                    print([k[0] for k in standard_mapping])
                                    print([k[0] for k in pos_list])
                                    raise RuntimeError("Could not find preverb in following verb form")
                            else:
                                first_preverb_data = verbal_affixes[0]
                                split_first_preverb = split_pos_feats(first_preverb_data[1])
                                first_preverb_short_pos = split_first_preverb[0]
                                if first_preverb_short_pos != "PVP":
                                    raise RuntimeError("first verbal affix following preposition is not a preverb")
                                reduced_verbform = tagged_original
                                for affix_data in verbal_affixes:
                                    affix_original = affix_data[0]
                                    split_affix = split_pos_feats(affix_data[1])
                                    affix_feats = split_affix[1]
                                    if affix_original == reduced_verbform[:len(affix_original)]:
                                        reduced_verbform = reduced_verbform[len(affix_original):]
                                    else:
                                        print(affix_original)
                                        print(reduced_verbform)
                                        print([k[0] for k in standard_mapping])
                                        print([k[0] for k in pos_list])
                                        raise RuntimeError("Could not find preverb in verb form")
                                    if affix_feats:
                                        tagged_pos = add_features(tagged_pos, affix_feats)
                                tagged_word_data = [tagged_original, tagged_pos, tagged_standard, tagged_head]
                                pos_list = pos_list[:j-last_pos_place+1] + [tagged_word_data] + pos_list[j+1:]
                                combine_subtract = True
                                break
                        # if the verb and POS have already been separated as necessary and need to be passed over
                        elif last_pos_data in compounded_particles or last_pos_data in compounded_conjunctions:
                            # ensure that the compounded particle or conjunction isn't repeated in the following verb
                            if last_original == tagged_original[:len(last_original)] and len(last_original) > 1:
                                tagged_original = tagged_original[len(last_original):]
                                tagged_standard = tagged_standard[len(last_standard):]
                                tagged_word_data = [tagged_original, tagged_pos, tagged_standard, tagged_head]
                                pos_list[j] = tagged_word_data
                                combine_subtract = True
                            if not verbal_affixes:
                                continue
                            else:
                                reduced_verbform = tagged_original
                                for affix_data in verbal_affixes:
                                    affix_original = affix_data[0]
                                    split_affix = split_pos_feats(affix_data[1])
                                    affix_feats = split_affix[1]
                                    if affix_original == reduced_verbform[:len(affix_original)]:
                                        reduced_verbform = reduced_verbform[len(affix_original):]
                                    else:
                                        print(affix_original)
                                        print(reduced_verbform)
                                        print([k[0] for k in standard_mapping])
                                        print([k[0] for k in pos_list])
                                        raise RuntimeError("Could not find preverb in verb form")
                                    if affix_feats:
                                        tagged_pos = add_features(tagged_pos, affix_feats)
                                tagged_word_data = [tagged_original, tagged_pos, tagged_standard, tagged_head]
                                pos_list = pos_list[:j-last_pos_place+1] + [tagged_word_data] + pos_list[j+1:]
                                combine_subtract = True
                                break
                        # if the last POS's data can't be found in any list
                        else:
                            print(last_pos_data)
                            print(tagged_word_data)
                            print([k[0] for k in standard_mapping])
                            print([k[0] for k in pos_list])
                            raise RuntimeError("Unknown combinable POS preceding verbal complex, add to list")
                    # if an unknown POS type precedes a verb form and any preverbal affixes
                    else:
                        print(last_pos_data)
                        print(tagged_word_data)
                        print([k[0] for k in standard_mapping])
                        print([k[0] for k in pos_list])
                        raise RuntimeError("Unknown POS type preceding verbal complex, identify POS")
    # Remove final remaining "infixed" pronoun from archaic construction in poem
    for i, tagged_word_data in enumerate(pos_list):
        if "<IFP" in tagged_word_data[1]:
            tagged_original = tagged_word_data[0]
            tagged_pos = tagged_word_data[1]
            tagged_standard = tagged_word_data[2]
            split_tagged_pos = split_pos_feats(tagged_pos)
            tagged_feats = split_tagged_pos[1]
            last_pos_data = pos_list[i-1]
            last_original = last_pos_data[0]
            last_pos = last_pos_data[1]
            last_standard = last_pos_data[2]
            last_head = last_pos_data[3]
            split_last_pos = split_pos_feats(last_pos)
            last_short_pos = split_last_pos[0]
            last_feats = split_last_pos[1]
            # if the last POS is an empty verbal particle, as expected
            if last_short_pos == "PART" and "PartType=Vb" in last_feats:
                combined_last_original = last_original + tagged_original
                combined_last_standard = last_standard + tagged_standard
                combined_last_pos = add_features(last_pos, tagged_feats)
                combined_last_data = [combined_last_original, combined_last_pos, combined_last_standard, last_head]
                pos_list = pos_list[:i-1] + [combined_last_data] + pos_list[i+1:]
                combine_subtract = True
                break
            else:
                raise RuntimeError("Unexpected infixed pronoun found")
    # Remove doubled emphatic suffixes, pronouns, etc. from the end of verb forms
    # list all POS types which are not likely to be suffixed to the end of a verb
    independent_postverbs = ["ADJ", "ADP", "ADV", "AUX", "CCONJ", "DET", "INTJ",
                             "NOUN", "NUM", "PROPN", "SCONJ", "VERB"]
    dependent_postverbs = ["PART", "PRON"]
    verbcount = 0
    for tagged_word_data in pos_list:
        split_tagged_pos = split_pos_feats(tagged_word_data[1])
        tagged_short_pos = split_tagged_pos[0]
        if tagged_short_pos == "VERB":
            verbcount += 1
    for i in range(verbcount):
        for j, tagged_word_data in enumerate(pos_list):
            tagged_original, tagged_pos, tagged_standard = tagged_word_data[0], tagged_word_data[1], tagged_word_data[2]
            split_tagged_pos = split_pos_feats(tagged_pos)
            tagged_short_pos = split_tagged_pos[0]
            # if the POS is a verb
            if tagged_short_pos == "VERB":
                # find the following POS
                next_pos_place = j + 1
                if next_pos_place < len(pos_list):
                    next_pos_data = pos_list[next_pos_place]
                else:
                    next_pos_data = False
                if next_pos_data:
                    next_original, next_pos, next_standard = next_pos_data[0], next_pos_data[1], next_pos_data[2]
                    split_next_pos = split_pos_feats(next_pos)
                    next_short_pos = split_next_pos[0]
                    next_feats = split_next_pos[1]
                    # if the word following the verb is never suffixed to a verb form
                    if next_short_pos in independent_postverbs:
                        continue
                    elif next_short_pos in dependent_postverbs:
                        # if the word following the verb is an emphatic suffix
                        if "PronType=Emp" in next_feats:
                            if next_original == tagged_original[-len(next_original):]:
                                tagged_original = tagged_original[:-len(next_original)]
                                tagged_standard = tagged_standard[:-len(next_standard)]
                                tagged_word_data = [tagged_original, tagged_pos, tagged_standard, tagged_head]
                                pos_list[j] = tagged_word_data
                                combine_subtract = True
                            else:
                                continue
                        # if the word following the verb is an anaphoric pronoun
                        elif "PronType=Ana" in next_feats:
                            if next_original == tagged_original[-len(next_original):]:
                                tagged_original = tagged_original[:-len(next_original)]
                                tagged_standard = tagged_standard[:-len(next_standard)]
                                tagged_word_data = [tagged_original, tagged_pos, tagged_standard, tagged_head]
                                pos_list[j] = tagged_word_data
                                combine_subtract = True
                            else:
                                continue
                        # if the word following the verb is a demonstrative particle
                        elif "PronType=Dem" in next_feats:
                            if next_original == tagged_original[-len(next_original):]:
                                raise RuntimeError("Potentially doubled verb suffix found")
                            else:
                                continue
                        elif "PronType=Prs" in next_feats:
                            # if there is a suffixed pronoun following a simple verb form
                            if next_original == tagged_original[-len(next_original):] and "Poss=Yes" not in next_feats:
                                tagged_pos = add_features(tagged_pos, next_feats, "combine", ["PronType"])
                                tagged_word_data = [tagged_original, tagged_pos, tagged_standard, tagged_head]
                                pos_list[j] = tagged_word_data
                                del pos_list[next_pos_place]
                                combine_subtract = True
                            else:
                                continue
                        elif "PronType=Ind" in next_feats:
                            continue
                        elif "PronType=Int" in next_feats:
                            continue
                        elif "PartType=Vb" in next_feats:
                            continue
                        elif "Polarity=Neg" in next_feats:
                            continue
                        else:
                            print(tagged_word_data)
                            print(next_pos_data)
                            print([k[0] for k in standard_mapping])
                            print([k[0] for k in pos_list])
                            raise RuntimeError("Potentially doubled verb suffix found")
                    # if the POS of the following word is unknown
                    else:
                        print(f'"{next_short_pos}"')
                        print(tagged_word_data)
                        print(next_pos_data)
                        print([k[0] for k in standard_mapping])
                        print([k[0] for k in pos_list])
                        raise RuntimeError("Unknown POS type following verb form, add to list")
            # if the tagged word is not a verb, move past it
            else:
                continue

    #                                               PART 2.1.2:
    #
    #                                                ARTICLE
    #
    # combine compounded articles with preceding prepositions

    #                                               PART 2.1.3:
    #
    #                                                  MISC
    #
    # remove doubled compounds of prefixed particles and nouns/adjectives following the two individually
    prepart_list = [['áer', '<PART Prefix=Yes>', 'aer', 'ér'],
                    ['am', '<PART Prefix=Yes>', 'am', 'an'],
                    ['an', '<PART Prefix=Yes>', 'an', 'an'],
                    ['co', '<PART Prefix=Yes>', 'co', 'com'],
                    ['com', '<PART Prefix=Yes>', 'com', 'com'],
                    ['chom', '<PART Prefix=Yes>', 'chom', 'com'],
                    ['déden', '<PART Prefix=Yes>', 'deden', 'déiden'],
                    ['dí', '<PART Prefix=Yes>', 'di', 'di'],
                    ['im', '<PART Prefix=Yes>', 'im', 'imm'],
                    ['mi', '<PART Prefix=Yes>', 'mi', 'mí'],
                    ['mí', '<PART Prefix=Yes>', 'mi', 'mí'],
                    ['neph', '<PART Polarity=Neg | Prefix=Yes>', 'neph', 'neph']]
    # count the instances of prefixed particles in the gloss
    prepart_count = 0
    for tagged_word_data in pos_list:
        split_tagged_pos = split_pos_feats(tagged_word_data[1])
        tagged_short_pos = split_tagged_pos[0]
        tagged_feats = split_tagged_pos[1]
        if tagged_short_pos == "PART" and 'Prefix=Yes' in tagged_feats:
            if tagged_word_data not in prepart_list:
                print(tagged_word_data)
                print([i[0] for i in standard_mapping])
                print([i[0] for i in pos_list])
                raise RuntimeError("Prefixed particle not in full list")
            elif tagged_word_data in prepart_list:
                prepart_count += 1
    for i in range(prepart_count):
        for j, tagged_word_data in enumerate(pos_list):
            tagged_original, tagged_pos, tagged_standard, tagged_head = \
                tagged_word_data[0], tagged_word_data[1], tagged_word_data[2], tagged_word_data[3]
            # if a prefixed particle is found in the gloss, look for the following POS, with which it combines
            if tagged_word_data in prepart_list:
                try:
                    next_pos_data = pos_list[j+1]
                # if the prefixed particle is the last POS in the gloss
                except IndexError:
                    next_pos_data = False
                # if a combining POS is found, look ahead one more place to find the compounded form of the two POS
                if next_pos_data:
                    next_original, next_pos, next_standard, next_head = \
                        next_pos_data[0], next_pos_data[1], next_pos_data[2], next_pos_data[3]
                    try:
                        third_pos_data = pos_list[j+2]
                    # if no POS follows the two combining POS, combine the two to create the compounded form
                    except IndexError:
                        third_pos_data = False
                        compounded_form = [tagged_original + next_original,
                                           next_pos,
                                           tagged_standard + next_standard,
                                           next_head]
                        # if the compound form of the two POS is found elsewhere in the gloss
                        if compounded_form in pos_list:
                            print(tagged_word_data)
                            print(next_pos_data)
                            print(compounded_form)
                            print([i[0] for i in standard_mapping])
                            print([i[0] for i in pos_list])
                            raise RuntimeError("Compound word form in gloss, but not following separate parts")
                        # if there is no compounded form of the two POS in the gloss, the gloss is already in order
                        else:
                            pass
                    # if there is a POS following the two combining POS
                    if third_pos_data:
                        third_original, third_pos, third_standard, third_head = \
                            third_pos_data[0], third_pos_data[1], third_pos_data[2], third_pos_data[3]
                        compounded_form = [tagged_original + next_original,
                                           next_pos,
                                           tagged_standard + next_standard,
                                           next_head]
                        # if the prefixed particle and following POS are duplicated in the third POS
                        if third_pos_data[:3] == compounded_form[:3]:
                            del pos_list[j+2]
                        # if the prefixed particle and following POS are duplicated somewhere else in the gloss
                        elif compounded_form in pos_list:
                            print(tagged_word_data)
                            print(next_pos_data)
                            print(compounded_form)
                            print([i[0] for i in standard_mapping])
                            print([i[0] for i in pos_list])
                            raise RuntimeError("Compound word form in gloss, but not following separate parts")
    # remove combined conjunction, 'arindí', where it doubles the breakdown, 'ar', 'ind', and 'í'
    arindi_list = [['airindi', '<SCONJ>', 'airindi', 'arindí'],
                   ['airindí', '<SCONJ>', 'airindi', 'arindí'],
                   ['arindi', '<SCONJ>', 'arindi', 'arindí'],
                   ['arindí', '<SCONJ>', 'arindi', 'arindí']]
    arindi_count = 0
    for tagged_word_data in pos_list:
        if tagged_word_data in arindi_list:
            arindi_count += 1
    for i in range(arindi_count):
        for j, tagged_word_data in enumerate(pos_list):
            if tagged_word_data in arindi_list:
                try:
                    last_pos_data = pos_list[j-1]
                except IndexError:
                    raise RuntimeError("Could not find breakdown of combined conjunction, 'airindí'")
                if last_pos_data:
                    last_three_pos = pos_list[j-3:j]
                    if last_three_pos in [[['ar', '<ADP AdpType=Prep | Definite=Def | Prefix=Yes>', 'ar', 'ar'],
                                           ['ind', '<DET AdpType=Prep | Case=Dat | Gender=Neut '
                                                   '| Number=Sing | PronType=Art>', 'ind', 'a'],
                                           ['í', '<PART PartType=Dct>', 'i', 'í']],
                                          [['ar', '<ADP AdpType=Prep | Definite=Def | Prefix=Yes>', 'ar', 'ar'],
                                           ['ind', '<DET AdpType=Prep | Case=Dat | Gender=Neut '
                                                   '| Number=Sing | PronType=Art>', 'ind', 'a'],
                                           ['i', '<PART PartType=Dct>', 'i', 'í']],
                                          [['air', '<ADP AdpType=Prep | Definite=Def | Prefix=Yes>', 'air', 'ar'],
                                           ['ind', '<DET AdpType=Prep | Case=Dat | Gender=Neut '
                                                   '| Number=Sing | PronType=Art>', 'ind', 'a'],
                                           ['í', '<PART PartType=Dct>', 'i', 'í']],
                                          [['air', '<ADP AdpType=Prep | Definite=Def | Prefix=Yes>', 'air', 'ar'],
                                           ['ind', '<DET AdpType=Prep | Case=Dat | Gender=Neut '
                                                   '| Number=Sing | PronType=Art>', 'ind', 'a'],
                                           ['i', '<PART PartType=Dct>', 'i', 'í']]]:
                        del pos_list[j]
                        combine_subtract = True
                    else:
                        print(last_three_pos)
                        print([i[0] for i in pos_list])
                        print([i[0] for i in standard_mapping])
                        raise RuntimeError("Could not find breakdown of combined conjunction, 'airindí'")
    # remove doubled 'ol', and 'chenae' breakdown of adverb 'olchenae'
    # cf. eDIL entries for 'olchena' and '1 ol, (al)' vs. entries for 'arindí' and '1 ar'
    olchena_list = [['olchene', '<ADV>', 'olchene', 'olchena'],
                    ['olchenae', '<ADV>', 'olchenae', 'olchena'],
                    ['olchenæ', '<ADV>', 'olchenae', 'olchena'],
                    ['olchaenae', '<ADV>', 'olchaenae', 'olchena'],
                    ['olchænae', '<ADV>', 'olchaenae', 'olchena']]
    # count the instances of the word in the gloss
    olchena_count = 0
    for tagged_word_data in pos_list:
        if tagged_word_data in olchena_list:
            olchena_count += 1
    for i in range(olchena_count):
        for j, tagged_word_data in enumerate(pos_list):
            if tagged_word_data in olchena_list:
                try:
                    last_pos_data = pos_list[j-1]
                    last_two_pos = pos_list[j-2:j]
                except IndexError:
                    last_pos_data = False
                try:
                    next_pos_data = pos_list[j+1]
                    next_two_pos = pos_list[j+1:j+3]
                except IndexError:
                    next_pos_data = False
                olchena_parts = [[['ol', '<ADP AdpType=Prep | Definite=Ind>', 'ol', 'ol'],
                                  ['chene', '<PRON PronType=Prs>', 'chene', 'cen']],
                                 [['ol', '<ADP AdpType=Prep | Definite=Ind>', 'ol', 'ol'],
                                  ['chenæ', '<PRON PronType=Prs>', 'chenae', 'cen']],
                                 [['ol', '<ADP AdpType=Prep | Definite=Ind>', 'ol', 'ol'],
                                  ['chenae', '<PRON PronType=Prs>', 'chenae', 'cen']],
                                 [['ol', '<ADP AdpType=Prep | Definite=Ind>', 'ol', 'ol'],
                                  ['chænae', '<PRON PronType=Prs>', 'chaenae', 'cen']],
                                 [['ol', '<ADP AdpType=Prep | Definite=Ind>', 'ol', 'ol'],
                                  ['chaenae', '<PRON PronType=Prs>', 'chaenae', 'cen']]]
                # find the two POS preceding and following the combined form, if there are two
                if last_pos_data:
                    # check if the preceding two POS make up the combined form and delete them if so
                    if last_two_pos in olchena_parts:
                        pos_list = pos_list[:j-2] + pos_list[j:]
                        combine_subtract = True
                        break
                    # if the preceding two POS did not make up the combined form, check the following two instead
                    elif next_pos_data:
                        if next_two_pos in olchena_parts:
                            pos_list = pos_list[:j+1] + pos_list[j+3:]
                            combine_subtract = True
                            break
                else:
                    raise RuntimeError("Could not find doubled parts of word to remove")
    # remove "-" from pos_list where Bauer has used it to represent a word reduced to zero
    # remove "-" from pos_list wherever it has not been automatically removed from parts-of-speech
    # remove spacing from pos_list wherever it has not been automatically removed from parts-of-speech
    for i, tagged_word_data in enumerate(pos_list):
        tagged_original = tagged_word_data[0]
        if tagged_original == "-":
            split_tagged_pos = split_pos_feats(tagged_word_data[1])
            tagged_pos = split_tagged_pos[0]
            tagged_feats = split_tagged_pos[1]
            # if a preposition has fallen into a following demonstrative particle
            # add the feature to the particle to show the existence of the preposition
            if tagged_pos == "ADP" and "AdpType=Prep" in tagged_feats:
                next_word_data = pos_list[i+1]
                if "PART" in next_word_data[1]:
                    next_word_data[1] = add_features(next_word_data[1], ["AdpType=Prep"])
                    pos_list[i+1] = next_word_data
                    del pos_list[i]
                    combine_subtract = True
                else:
                    print(tagged_word_data)
                    print(next_word_data)
                    print(pos_list)
                    raise RuntimeError("Word reduced to zero")
            elif tagged_pos == "PART" and "PronType=Rel" in tagged_feats:
                last_word_data = pos_list[i-1]
                if "ADP" in last_word_data[1]:
                    last_word_data[1] = add_features(last_word_data[1], tagged_feats)
                    pos_list[i-1] = last_word_data
                    del pos_list[i]
                    combine_subtract = True
                else:
                    print(tagged_word_data)
                    print(last_word_data)
                    print(pos_list)
                    raise RuntimeError("Word reduced to zero")
            else:
                print(tagged_word_data)
                print(pos_list)
                raise RuntimeError("Word reduced to zero")
        elif "-" in tagged_original:
            print(tagged_word_data)
            print(pos_list)
            raise RuntimeError("Hyphen in POS tagged word")
        elif " " in tagged_original:
            print(tagged_word_data)
            print(pos_list)
            raise RuntimeError("Space in POS tagged word")
    # remove any words POS tagged as unnecessary repetitions of other tagged words (e.g. samlid/samlaid)
    for i, tagged_word_data in enumerate(pos_list):
        split_tagged_pos = split_pos_feats(tagged_word_data[1])
        tagged_pos = split_tagged_pos[0]
        if tagged_pos == "UNR":
            del pos_list[i]
            combine_subtract = True
    # change the POS tags of any word tagged as an unknown POS to <X> and add the typo feature
    for i, tagged_word_data in enumerate(pos_list):
        tagged_original = tagged_word_data[0]
        tagged_standard = tagged_word_data[2]
        tagged_head = tagged_word_data[3]
        split_tagged_pos = split_pos_feats(tagged_word_data[1])
        tagged_pos = split_tagged_pos[0]
        if tagged_pos == "UNK":
            new_pos = "<X Typo=Yes>"
            pos_list[i] = [tagged_original, new_pos, tagged_standard, tagged_head]
            combine_subtract = True

    #                                             PART 2.1 (reprise):
    #
    # update rating to show gloss has had content combined or removed
    if combine_subtract:
        tags_rating += 1

    #                                                PART 2.2:
    #
    # if Bauer has analysed an instance of 'ɫ' but Hofman has expanded it as latin 'vel', revert it to 'ɫ' and tag
    i_count = False
    # if there's any instance of 'ɫ' in Bauer's analysis, count how many there are in the analysis
    for i in pos_list:
        if i == ['ɫ', '<CCONJ>', 'no', 'nó']:
            i_count = pos_list.count(i)
            break
    # then count how many instances of 'no' or 'nó' Hofman has in his gloss
    if i_count:
        j_count = 0
        for j in standard_mapping:
            if j[:2] in [('no', 'no'), ('nó', 'no')]:
                j_count += 1
        # if the two counts do not match, find the difference
        if j_count != i_count:
            missing_count = i_count - j_count
            # if there are more instances in Bauer's analysis than Hofman's gloss
            if missing_count > 0:
                # check for instances of 'vel' in Hofman's gloss used instead, and change them to 'ɫ'
                for k in range(missing_count):
                    for l, tok_maping in enumerate(standard_mapping):
                        if tok_maping[:2] == ('vel', 'vel'):
                            standard_mapping[l] = ('ɫ', 'no', tok_maping[2])
            # if there are more instances in Hofman's gloss than Bauer's analysis
            elif missing_count < 0:
                # look for instances of nó written in full in Bauer's gloss
                alts_found = 0
                for k in range(abs(missing_count)):
                    for word_an in pos_list:
                        if word_an in [['nó', '<CCONJ>', 'no', 'nó']]:
                            alts_found += 1
                if missing_count + alts_found != 0:
                    pvp_no_count = pos_list.count(['no', '<PART PartType=Vb>', 'no', 'no'])
                    if missing_count + alts_found + pvp_no_count != 0:
                        print(missing_count, alts_found, pvp_no_count)
                        print([i[0] for i in standard_mapping])
                        print([i[0] for i in pos_list])
                        print(pos_list)
                        raise RuntimeError("Missing 'ɫ' in Bauer's analysis, or 'no/nó' repeated by Hofman")

    #                                                 PART 3:
    #
    # Connect tagged words from Bauer's analysis with their counterparts from Hofman's gloss,
    # Apply reliability rating for the match between words in the gloss as a whole.

    # include '.i.' in pos-list so it can be tagged
    if ".i." in standard_list:
        if pos_list.count([".i.", "<ADV Abbr=Yes>", ".i.", ".i."]) + \
                pos_list.count([".i.", "<ADV Abbr=Yes | Typo=Yes>", ".i.", ".i."]) != standard_list.count(".i."):
            i_count = standard_list.count(".i.")
            tagged_i = pos_list.count([".i.", "<ADV Abbr=Yes>", ".i."]) + \
                       pos_list.count([".i.", "<ADV Abbr=Yes | Typo=Yes>", ".i.", ".i."])
            i_diff = i_count - tagged_i
            for _ in range(i_diff):
                pos_list.append([".i.", "<ADV Abbr=Yes>", ".i.", ".i."])
    # check reliability of cross-tagging and apply score to output
    # measure length of POS list against token list after accounting for ".i." symbols and hyphens
    # increase ten digits if no. of tokens don't match
    if len(pos_list) != len(standard_list):
        tags_rating += 10

    #                                                 PART 3.1:
    #
    # for each valid (POS tag in use) tagged word, if a perfect match can be found:
    #     1. align its position in the POS-list with the position of its counterpart in the Gloss-list
    #     2. add Bauer's original word, the pos tag, and the edit distance, to the tagged-gloss list
    alignment_list = list()
    used_pos = list()
    reducable_standard_mapping = standard_mapping[:]
    token_place = -1
    # for each tagged word in Bauer's analysis, in order, get the word's data
    for pos_place, word_pos_data in enumerate(pos_list):
        if pos_place not in used_pos:
            word_original = word_pos_data[0]
            word_tag = word_pos_data[1]
            word_standard = word_pos_data[2]
            word_head = word_pos_data[3]
            # if the tagged word is not the last word in the analysis, get the following word's data also
            last_pos_place = len(pos_list) - 1
            next_pos_data = False
            next_original = False
            next_tag = False
            next_standard = False
            next_combo_standard = False
            if pos_place < last_pos_place and pos_place + 1 not in used_pos:
                next_pos_data = pos_list[pos_place + 1]
                next_original = next_pos_data[0]
                next_tag = next_pos_data[1]
                next_standard = next_pos_data[2]
                next_head = next_pos_data[3]
                next_combo_standard = word_standard + next_standard
            # if the tagged word is neither the last word nor the second last wrd in the analysis
            # get the data of the following two words also
            third_pos_data = False
            third_original = False
            third_tag = False
            third_combo_standard = False
            if pos_place < last_pos_place - 1 and pos_place + 1 not in used_pos and pos_place + 2 not in used_pos:
                third_pos_data = pos_list[pos_place + 2]
                third_original = third_pos_data[0]
                third_tag = third_pos_data[1]
                third_standard = third_pos_data[2]
                third_head = third_pos_data[3]
                third_combo_standard = word_standard + next_standard + third_standard
            # check the edit distance between the standard form of the first POS tagged word in Bauer's analysis
            # and the standard form of the first (i.e. next) token in Hofman's gloss
            for token_list in reducable_standard_mapping:
                token_original = token_list[0]
                token_standard = token_list[1]
                eddist = ed(word_standard, token_standard, substitution_cost=2)
                # if an edit distance of zero occurs assume the two are a match
                # shorten the reducable copy of Hofmann's gloss to the point after where the match was found
                # add Bauer's word, its POS tag, Hofman's word, the edit distance, and indices for the match to a
                # matching-words list
                if eddist == 0:
                    reduce_by = reducable_standard_mapping.index(token_list) + 1
                    token_place += reduce_by
                    reducable_standard_mapping = reducable_standard_mapping[reduce_by:]
                    lowest_eddist = [word_original, word_tag, token_original, eddist, word_head,
                                     [token_place, pos_place]]
                    alignment_list.append((pos_place, token_place))
                    tagged_gloss.append(lowest_eddist)
                    break
                elif next_pos_data:
                    eddist = ed(next_combo_standard, token_standard, substitution_cost=2)
                    if eddist == 0:
                        reduce_by = reducable_standard_mapping.index(token_list) + 1
                        token_place += reduce_by
                        reducable_standard_mapping = reducable_standard_mapping[reduce_by:]
                        lowest_eddist = [[word_original, word_tag, token_original, eddist, word_head,
                                          [token_place, pos_place]],
                                         [next_original, next_tag, token_original, eddist, next_head,
                                          [token_place, pos_place+1]]]
                        alignment_list += [(pos_place, token_place), (pos_place + 1, token_place)]
                        used_pos += [pos_place, pos_place + 1]
                        tagged_gloss += lowest_eddist
                        break
                    elif third_pos_data:
                        eddist = ed(third_combo_standard, token_standard, substitution_cost=2)
                        if eddist == 0:
                            reduce_by = reducable_standard_mapping.index(token_list) + 1
                            token_place += reduce_by
                            reducable_standard_mapping = reducable_standard_mapping[reduce_by:]
                            lowest_eddist = [[word_original, word_tag, token_original, eddist, word_head,
                                              [token_place, pos_place]],
                                             [next_original, next_tag, token_original, eddist, next_head,
                                              [token_place, pos_place + 1]],
                                             [third_original, third_tag, token_original, eddist, third_head,
                                              [token_place, pos_place + 2]]]
                            alignment_list += [(pos_place, token_place),
                                               (pos_place + 1, token_place),
                                               (pos_place + 2, token_place)]
                            used_pos += [pos_place, pos_place + 1, pos_place + 2]
                            tagged_gloss += lowest_eddist
                            break
    # if any words or word-combos have been aligned yet
    if alignment_list:
        # separate the list of words and word-combos which have been perfectly aligned into
        # separate lists for each used word/word-combo and tag
        used_pos = list(list(zip(*alignment_list))[0])
        used_toks = list(list(zip(*alignment_list))[1])
    else:
        used_pos = list()
        used_toks = list()

    #                                                 PART 3.2:
    #
    # for the remaining words in Bauer's analysis which cannot be mapped perfectly to a word in Hofman's gloss
    # find the word in Hofman's gloss with the lowest edit distance from the each analysed word and match these
    lowest_eddist = False
    lowest_edlist = False
    # for each remaining tagged word in Bauer's analysis, in order, get the word's data
    for pos_place, word_pos_data in enumerate(pos_list):
        if pos_place not in used_pos and word_pos_data != ['.i.', '<ADV Abbr=Yes>', '.i.', '.i.']:
            word_original = word_pos_data[0]
            word_tag = word_pos_data[1]
            word_standard = word_pos_data[2]
            word_head = word_pos_data[3]
            last_pos_place = len(pos_list) - 1
            next_pos_data = False
            next_original = False
            next_tag = False
            next_combo_standard = False
            third_pos_data = False
            third_original = False
            third_tag = False
            third_combo_standard = False
            # if the tagged word is not the last word in the analysis, and the following word hasn't been used yet
            # get the following word's data also
            if pos_place < last_pos_place and pos_place + 1 not in used_pos:
                next_pos_data = pos_list[pos_place + 1]
                next_original = next_pos_data[0]
                next_tag = next_pos_data[1]
                next_standard = next_pos_data[2]
                next_head = next_pos_data[3]
                next_combo_standard = word_standard + next_standard
                # if the tagged word is neither the last word nor the second last wrd in the analysis
                # and neither the following word nor the next word after that have been used yet
                # get the data of the following two words also
                if pos_place < last_pos_place - 1 and pos_place + 1 not in used_pos and pos_place + 2 not in used_pos:
                    third_pos_data = pos_list[pos_place + 2]
                    third_original = third_pos_data[0]
                    third_tag = third_pos_data[1]
                    third_standard = third_pos_data[2]
                    third_head = third_pos_data[3]
                    third_combo_standard = word_standard + next_standard + third_standard
            # check the edit distance between the standard form of the first POS tagged word in Bauer's analysis
            # and the standard form of the first (i.e. next) token in Hofman's gloss
            for token_place, token_list in enumerate(standard_mapping):
                if token_place not in used_toks and token_list[0] != ".i.":
                        token_original = token_list[0]
                        token_standard = token_list[1]
                        max_poss_ed = len(word_standard) + len(token_standard)
                        eddist = ed(word_standard, token_standard, substitution_cost=2)
                        # find the lowest edit distance between the standard Bauer word and a standard Hofman token,
                        # if the edit dist. is lower than the maximum possible edit dist. between the two strings,
                        # assume the two are a match and identify the pair as the lowest-edit-distance candidates
                        if not lowest_eddist:
                            if max_poss_ed > eddist:
                                lowest_eddist = [word_original, word_tag, token_original, eddist, word_head,
                                                 [token_place, pos_place]]
                                if third_pos_data:
                                    max_poss_ed = len(third_combo_standard) + len(token_standard)
                                    eddist = ed(third_combo_standard, token_standard, substitution_cost=2)
                                    if max_poss_ed > eddist and eddist < lowest_eddist[3]:
                                        lowest_eddist = False
                                        lowest_edlist = [[word_original, word_tag, token_original, eddist, word_head,
                                                          [token_place, pos_place]],
                                                         [next_original, next_tag, token_original, eddist, next_head,
                                                          [token_place, pos_place+1]],
                                                         [third_original, third_tag, token_original, eddist, third_head,
                                                          [token_place, pos_place+2]]]
                                elif next_pos_data:
                                    max_poss_ed = len(next_combo_standard) + len(token_standard)
                                    eddist = ed(next_combo_standard, token_standard, substitution_cost=2)
                                    if max_poss_ed > eddist and eddist < lowest_eddist[3]:
                                        lowest_eddist = False
                                        lowest_edlist = [[word_original, word_tag, token_original, eddist, word_head,
                                                          [token_place, pos_place]],
                                                         [next_original, next_tag, token_original, eddist, next_head,
                                                          [token_place, pos_place + 1]]]
                        elif eddist < lowest_eddist[3]:
                            if max_poss_ed > eddist:
                                lowest_eddist = [word_original, word_tag, token_original, eddist, word_head,
                                                 [token_place, pos_place]]
                                if third_pos_data:
                                    max_poss_ed = len(third_combo_standard) + len(token_standard)
                                    eddist = ed(third_combo_standard, token_standard, substitution_cost=2)
                                    if max_poss_ed > eddist and eddist < lowest_eddist[3]:
                                        lowest_eddist = False
                                        lowest_edlist = [[word_original, word_tag, token_original, eddist, word_head,
                                                          [token_place, pos_place]],
                                                         [next_original, next_tag, token_original, eddist, next_head,
                                                          [token_place, pos_place+1]],
                                                         [third_original, third_tag, token_original, eddist, third_head,
                                                          [token_place, pos_place+2]]]
                                elif next_pos_data:
                                    max_poss_ed = len(next_combo_standard) + len(token_standard)
                                    eddist = ed(next_combo_standard, token_standard, substitution_cost=2)
                                    if max_poss_ed > eddist and eddist < lowest_eddist[3]:
                                        lowest_eddist = False
                                        lowest_edlist = [[word_original, word_tag, token_original, eddist, word_head,
                                                          [token_place, pos_place]],
                                                         [next_original, next_tag, token_original, eddist, next_head,
                                                          [token_place, pos_place + 1]]]
            # if the lowest non-zero edit distance has been found between the Bauer word and a Hofman token
            # assume the two are a match
            # add Bauer's word, its POS tag, the Hofman word, the edit distance, and indices for the match to a
            # matching-words list
            if lowest_eddist:
                token_place = lowest_eddist[5][0]
                pos_place = lowest_eddist[5][1]
                place_at = 0
                for i, check_match in enumerate(tagged_gloss):
                    check_tagplace = check_match[5][0]
                    if check_tagplace < token_place:
                        if i + 1 == len(tagged_gloss):
                            place_at = i + 1
                        else:
                            continue
                    else:
                        place_at = i
                        break
                tagged_gloss = tagged_gloss[:place_at] + [lowest_eddist] + tagged_gloss[place_at:]
                alignment_list.append((pos_place, token_place))
                used_toks.append(token_place)
                used_pos.append(pos_place)
                lowest_eddist = False
            elif lowest_edlist:
                check_token = lowest_edlist[0]
                check_token_place = check_token[5][0]
                place_at = 0
                for i, check_match in enumerate(tagged_gloss):
                    check_tagplace = check_match[5][0]
                    if check_tagplace < check_token_place:
                        if i + 1 == len(tagged_gloss):
                            place_at = i + 1
                        else:
                            continue
                    else:
                        place_at = i
                        break
                tagged_gloss = tagged_gloss[:place_at] + lowest_edlist + tagged_gloss[place_at:]
                for combined_matched_token in lowest_edlist:
                    token_place = combined_matched_token[5][0]
                    pos_place = combined_matched_token[5][1]
                    alignment_list.append((pos_place, token_place))
                    used_toks.append(token_place)
                    used_pos.append(pos_place)
                lowest_edlist = False
    # if any POS tagged words remain unmatched, but all tokens from Hofman's gloss have been matched
    if alignment_list:
        # separate the list of words which have already been aligned with their best possible candidates
        used_pos = list(list(zip(*alignment_list))[0])
    else:
        used_pos = list()

    #                                                 PART 3.3:
    #
    # Test if there are any words remaining in Bauer's analysis, add them as appropriate to the tagged gloss
    # If they are unexpected, raise an error
    reducable_standard_mapping = standard_mapping[:]
    token_place = -1
    for pos_place, word_pos_data in enumerate(pos_list):
        if pos_place not in used_pos:
            word_original = word_pos_data[0]
            word_tag = word_pos_data[1]
            word_standard = word_pos_data[2]
            word_head = word_pos_data[3]
            # insert instances of .i. at the correct location as per Hofman's gloss
            if word_pos_data == ['.i.', '<ADV Abbr=Yes>', '.i.', '.i.']:
                for token_list in reducable_standard_mapping:
                    token_original = token_list[0]
                    token_standard = token_list[1]
                    eddist = ed(word_standard, token_standard, substitution_cost=2)
                    if eddist == 0:
                        reduce_by = reducable_standard_mapping.index(token_list) + 1
                        token_place += reduce_by
                        reducable_standard_mapping = reducable_standard_mapping[reduce_by:]
                        lowest_eddist = [word_original, word_tag, token_original, eddist, word_head,
                                         [token_place, token_place]]
                        place_at = 0
                        for i, check_match in enumerate(tagged_gloss):
                            check_tagplace = check_match[5][0]
                            if check_tagplace < token_place:
                                if i + 1 == len(tagged_gloss):
                                    place_at = i + 1
                                else:
                                    continue
                            else:
                                place_at = i
                                break
                        tagged_gloss = tagged_gloss[:place_at] + [lowest_eddist] + tagged_gloss[place_at:]
                        break
            elif pos_place not in used_pos:
                print(word_pos_data)
                print(tagged_gloss)
                print([i[0] for i in pos_list])
                print([i[0] for i in standard_mapping])
                raise RuntimeError("Unexpected words remaining unmatched in Bauer's analysis")

    #                                                 PART 4:
    #
    # Insert the missing Latin words back into the correct place within the gloss
    tagged_matches = [i[5] for i in tagged_gloss]
    matched_toks = [i[0] for i in tagged_matches]
    for i, lat_word_data in enumerate(standard_mapping):
        if i not in matched_toks:
            if lat_word_data[0] == "᚛":
                latin_implant = [lat_word_data[0], "<PUNCT>", lat_word_data[1], 0, "᚛",
                                 [lat_word_data[2], lat_word_data[2]]]
            else:
                latin_implant = [lat_word_data[0], "<X Foreign=Yes>", lat_word_data[1], 0, "_",
                                 [lat_word_data[2], lat_word_data[2]]]
            place_at = 0
            for j, check_match in enumerate(tagged_gloss):
                check_tagplace = check_match[5][0]
                if check_tagplace < i:
                    if j + 1 == len(tagged_gloss):
                        place_at = j + 1
                    else:
                        continue
                else:
                    place_at = j
                    break
            tagged_gloss = tagged_gloss[:place_at] + [latin_implant] + tagged_gloss[place_at:]
    # remove all indeces from tagged-gloss list for output
    for i, word in enumerate(tagged_gloss):
        tagged_gloss[i] = word[:5]
    # check reliability of cross-tagging and update score before output
    # increase thousand digit if edit distance not 0 for all tokens
    dist_list = [i[3] for i in tagged_gloss]
    for i in dist_list:
        if i != 0:
            tags_rating += 100
            break
    # remove edit distances and original Hofman token from token data before output
    # then add reliability score for gloss and any possible word matches to the tagged-gloss list before output
    tagged_gloss = [tags_rating, tph_ref, [[i[0], i[4], i[1]] for i in tagged_gloss], gloss_trans]
    return tagged_gloss


# save a list of all POS-tagged glosses
def save_poslist():
    pos_list = list()
    for glossnum, gloss in enumerate(glosslist):
        tagged_gloss = matchword_levdist(map_glosswords(gloss, wordslist[glossnum]))
        pos_list.append(tagged_gloss[1:])
    save_obj("SG POS-tagged", pos_list)
    return "Created File: 'SG POS-tagged.pkl'"


# #                                              CREATE RESOURCES


# print(save_poslist())


# #                                               TEST FUNCTIONS


# # Test Function: standardise_glosschars()

# print(standardise_glosschars(clean_gloss(" ".join(glosslist))))
# print(standardise_glosschars('áéíóúḟṁṅṡ⁊'))


# # Test Function: standardise_wordchars()

# justwordslist = list()
# for i in wordslist:
#     for j in i:
#         justwordslist.append(clean_word(j[0]))
# print(standardise_wordchars(" ".join(justwordslist)))
# print(standardise_wordchars('Íáæǽéíóúċḟṁṅṡ⁊ɫ'))


# # Test Function: remove_glosshyphens()

# # Print one gloss from Hofman's corpus both before and after hyphenation is removed
# testgloss = glosslist[1576]
# # testgloss = "issí tra in dias-sa rosechestar-som"
# # testgloss = ".i. a n-dliged n-ísin neph-accomoil inna teora liter i-noen-sillaib"
# print(clean_gloss(testgloss))
# print(remove_glosshyphens(clean_gloss(testgloss)))

# # Print all glosses from Hofman's corpus with hyphenation removed
# for gl in glosslist:
#     clean = remove_glosshyphens(clean_gloss(gl))
#     print(clean)


# # Test Function: matchword_levdist()

# # Test edit distance function on all glosses
# for glossnum, gloss in enumerate(glosslist):
#     check = matchword_levdist(map_glosswords(gloss, wordslist[glossnum]))
#     if check:
#         print(glossnum, check)

# # Test edit distance function on a range of glosses
# test_on = glosslist
# start_gloss = 0
# stop_gloss = 27
# for glossnum in range(start_gloss, stop_gloss):
#     print(glossnum, matchword_levdist(map_glosswords(test_on[glossnum], wordslist[glossnum])))


# #                                               TEST OUTPUTS


# # Print the number of glosses containing an error code of 0 (i.e. perfectly matched glosses)
# count = 0
# for glossnum, gloss in enumerate(glosslist):
#     check = matchword_levdist(map_glosswords(gloss, wordslist[glossnum]))
#     if check[0] == 0:
#         count += 1
#         print(count, glossnum, check)

# # Produce a list of all error codes which occur in output of matchword_levdist function applied to all glosses
# # Print the number and percentage of glosses containing each error code
# output_glosslist = [matchword_levdist(map_glosswords(j, wordslist[i])) for i, j in enumerate(glosslist)]
# error_codes = sorted(list(set([i[0] for i in output_glosslist])))
# for ercode in error_codes:
#     ercode_zeros = str(ercode).zfill(3)
#     error_message = False
#     errors_list = list()
#     if ercode_zeros == "000":
#         error_message = "no errors"
#     else:
#         if ercode_zeros[2] == "1":
#             errors_list.append("some changes made to Bauer's analysis of the copula, verbal complex or other "
#                                "duplicated tokens")
#         if ercode_zeros[1] == "1":
#             errors_list.append("a different number of words in Hofman's gloss and Bauer's analysis of the gloss")
#         if ercode_zeros[0] == "1":
#             errors_list.append("a variation in spelling between some words in Hofman's gloss and Bauer's analysis")
#         error_message = ", and ".join(errors_list) + " which may have caused errors in word matching between Hofman " \
#                                                     "and Bauer's corpora"
#     codecount = 0
#     for outgloss in output_glosslist:
#         if outgloss[0] == ercode:
#             codecount += 1
#     percentage = (codecount / len(output_glosslist)) * 100
#     print(f"{ercode_zeros}: {codecount} glosses ({str(percentage)[:5]}%) with {error_message}")
