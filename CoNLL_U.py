
from conllu import parse, TokenList
from collections import OrderedDict
import re


def split_pos_feats(pos_tag):
    """split a full POS tag into the UD POS and a list of features"""
    pospat = re.compile(r'<[A-Z]+[ >]')
    pospatitir = pospat.finditer(pos_tag)
    pos = None
    for posfind in pospatitir:
        pos = posfind.group()[1:-1]
    featspat = re.compile(r' [\w\d =|]+>')
    featspatitir = featspat.finditer(pos_tag)
    feats = ""
    for featsfind in featspatitir:
        feats = featsfind.group()[1:-1]
        feats = feats.split(" | ")
    return [pos, [i for i in feats]]


def add_features(pos_tag, feat_list, doubling=None, doubling_list=None):
    """add all features in a list to the features in a full POS tag
       ensure features are ordered alphabetically
       if features already exist and no doubling/replacing of features isn't specified, raise error"""
    pos_split = split_pos_feats(pos_tag)
    pos = pos_split[0]
    feats = pos_split[1]
    recombined_pos = f'<{pos}>'
    for extra_feat in feat_list:
        if extra_feat not in feats:
            feats.append(extra_feat)
    feats.sort()
    feat_type_list = list()
    replace_feat_list = list()
    doubled_feat_list = list()
    for full_feat in feats:
        feat_split = full_feat.split("=")
        feat_type = feat_split[0]
        if feat_type not in feat_type_list:
            feat_type_list.append(feat_type)
        elif feat_type in feat_type_list:
            if not doubling:
                print(feat_type)
                print(feats)
                raise RuntimeError("Two features of the same type found when combining word features")
            elif doubling == "replace":
                replace_feat_list.append(feat_type)
            elif doubling == "combine":
                doubled_feat_list.append(feat_type)
            else:
                print(feat_type)
                print(feats)
                raise RuntimeError("Two features of the same type found when combining word features\n"
                                   "Doubling option not recognised")
    if replace_feat_list:
        replaceables = doubling_list[0]
        replacements = doubling_list[1]
        for check_replace_type in replace_feat_list:
            replace_feat, replace_with = False, False
            for i, replaceable in enumerate(replaceables):
                if check_replace_type in replaceable:
                    replace_feat = replaceable
                    replace_with = replacements[i]
                    break
            if replace_feat in feats and replace_with in feats:
                del feats[feats.index(replace_feat)]
            elif not replace_feat and not replace_with:
                print(check_replace_type)
                print(feats)
                raise RuntimeError("Two features of the same type found when combining word features, "
                                   "no replacement options given.")
            else:
                print(check_replace_type)
                print(feats)
                raise RuntimeError("Two features of the same type found when combining word features\n"
                                   f"{replace_feat} can be replaced with {replace_with} only")
    elif doubled_feat_list:
        for double_feat in doubled_feat_list:
            doubled_values = list()
            for check_double in feats:
                if double_feat in check_double:
                    double_val = check_double.split("=")[1]
                    if double_val not in doubled_values:
                        doubled_values.append(double_val)
            if doubled_values:
                doubled_values.sort()
                doubled_values = ','.join(doubled_values)
                doubled_value = f'{double_feat}={doubled_values}'
                feats = [i for i in feats if double_feat not in i]
                feats.append(doubled_value)
                feats.sort()
    feats = " | ".join(feats)
    if feats:
        recombined_pos = f'<{pos} {feats}>'
    return recombined_pos


def remove_features(pos_tag, feat_list):
    """remove all features in a list from the features in a full POS tag
       ensure that remaining features are ordered alphabetically"""
    pos_split = split_pos_feats(pos_tag)
    pos = pos_split[0]
    feats = pos_split[1]
    for unwanted_feat in feat_list:
        if unwanted_feat in feats:
            while unwanted_feat in feats:
                feats.remove(unwanted_feat)
    feats.sort()
    feats = " | ".join(feats)
    recombined_pos = f'<{pos}>'
    if feats:
        recombined_pos = f'<{pos} {feats}>'
    return recombined_pos


