from OpenXlsx import list_xlsx
from Clean_Glosses import clean_gloss, clean_word
from conllu import parse
import nltk
import random


def get_glosses(gloss_file, file_type):
    """Get a numbered list of POS tagged sentences from either the original Excel file, or the new CoNLL-U files"""

    # If the input is the combined Excel file
    if file_type == "excel":
        compiled_glosses = list()
        glosslist = list()
        sgData = list_xlsx(gloss_file, "Sheet 1")
        for datum in sgData:
            glossnum = datum[0]
            token = clean_word(datum[2])
            postag = datum[5]
            if not glosslist:
                glosslist.extend([glossnum, clean_gloss(datum[10], lowercase=True, rem_greek=True, rem_hyphen=True),
                                  list()])
            if datum == sgData[-1]:
                glosslist[-1].append((token, postag))
                compiled_glosses.append(glosslist)
            elif glossnum == glosslist[0]:
                glosslist[-1].append((token, postag))
            elif glossnum != glosslist[0]:
                compiled_glosses.append(glosslist)
                glosslist = [glossnum, clean_gloss(datum[10], lowercase=True, rem_greek=True, rem_hyphen=True),
                             [(token, postag)]]
        for glossnum, gloss in enumerate(compiled_glosses):
            compiled_glosses[glossnum] = [glossnum + 1, gloss[1], gloss[2]]

    # If the input is a CoNLL-U file
    elif file_type == "conllu":
        with open(gloss_file, mode="r", encoding="utf-8") as conllu_glosses:
            sgData = parse(conllu_glosses.read())
        compiled_glosses = sgData

    else:
        raise RuntimeError("Glosses' file_type must be 'excel', 'conllu'.")
    return compiled_glosses


def get_pos_tags(file):
    """Extracts POS-tags from either Excel or CoNLL-U files"""

    # extract UD POS-tags Excel files
    if isinstance(file[0][-1], list):
        pos_tags = [gloss_data[-1] for gloss_data in file]

    # extract UD POS-tags CoNLL-U files
    elif isinstance(file[0][-1], dict):
        pos_tags = [[(token.get("form"), token.get("upos")) for token in sentence] for sentence in file]

    else:
        raise RuntimeError("Input file must be of type Excel or CoNLL-U")

    return pos_tags


def randomise_test_split(total, test_percent):
    """returns a random sample of numbers which make up a selected percentage
       of the total number of available glosses"""

    one_percent = total / 100
    selected_percent = int(one_percent * test_percent)
    random_sample = sorted(random.sample(range(total), selected_percent))
    remainder = [i for i in range(total) if i not in random_sample]
    return [remainder, random_sample]


def separate_test(file, train_indices, test_indices):
    training_data = [file[i] for i in train_indices]
    test_data = [file[i] for i in test_indices]
    return [training_data, test_data]


def train_pos_tagger(pos_file):
    """Train's a POS-tagger model for a selected language"""

    # train the tagger
    pos_tagger = nltk.UnigramTagger(pos_file)

    return pos_tagger


def test_random_selection(corpora, test_set_percentage=10):
    """Tests NLTK unigram tagger on the same random selection of glosses for each corpus inputted"""

    # Ensure all corpora are the same length
    corp_iter = iter(corpora)
    corpora_length = len(next(corp_iter))
    if not all(len(corp_len) == corpora_length for corp_len in corp_iter):
        raise ValueError('Not all corpora entered have same length!')

    # Get a random sample of gloss indices to be the test glosses, and let the remainder be training glosses
    split_indices = randomise_test_split(corpora_length, test_set_percentage)
    train_gloss_indices = split_indices[0]
    test_gloss_indices = split_indices[1]

    results = list()

    # For each corpus being tested
    for corpus in corpora:

        # Get separate the glosses into test and training sets based on the random indices
        test_split = separate_test(corpus, train_gloss_indices, test_gloss_indices)
        train_set = test_split[0]
        test_set = test_split[1]

        # Train a POS tagger on the training files
        tagger = train_pos_tagger(train_set)

        # Test POS-tagger on the test files
        results.append(tagger.evaluate(test_set))

    return results


def multi_test_random(corpora, test_percent, tests_range, verbose=True):
    """Tests NLTK unigram tagger on the same random selection of glosses for each corpus inputted
       Carries out this test several times for each corpus and averages the scores"""

    # Carry train and evaluate POS-tagger on same random sample of glosses multiple times
    # Random sample changes each time
    multi_test_results = list()
    for i in range(tests_range):
        if verbose:
            print(f"Test {i} of {tests_range} in progress ...")
        multi_test_results.append(test_random_selection(corpora, test_percent))

    # Average the results
    multi_test_results = [sum(elts) for elts in zip(*multi_test_results)]
    multi_test_results = [(summed_test / tests_range) for summed_test in multi_test_results]

    return multi_test_results


if __name__ == "__main__":

    # Get all original glosses and "word-forms"
    original_glossdata = get_glosses("SG. Combined Data", "excel")
    original_words = get_pos_tags(original_glossdata)

    # Get all combined-tokens glosses and tokens
    combined_glossdata = get_glosses("sga_dipsgg-ud-test_combined_POS.conllu", "conllu")
    combined_tokens = get_pos_tags(combined_glossdata)

    # Get all separated-tokens glosses and tokens
    split_glossdata = get_glosses("sga_dipsgg-ud-test_split_POS.conllu", "conllu")
    split_tokens = get_pos_tags(split_glossdata)

    # Train taggers and test on random selection of glosses and test
    # Print score for each corpus tested
    for i in test_random_selection([original_words, combined_tokens, split_tokens], 5):
        print(i)

    # Train taggers and test on random selection of glosses multiple times
    # Print average score for each corpus tested
    for i in multi_test_random([original_words, combined_tokens, split_tokens], 5, 1000):
        print(i)