def update_feature(pos_tag, feature_replacement):
    """remove a selected feature/value pair, replace it with the same feature with an updated value"""
    pos_split = split_pos_feats(pos_tag)
    feats = pos_split[1]
    feat_split = feature_replacement.split("=")
    feat_name = feat_split[0] + "="
    recombined_pos = pos_tag
    for feature in feats:
        if feature[:len(feat_name)] == feat_name:
            reduced_pos = remove_features(pos_tag, [feature])
            recombined_pos = add_features(reduced_pos, [feature_replacement])
            break
    return recombined_pos


def update_tag(pos_tag, tag_relacement):
    new_tag = f'<{tag_relacement}>'
    pos_split = split_pos_feats(pos_tag)
    feats = pos_split[1]
    recombined_pos = add_features(new_tag, feats)
    return recombined_pos


def get_pos(pos_tag):
    """return only the POS from a full POS (one which may include features)"""
    pospat = re.compile(r'<[A-Z]+[ >]')
    pospatitir = pospat.finditer(pos_tag)
    for posfind in pospatitir:
        pos = posfind.group()[1:-1]
        return pos


def get_feats(pos_tag):
    """return an ordered dictionary containing each feature (if any) from a full POS"""
    featspat = re.compile(r' [\w\d =|]+>')
    featspatitir = featspat.finditer(pos_tag)
    feats = None
    for featsfind in featspatitir:
        feats = featsfind.group()[1:-1]
        feats = feats.split(" | ")
    if feats:
        feats = OrderedDict({i.split("=")[0]: i.split("=")[1] for i in feats})
    return feats


def compile_sent(sent):
    """compile a list of sublists, [word, full POS] format, into a CoNLL-U format sentence"""
    sent_list = list()
    for i, tok_data in enumerate(sent):
        tok_id = i + 1
        tok = tok_data[0]
        pos = get_pos(tok_data[1])
        feats = get_feats(tok_data[1])
        compiled_tok = OrderedDict({'id': tok_id, 'form': tok, 'lemma': tok, 'upostag': pos, 'xpostag': None,
                                    'feats': feats, 'head': None, 'deprel': None, 'deps': None, 'misc': None})
        sent_list.append(compiled_tok)
    sent_list = TokenList(sent_list).serialize()
    return sent_list


# #                                                  Test Functions

# test_pos1 = '<DET Case=Nom | Gender=Neut | Number=Sing>'
# test_pos2 = '<CCONJ>'


# # test split_pos_feats() function
# print(split_pos_feats(test_pos1))
# print(split_pos_feats(test_pos2))

# # test add_features() function
# print(add_features(test_pos1, ['Polarity=Neg', 'Person=3']))
# print(add_features(test_pos2, ['Polarity=Neg', 'Person=3']))
# print(add_features(test_pos1, ['Polarity=Neg', 'Person=3', 'Case=Voc', 'Gender=Masc'],
#                    "replace", [["Case=Nom", "Gender=Neut"], ["Case=Voc", "Gender=Masc"]]))
# print(add_features(test_pos1, ['Polarity=Neg', 'Person=3', 'Gender=Masc'], "combine", ['Gender']))

# # test remove_features() function
# print(remove_features(test_pos1, ['Gender=Neut', 'Case=Nom']))
# print(remove_features(test_pos2, ['Gender=Neut', 'Case=Nom']))

# # test update_feature() function
# print(update_feature(test_pos1, 'Case=Acc'))
# print(update_feature(test_pos2, 'Case=Acc'))

# # test update_feature() function
# print(update_tag(test_pos1, "PART"))
# print(update_tag(test_pos2, "PART"))


# s1 = [['.i.', '<SYM Abbr=Yes>'], ['cid', '<AUX Polarity=Pos | VerbType=Cop>'], ['bec', '<ADJ>'],
#       ['cid', '<AUX Polarity=Pos | VerbType=Cop>'], ['mar', '<ADJ>'],
#       ['ind', '<DET Case=Nom | Gender=Fem | Number=Sing>'], ['inducbál', '<NOUN>'],
#       ['ó', '<ADP AdpType=Prep | Definite=Ind>'], ['dia', '<NOUN>'], ['tar', '<ADP AdpType=Prep | Definite=Ind>'],
#       ['hési', '<NOUN>'], ['denmo', '<NOUN>'], ['ind', '<DET Case=Gen | Gender=Masc | Number=Sing>'],
#       ['libuir', '<NOUN>'], ['bith', '<AUX Polarity=Pos | VerbType=Cop>'], ['má', '<ADJ>'], ['de', '<PRON>'],
#       ['do', '<ADP AdpType=Prep | Definite=Ind>'], ['buith', '<NOUN>'], ['dait', '<PRON>'], ['siu', '<PRON>'],
#       ['hi', '<ADP AdpType=Prep | Definite=Ind>'], ['coimthecht', '<NOUN>'], ['oco', '<PRON>']]
# s2 = [['buaid', '<NOUN>'], ['lie', '<NOUN>'], ['vel', '<X>'], ['lapis', '<X>'], ['victorie', '<X>']]

# # test get_pos() and get_feats() functions
# test_tok = 0
# print(s1[test_tok][0])
# print(get_pos(s1[test_tok][1]))
# print(get_feats(s1[test_tok][1]))

# # test compile_sent() function
# print(compile_sent(s1))


# #                                                  Test conllu Library

# data = """
# # id = 15b11
# # text = buaid lie ɫ lapis victorie
# 1   buaid      búaid   NOUN   _   _   _   _   _   _
# 2   lie        lía     NOUN   _   _   _   _   _   _
# 3   vel        _       X      _   _   _   _   _   _
# 4   lapis      _       X      _   _   _   _   _   _
# 5   victorie   _       X      _   _   _   _   _   _
#
# # id = 2a7
# # text = .i. cid bec cid mar indinducbál ó dia tarhési denmo ind libuir bith má de do buith daitsiu hi coimthecht oco ·'
# 1   .            .            PUNCT   _    PunctSide=Ini                          _   _       _   SpaceAfter=No
# 2   i            i            ADV     _    Abbr=Yes                               _   _       _   SpaceAfter=No
# 3   .            .            PUNCT   _    PunctSide=Fin                          _   _       _   _
# 4   cid          cid          AUX     _    Polarity=Pos | VerbType=Cop            _   _       _   _
# 5   bec          bec          ADJ     _    _                                      _   _       _   _
# 6   cid          cid          AUX     _    Polarity=Pos | VerbType=Cop            _   _       _   _
# 7   mar          mór          ADJ     _    _                                      _   _       _   _
# 8   ind          in           DET     _    Case=Nom | Gender=Fem | Number=Sing    _   _       _   SpaceAfter=No
# 9   inducbál     inducbál     NOUN    _    _                                      _   _       _   _
# 10  ó            ó            ADP     _    AdpType=Prep | Definite=Ind            _   _       _   _
# 11  dia          día          NOUN    _    _                                      _   _       _   _
# 12  tar          tar          ADP     _    AdpType=Prep | Definite=Ind            _   _       _   SpaceAfter=No
# 13  hési         éis          NOUN    _    _                                      _   _       _   _
# 14  denmo        dénum        NOUN    _    _                                      _   _       _   _
# 15  ind          in           DET     _    Case=Gen | Gender=Masc | Number=Sing   _   _       _   _
# 16  libuir       lebor        NOUN    _    _                                      _   _       _   _
# 17  bith         is           AUX     _    Polarity=Pos | VerbType=Cop            _   _       _   _
# 18  má           mór          ADJ     _    _                                      _   _       _   _
# 19  de           de           PRON    _    _                                      _   _       _   _
# 20  do           do           ADP     _    AdpType=Prep | Definite=Ind            _   _       _   _
# 21  buith        both         NOUN    _    _                                      _   _       _   _
# 22  dait         dait         PRON    _    _                                      _   _       _   SpaceAfter=No
# 23  siu          so           PRON    _    _                                      _   _       _   _
# 24  hi           i            ADP     _    AdpType=Prep | Definite=Ind            _   _       _   _
# 25  coimthecht   coimitecht   NOUN    _    _                                      _   _       _   _
# 26  oco          oc           PRON    _    _                                      _   _       _   _
#
# """

# sentences = parse(data)
# sentence_1 = sentences[0]
# sentence_2 = sentences[1]
# print(sentence_1)
# print(sentence_2)
# token = sentence_1[0]
# print(token)
# print(sentence_1.serialize())
# print(sentence_2.serialize())

# file_test = sentence_1.serialize() + sentence_2.serialize()
# with open("Test.conllu", "w") as text_file:
#     print(f"{file_test}", file=text_file)

