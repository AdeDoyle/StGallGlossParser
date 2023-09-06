from OpenXlsx import list_xlsx
from Clean_Glosses import clean_gloss, clean_word
from conllu import parse
import nltk
from nltk.tag import brill, brill_trainer
import random


def get_glosses(gloss_file, file_type, combined_analyses=False):
    """Get a numbered list of POS tagged sentences from either the original Excel file, or the new CoNLL-U files"""

    # If the input is the combined Excel file
    if file_type == "excel":
        compiled_glosses = list()
        glosslist = list()
        sgData = list_xlsx(gloss_file, "Sheet 1")
        for datum in sgData:
            glossnum = datum[0]
            token = clean_word(datum[2])
            word_class = datum[5]
            if not word_class:
                word_class = ""
            if not combined_analyses:
                postag = word_class
            else:
                sub_class = datum[6]
                if not sub_class:
                    sub_class = ""
                morph = datum[7]
                if not morph:
                    morph = ""
                postag = f"{word_class} - {sub_class} - {morph}"
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
    """Extracts words/tokens and associated analyses/POS-tags from either Excel or CoNLL-U files"""

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


def train_pos_tagger(pos_file, tagger_style="n-gram", ngram=1):
    """Train's an n-gram POS-tagger model for a selected language"""

    universal_cutoff = 0

    if tagger_style == "brill":

        templates = [
            brill.Template(brill.Pos([-1])),
            brill.Template(brill.Pos([1])),
            brill.Template(brill.Pos([-2])),
            brill.Template(brill.Pos([2])),
            brill.Template(brill.Pos([-2, -1])),
            brill.Template(brill.Pos([1, 2])),
            brill.Template(brill.Pos([-3, -2, -1])),
            brill.Template(brill.Pos([1, 2, 3])),
            brill.Template(brill.Pos([-1]), brill.Pos([1])),
            brill.Template(brill.Word([-1])),
            brill.Template(brill.Word([1])),
            brill.Template(brill.Word([-2])),
            brill.Template(brill.Word([2])),
            brill.Template(brill.Word([-2, -1])),
            brill.Template(brill.Word([1, 2])),
            brill.Template(brill.Word([-3, -2, -1])),
            brill.Template(brill.Word([1, 2, 3])),
            brill.Template(brill.Word([-1]), brill.Word([1])),
        ]
        post1 = nltk.UnigramTagger(pos_file, cutoff=universal_cutoff)
        trainer = brill_trainer.BrillTaggerTrainer(post1, templates, deterministic=True)
        pos_tagger = trainer.train(pos_file)

    elif tagger_style == "HMM":
        pos_tagger = nltk.HiddenMarkovModelTagger.train(pos_file)

    elif tagger_style == "n-gram":
        if ngram < 1:
            raise RuntimeError(f"n value of {ngram} not possible")
        elif ngram == 1:
            pos_tagger = nltk.UnigramTagger(pos_file, cutoff=universal_cutoff)
        elif ngram == 2:
            post1 = nltk.UnigramTagger(pos_file, cutoff=universal_cutoff)
            pos_tagger = nltk.BigramTagger(pos_file, backoff=post1, cutoff=universal_cutoff)
        elif ngram == 3:
            post1 = nltk.UnigramTagger(pos_file, cutoff=universal_cutoff)
            post2 = nltk.BigramTagger(pos_file, backoff=post1, cutoff=universal_cutoff)
            pos_tagger = nltk.NgramTagger(ngram, pos_file, backoff=post2, cutoff=universal_cutoff)
        elif ngram == 4:
            post1 = nltk.UnigramTagger(pos_file, cutoff=universal_cutoff)
            post2 = nltk.BigramTagger(pos_file, backoff=post1, cutoff=universal_cutoff)
            post3 = nltk.NgramTagger(3, pos_file, backoff=post2, cutoff=universal_cutoff)
            pos_tagger = nltk.NgramTagger(ngram, pos_file, backoff=post3, cutoff=universal_cutoff)
        elif ngram == 5:
            post1 = nltk.UnigramTagger(pos_file, cutoff=universal_cutoff)
            post2 = nltk.BigramTagger(pos_file, backoff=post1, cutoff=universal_cutoff)
            post3 = nltk.NgramTagger(3, pos_file, backoff=post2, cutoff=universal_cutoff)
            post4 = nltk.NgramTagger(4, pos_file, backoff=post3, cutoff=universal_cutoff)
            pos_tagger = nltk.NgramTagger(ngram, pos_file, backoff=post4, cutoff=universal_cutoff)
        elif ngram == 6:
            post1 = nltk.UnigramTagger(pos_file, cutoff=universal_cutoff)
            post2 = nltk.BigramTagger(pos_file, backoff=post1, cutoff=universal_cutoff)
            post3 = nltk.NgramTagger(3, pos_file, backoff=post2, cutoff=universal_cutoff)
            post4 = nltk.NgramTagger(4, pos_file, backoff=post3, cutoff=universal_cutoff)
            post5 = nltk.NgramTagger(5, pos_file, backoff=post4, cutoff=universal_cutoff)
            pos_tagger = nltk.NgramTagger(ngram, pos_file, backoff=post5, cutoff=universal_cutoff)
        else:
            raise RuntimeError(f"n value of {ngram} not possible")

    elif tagger_style == "perceptron":
        pos_tagger = nltk.PerceptronTagger(load=False)
        pos_tagger.train(pos_file)

    else:
        raise RuntimeError(f"Style of POS-tagger not supported: {tagger_style}")

    return pos_tagger


def test_random_selection(corpora, test_set_percentage=10, tagger_style="n-gram", ngram=1):
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

        # Separate the glosses into test and training sets based on the random indices
        test_split = separate_test(corpus, train_gloss_indices, test_gloss_indices)
        train_set = test_split[0]
        test_set = test_split[1]

        # Separate the test set into tokens and correct POS-tags
        test_toks = [[token[0] for token in sent] for sent in test_set]
        test_pos = [[token[1] for token in sent] for sent in test_set]

        # Train a POS-tagger on the training files
        tagger = train_pos_tagger(train_set, tagger_style, ngram)

        # Evaluate POS tagger on the test files
        correct = list()
        incorrect = list()
        # Test the tagger on each gloss, and compile a list of POS "guesses" for each gloss in the test set
        for gloss_indx, test_gloss in enumerate(test_toks):
            guesses = tagger.tag(test_gloss)
            guesses = [guess[1] if guess[1] else "No Guess" for guess in guesses]
            true_tags = test_pos[gloss_indx]
            # Combine POS "guesses" with the correct POS-tags in a list for each gloss
            combined_guess_answers = zip(guesses, true_tags)
            # Check whether each pair in the guesses-corrects match, indicating a correct guess by the tagger
            for combo in combined_guess_answers:
                # Add each correctly tagged POS to a list of correctly tagged parts-of-speech
                if combo[0] == combo[1]:
                    correct.append(combo[1])
                # Add each incorrectly tagged POS to a list of incorrectly tagged parts-of-speech
                else:
                    incorrect.append(combo[1])
        total = len(correct + incorrect)
        accuracy = len(correct) / total

        # Add a list containing the accuracy of the tagger for the single pass to the results
        # Also add a list of all correctly guessed POS tags, and another of all incorrectly guessed POS tags
        results.append([accuracy, correct, incorrect])

    return results


def multi_test_random(corpora, test_percent, tests_range, tagger_style="n-gram", ngram=1,  verbose=True):
    """Tests NLTK unigram tagger on the same random selection of glosses for each corpus inputted
       Carries out this test several times for each corpus and averages the scores"""

    # Train and evaluate POS-tagger on a random sample of glosses multiple times
    # Random sample changes each pass, but remains the same for each corpus being tested in a given pass
    multi_test_results = list()
    for test_num in range(tests_range):
        if verbose:
            print(f"Test {test_num + 1} of {tests_range} in progress ...")
        multi_test_results.append(test_random_selection(corpora, test_percent, tagger_style, ngram))

    # Extract the accuracies for each pass from the combined results
    multi_test_accuracies = [[results[0] for results in tagging_pass] for tagging_pass in multi_test_results]

    # Average the accuracy results
    multi_test_accuracies = [sum(elts) for elts in zip(*multi_test_accuracies)]
    multi_test_accuracies = [(summed_test / tests_range) for summed_test in multi_test_accuracies]

    # Extract the correctly guessed parts-of-speech from the combined results
    multi_test_corrects = [[results[1] for results in tagging_pass] for tagging_pass in multi_test_results]
    combined_corrects = [[a for b in pos_pass for a in b] for pos_pass in zip(*multi_test_corrects)]
    # Distill a sorted list of unique correctly tagged parts-of-speech for use in averaging correct guesses
    all_correct_pos = list()
    for tok_standard in combined_corrects:
        all_correct_pos.append(sorted(list(set(tok_standard))))

    # Extract the incorrectly guessed parts-of-speech from the combined results
    multi_test_incorrects = [[results[2] for results in tagging_pass] for tagging_pass in multi_test_results]
    combined_incorrects = [[a for b in pos_pass for a in b] for pos_pass in zip(*multi_test_incorrects)]
    # Distill a sorted list of unique incorrectly tagged parts-of-speech for use in averaging incorrect guesses
    all_incorrect_pos = list()
    for tok_standard in combined_incorrects:
        all_incorrect_pos.append(sorted(list(set(tok_standard))))

    # Average the accuracy of correctly guessed parts-of-speech
    correct_pos_counts = list()
    for std_indx, tok_standard in enumerate(all_correct_pos):
        correct_pos_counts.append(
            [
                [
                    pos_type,
                    combined_corrects[std_indx].count(pos_type) /
                    (
                            combined_corrects[std_indx].count(pos_type) + combined_incorrects[std_indx].count(pos_type)
                     )
                ] for pos_type in tok_standard
            ]
        )

    # Average the accuracy of incorrectly guessed parts-of-speech
    incorrect_pos_counts = list()
    for std_indx, tok_standard in enumerate(all_incorrect_pos):
        incorrect_pos_counts.append(
            [
                [
                    pos_type,
                    combined_incorrects[std_indx].count(pos_type) /
                    (
                            combined_corrects[std_indx].count(pos_type) + combined_incorrects[std_indx].count(pos_type)
                    )
                ] for pos_type in tok_standard
            ]
        )

    return list(zip(multi_test_accuracies, correct_pos_counts, incorrect_pos_counts))


def pos_percent(test_output, pos_totals_list):
    """Determine the percentage of unique POS-tags occurring in the test-sets
       Also calculate the percentage of tokens correctly and incorrectly POS-tagged within the test-sets"""

    if isinstance(test_output[0], tuple):
        test_output = [
            [
                info if isinstance(info, float) else [pos_info[0] for pos_info in info] for info in style
            ] for style in test_output
        ]

    percentages = list()
    for tok_standard_indx, output in enumerate(test_output):
        percent_occurring = 100 * (len(sorted(list(set(output[1] + output[2])))) / pos_totals_list[tok_standard_indx])
        percent_correct = 100 * (len(sorted(list(set(output[1])))) / pos_totals_list[tok_standard_indx])
        percent_incorrect = 100 * (len(sorted(list(set(output[2])))) / pos_totals_list[tok_standard_indx])
        percentages.append([percent_occurring, percent_correct, percent_incorrect])

    return percentages


if __name__ == "__main__":

    # Get all original glosses and combined analyses
    combined_original_data = get_glosses("SG. Combined Data", "excel", True)
    combined_analyses = get_pos_tags(combined_original_data)

    # Get all original glosses and "word-forms"
    original_glossdata = get_glosses("SG. Combined Data", "excel")
    original_words = get_pos_tags(original_glossdata)

    # Get all combined-tokens glosses and tokens
    combined_glossdata = get_glosses("sga_dipsgg-ud-test_combined_POS.conllu", "conllu")
    combined_tokens = get_pos_tags(combined_glossdata)

    # Get all separated-tokens glosses and tokens
    split_glossdata = get_glosses("sga_dipsgg-ud-test_split_POS.conllu", "conllu")
    split_tokens = get_pos_tags(split_glossdata)

    # Calculate the number of unique parts-of-speech for each word-separation/tokenisation style
    unique_combo_anal = len(sorted(list(set([pair[1] for pair in [a for b in combined_analyses for a in b]]))))
    unique_orig_words = len(sorted(list(set([pair[1] for pair in [a for b in original_words for a in b]]))))
    unique_combo_toks = len(sorted(list(set([pair[1] for pair in [a for b in combined_tokens for a in b]]))))
    unique_split_toks = len(sorted(list(set([pair[1] for pair in [a for b in split_tokens for a in b]]))))
    print(f"Total unique combined analyses:\n    {unique_combo_anal}\n"
          f"Total unique word classes:\n    {unique_orig_words}\n"
          f"Total unique parts-of-speech (combined tokens):\n    {unique_combo_toks}\n"
          f"Total unique parts-of-speech (separated tokens):\n    {unique_split_toks}")
    print()
    sorted_pos_totals = [unique_combo_anal, unique_orig_words, unique_combo_toks, unique_split_toks]

    # Combine annotated corpora in a list
    combined_corpora = [combined_analyses, original_words, combined_tokens, split_tokens]

    # Set number of passes for Monte Carlo cross-validation
    num_passes = 1000

    # Set n for n-gram POS-tagger
    tagger_n = 1

    # Train Brill taggers and test on random selection of glosses multiple times
    brill_multi_pass = multi_test_random(combined_corpora, 5, num_passes, "brill")

    print()
    print(f"Brill tagging with {num_passes} passes.")

    # Print average score (with/without word-level breakdown) for each corpus tested
    for i in brill_multi_pass[2:]:
        print(i)
        # print(i[0])

    # Output the overall accuracy over multiple passes, and percentage of all unique POS-tags occurring in test-set
    # Also output percentage of unique POS-tags both correctly and incorrectly assigned
    multi_pass_percentages = pos_percent(brill_multi_pass, sorted_pos_totals)
    for tok_style_indx, output in enumerate(brill_multi_pass):
        print(
            f"Accuracy: {output[0]},\n"
            f"  Unique POS-tags occurring in test-set: {multi_pass_percentages[tok_style_indx][0]}%\n"
            f"  Unique POS-tags occurring in test-set correctly tagged: {multi_pass_percentages[tok_style_indx][1]}%\n"
            f"  Unique POS-tags occurring in test-set incorrectly tagged: {multi_pass_percentages[tok_style_indx][2]}%"
        )
    print()

    # Train HMM taggers and test on random selection of glosses multiple times
    hmm_multi_pass = multi_test_random(combined_corpora, 5, num_passes, "HMM")

    print()
    print(f"HMM tagging with {num_passes} passes.")

    # Print average score (with/without word-level breakdown) for each corpus tested
    for i in hmm_multi_pass[2:]:
        print(i)
        # print(i[0])

    # Output the overall accuracy over multiple passes, and percentage of all unique POS-tags occurring in test-set
    # Also output percentage of unique POS-tags both correctly and incorrectly assigned
    multi_pass_percentages = pos_percent(hmm_multi_pass, sorted_pos_totals)
    for tok_style_indx, output in enumerate(hmm_multi_pass):
        print(
            f"Accuracy: {output[0]},\n"
            f"  Unique POS-tags occurring in test-set: {multi_pass_percentages[tok_style_indx][0]}%\n"
            f"  Unique POS-tags occurring in test-set correctly tagged: {multi_pass_percentages[tok_style_indx][1]}%\n"
            f"  Unique POS-tags occurring in test-set incorrectly tagged: {multi_pass_percentages[tok_style_indx][2]}%"
        )
    print()

    # Train n-gram taggers and test on random selection of glosses multiple times
    ngram_multi_pass = multi_test_random(combined_corpora, 5, num_passes, "n-gram", tagger_n)

    print()
    print(f"N-gram tagging with {num_passes} passes and n={tagger_n}.")

    # Print average score for each corpus tested
    for i in ngram_multi_pass[2:]:
        print(i)
        # print(i[0])

    # Output the overall accuracy over multiple passes, and percentage of all unique POS-tags occurring in test-set
    # Also output percentage of unique POS-tags both correctly and incorrectly assigned
    multi_pass_percentages = pos_percent(ngram_multi_pass, sorted_pos_totals)
    for tok_style_indx, output in enumerate(ngram_multi_pass):
        print(
            f"Accuracy: {output[0]},\n"
            f"  Unique POS-tags occurring in test-set: {multi_pass_percentages[tok_style_indx][0]}%\n"
            f"  Unique POS-tags occurring in test-set correctly tagged: {multi_pass_percentages[tok_style_indx][1]}%\n"
            f"  Unique POS-tags occurring in test-set incorrectly tagged: {multi_pass_percentages[tok_style_indx][2]}%"
        )
    print()

    # Train Perceptron taggers and test on random selection of glosses multiple times
    perceptron_multi_pass = multi_test_random(combined_corpora, 5, num_passes, "perceptron")

    print()
    print(f"Perceptron tagging with {num_passes} passes.")

    # Print average score for each corpus tested
    for i in perceptron_multi_pass[2:]:
        print(i)
        # print(i[0])

    # Output the overall accuracy over multiple passes, and percentage of all unique POS-tags occurring in test-set
    # Also output percentage of unique POS-tags both correctly and incorrectly assigned
    multi_pass_percentages = pos_percent(perceptron_multi_pass, sorted_pos_totals)
    for tok_style_indx, output in enumerate(perceptron_multi_pass):
        print(
            f"Accuracy: {output[0]},\n"
            f"  Unique POS-tags occurring in test-set: {multi_pass_percentages[tok_style_indx][0]}%\n"
            f"  Unique POS-tags occurring in test-set correctly tagged: {multi_pass_percentages[tok_style_indx][1]}%\n"
            f"  Unique POS-tags occurring in test-set incorrectly tagged: {multi_pass_percentages[tok_style_indx][2]}%"
        )
    print()

    ten_thousand_pass_test_results = [
        (0.47146099077543124, [
            ['Precedes and forms compd. with qualified noun -  - composition form', 1.0],
            ['adjective -  - in adverbial phrase i recc', 0.6465696465696466],
            ['adjective -  - nom.sg.', 0.7044388609715243],
            ['adjective -  - nom.sg.masc.', 0.38148443735035914],
            ['adjective - i - acc.pl.', 0.492573071394346],
            ['adjective - i - comparative', 0.44903362456976437],
            ['adjective - i - dat.sg.', 0.7152394775036285],
            ['adjective - i - dat.sg.neut.', 0.27523727351164795],
            ['adjective - i - gen.pl.', 0.7484029484029484],
            ['adjective - i - nom.pl.fem.', 0.707667731629393],
            ['adjective - i - nom.sg.', 0.5072445239921589],
            ['adjective - i - nom.sg.fem.', 0.21603116515169402],
            ['adjective - i - nom.sg.masc.', 0.09403028257305429],
            ['adjective - i - nom.sg.neut.', 0.22912829957028852],
            ['adjective - i̯o, i̯ā - acc.pl.masc.', 0.49449059162569925],
            ['adjective - i̯o, i̯ā - acc.sg.', 0.03454648848450384],
            ['adjective - i̯o, i̯ā - acc.sg.fem.', 0.19144958245045493],
            ['adjective - i̯o, i̯ā - acc.sg.neut.', 0.21331885026737968],
            ['adjective - i̯o, i̯ā - clitic form', 0.44573495811119573],
            ['adjective - i̯o, i̯ā - composition form', 0.4673802242609582],
            ['adjective - i̯o, i̯ā - dat.pl.', 0.0002231644722160232],
            ['adjective - i̯o, i̯ā - dat.pl.masc.', 0.0008016032064128256],
            ['adjective - i̯o, i̯ā - dat.sg.', 0.09323254139668827],
            ['adjective - i̯o, i̯ā - dat.sg.fem', 0.18383838383838383],
            ['adjective - i̯o, i̯ā - dat.sg.masc.', 0.401729018437763],
            ['adjective - i̯o, i̯ā - dat.sg.neut.', 0.00011727453969743169],
            ['adjective - i̯o, i̯ā - gen.pl.fem.', 0.31796448087431695],
            ['adjective - i̯o, i̯ā - gen.sg.', 0.3801940781288878],
            ['adjective - i̯o, i̯ā - gen.sg.fem.', 0.12361795657386439],
            ['adjective - i̯o, i̯ā - gen.sg.masc.', 0.3976145488899386],
            ['adjective - i̯o, i̯ā - gen.sg.neut.', 0.20871103250055273],
            ['adjective - i̯o, i̯ā - nom.pl.', 0.15417233378670295],
            ['adjective - i̯o, i̯ā - nom.pl.masc.', 0.000310896937665164],
            ['adjective - i̯o, i̯ā - nom.sg.', 0.19244850337946573],
            ['adjective - i̯o, i̯ā - nom.sg.fem.', 0.3390057695669911],
            ['adjective - i̯o, i̯ā - nom.sg.masc.', 0.0541661917246096],
            ['adjective - i̯o, i̯ā - nom.sg.neut.', 0.15811353211009174],
            ['adjective - o, ā - acc.pl.neut.', 0.7108554277138569],
            ['adjective - o, ā - acc.sg.fem.', 0.22445561139028475],
            ['adjective - o, ā - comparative', 0.49489113827349124],
            ['adjective - o, ā - composition form', 0.4415700267618198],
            ['adjective - o, ā - dat.du.', 0.9546351084812623],
            ['adjective - o, ā - dat.sg.neut.', 0.12522135087275488],
            ['adjective - o, ā - gen.pl.masc.', 0.6345895020188426],
            ['adjective - o, ā - gen.sg.', 0.5901574803149606],
            ['adjective - o, ā - gen.sg.neut.', 0.3764618064195073],
            ['adjective - o, ā - nom.pl.', 0.00011834319526627219],
            ['adjective - o, ā - nom.pl.neut.', 0.10655257296917126],
            ['adjective - o, ā - nom.sg.', 0.36439896972990854],
            ['adjective - o, ā - nom.sg.fem.', 0.07773214464589803],
            ['adjective - o, ā - nom.sg.masc.', 0.0799282304749653],
            ['adjective - o, ā - nom.sg.neut.', 0.12662788902043548],
            ['adjective - o, ā - superlative', 0.47653256704980845],
            ['adjective - o, ā - voc.sg.fem.', 0.9453993933265925],
            ['adjective - o, ā and noun - gen.sg.', 0.8283963227783453],
            ['adjective - o, ā and noun - nom.sg.', 0.7447354904982023],
            ['adjective - prefix - composition form', 0.9443892750744787],
            ['adjective - u - comparative', 0.997539975399754],
            ['adjective - u - composition form', 0.9056571815718157],
            ['adjective - u - dat.pl.', 1.0],
            ['adjective - u - nom.sg.', 0.8466399506781751],
            ['adjective - u - nom.sg.masc.', 0.6261744966442953],
            ['adjective, demonstrative pronominal - this, these - ', 0.7765853658536586],
            ['adjective, indefinite pronominal -  - dat.sg.', 0.002485089463220676],
            ['adjective, indefinite pronominal -  - dat.sg.masc.', 0.8410649455425575],
            ['adjective, pronominal (preceding noun) -  - acc.sg.fem.', 0.026733121884911646],
            ['adjective, pronominal (preceding noun) -  - dat.sg.fem', 0.004875545291249679],
            ['adjective, pronominal (preceding noun) -  - dat.sg.masc.', 0.04887410440122825],
            ['adjective, pronominal (preceding noun) -  - gen.sg.fem.', 0.046466602129719266],
            ['adverb -  - ', 0.6956369819935242],
            ['adverb - autonomous negative - ', 0.9565667011375388],
            ['adverb - conjunctive - ', 1.0],
            ['adverb; preposition, with accusative -  - adverbial form', 0.9588053553038105],
            ['article - fem - dat.pl + do 1', 0.0012340600575894694],
            ['article - fem - gen.sg.', 0.9004810941910858],
            ['article - fem - nom.sg.', 0.41076596071602345],
            ['article - m - dat.pl + do 1', 0.00033760972316002703],
            ['article - m - dat.sg. + i 2', 0.2616837918462048],
            ['article - m - nom.sg.', 0.9030226201323139],
            ['article - n - acc.sg. + fri', 0.00022598870056497175],
            ['article - n - dat.pl + do 1', 0.689935064935065],
            ['article - n - dat.pl. + i 2', 1.0],
            ['article - n - dat.sg. + do 1', 0.08223259509385242],
            ['article - n - dat.sg. + i 2', 0.0048672566371681415],
            ['article - n - dat.sg. + ó 1', 0.9565390926426892],
            ['article - n - gen.sg.', 0.03648724756617588],
            ['article - n - nom.sg.', 0.9556622034888382],
            ['conjunction (disjunct) and discourse marker -  - ', 0.10423525890451961],
            ['conjunction (disjunct) and discourse marker -  - disjoins members within the clause', 0.9332257878665668],
            ['conjunction (leniting) - coordinating - joining two sentences or clauses', 1.0],
            ['conjunction (nasalizing, conjunct) -  - ', 0.9788819250421606],
            ['conjunction -  - ', 1.0],
            ['conjunction - causal - ', 0.9828044239426443],
            ['conjunction - causal; coordinating and subordinating - ', 0.9035916107255281],
            ['conjunction - concessive and explicative (leniting) - ', 0.9798796283671919],
            ['conjunction - conditional - ', 0.9419797222059427],
            ['conjunction - conditional, temporal - ', 0.9988950276243094],
            ['conjunction - disjunct (leniting) - ', 0.6804697156983931],
            ['conjunction - negative subordinating - ', 0.8141194141945175],
            ['conjunction - subordinate negative, with infixed pronouns Class C - ', 0.03985969387755102],
            ['conjunction - temporal - ', 0.9478584729981379],
            ['conjunction - temporal, adversative; (prep la + dem pron so 1 acc sg nt) - ', 1.0],
            ['conjunction and adverb (conjunctive) -  - ', 0.9735473159933592],
            ['conjunction and preposition -  - acc.sg.', 0.7449443882709808],
            ['emphasizing particle -  - ', 0.9200847585893749],
            ['noun - [m, ?] u - nom.sg.', 0.9478957915831663],
            ['noun - [m] i - gen.sg.', 0.9863907003118798],
            ['noun - adjectival noun - nom.pl.neut.', 0.8970684039087948],
            ['noun - f - dat.pl.', 1.0],
            ['noun - f - dat.sg.', 0.3217954443948191],
            ['noun - f - gen.pl.', 1.0],
            ['noun - f - nom.pl.', 0.7028315110737314],
            ['noun - f - nom.sg.', 0.24060765618329302],
            ['noun - f, i - acc.sg.', 0.4340684068406841],
            ['noun - f, i - dat.sg.', 0.15774410774410774],
            ['noun - f, i - dat.sg. (?)', 1.0],
            ['noun - f, i - gen.sg.', 0.4528124264532831],
            ['noun - f, i - nom.sg.', 0.5922279792746113],
            ['noun - f, i and n - dat.sg.', 0.05160857908847185],
            ['noun - f, i, ī - acc.sg.', 0.768562030075188],
            ['noun - f, i̯ā - acc.sg.', 0.20043067748881896],
            ['noun - f, i̯ā - composition form', 0.9631525076765609],
            ['noun - f, i̯ā - dat.du.', 0.9551020408163265],
            ['noun - f, i̯ā - dat.sg.', 0.2550106856119679],
            ['noun - f, i̯ā - gen.du.', 0.5235655737704918],
            ['noun - f, i̯ā - gen.pl.', 0.38699186991869916],
            ['noun - f, i̯ā - gen.sg.', 0.40006895759108146],
            ['noun - f, i̯ā - nom.sg.', 0.3789179247451912],
            ['noun - f, k - acc.sg.', 0.9980353634577603],
            ['noun - f, k - gen.sg.', 0.5043218085106383],
            ['noun - f, k - nom.sg.', 0.7484029484029484],
            ['noun - f, mixed ā-, ī-, i- - dat.sg.', 0.990899689762151],
            ['noun - f, mixed ā-, ī-, i- - gen.sg.', 0.7538538040775733],
            ['noun - f, mixed ā-, ī-, i- - nom.sg.', 0.7418616480162767],
            ['noun - f, n (?) - nom.sg.', 0.9507186858316222],
            ['noun - f, n - acc.pl.', 0.8636763412489006],
            ['noun - f, n - acc.sg.', 0.13109048723897912],
            ['noun - f, n - dat.pl.', 0.8416405582455141],
            ['noun - f, n - dat.sg.', 0.7180633871281353],
            ['noun - f, n - gen.sg.', 0.8490566037735849],
            ['noun - f, n - nom.sg.', 0.6589529897240877],
            ['noun - f, r - gen.sg.', 1.0],
            ['noun - f, r - nom.sg.', 0.47246525990735977],
            ['noun - f, ā - acc.pl.', 0.0016348773841961854],
            ['noun - f, ā - acc.sg.', 0.5841096145202039],
            ['noun - f, ā - composition form', 0.5621034114468807],
            ['noun - f, ā - dat.pl.', 0.5312370421561852],
            ['noun - f, ā - dat.sg.', 0.34750865471395664],
            ['noun - f, ā - dat.sg. (?)', 0.7714658831211231],
            ['noun - f, ā - gen.pl.', 0.004716157205240175],
            ['noun - f, ā - gen.sg.', 0.4580114568229897],
            ['noun - f, ā - nom.pl.', 0.40525838621940163],
            ['noun - f, ā - nom.sg.', 0.6564483122144821],
            ['noun - f, ā and m, u - acc.sg.', 0.9338582677165355],
            ['noun - f, ā; adjective - acc.sg.', 0.9854397204426325],
            ['noun - gender unknown, i-stem - gen.sg.', 0.000505050505050505],
            ['noun - gender unknown, i-stem - nom.pl.', 0.5524202300846538],
            ['noun - gender unknown, i-stem - nom.sg.', 0.9046156893819335],
            ['noun - i - acc.sg.', 0.9485657764589516],
            ['noun - i - nom.sg.', 0.232706002034588],
            ['noun - m - nom.sg.', 0.4085412735024813],
            ['noun - m and f - nom.sg.', 0.4928076718167288],
            ['noun - m and n, o - dat.sg.', 0.798049573344169],
            ['noun - m and n, o - gen.sg.', 0.9551656920077972],
            ['noun - m and n, o - nom.sg.', 0.5532400799314873],
            ['noun - m, dent. - gen.sg.', 0.31106612685560053],
            ['noun - m, i - acc.pl.', 0.8672108301811666],
            ['noun - m, i - acc.sg.', 0.07144935972060536],
            ['noun - m, i - dat.sg.', 0.2859163467367145],
            ['noun - m, i - gen.sg.', 0.4180468303826385],
            ['noun - m, i - nom.sg.', 0.24530438257626216],
            ['noun - m, i̯o - nom.sg.', 0.25882980141276823],
            ['noun - m, i̯o and i - gen.sg.', 0.9505154639175257],
            ['noun - m, i̯o and i - nom.sg.', 0.7415446744068652],
            ['noun - m, k - nom.sg.', 0.979253112033195],
            ['noun - m, o - acc.pl.', 0.742663004192569],
            ['noun - m, o - acc.sg.', 0.29910737320055725],
            ['noun - m, o - composition form', 0.19541155162004428],
            ['noun - m, o - dat.pl.', 0.5676564872616838],
            ['noun - m, o - dat.sg.', 0.5485953661117229],
            ['noun - m, o - gen.pl.', 0.00035214367461924466],
            ['noun - m, o - gen.sg.', 0.5975765869162178],
            ['noun - m, o - nom.pl.', 0.2952517985611511],
            ['noun - m, o - nom.sg.', 0.4336289634209814],
            ['noun - m, o and f, ā - nom.sg.', 0.31786074672048437],
            ['noun - m, o orig. n - dat.sg.', 0.9939879759519038],
            ['noun - m, o orig. n, s (?) - nom.sg.', 0.9563492063492064],
            ['noun - m, r - gen.sg.', 0.9916870415647921],
            ['noun - m, r - nom.sg.', 0.276850306065665],
            ['noun - m, t - acc.pl.', 0.9457364341085271],
            ['noun - m, t - gen.sg.', 0.4724689165186501],
            ['noun - m, t - nom.sg.', 0.14928169893816365],
            ['noun - m, u - acc.sg.', 0.23464343986946923],
            ['noun - m, u - composition form', 0.0005577244841048522],
            ['noun - m, u - dat.pl.', 0.2903573629081947],
            ['noun - m, u - dat.sg.', 0.33303473997947847],
            ['noun - m, u - gen.sg.', 0.5576622200263505],
            ['noun - m, u - nom.pl.', 0.02172321210641933],
            ['noun - m, u - nom.sg.', 0.5301984732824427],
            ['noun - n (?), o - acc.sg.', 0.751219512195122],
            ['noun - n - nom.sg.', 0.12236762284426726],
            ['noun - n and m, o - gen.sg.', 0.6379310344827587],
            ['noun - n and m, u - dat.du.', 0.8388401888064734],
            ['noun - n and m, u - nom.sg.', 0.9368797141722905],
            ['noun - n, i - gen.sg.', 0.9426310583580614],
            ['noun - n, i̯o & adjective - nom.sg.', 0.7550617283950617],
            ['noun - n, i̯o - acc.sg.', 0.014695652173913044],
            ['noun - n, i̯o - dat.sg.', 0.15785011868429977],
            ['noun - n, i̯o - gen.sg.', 0.16666666666666666],
            ['noun - n, i̯o - nom.sg.', 0.42441980579849875],
            ['noun - n, n - acc.pl.', 0.12281639928698752],
            ['noun - n, n - dat.pl.', 0.7398103476958908],
            ['noun - n, n - dat.sg.', 0.6657868690201254],
            ['noun - n, n - gen.pl.', 0.2833634356813165],
            ['noun - n, n - gen.sg.', 0.700371920037192],
            ['noun - n, n - nom.pl.', 0.41215715344699777],
            ['noun - n, n - nom.sg.', 0.8305193075898801],
            ['noun - n, o (m, o?) - acc.sg.', 0.032168886654938424],
            ['noun - n, o (m, o?) - dat.sg.', 0.0003259452411994785],
            ['noun - n, o (m, o?) - gen.sg.', 0.9272195722418833],
            ['noun - n, o (m, o?) - nom.sg.', 0.13634204275534442],
            ['noun - n, o - acc.pl.', 0.15661839003031325],
            ['noun - n, o - acc.sg.', 0.29921701478473517],
            ['noun - n, o - dat.sg.', 0.5301204819277109],
            ['noun - n, o - gen.pl.', 0.16295427901524032],
            ['noun - n, o - gen.sg.', 0.5970737197523917],
            ['noun - n, o - nom.sg.', 0.6505645375645722],
            ['noun - n, o, later m, o - acc.sg.', 0.0009678199854827002],
            ['noun - n, o, later m, o - dat.sg.', 0.9480782198246797],
            ['noun - n, o, later m, o - gen.sg.', 0.9979722879351132],
            ['noun - n, o, later m, o - nom.sg.', 0.7505815885676305],
            ['noun - n, s and n, o - acc./dat.sg.', 0.06551952349437459],
            ['noun - n, s and n, o - composition form', 0.05467196819085487],
            ['noun - n, s and n, o - dat.sg.', 0.6767250942977591],
            ['noun - n, u - gen.sg.', 0.38010657193605685],
            ['noun - n, u - nom.sg.', 0.4870077141697117],
            ['noun - n, u or o - nom.sg.', 0.9268468989446291],
            ['noun - o (?) - dat.sg.', 1.0],
            ['noun - o - acc.sg.', 0.9128566517703678],
            ['noun - o - dat.sg.', 0.6494736842105263],
            ['noun - o - nom.sg.', 0.15137067938021453],
            ['noun - unknown declension - nom.sg.', 0.2819281616363183],
            ['noun and adjective - i - acc.sg.', 0.998015873015873],
            ['noun, proper -  - gen.sg.', 0.1329059829059829],
            ['noun, proper -  - nom.sg.', 0.08892155061546941],
            ['number - adjective - composition form', 0.723060536126398],
            ['number - adjective - dat.du.', 0.10553783705421861],
            ['number - adjective - dat.du.masc.', 0.010040160642570281],
            ['number - adjective - gen.du.fem.', 0.8443839683325086],
            ['number - adjective - gen.pl.fem.', 0.06256410256410257],
            ['number - adjective - nom.du.fem.', 0.19370011402508552],
            ['number - adjective - nom.pl.fem.', 0.012036108324974924],
            ['particle - connective - ', 1.0],
            ['particle - interrrogative - ', 0.24190457942134508],
            ['particle - negative - ', 0.9898213582769415],
            ['particle - negative dependent relative - ', 0.9756389394084426],
            ['particle - prefix - composition form', 0.6009254627313657],
            ['particle - prefix and preverb - composition form', 0.6582633053221288],
            ['particle - prefix, negative - ', 1.0],
            ['particle - prefix, privative - composition form', 0.027683997299122215],
            ['particle - preverb - ', 0.9120374064439941],
            ['particle - preverb - *ad-com-lā', 0.19485772064134046],
            ['particle - preverb - *ad-tā- (*bw-)', 0.3301364023870418],
            ['particle - preverb - *ar-ber-', 0.3706636500754148],
            ['particle - preverb - *ar-fo-em-', 0.2587118351494228],
            ['particle - preverb - *as-gnina-', 0.874938574938575],
            ['particle - preverb - *com-to-eter-reth-', 0.00202020202020202],
            ['particle - preverb - *com-uss-anā-', 0.04757085020242915],
            ['particle - preverb - *com-uss-scochī-', 0.01038781163434903],
            ['particle - preverb - *con-icc-', 0.021759367000232722],
            ['particle - preverb - *de-gnī-', 0.031929165548698686],
            ['particle - preverb - *dī-en-lā-', 0.5668571428571428],
            ['particle - preverb - *dī-ro-uss-scōchī-', 0.1263986997562043],
            ['particle - preverb - *ess-ber-', 0.05588512734514202],
            ['particle - preverb - *ess-inde-fēd-', 0.01694373401534527],
            ['particle - preverb - *for-cennā-', 0.00033178500331785003],
            ['particle - preverb - *for-con-gari-', 0.0003178639542275906],
            ['particle - preverb - *for-de-en-gari-', 0.20453544693967415],
            ['particle - preverb - *imm-com-arc-', 0.021244309559939303],
            ['particle - preverb - *imm-fo-longī-', 0.339],
            ['particle - preverb - *imm-imm-gabi-', 0.0025201612903225806],
            ['particle - preverb - *in-com-sech', 0.36015356314484526],
            ['particle - preverb - *remi-tēg-', 0.0019398642095053346],
            ['particle - preverb - *to-ad-fēd-', 0.08839220014716703],
            ['particle - preverb - *to-ari-uss-gabi- (?)', 0.31768707482993197],
            ['particle - preverb - *to-ber-', 0.26468501143262635],
            ['particle - preverb - *to-con-sechi-', 0.4797365754812563],
            ['particle - preverb - *to-de-uss-reg-', 0.33299629255139873],
            ['particle - preverb - *to-fo-rindā-', 0.0992470536883457],
            ['particle - preverb - *to-for-mag-', 0.2183145321831453],
            ['particle - preverb - *to-iarm-fo-reth-', 0.3723509117792016],
            ['particle - preverb - *to-in-com-icc-', 0.6231204406729195],
            ['particle - preverb - *to-tēg- (*to-reg-, *to-lud-, *to-di-com-fād-)', 0.0006205013651030033],
            ['particle - preverb - *to-uss-sem-', 0.20013793103448277],
            ['particle - preverb - díxnigidir', 0.23882113821138212],
            ['particle - transitional - ', 1.0],
            ['particle, emphatic pronominal - 1sg - ', 0.7568385226270011],
            ['particle, emphatic pronominal - 3pl - ', 0.0966458826058912],
            ['particle, emphatic pronominal - 3sg f - ', 0.18647093830589168],
            ['particle, emphatic pronominal - 3sg m, n - ', 0.9579152377323341],
            ['preposition, nominal, with gen - nasalizing - ', 0.7977254264825345],
            ['preposition, with acc -  - acc.', 0.9472314897003459],
            ['preposition, with acc -  - acc. + suff.pron.3pl.', 0.8992304873580066],
            ['preposition, with acc; and adversative conjunction -  - ', 0.9818005880382598],
            ['preposition, with acc; and conjunction -  - ', 0.20941929583904892],
            ['preposition, with acc; and conjunction -  - acc.', 0.6375534860307073],
            ['preposition, with acc; geminating -  - acc.', 0.9862427729712575],
            ['preposition, with acc; geminating -  - acc. + suff.pron.1pl.', 0.9865567533291059],
            ['preposition, with acc; geminating -  - acc. + suff.pron.1sg.', 0.7757482394366197],
            ['preposition, with acc; geminating -  - acc. + suff.pron.2sg.', 0.8847616916536137],
            ['preposition, with acc; geminating -  - acc. + suff.pron.3pl.', 0.9593415007656968],
            ['preposition, with acc; geminating -  - acc. + suff.pron.3sg.fem.', 0.7288644322161081],
            ['preposition, with acc; geminating -  - acc. + suff.pron.3sg.masc./neut.', 0.8879136109025813],
            ['preposition, with acc; leniting -  - acc.', 0.9696705041683208],
            ['preposition, with acc; leniting -  - acc. + suff.pron.3pl.', 0.9538461538461539],
            ['preposition, with acc; leniting -  - acc. + suff.pron.3sg.masc./neut.', 0.8795041495955458],
            ['preposition, with acc; leniting; and conjunction -  - ', 1.0],
            ['preposition, with acc; leniting; and conjunction -  - acc. + suff.pron.3sg.masc./neut.',
             0.8080505655355955],
            ['preposition, with dat -  - dat.', 0.7059798697454115],
            ['preposition, with dat -  - dat. + suff.pron.3sg.masc./neut.', 0.4904522613065327],
            ['preposition, with dat and acc; leniting -  - acc.', 0.48650279471544716],
            ['preposition, with dat and acc; leniting -  - acc. + suff.pron.3pl.', 0.3999171156237049],
            ['preposition, with dat and acc; leniting -  - acc. + suff.pron.3sg.masc./neut.', 0.9358609921127438],
            ['preposition, with dat and acc; leniting -  - dat.', 0.3469701558604944],
            ['preposition, with dat and acc; leniting -  - dat. + suff.pron.3pl.', 0.8766266266266266],
            ['preposition, with dat and acc; leniting -  - dat. + suff.pron.3sg.fem.', 1.0],
            ['preposition, with dat and acc; nasalizing -  - acc. + suff.pron.3sg.fem.', 1.0],
            ['preposition, with dat and acc; nasalizing -  - dat.', 0.7586542116644129],
            ['preposition, with dat and acc; nasalizing -  - dat. + suff.pron.3pl.', 0.9751492026220526],
            ['preposition, with dat and acc; nasalizing -  - dat. + suff.pron.3sg.fem.', 0.8831136533200696],
            ['preposition, with dat and acc; nasalizing -  - dat. + suff.pron.3sg.masc./neut.', 0.9753828119276138],
            ['preposition, with dat; geminating -  - dat. + suff.pron.3sg.masc./neut.', 0.27431632365379194],
            ['preposition, with dat; leniting -  - dat.', 0.9486611447902712],
            ['preposition, with dat; leniting -  - dat. + def.art.sg.', 0.1094752365736758],
            ['preposition, with dat; leniting -  - dat. + suff.pron.1pl.', 0.7789725209080047],
            ['preposition, with dat; leniting -  - dat. + suff.pron.1sg.', 1.0],
            ['preposition, with dat; leniting -  - dat. + suff.pron.2sg.', 0.7140401146131805],
            ['preposition, with dat; leniting -  - dat. + suff.pron.3pl.', 0.8495566453658295],
            ['preposition, with dat; leniting -  - dat. + suff.pron.3sg.masc./neut.', 0.46425677240101876],
            ['preposition, with dat; nasalizing -  - dat.', 0.6615897765632535],
            ['preposition, with dat; nasalizing -  - dat. + suff.pron.3sg.fem.', 0.9091516366065464],
            ['preposition, with dat; nasalizing -  - dat. + suff.pron.3sg.masc./neut.', 1.0],
            ['preposition, with gen; and conjunction -  - ', 0.6185636856368564],
            ['pronoun - interrogative - ', 0.9474237644584648],
            ['pronoun, anaphoric - enclitic - ', 0.33485694938208904],
            ['pronoun, anaphoric - enclitic - nom.pl.', 0.9586831639416703],
            ['pronoun, anaphoric - enclitic - nom.sg.fem.', 0.5901830931047916],
            ['pronoun, anaphoric - indeclinable neuter enclitic - ', 1.0],
            ['pronoun, anaphoric - neuter, stressed - acc.sg.', 0.9774289284598563],
            ['pronoun, anaphoric - neuter, stressed - dat.sg.', 0.0010141987829614604],
            ['pronoun, anaphoric - stressed - acc.sg.fem.', 0.9586349534643226],
            ['pronoun, anaphoric - stressed - acc.sg.masc.', 0.4980276134122288],
            ['pronoun, anaphoric - stressed - dat.pl.', 0.9917582417582418],
            ['pronoun, anaphoric - stressed - dat.sg.neut.', 0.9664299548095545],
            ['pronoun, demonstrative - neuter, indeclinable - ', 0.795190380761523],
            ['pronoun, demonstrative - that, those - ', 1.0],
            ['pronoun, indeclinable  -  - acc.sg.', 0.03607843137254902],
            ['pronoun, indeclinable  -  - dat.sg.', 0.2327543424317618],
            ['pronoun, indeclinable  -  - nom.sg.', 0.17306263926714532],
            ['pronoun, indeclinable, accented, deictic -  - dat.sg.neut.', 0.8940983606557377],
            ['pronoun, indeclinable, accented, deictic -  - nom.sg.neut.', 0.8982621899780665],
            ['pronoun, indefinite -  - nom.sg.', 1.0],
            ['pronoun, indefinite - m - dat.sg.', 0.9945770065075922],
            ['pronoun, indefinite - m - gen.sg.', 1.0],
            ['pronoun, indefinite - m - nom.sg.', 1.0],
            ['pronoun, infixed, class A - 1sg - ', 0.9848],
            ['pronoun, infixed, class A - 3pl - ', 0.6931673052362708],
            ['pronoun, infixed, class B - 3sg n (leniting) - ', 0.0035419126328217238],
            ['pronoun, infixed, class C - 3pl (geminating) - ', 0.011067708333333334],
            ['pronoun, infixed, class C - 3sg n (leniting) - ', 0.21544271926143516],
            ['pronoun, interrogative and indefinite -  - ', 0.27312669274751733],
            ['pronoun, non-neuter -  - acc.sg.', 0.46502463054187193],
            ['pronoun, personal - 2sg - ', 0.9571865443425076],
            ['pronoun, personal - 3pl - ', 0.5905519641969169],
            ['pronoun, personal - 3sg f - ', 0.9463616190986304],
            ['pronoun, personal - 3sg m - ', 0.3395120911899435],
            ['pronoun, personal - 3sg n - ', 0.9362522446392733],
            ['pronoun, possessive, stressed - 3sg and pl - pl.', 0.7256819351518271],
            ['pronoun, possessive, stressed - 3sg and pl - sg.', 0.5793966989186112],
            ['pronoun, possessive, unstressed - 1sg (leniting) - ', 0.9201797892126472],
            ['pronoun, possessive, unstressed - 3sg m, n (leniting) - ', 0.18160565797650402],
            ['pronoun, reflexive -  - ', 0.24386966745045346],
            ['pronoun, reflexive -  - 3sg.', 0.0032854209445585215],
            ['pronoun, reflexive -  - 3sg.fem.', 0.014163372859025032],
            ['pronoun, reflexive -  - 3sg.neut.', 0.7639833296775609],
            ['see amail -  - ', 0.02891156462585034],
            ['verb - AI - 3pl.pres.ind.', 0.39032746394709583],
            ['verb - AI - 3pl.pres.ind.pass.', 0.12896636252212992],
            ['verb - AI - 3sg.perf.', 0.21467764060356653],
            ['verb - AI - 3sg.pres.ind.', 0.5946529231760348],
            ['verb - AI - 3sg.pres.ind. + infix.pron. Class C 3sg.fem.', 0.9631901840490797],
            ['verb - AI - 3sg.pres.ind.pass.', 0.35505124450951686],
            ['verb - AI - 3sg.pres.ind.rel.', 0.5462209302325581],
            ['verb - AII - 3pl.pres.ind.', 0.14370003806623524],
            ['verb - AII - 3pl.pres.ind.rel.', 0.3027636251350934],
            ['verb - AII - 3sg.pass.perf.', 0.6254705144291092],
            ['verb - AII - 3sg.pres.ind.', 0.34809069212410504],
            ['verb - AII - 3sg.pres.ind.pass.', 0.20916820702402958],
            ['verb - AII - 3sg.pres.ind.rel.', 0.03666499246609744],
            ['verb - AII - 3sg.pres.subj.rel.', 0.003380009657170449],
            ['verb - AIII - 3pl.pres.ind.', 0.21398002853067047],
            ['verb - AIII - 3pl.pres.ind.rel.', 0.9454545454545454],
            ['verb - AIII - 3sg.perf.', 0.37565922920892497],
            ['verb - AIII - 3sg.pres.ind.', 0.5483595169391899],
            ['verb - AIII - 3sg.pres.ind.pass.', 0.21613768439874834],
            ['verb - AIII - 3sg.pres.ind.pass.rel.', 0.968],
            ['verb - BI (?) - 1sg.pres.ind.', 0.9452313503305004],
            ['verb - BI - 1sg.perf. + infix pron Class C 3sg.neut.', 0.9451679232350926],
            ['verb - BI - 1sg.pres.ind.', 0.28211965480461554],
            ['verb - BI - 1sg.pres.ind. + infix pron Class A 3sg.neut.', 0.75],
            ['verb - BI - 1sg.pres.ind. + infix pron Class C 3sg.neut.', 0.6372347707049966],
            ['verb - BI - 2sg.pres.subj.', 0.3269168026101142],
            ['verb - BI - 3pl.pres.ind.', 0.3616206534494472],
            ['verb - BI - 3pl.pres.ind.pass.', 0.0072319652865666245],
            ['verb - BI - 3pl.pres.ind.rel.', 0.7507660878447395],
            ['verb - BI - 3pl.pres.subj.pass.', 0.4812182741116751],
            ['verb - BI - 3sg.pass.perf.', 0.18939300284336755],
            ['verb - BI - 3sg.perf.', 0.4229513418810225],
            ['verb - BI - 3sg.pres.ind.', 0.4169115246490369],
            ['verb - BI - 3sg.pres.ind.pass.', 0.6101850288278291],
            ['verb - BI - 3sg.pres.ind.rel.', 0.6171894924764091],
            ['verb - BII - 3sg.perf. + infix.pron. Class C 3sg.neut.', 0.908321060382916],
            ['verb - BII - 3sg.pres.ind.', 0.17366997294860234],
            ['verb - BII - 3sg.pres.ind.rel.', 0.636795655125594],
            ['verb - BII - 3sg.pres.subj.', 1.0],
            ['verb - BIV - 1sg.pres.ind.', 0.4781297134238311],
            ['verb - BV - 3sg.pres.ind.pass.', 0.536421992743511],
            ['verb - copula - 3pl.fut.', 0.6389452332657201],
            ['verb - copula - 3pl.pres.ind.', 0.9175319175632862],
            ['verb - copula - 3pl.pres.ind.rel.', 0.2302134281903068],
            ['verb - copula - 3pl.pres.subj.rel.', 0.788174139051332],
            ['verb - copula - 3sg.cons.pres.', 0.014285714285714285],
            ['verb - copula - 3sg.impv.', 0.996005326231691],
            ['verb - copula - 3sg.past.subj.', 0.7294102307792603],
            ['verb - copula - 3sg.perf.', 0.5756584610087795],
            ['verb - copula - 3sg.pres.ind.', 0.7534873969907594],
            ['verb - copula - 3sg.pres.ind.rel.', 0.9861222627737226],
            ['verb - copula - 3sg.pres.subj.', 0.7810745264261837],
            ['verb - copula - 3sg.pres.subj.rel.', 0.6669634906500446],
            ['verb - copula - 3sg.pret.', 0.00032797638570022957],
            ['verb - substantive verb - 3pl.cons.pres.', 0.7168402617752788],
            ['verb - substantive verb - 3pl.cons.pres.rel.', 0.8036854588578727],
            ['verb - substantive verb - 3pl.past.subj.', 0.9979702300405954],
            ['verb - substantive verb - 3pl.pres.ind.', 0.8368583271335955],
            ['verb - substantive verb - 3sg.cons.pres.', 0.7029903525938133],
            ['verb - substantive verb - 3sg.cons.pres.rel.', 0.9229935329520392],
            ['verb - substantive verb - 3sg.fut.', 0.3796334012219959],
            ['verb - substantive verb - 3sg.imperf.', 0.7571500250878074],
            ['verb - substantive verb - 3sg.past.subj.', 0.31500276803838345],
            ['verb - substantive verb - 3sg.perf.', 0.8226011246145475],
            ['verb - substantive verb - 3sg.pres.ind.', 0.6288663328989781],
            ['verb - substantive verb - 3sg.pres.ind.rel.', 0.9806709017663464],
            ['verb - substantive verb - 3sg.pres.subj.', 0.572415536270958]
        ],
         [
          [' -  - ', 1.0], ['abbreviation -  - ', 1.0], ['adjective -  - ', 1.0], ['adjective -  - acc.sg.', 1.0],
          ['adjective -  - dat.pl.masc.', 1.0], ['adjective -  - gen.sg.', 1.0], ['adjective -  - gen.sg.masc.', 1.0],
          ['adjective -  - in adverbial phrase i recc', 0.35343035343035345],
          ['adjective -  - nom.sg.', 0.2955611390284757], ['adjective -  - nom.sg.masc.', 0.6185155626496409],
          ['adjective -  - nom.sg.neut.', 1.0], ['adjective - i - ', 1.0],
          ['adjective - i - acc.pl.', 0.5074269286056541], ['adjective - i - acc.pl.fem.', 1.0],
          ['adjective - i - acc.pl.neut.', 1.0], ['adjective - i - acc.sg.', 1.0], ['adjective - i - acc.sg.fem', 1.0],
          ['adjective - i - acc.sg.fem.', 1.0], ['adjective - i - acc.sg.masc.', 1.0],
          ['adjective - i - acc.sg.neut.', 1.0], ['adjective - i - comparative', 0.5509663754302356],
          ['adjective - i - composition form', 1.0], ['adjective - i - dat.pl.', 1.0],
          ['adjective - i - dat.pl.fem.', 1.0], ['adjective - i - dat.pl.neut.', 1.0],
          ['adjective - i - dat.sg.', 0.28476052249637157], ['adjective - i - dat.sg.fem', 1.0],
          ['adjective - i - dat.sg.masc.', 1.0], ['adjective - i - dat.sg.neut.', 0.724762726488352],
          ['adjective - i - gen.pl.', 0.2515970515970516], ['adjective - i - gen.pl.fem.', 1.0],
          ['adjective - i - gen.sg.', 1.0], ['adjective - i - gen.sg.fem.', 1.0], ['adjective - i - gen.sg.masc.', 1.0],
          ['adjective - i - gen.sg.neut.', 1.0], ['adjective - i - nom.pl.', 1.0],
          ['adjective - i - nom.pl.fem.', 0.29233226837060705], ['adjective - i - nom.sg.', 0.49275547600784114],
          ['adjective - i - nom.sg.fem.', 0.783968834848306], ['adjective - i - nom.sg.masc.', 0.9059697174269457],
          ['adjective - i - nom.sg.neut.', 0.7708717004297114], ['adjective - i - superlative', 1.0],
          ['adjective - indeclinable (?) - nom.sg.', 1.0], ['adjective - i̯o, i̯ā - acc.du.fem.', 1.0],
          ['adjective - i̯o, i̯ā - acc.pl.', 1.0], ['adjective - i̯o, i̯ā - acc.pl.fem.', 1.0],
          ['adjective - i̯o, i̯ā - acc.pl.masc.', 0.5055094083743007], ['adjective - i̯o, i̯ā - acc.pl.neut.', 1.0],
          ['adjective - i̯o, i̯ā - acc.sg.', 0.9654535115154962], ['adjective - i̯o, i̯ā - acc.sg.fem', 1.0],
          ['adjective - i̯o, i̯ā - acc.sg.fem.', 0.808550417549545], ['adjective - i̯o, i̯ā - acc.sg.masc.', 1.0],
          ['adjective - i̯o, i̯ā - acc.sg.neut.', 0.7866811497326203], ['adjective - i̯o, i̯ā - adverbial form', 1.0],
          ['adjective - i̯o, i̯ā - clitic form', 0.5542650418888042], ['adjective - i̯o, i̯ā - comparative', 1.0],
          ['adjective - i̯o, i̯ā - composition form', 0.5326197757390418], ['adjective - i̯o, i̯ā - dat.du.', 1.0],
          ['adjective - i̯o, i̯ā - dat.du.neut.', 1.0], ['adjective - i̯o, i̯ā - dat.pl.', 0.999776835527784],
          ['adjective - i̯o, i̯ā - dat.pl.fem.', 1.0], ['adjective - i̯o, i̯ā - dat.pl.masc.', 0.9991983967935871],
          ['adjective - i̯o, i̯ā - dat.pl.neut.', 1.0], ['adjective - i̯o, i̯ā - dat.sg.', 0.9067674586033118],
          ['adjective - i̯o, i̯ā - dat.sg.fem', 0.8161616161616162], ['adjective - i̯o, i̯ā - dat.sg.masc + ó 1', 1.0],
          ['adjective - i̯o, i̯ā - dat.sg.masc.', 0.598270981562237],
          ['adjective - i̯o, i̯ā - dat.sg.neut.', 0.9998827254603025], ['adjective - i̯o, i̯ā - gen.pl.', 1.0],
          ['adjective - i̯o, i̯ā - gen.pl.fem.', 0.682035519125683], ['adjective - i̯o, i̯ā - gen.pl.masc.', 1.0],
          ['adjective - i̯o, i̯ā - gen.pl.neut.', 1.0], ['adjective - i̯o, i̯ā - gen.sg.', 0.6198059218711122],
          ['adjective - i̯o, i̯ā - gen.sg.fem.', 0.8763820434261356],
          ['adjective - i̯o, i̯ā - gen.sg.masc.', 0.6023854511100614],
          ['adjective - i̯o, i̯ā - gen.sg.neut.', 0.7912889674994472], ['adjective - i̯o, i̯ā - nom.du.fem.', 1.0],
          ['adjective - i̯o, i̯ā - nom.pl.', 0.8458276662132971], ['adjective - i̯o, i̯ā - nom.pl.fem.', 1.0],
          ['adjective - i̯o, i̯ā - nom.pl.masc.', 0.9996891030623348], ['adjective - i̯o, i̯ā - nom.pl.neut.', 1.0],
          ['adjective - i̯o, i̯ā - nom.sg.', 0.8075514966205343],
          ['adjective - i̯o, i̯ā - nom.sg.fem.', 0.6609942304330089],
          ['adjective - i̯o, i̯ā - nom.sg.masc.', 0.9458338082753904],
          ['adjective - i̯o, i̯ā - nom.sg.neut.', 0.8418864678899083], ['adjective - i̯o, i̯ā - voc.sg.', 1.0],
          ['adjective - o, ā - acc.du.masc.', 1.0], ['adjective - o, ā - acc.pl.', 1.0],
          ['adjective - o, ā - acc.pl.masc.', 1.0], ['adjective - o, ā - acc.pl.neut.', 0.2891445722861431],
          ['adjective - o, ā - acc.sg.', 1.0], ['adjective - o, ā - acc.sg.fem.', 0.7755443886097152],
          ['adjective - o, ā - acc.sg.masc.', 1.0], ['adjective - o, ā - acc.sg.neut.', 1.0],
          ['adjective - o, ā - comparative', 0.5051088617265088],
          ['adjective - o, ā - composition form', 0.5584299732381802],
          ['adjective - o, ā - dat.du.', 0.045364891518737675], ['adjective - o, ā - dat.pl.', 1.0],
          ['adjective - o, ā - dat.pl.fem.', 1.0], ['adjective - o, ā - dat.pl.masc.', 1.0],
          ['adjective - o, ā - dat.pl.neut.', 1.0], ['adjective - o, ā - dat.sg.', 1.0],
          ['adjective - o, ā - dat.sg.fem', 1.0], ['adjective - o, ā - dat.sg.masc.', 1.0],
          ['adjective - o, ā - dat.sg.neut.', 0.8747786491272451], ['adjective - o, ā - gen.pl.fem.', 1.0],
          ['adjective - o, ā - gen.pl.masc.', 0.3654104979811575], ['adjective - o, ā - gen.pl.neut.', 1.0],
          ['adjective - o, ā - gen.sg.', 0.4098425196850394], ['adjective - o, ā - gen.sg.fem.', 1.0],
          ['adjective - o, ā - gen.sg.masc.', 1.0], ['adjective - o, ā - gen.sg.neut.', 0.6235381935804927],
          ['adjective - o, ā - nom.du.neut.', 1.0], ['adjective - o, ā - nom.pl.', 0.9998816568047337],
          ['adjective - o, ā - nom.pl.fem.', 1.0], ['adjective - o, ā - nom.pl.masc.', 1.0],
          ['adjective - o, ā - nom.pl.neut.', 0.8934474270308287], ['adjective - o, ā - nom.sg.', 0.6356010302700914],
          ['adjective - o, ā - nom.sg.fem.', 0.9222678553541019],
          ['adjective - o, ā - nom.sg.masc.', 0.9200717695250347],
          ['adjective - o, ā - nom.sg.neut.', 0.8733721109795646],
          ['adjective - o, ā - superlative', 0.5234674329501916],
          ['adjective - o, ā - voc.sg.fem.', 0.054600606673407485],
          ['adjective - o, ā and adverb - composition form', 1.0], ['adjective - o, ā and adverb - dat.sg.neut.', 1.0],
          ['adjective - o, ā and noun - acc.pl.', 1.0], ['adjective - o, ā and noun - acc.sg.', 1.0],
          ['adjective - o, ā and noun - comparative', 1.0],
          ['adjective - o, ā and noun - gen.sg.', 0.17160367722165476], ['adjective - o, ā and noun - nom.pl.', 1.0],
          ['adjective - o, ā and noun - nom.pl.neut.', 1.0],
          ['adjective - o, ā and noun - nom.sg.', 0.25526450950179763],
          ['adjective - o, ā and noun - nom.sg.masc.', 1.0], ['adjective - o, ā and noun - nom.sg.neut.', 1.0],
          ['adjective - o, ā, i - nom.sg.masc.', 1.0], ['adjective - prefix - composition form', 0.05561072492552135],
          ['adjective - u (?) - nom.sg.neut.', 1.0], ['adjective - u - acc.pl.masc.', 1.0],
          ['adjective - u - comparative', 0.0024600246002460025],
          ['adjective - u - composition form', 0.09434281842818429], ['adjective - u - dat.pl.fem.', 1.0],
          ['adjective - u - dat.pl.masc.', 1.0], ['adjective - u - dat.sg.', 1.0], ['adjective - u - gen.sg.fem.', 1.0],
          ['adjective - u - nom.sg.', 0.1533600493218249], ['adjective - u - nom.sg.masc.', 0.3738255033557047],
          ['adjective - u - nom.sg.neut.', 1.0], ['adjective and noun - u - nom.sg.', 1.0],
          ['adjective, demonstrative -  - dat.pl.fem.', 1.0], ['adjective, demonstrative -  - nom.pl.neut.', 1.0],
          ['adjective, demonstrative pronominal - this, these - ', 0.22341463414634147],
          ['adjective, demonstrative pronominal - this, these - acc.pl.', 1.0],
          ['adjective, demonstrative pronominal - this, these - acc.sg.fem.', 1.0],
          ['adjective, demonstrative pronominal - this, these - acc.sg.masc.', 1.0],
          ['adjective, demonstrative pronominal - this, these - acc.sg.neut.', 1.0],
          ['adjective, demonstrative pronominal - this, these - dat.pl.masc.', 1.0],
          ['adjective, demonstrative pronominal - this, these - dat.pl.neut.', 1.0],
          ['adjective, demonstrative pronominal - this, these - nom.pl.fem.', 1.0],
          ['adjective, demonstrative pronominal - this, these - nom.pl.masc.', 1.0],
          ['adjective, demonstrative pronominal - this, these - nom.sg.', 1.0],
          ['adjective, demonstrative pronominal - this, these - nom.sg.masc.', 1.0],
          ['adjective, demonstrative pronominal - this, these - nom.sg.neut.', 1.0],
          ['adjective, indefinite pronominal -  - ', 1.0], ['adjective, indefinite pronominal -  - acc.pl.', 1.0],
          ['adjective, indefinite pronominal -  - acc.pl.masc.', 1.0],
          ['adjective, indefinite pronominal -  - acc.sg.', 1.0],
          ['adjective, indefinite pronominal -  - acc.sg.fem.', 1.0],
          ['adjective, indefinite pronominal -  - acc.sg.masc.', 1.0],
          ['adjective, indefinite pronominal -  - acc.sg.neut.', 1.0],
          ['adjective, indefinite pronominal -  - dat.sg.', 0.9975149105367793],
          ['adjective, indefinite pronominal -  - dat.sg.masc.', 0.15893505445744252],
          ['adjective, indefinite pronominal -  - dat.sg.neut.', 1.0],
          ['adjective, indefinite pronominal -  - gen.sg.fem.', 1.0],
          ['adjective, indefinite pronominal -  - gen.sg.masc.', 1.0],
          ['adjective, indefinite pronominal -  - gen.sg.neut.', 1.0],
          ['adjective, indefinite pronominal -  - nom.sg.', 1.0],
          ['adjective, indefinite pronominal -  - nom.sg.fem.', 1.0],
          ['adjective, indefinite pronominal -  - nom.sg.neut.', 1.0],
          ['adjective, pronominal (preceding noun) -  - acc.sg.', 1.0],
          ['adjective, pronominal (preceding noun) -  - acc.sg.fem.', 0.9732668781150884],
          ['adjective, pronominal (preceding noun) -  - acc.sg.masc.', 1.0],
          ['adjective, pronominal (preceding noun) -  - acc.sg.neut.', 1.0],
          ['adjective, pronominal (preceding noun) -  - dat.pl.fem.', 1.0],
          ['adjective, pronominal (preceding noun) -  - dat.pl.masc.', 1.0],
          ['adjective, pronominal (preceding noun) -  - dat.sg.fem', 0.9951244547087503],
          ['adjective, pronominal (preceding noun) -  - dat.sg.masc.', 0.9511258955987717],
          ['adjective, pronominal (preceding noun) -  - dat.sg.neut.', 1.0],
          ['adjective, pronominal (preceding noun) -  - gen.sg. masc./neut.', 1.0],
          ['adjective, pronominal (preceding noun) -  - gen.sg.fem.', 0.9535333978702807],
          ['adjective, pronominal (preceding noun) -  - gen.sg.neut.', 1.0],
          ['adjective, pronominal (preceding noun) -  - nom.du.fem.', 1.0],
          ['adjective, pronominal (preceding noun) -  - nom.pl.', 1.0],
          ['adjective, pronominal (preceding noun) -  - nom.sg.fem.', 1.0],
          ['adjective, pronominal (preceding noun) -  - nom.sg.masc.', 1.0],
          ['adjective, pronominal (preceding noun) -  - nom.sg.neut.', 1.0], ['adverb -  - ', 0.3043630180064758],
          ['adverb -  - acc.', 1.0], ['adverb -  - dat.sg.', 1.0], ['adverb -  - dat.sg.neut.', 1.0],
          ['adverb - autonomous negative - ', 0.04343329886246122],
          ['adverb; preposition, with accusative -  - acc.', 1.0],
          ['adverb; preposition, with accusative -  - adverbial form', 0.0411946446961895],
          ['article - fem - acc.du.', 1.0], ['article - fem - acc.pl.', 1.0], ['article - fem - acc.pl. + for 1', 1.0],
          ['article - fem - acc.pl. + fri', 1.0], ['article - fem - acc.pl. + i 2', 1.0],
          ['article - fem - acc.pl. + la', 1.0], ['article - fem - acc.sg + i 2', 1.0],
          ['article - fem - acc.sg.', 1.0], ['article - fem - acc.sg. + for 1', 1.0],
          ['article - fem - acc.sg. + fri', 1.0], ['article - fem - acc.sg. + imm 1', 1.0],
          ['article - fem - acc.sg. + la', 1.0], ['article - fem - acc.sg. + tre 1', 1.0],
          ['article - fem - dat.pl + de 1', 1.0], ['article - fem - dat.pl + do 1', 0.9987659399424106],
          ['article - fem - dat.pl. + i 2', 1.0], ['article - fem - dat.pl. + ó 1', 1.0],
          ['article - fem - dat.sg.', 1.0], ['article - fem - dat.sg. + a 5', 1.0],
          ['article - fem - dat.sg. + de 1', 1.0], ['article - fem - dat.sg. + do 1', 1.0],
          ['article - fem - dat.sg. + for 1', 1.0], ['article - fem - dat.sg. + i 2', 1.0],
          ['article - fem - dat.sg. + oc', 1.0], ['article - fem - dat.sg. + íar 1', 1.0],
          ['article - fem - dat.sg. + ó 1', 1.0], ['article - fem - gen.du.', 1.0], ['article - fem - gen.pl.', 1.0],
          ['article - fem - gen.sg.', 0.09951890580891416], ['article - fem - nom.du.', 1.0],
          ['article - fem - nom.pl.', 1.0], ['article - fem - nom.sg', 1.0],
          ['article - fem - nom.sg.', 0.5892340392839766], ['article - fem - nom.sg. + í 1', 1.0],
          ['article - m - acc.du.', 1.0], ['article - m - acc.pl.', 1.0], ['article - m - acc.pl. + fri', 1.0],
          ['article - m - acc.pl. + la', 1.0], ['article - m - acc.pl. + tar', 1.0], ['article - m - acc.sg.', 1.0],
          ['article - m - acc.sg. + ar 1', 1.0], ['article - m - acc.sg. + for 1', 1.0],
          ['article - m - acc.sg. + fri', 1.0], ['article - m - acc.sg. + la', 1.0],
          ['article - m - acc.sg. + tre 1', 1.0], ['article - m - dat.pl + de 1', 1.0],
          ['article - m - dat.pl + do 1', 0.99966239027684], ['article - m - dat.pl + for 1', 1.0],
          ['article - m - dat.pl. + i 2', 1.0], ['article - m - dat.pl. + oc', 1.0],
          ['article - m - dat.pl. + ó 1', 1.0], ['article - m - dat.sg.', 1.0], ['article - m - dat.sg. + a 5', 1.0],
          ['article - m - dat.sg. + de 1', 1.0], ['article - m - dat.sg. + do 1', 1.0],
          ['article - m - dat.sg. + fo 1', 1.0], ['article - m - dat.sg. + for 1', 1.0],
          ['article - m - dat.sg. + i 2', 0.7383162081537952], ['article - m - dat.sg. + oc', 1.0],
          ['article - m - dat.sg. + ó 1', 1.0], ['article - m - gen.du.', 1.0], ['article - m - gen.pl.', 1.0],
          ['article - m - gen.sg.', 1.0], ['article - m - gen.sg. + í 1', 1.0], ['article - m - nom.du.', 1.0],
          ['article - m - nom.pl.', 1.0], ['article - m - nom.sg.', 0.09697737986768609],
          ['article - m - nom.sg. + í 1', 1.0], ['article - n - acc.pl.', 1.0], ['article - n - acc.pl. + fo 1', 1.0],
          ['article - n - acc.pl. + fri', 1.0], ['article - n - acc.pl. + la', 1.0],
          ['article - n - acc.sg + i 2', 1.0], ['article - n - acc.sg.', 1.0], ['article - n - acc.sg. + for 1', 1.0],
          ['article - n - acc.sg. + fri', 0.999774011299435], ['article - n - acc.sg. + la', 1.0],
          ['article - n - acc.sg. + tre 1', 1.0], ['article - n - dat.pl + do 1', 0.31006493506493504],
          ['article - n - dat.sg.', 1.0], ['article - n - dat.sg. + a 5', 1.0], ['article - n - dat.sg. + ar 1', 1.0],
          ['article - n - dat.sg. + de 1', 1.0], ['article - n - dat.sg. + do 1', 0.9177674049061476],
          ['article - n - dat.sg. + fo 1', 1.0], ['article - n - dat.sg. + i 2', 0.9951327433628319],
          ['article - n - dat.sg. + oc', 1.0], ['article - n - dat.sg. + íar 1', 1.0],
          ['article - n - dat.sg. + ó 1', 0.043460907357310744], ['article - n - gen.du.', 1.0],
          ['article - n - gen.pl.', 1.0], ['article - n - gen.pl. + í 1', 1.0],
          ['article - n - gen.sg.', 0.9635127524338242], ['article - n - gen.sg. + í 1', 1.0],
          ['article - n - nom.du.', 1.0], ['article - n - nom.pl.', 1.0], ['article - n - nom.pl. + í 1', 1.0],
          ['article - n - nom.sg.', 0.044337796511161764],
          ['conjunction (disjunct) and discourse marker -  - ', 0.8957647410954804],
          ['conjunction (disjunct) and discourse marker -  - disjoins co-ordinate clauses', 1.0],
          ['conjunction (disjunct) and discourse marker -  - disjoins members within the clause', 0.0667742121334332],
          ['conjunction (leniting) - coordinating - ', 1.0],
          ['conjunction (leniting) - coordinating - introducing sentence or clause', 1.0],
          ['conjunction (leniting) - coordinating - joining conj prep and noun', 1.0],
          ['conjunction (leniting) - coordinating - joining two Latin lemmata', 1.0],
          ['conjunction (leniting) - coordinating - joining two Latin phrases', 1.0],
          ['conjunction (leniting) - coordinating - joining two adjectives', 1.0],
          ['conjunction (leniting) - coordinating - joining two nouns', 1.0],
          ['conjunction (leniting) - coordinating - joining two nouns (letters of the alphabet)', 1.0],
          ['conjunction (leniting) - coordinating - joining two nouns with adjectives', 1.0],
          ['conjunction (leniting) - coordinating - joining two nouns with articles', 1.0],
          ['conjunction (leniting) - coordinating - joining two nouns with prepositions', 1.0],
          ['conjunction (leniting) - coordinating - joining two verbs', 1.0],
          ['conjunction (leniting, non-conjunct particle) -  - ', 1.0], ['conjunction (nasalizing) - temporal - ', 1.0],
          ['conjunction (nasalizing, conjunct) -  - ', 0.02111807495783936],
          ['conjunction (nasalizing, conjunct) -  - co 4 + copula', 1.0],
          ['conjunction - accumulative, adversative - ', 1.0], ['conjunction - causal - ', 0.017195576057355638],
          ['conjunction - causal; coordinating and subordinating - ', 0.09640838927447187],
          ['conjunction - comparative - ', 1.0],
          ['conjunction - concessive and explicative (leniting) - ', 0.02012037163280809],
          ['conjunction - concessive and explicative (leniting) - with copula', 1.0],
          ['conjunction - conditional - ', 0.058020277794057315], ['conjunction - conditional - ma + ní + copula', 1.0],
          ['conjunction - conditional - with 3pl.pres.sub. of copula', 1.0],
          ['conjunction - conditional - with 3sg.pres.subj. of copula', 1.0],
          ['conjunction - conditional - with negative', 1.0],
          ['conjunction - conditional, temporal - ', 0.0011049723756906078],
          ['conjunction - disjunct (leniting) - ', 0.3195302843016069], ['conjunction - disjunct - 1pl.', 1.0],
          ['conjunction - disjunct - 2sg.', 1.0], ['conjunction - disjunct - 3pl.', 1.0],
          ['conjunction - final (purpose), and explicative - ', 1.0],
          ['conjunction - introducing an optative clause - ', 1.0],
          ['conjunction - negative (geminating), before non-verbs; na before stressed words - ', 1.0],
          ['conjunction - negative (geminating), before non-verbs; na before stressed words - joining two nouns', 1.0],
          ['conjunction - negative subordinating - ', 0.18588058580548253],
          ['conjunction - subordinate negative, with infixed pronouns Class C - ', 0.9601403061224489],
          ['conjunction - subordinate negative, with infixed pronouns Class C - infix pron Class C 3sg n', 1.0],
          ['conjunction - subordinate negative, with infixed pronouns Class C - infix pron class C 3sg m', 1.0],
          ['conjunction - temporal - ', 0.0521415270018622],
          ['conjunction and adverb (conjunctive) -  - ', 0.02645268400664084],
          ['conjunction and preposition -  - acc.sg.', 0.2550556117290192],
          ['conjunction w/ subordinate negation -  - ', 1.0], ['emphasizing particle -  - ', 0.0799152414106251],
          ['exclamation form -  - ', 1.0], ['interjection -  - ', 1.0], ['interjection -  - nom.sg.', 1.0],
          ['noun - [f, i̯ā] - nom.sg.', 1.0], ['noun - [f, ā] - nom.sg.', 1.0], ['noun - [m, ?] i̯o - nom.sg.', 1.0],
          ['noun - [m, ?] u - nom.sg.', 0.052104208416833664], ['noun - [m, o] - nom.sg.', 1.0],
          ['noun - [m, u] - acc.sg.', 1.0], ['noun - [m, u] - nom.sg.', 1.0], ['noun - [m] i - dat.pl.', 1.0],
          ['noun - [m] i - gen.sg.', 0.013609299688120215], ['noun - [m] i - nom.pl.', 1.0],
          ['noun - [m] i - nom.sg.', 1.0], ['noun - [m] o - dat.pl.', 1.0], ['noun - [m] u - nom.sg.', 1.0],
          ['noun - [n, o] - nom.pl.', 1.0], ['noun - [n] ? - nom.sg.', 1.0], ['noun - [n], o - nom.sg.', 1.0],
          ['noun - adjectival noun - acc.sg.neut.', 1.0],
          ['noun - adjectival noun - nom.pl.neut.', 0.10293159609120521], ['noun - adjectival noun - nom.sg.', 1.0],
          ['noun - adjectival noun - nom.sg.neut.', 1.0], ['noun - f - acc.pl.', 1.0], ['noun - f - acc.sg.', 1.0],
          ['noun - f - dat.sg.', 0.6782045556051809], ['noun - f - gen.sg.', 1.0],
          ['noun - f - nom.pl.', 0.29716848892626857], ['noun - f - nom.sg.', 0.759392343816707],
          ['noun - f and m - gen.sg.', 1.0], ['noun - f and m - nom.sg.', 1.0], ['noun - f and n - gen.sg.neut.', 1.0],
          ['noun - f and n - nom.pl.', 1.0], ['noun - f, ? - nom.sg.', 1.0], ['noun - f, d - acc.sg.', 1.0],
          ['noun - f, i  - nom.sg.', 1.0], ['noun - f, i (?) - nom.sg.', 1.0], ['noun - f, i - acc.pl.', 1.0],
          ['noun - f, i - acc.sg.', 0.565931593159316], ['noun - f, i - composition form', 1.0],
          ['noun - f, i - dat.pl.', 1.0], ['noun - f, i - dat.sg.', 0.8422558922558923], ['noun - f, i - gen.pl.', 1.0],
          ['noun - f, i - gen.sg.', 0.5471875735467169], ['noun - f, i - nom.du.', 1.0], ['noun - f, i - nom.pl.', 1.0],
          ['noun - f, i - nom.sg.', 0.4077720207253886], ['noun - f, i and n - dat.sg.', 0.9483914209115282],
          ['noun - f, i and n - nom.du.', 1.0], ['noun - f, i and n - nom.sg.', 1.0],
          ['noun - f, i, later also k - nom.sg.', 1.0], ['noun - f, i, ī - acc.sg.', 0.23143796992481203],
          ['noun - f, i, ī - dat.sg.', 1.0], ['noun - f, i̯a (?) - nom.sg.', 1.0],
          ['noun - f, i̯ā & m, i̯o - dat.sg.', 1.0], ['noun - f, i̯ā (?) - acc.sg.', 1.0],
          ['noun - f, i̯ā - acc./dat.sg.', 1.0], ['noun - f, i̯ā - acc.du.', 1.0], ['noun - f, i̯ā - acc.pl.', 1.0],
          ['noun - f, i̯ā - acc.sg.', 0.7995693225111811], ['noun - f, i̯ā - composition form', 0.0368474923234391],
          ['noun - f, i̯ā - dat.du.', 0.044897959183673466], ['noun - f, i̯ā - dat.pl.', 1.0],
          ['noun - f, i̯ā - dat.sg.', 0.7449893143880321], ['noun - f, i̯ā - dat.sg. (?)', 1.0],
          ['noun - f, i̯ā - gen.du.', 0.4764344262295082], ['noun - f, i̯ā - gen.pl.', 0.6130081300813008],
          ['noun - f, i̯ā - gen.sg.', 0.5999310424089185], ['noun - f, i̯ā - nom.du.', 1.0],
          ['noun - f, i̯ā - nom.pl.', 1.0], ['noun - f, i̯ā - nom.sg.', 0.6210820752548089],
          ['noun - f, i̯ā - voc.sg.', 1.0], ['noun - f, k - acc.sg.', 0.0019646365422396855],
          ['noun - f, k - dat.sg.', 1.0], ['noun - f, k - gen.sg.', 0.4956781914893617], ['noun - f, k - nom.pl.', 1.0],
          ['noun - f, k - nom.sg.', 0.2515970515970516], ['noun - f, mixed ā-, ī-, i- - dat.sg.', 0.009100310237849017],
          ['noun - f, mixed ā-, ī-, i- - gen.sg.', 0.24614619592242665],
          ['noun - f, mixed ā-, ī-, i- - nom.sg.', 0.2581383519837233],
          ['noun - f, n (?) - nom.sg.', 0.049281314168377825], ['noun - f, n - acc.pl.', 0.1363236587510994],
          ['noun - f, n - acc.sg.', 0.8689095127610209], ['noun - f, n - dat.pl.', 0.1583594417544859],
          ['noun - f, n - dat.sg.', 0.28193661287186467], ['noun - f, n - gen.pl.', 1.0],
          ['noun - f, n - gen.sg.', 0.1509433962264151], ['noun - f, n - nom.du.', 1.0], ['noun - f, n - nom.pl.', 1.0],
          ['noun - f, n - nom.sg.', 0.3410470102759123], ['noun - f, nt - nom.sg.', 1.0],
          ['noun - f, r - composition form', 1.0], ['noun - f, r - nom.sg.', 0.5275347400926402],
          ['noun - f, t - acc.sg.', 1.0], ['noun - f, t - nom.sg.', 1.0], ['noun - f, u - nom.sg.', 1.0],
          ['noun - f, ā (?) - gen.sg.', 1.0], ['noun - f, ā (?) - nom.sg.', 1.0], ['noun - f, ā - ', 1.0],
          ['noun - f, ā - acc./dat.sg.', 1.0], ['noun - f, ā - acc.du.', 1.0],
          ['noun - f, ā - acc.pl.', 0.9983651226158038], ['noun - f, ā - acc.pl.masc.', 1.0],
          ['noun - f, ā - acc.sg.', 0.415890385479796], ['noun - f, ā - adverbial form', 1.0],
          ['noun - f, ā - composition form', 0.4378965885531193], ['noun - f, ā - dat.du.', 1.0],
          ['noun - f, ā - dat.pl.', 0.4687629578438148], ['noun - f, ā - dat.sg.', 0.6524913452860434],
          ['noun - f, ā - dat.sg. (?)', 0.22853411687887693], ['noun - f, ā - dat.sg.neut.', 1.0],
          ['noun - f, ā - gen.du.', 1.0], ['noun - f, ā - gen.pl.', 0.9952838427947598],
          ['noun - f, ā - gen.pl.fem.', 1.0], ['noun - f, ā - gen.sg.', 0.5419885431770103],
          ['noun - f, ā - nom.du.', 1.0], ['noun - f, ā - nom.pl.', 0.5947416137805984],
          ['noun - f, ā - nom.sg.', 0.3435516877855179], ['noun - f, ā - voc.sg.', 1.0],
          ['noun - f, ā and i - acc.sg.', 1.0], ['noun - f, ā and i - gen.pl.', 1.0],
          ['noun - f, ā and i - nom.sg.', 1.0], ['noun - f, ā and m, u - acc.sg.', 0.06614173228346457],
          ['noun - f, ā and m, u - dat.sg.', 1.0], ['noun - f, ā and m, u - gen.sg.', 1.0],
          ['noun - f, ā and m, u - nom.sg.', 1.0], ['noun - f, ā, later also m, o - nom.sg.', 1.0],
          ['noun - f, ā; adjective - acc.sg.', 0.014560279557367502], ['noun - f, ā; adjective - gen.sg.', 1.0],
          ['noun - f, ā; also f, n - acc.sg.', 1.0], ['noun - f, ī - acc.sg.', 1.0], ['noun - f, ī - nom.sg.', 1.0],
          ['noun - gender not attested in OIr. - dat.sg.', 1.0], ['noun - gender unknown, i-stem - acc.pl.', 1.0],
          ['noun - gender unknown, i-stem - acc.sg.', 1.0], ['noun - gender unknown, i-stem - adverbial form', 1.0],
          ['noun - gender unknown, i-stem - dat.sg.', 1.0], ['noun - gender unknown, i-stem - gen.pl.', 1.0],
          ['noun - gender unknown, i-stem - gen.sg.', 0.9994949494949495],
          ['noun - gender unknown, i-stem - nom.pl.', 0.4475797699153462],
          ['noun - gender unknown, i-stem - nom.sg.', 0.09538431061806656], ['noun - i  - nom.sg.', 1.0],
          ['noun - i - acc.sg.', 0.051434223541048464], ['noun - i - composition form', 1.0],
          ['noun - i - dat.sg.', 1.0], ['noun - i - gen.sg.', 1.0], ['noun - i - nom.sg.', 0.767293997965412],
          ['noun - irregular - gen.pl.', 1.0], ['noun - i̯o - dat.sg.', 1.0], ['noun - i̯o - gen.sg.', 1.0],
          ['noun - i̯o - nom.pl.', 1.0], ['noun - i̯o - nom.sg.', 1.0], ['noun - m - acc.sg.', 1.0],
          ['noun - m - dat.pl.', 1.0], ['noun - m - dat.sg.', 1.0], ['noun - m - gen.sg.', 1.0],
          ['noun - m - nom.du.', 1.0], ['noun - m - nom.sg.', 0.5914587264975187], ['noun - m and f - acc.sg.', 1.0],
          ['noun - m and f - gen.sg.', 1.0], ['noun - m and f - nom.sg.', 0.5071923281832712],
          ['noun - m and f - nom.sg.masc.', 1.0], ['noun - m and n - dat.sg.', 1.0], ['noun - m and n - nom.sg.', 1.0],
          ['noun - m and n, o (?) - nom.sg.', 1.0], ['noun - m and n, o - composition form', 1.0],
          ['noun - m and n, o - dat.sg.', 0.20195042665583096], ['noun - m and n, o - dat.sg.masc.', 1.0],
          ['noun - m and n, o - gen.pl.', 1.0], ['noun - m and n, o - gen.sg.', 0.04483430799220273],
          ['noun - m and n, o - nom.du.', 1.0], ['noun - m and n, o - nom.sg.', 0.44675992006851273],
          ['noun - m or n, i̯o - dat.sg.', 1.0], ['noun - m or n, i̯o - gen.pl.', 1.0],
          ['noun - m or n, i̯o - gen.sg.', 1.0], ['noun - m u (?) - nom.sg.', 1.0], ['noun - m, (n)k - dat.sg.', 1.0],
          ['noun - m, (n)k - gen.sg.', 1.0], ['noun - m, (n)k - nom.pl.', 1.0], ['noun - m, (n)k - nom.sg.', 1.0],
          ['noun - m, [i] - nom.sg.', 1.0], ['noun - m, and f - nom.sg.', 1.0], ['noun - m, and f, i - nom.sg.', 1.0],
          ['noun - m, dent. - acc.sg.', 1.0], ['noun - m, dent. - dat.sg.', 1.0],
          ['noun - m, dent. - gen.sg.', 0.6889338731443995], ['noun - m, dent. - nom.sg.', 1.0],
          ['noun - m, g - composition form', 1.0], ['noun - m, i (?) - nom.sg.', 1.0],
          ['noun - m, i - acc.pl.', 0.13278916981883337], ['noun - m, i - acc.sg.', 0.9285506402793946],
          ['noun - m, i - dat.pl.', 1.0], ['noun - m, i - dat.sg.', 0.7140836532632855],
          ['noun - m, i - gen.sg.', 0.5819531696173615], ['noun - m, i - nom.pl.', 1.0],
          ['noun - m, i - nom.sg.', 0.7546956174237378], ['noun - m, i̯o (?) - nom.pl.', 1.0],
          ['noun - m, i̯o (?) - nom.sg.', 1.0], ['noun - m, i̯o - dat.pl.', 1.0], ['noun - m, i̯o - dat.sg.', 1.0],
          ['noun - m, i̯o - gen.pl.', 1.0], ['noun - m, i̯o - gen.sg.', 1.0], ['noun - m, i̯o - nom.pl.', 1.0],
          ['noun - m, i̯o - nom.sg.', 0.7411701985872318], ['noun - m, i̯o and i - dat.pl.', 1.0],
          ['noun - m, i̯o and i - gen.sg.', 0.049484536082474224], ['noun - m, i̯o and i - nom.pl.', 1.0],
          ['noun - m, i̯o and i - nom.sg.', 0.2584553255931348], ['noun - m, k - nom.sg.', 0.02074688796680498],
          ['noun - m, n - dat.sg.', 1.0], ['noun - m, n - gen.sg.', 1.0], ['noun - m, n - nom.sg.', 1.0],
          ['noun - m, nt - dat.sg.', 1.0], ['noun - m, nt - nom.pl.', 1.0], ['noun - m, nt - nom.sg.', 1.0],
          ['noun - m, o (?) - nom.sg.', 1.0], ['noun - m, o - acc.du.', 1.0],
          ['noun - m, o - acc.pl.', 0.25733699580743097], ['noun - m, o - acc.sg.', 0.7008926267994428],
          ['noun - m, o - composition form', 0.8045884483799557], ['noun - m, o - dat.du.', 1.0],
          ['noun - m, o - dat.pl.', 0.43234351273831617], ['noun - m, o - dat.sg.', 0.45140463388827706],
          ['noun - m, o - gen.pl.', 0.9996478563253808], ['noun - m, o - gen.sg.', 0.4024234130837821],
          ['noun - m, o - nom.du.', 1.0], ['noun - m, o - nom.pl.', 0.704748201438849],
          ['noun - m, o - nom.sg.', 0.5663710365790185], ['noun - m, o - voc.pl.', 1.0], ['noun - m, o - voc.sg.', 1.0],
          ['noun - m, o also f, ā and i - gen.pl.', 1.0], ['noun - m, o and f, ā - composition form', 1.0],
          ['noun - m, o and f, ā - dat.sg.', 1.0], ['noun - m, o and f, ā - nom.sg.', 0.6821392532795156],
          ['noun - m, o and u - acc.sg.', 1.0], ['noun - m, o and u - dat.sg.', 1.0],
          ['noun - m, o and u - nom.pl.', 1.0], ['noun - m, o and u - nom.sg.', 1.0],
          ['noun - m, o orig. n - acc.sg.', 1.0], ['noun - m, o orig. n - dat.sg.', 0.006012024048096192],
          ['noun - m, o orig. n - nom.sg.', 1.0], ['noun - m, o orig. n - nom.sg.neut.', 1.0],
          ['noun - m, o orig. n, s (?) - nom.sg.', 0.04365079365079365],
          ['noun - m, o, later also f, ā - nom.sg.', 1.0], ['noun - m, r - acc.sg.', 1.0],
          ['noun - m, r - composition form', 1.0], ['noun - m, r - dat.pl.', 1.0], ['noun - m, r - dat.sg.', 1.0],
          ['noun - m, r - gen.sg.', 0.008312958435207823], ['noun - m, r - nom.sg.', 0.723149693934335],
          ['noun - m, t - acc.pl.', 0.05426356589147287], ['noun - m, t - acc.sg.', 1.0],
          ['noun - m, t - dat.sg.', 1.0], ['noun - m, t - gen.sg.', 0.5275310834813499], ['noun - m, t - nom.pl.', 1.0],
          ['noun - m, t - nom.sg.', 0.8507183010618363], ['noun - m, t and f, t - gen.sg.', 1.0],
          ['noun - m, u (?) - dat.pl.', 1.0], ['noun - m, u (?) - dat.sg.', 1.0], ['noun - m, u (?) - nom.pl.', 1.0],
          ['noun - m, u (?) - nom.sg.', 1.0], ['noun - m, u - ', 1.0], ['noun - m, u - acc./dat.sg.', 1.0],
          ['noun - m, u - acc.du.', 1.0], ['noun - m, u - acc.pl.', 1.0], ['noun - m, u - acc.sg.', 0.7653565601305308],
          ['noun - m, u - composition form', 0.9994422755158952], ['noun - m, u - dat.pl.', 0.7096426370918053],
          ['noun - m, u - dat.sg.', 0.6669652600205215], ['noun - m, u - gen.du.', 1.0], ['noun - m, u - gen.pl.', 1.0],
          ['noun - m, u - gen.sg.', 0.44233777997364954], ['noun - m, u - nom.du.', 1.0],
          ['noun - m, u - nom.pl.', 0.9782767878935806], ['noun - m, u - nom.sg.', 0.46980152671755726],
          ['noun - m, u and n, o - dat.sg.', 1.0], ['noun - m, u and n, o - gen.sg.', 1.0],
          ['noun - m, u and o - acc.sg.', 1.0], ['noun - m, u and o - dat.sg.', 1.0],
          ['noun - m, u and o - gen.sg.', 1.0], ['noun - m, u and o - nom.sg.', 1.0],
          ['noun - n (?), o - acc.sg.', 0.24878048780487805], ['noun - n (?), o - dat.sg.', 1.0],
          ['noun - n (?), o - gen.sg.', 1.0], ['noun - n (?), o - nom.sg.', 1.0], ['noun - n - acc.sg.', 1.0],
          ['noun - n - dat.sg.', 1.0], ['noun - n - gen.pl.', 1.0], ['noun - n - gen.sg.', 1.0],
          ['noun - n - nom.du.', 1.0], ['noun - n - nom.pl.', 1.0], ['noun - n - nom.sg.', 0.8776323771557327],
          ['noun - n and m, o - acc.pl.', 1.0], ['noun - n and m, o - acc.pl.neut.', 1.0],
          ['noun - n and m, o - acc.sg.', 1.0], ['noun - n and m, o - dat.pl.', 1.0],
          ['noun - n and m, o - gen.sg.', 0.3620689655172414], ['noun - n and m, o - nom.pl.neut.', 1.0],
          ['noun - n and m, o - nom.sg.', 1.0], ['noun - n and m, u - acc.sg.', 1.0],
          ['noun - n and m, u - dat.du.', 0.16115981119352663], ['noun - n and m, u - dat.sg.', 1.0],
          ['noun - n and m, u - gen.du.', 1.0], ['noun - n and m, u - nom.sg.', 0.06312028582770941],
          ['noun - n and m, u - nom.sg.neut.', 1.0], ['noun - n, i - composition form', 1.0],
          ['noun - n, i - gen.sg.', 0.057368941641938676], ['noun - n, i - nom.sg.', 1.0],
          ['noun - n, i̯o & adjective - dat.pl.', 1.0], ['noun - n, i̯o & adjective - dat.sg.', 1.0],
          ['noun - n, i̯o & adjective - gen.pl.', 1.0], ['noun - n, i̯o & adjective - gen.sg.neut.', 1.0],
          ['noun - n, i̯o & adjective - nom.pl.', 1.0], ['noun - n, i̯o & adjective - nom.sg.', 0.24493827160493828],
          ['noun - n, i̯o & adjective - nom.sg.neut.', 1.0], ['noun - n, i̯o - acc.pl.', 1.0],
          ['noun - n, i̯o - acc.sg.', 0.985304347826087], ['noun - n, i̯o - composition form', 1.0],
          ['noun - n, i̯o - dat.pl.', 1.0], ['noun - n, i̯o - dat.sg.', 0.8421498813157002],
          ['noun - n, i̯o - gen.pl.', 1.0], ['noun - n, i̯o - gen.sg.', 0.8333333333333334],
          ['noun - n, i̯o - nom.pl.', 1.0], ['noun - n, i̯o - nom.sg.', 0.5755801942015013],
          ['noun - n, n - acc.du.', 1.0], ['noun - n, n - acc.pl.', 0.8771836007130125], ['noun - n, n - acc.sg.', 1.0],
          ['noun - n, n - dat.pl.', 0.2601896523041091], ['noun - n, n - dat.sg.', 0.33421313097987465],
          ['noun - n, n - gen.pl.', 0.7166365643186835], ['noun - n, n - gen.sg.', 0.299628079962808],
          ['noun - n, n - nom.pl.', 0.5878428465530022], ['noun - n, n - nom.sg.', 0.16948069241011984],
          ['noun - n, nt - acc.sg.', 1.0], ['noun - n, nt - dat.sg.', 1.0], ['noun - n, o (?) - nom.sg.', 1.0],
          ['noun - n, o (m, o?) - acc.sg.', 0.9678311133450616], ['noun - n, o (m, o?) - dat.sg.', 0.9996740547588006],
          ['noun - n, o (m, o?) - gen.sg.', 0.07278042775811663], ['noun - n, o (m, o?) - nom.pl.', 1.0],
          ['noun - n, o (m, o?) - nom.sg.', 0.8636579572446555], ['noun - n, o - acc.pl.', 0.8433816099696868],
          ['noun - n, o - acc.sg.', 0.7007829852152648], ['noun - n, o - dat.du.', 1.0], ['noun - n, o - dat.pl.', 1.0],
          ['noun - n, o - dat.sg.', 0.46987951807228917], ['noun - n, o - gen.du.', 1.0],
          ['noun - n, o - gen.pl.', 0.8370457209847597], ['noun - n, o - gen.sg.', 0.40292628024760835],
          ['noun - n, o - nom.du.', 1.0], ['noun - n, o - nom.pl.', 1.0], ['noun - n, o - nom.sg.', 0.3494354624354278],
          ['noun - n, o and f, ā - gen.sg.', 1.0], ['noun - n, o and u - gen.sg.', 1.0],
          ['noun - n, o, later m, o - acc.sg.', 0.9990321800145173],
          ['noun - n, o, later m, o - dat.sg.', 0.051921780175320294], ['noun - n, o, later m, o - dat.sg.neut.', 1.0],
          ['noun - n, o, later m, o - gen.sg.', 0.002027712064886786],
          ['noun - n, o, later m, o - nom.sg.', 0.24941841143236956], ['noun - n, s (?) - nom.pl.', 1.0],
          ['noun - n, s - acc.sg.', 1.0], ['noun - n, s - gen.sg.', 1.0], ['noun - n, s - nom.sg.', 1.0],
          ['noun - n, s and n, o - acc./dat.sg.', 0.9344804765056254], ['noun - n, s and n, o - acc.sg.', 1.0],
          ['noun - n, s and n, o - composition form', 0.9453280318091452],
          ['noun - n, s and n, o - dat.sg.', 0.32327490570224093], ['noun - n, s and n, o - gen.du.', 1.0],
          ['noun - n, s and n, o - nom.sg.', 1.0], ['noun - n, t - acc.sg.', 1.0], ['noun - n, u - acc.sg.', 1.0],
          ['noun - n, u - composition form', 1.0], ['noun - n, u - gen.sg.', 0.6198934280639432],
          ['noun - n, u - nom.du.', 1.0], ['noun - n, u - nom.pl.', 1.0], ['noun - n, u - nom.sg.', 0.5129922858302882],
          ['noun - n, u or o - acc.sg.', 1.0], ['noun - n, u or o - adverbial form', 1.0],
          ['noun - n, u or o - dat.sg.', 1.0], ['noun - n, u or o - nom.sg.', 0.07315310105537083],
          ['noun - o (gender uncertain) - dat.sg.', 1.0], ['noun - o (gender uncertain) - gen.sg.', 1.0],
          ['noun - o - acc.sg.', 0.08714334822963217], ['noun - o - composition form', 1.0],
          ['noun - o - dat.sg.', 0.3505263157894737], ['noun - o - gen.sg.', 1.0],
          ['noun - o - nom.sg.', 0.8486293206197855], ['noun - o [n ?] - acc.sg.', 1.0],
          ['noun - o [n ?] - composition form', 1.0], ['noun - o [n ?] - dat.sg.', 1.0],
          ['noun - o [n ?] - nom.sg.', 1.0], ['noun - u (?) - acc.sg.', 1.0], ['noun - u (?) - nom.sg.', 1.0],
          ['noun - uncertain gender - nom.pl.', 1.0], ['noun - uncertain gender - nom.sg.', 1.0],
          ['noun - unknown declension - acc.sg.', 1.0], ['noun - unknown declension - composition form', 1.0],
          ['noun - unknown declension - dat.du.', 1.0], ['noun - unknown declension - dat.sg.', 1.0],
          ['noun - unknown declension - gen.sg.', 1.0], ['noun - unknown declension - nom.du.', 1.0],
          ['noun - unknown declension - nom.pl.', 1.0], ['noun - unknown declension - nom.sg.', 0.7180718383636817],
          ['noun and adjective -  - nom.sg.fem.', 1.0], ['noun and adjective - i - acc.sg.', 0.001984126984126984],
          ['noun and adjective - i - adverbial form', 1.0], ['noun and adjective - i - nom.sg.neut.', 1.0],
          ['noun and adjective - o, ā - comparative', 1.0], ['noun and adjective - o, ā - composition form', 1.0],
          ['noun and adjective - o, ā - nom.pl.', 1.0], ['noun, proper -  - ', 1.0], ['noun, proper -  - acc.sg.', 1.0],
          ['noun, proper -  - dat.sg.', 1.0], ['noun, proper -  - gen.sg.', 0.8670940170940171],
          ['noun, proper -  - nom.sg.', 0.9110784493845306], ['noun, proper -  - voc.sg.', 1.0],
          ['noun, proper - f, i - gen.sg.', 1.0], ['noun, proper - m, i̯o - nom.pl.', 1.0],
          ['noun, proper - m, i̯o - nom.sg.masc.', 1.0], ['number - adjective - acc.du.', 1.0],
          ['number - adjective - acc.du.fem.', 1.0], ['number - adjective - acc.du.masc.', 1.0],
          ['number - adjective - acc.du.neut.', 1.0], ['number - adjective - acc.pl.', 1.0],
          ['number - adjective - acc.pl.neut.', 1.0], ['number - adjective - acc.sg.', 1.0],
          ['number - adjective - acc.sg.fem.', 1.0], ['number - adjective - composition form', 0.27693946387360197],
          ['number - adjective - dat.du.', 0.8944621629457814], ['number - adjective - dat.du.fem.', 1.0],
          ['number - adjective - dat.du.masc.', 0.9899598393574297], ['number - adjective - dat.du.neut.', 1.0],
          ['number - adjective - dat.pl.fem.', 1.0], ['number - adjective - dat.pl.masc.', 1.0],
          ['number - adjective - dat.sg.', 1.0], ['number - adjective - dat.sg.fem', 1.0],
          ['number - adjective - dat.sg.masc.', 1.0], ['number - adjective - gen.du.fem.', 0.15561603166749133],
          ['number - adjective - gen.du.fem. + in 2', 1.0], ['number - adjective - gen.du.masc.', 1.0],
          ['number - adjective - gen.du.neut.', 1.0], ['number - adjective - gen.pl.fem.', 0.9374358974358974],
          ['number - adjective - gen.pl.masc.', 1.0], ['number - adjective - gen.sg.masc.', 1.0],
          ['number - adjective - nom.du.fem.', 0.8062998859749145], ['number - adjective - nom.du.masc.', 1.0],
          ['number - adjective - nom.du.neut.', 1.0], ['number - adjective - nom.pl.', 1.0],
          ['number - adjective - nom.pl.fem.', 0.9879638916750251], ['number - adjective - nom.pl.masc.', 1.0],
          ['number - adjective - nom.pl.neut.', 1.0], ['number - adjective - nom.sg.', 1.0],
          ['number - adjective - nom.sg.masc.', 1.0], ['number - adjective - nom.sg.neut.', 1.0],
          ['number - adjective - uninflected', 1.0], ['particle - asseverative - ', 1.0],
          ['particle - demonstrative relative - ', 1.0], ['particle - interjection - ', 1.0],
          ['particle - interrrogative - ', 0.7580954205786549], ['particle - negative - ', 0.010178641723058466],
          ['particle - negative - ar·cuirethar', 1.0],
          ['particle - negative dependent relative - ', 0.024361060591557383], ['particle - numerical - ', 1.0],
          ['particle - prefix - ', 1.0], ['particle - prefix - *tris-gatā-', 1.0],
          ['particle - prefix - composition form', 0.39907453726863434],
          ['particle - prefix and preverb - *dī-mī-ad-cī-', 1.0],
          ['particle - prefix and preverb - composition form', 0.34173669467787116],
          ['particle - prefix, intensive - ', 1.0], ['particle - prefix, privative - ', 1.0],
          ['particle - prefix, privative - composition form', 0.9723160027008778],
          ['particle - preverb - ', 0.08796259355600594], ['particle - preverb - *ad-cobrā-', 1.0],
          ['particle - preverb - *ad-com-lā', 0.8051422793586596], ['particle - preverb - *ad-con-uss-ding-', 1.0],
          ['particle - preverb - *ad-cori-', 1.0], ['particle - preverb - *ad-cuindmin- (?) very unclear', 1.0],
          ['particle - preverb - *ad-dam-', 1.0],
          ['particle - preverb - *ad-fēd- (perhaps better in-fēd- (cf. Thurneysen p. 520 §842 B 1))', 1.0],
          ['particle - preverb - *ad-glādī-', 1.0], ['particle - preverb - *ad-kwis-', 1.0],
          ['particle - preverb - *ad-ro-slī-', 1.0], ['particle - preverb - *ad-rīmī-', 1.0],
          ['particle - preverb - *ad-sodī-', 1.0], ['particle - preverb - *ad-to-air-ber-', 1.0],
          ['particle - preverb - *ad-to-fo-rindā-', 1.0], ['particle - preverb - *ad-toibī-', 1.0],
          ['particle - preverb - *ad-trebā-', 1.0], ['particle - preverb - *ad-tā- (*bw-)', 0.6698635976129582],
          ['particle - preverb - *ad-āgi-', 1.0], ['particle - preverb - *air-com-dālī-', 1.0],
          ['particle - preverb - *air-fo-laim-', 1.0], ['particle - preverb - *aith-gnin-', 1.0],
          ['particle - preverb - *aith-gon-', 1.0], ['particle - preverb - *ar + comét', 1.0],
          ['particle - preverb - *ar-ber-', 0.6293363499245852], ['particle - preverb - *ar-celā-', 1.0],
          ['particle - preverb - *ar-cori-', 1.0], ['particle - preverb - *ar-crin-', 1.0],
          ['particle - preverb - *ar-de-bina-', 1.0], ['particle - preverb - *ar-fo-ciall-', 1.0],
          ['particle - preverb - *ar-fo-em-', 0.7412881648505772], ['particle - preverb - *ar-gari-', 1.0],
          ['particle - preverb - *ar-guid', 1.0], ['particle - preverb - *ar-icc-', 1.0],
          ['particle - preverb - *ar-lēgā-', 1.0], ['particle - preverb - *ar-sistā-', 1.0],
          ['particle - preverb - *ar-tā- (*ar-bī-)', 1.0], ['particle - preverb - *ar-uss-lēcī-', 1.0],
          ['particle - preverb - *as-gnina-', 0.12506142506142506], ['particle - preverb - *centa-bī-', 1.0],
          ['particle - preverb - *com-(to-)tud- (*com-(to-)cera-)', 1.0], ['particle - preverb - *com-fo-dam', 1.0],
          ['particle - preverb - *com-gabi-', 1.0], ['particle - preverb - *com-imm-clow-', 1.0],
          ['particle - preverb - *com-sodī-', 1.0], ['particle - preverb - *com-to-eter-reth-', 0.997979797979798],
          ['particle - preverb - *com-to-tíag-', 1.0], ['particle - preverb - *com-uss-anā-', 0.9524291497975709],
          ['particle - preverb - *com-uss-scochī-', 0.989612188365651], ['particle - preverb - *con-ar-clow-', 1.0],
          ['particle - preverb - *con-ar-org-', 1.0], ['particle - preverb - *con-delcā-', 1.0],
          ['particle - preverb - *con-en-tēg-', 1.0], ['particle - preverb - *con-icc-', 0.9782406329997673],
          ['particle - preverb - *con-mesc-', 1.0], ['particle - preverb - *con-rig-', 1.0],
          ['particle - preverb - *con-secrā- < Lat. consecrare', 1.0], ['particle - preverb - *con-to-sow-', 1.0],
          ['particle - preverb - *con-uss-ding-', 1.0], ['particle - preverb - *de-ess-rig-', 1.0],
          ['particle - preverb - *de-gnī-', 0.9680708344513013], ['particle - preverb - *do-fo-cori-', 1.0],
          ['particle - preverb - *dē-en-kwis-', 1.0], ['particle - preverb - *dī-donā-', 1.0],
          ['particle - preverb - *dī-en-lā-', 0.43314285714285716], ['particle - preverb - *dī-fo-nig-', 1.0],
          ['particle - preverb - *dī-gabi-', 1.0], ['particle - preverb - *dī-mī-ad-cī-', 1.0],
          ['particle - preverb - *dī-ro-uss-scōchī-', 0.8736013002437957], ['particle - preverb - *dī-slondī-', 1.0],
          ['particle - preverb - *dī-uss-ret-', 1.0], ['particle - preverb - *dī-uss-sech-', 1.0],
          ['particle - preverb - *en-(com-)tā-', 1.0], ['particle - preverb - *es-to-fāscī-', 1.0],
          ['particle - preverb - *ess-balni- (*ad-bath-)', 1.0], ['particle - preverb - *ess-ber-', 0.9441148726548579],
          ['particle - preverb - *ess-com-lu-', 1.0], ['particle - preverb - *ess-gūsī-', 1.0],
          ['particle - preverb - *ess-ind(e)-gabi-', 1.0], ['particle - preverb - *ess-inde-fēd-', 0.9830562659846548],
          ['particle - preverb - *ess-lenā-', 1.0], ['particle - preverb - *ess-org- (*ess-com-org-)', 1.0],
          ['particle - preverb - *ess-rina-', 1.0], ['particle - preverb - *ess-toidī-', 1.0],
          ['particle - preverb - *eter-gabi-', 1.0], ['particle - preverb - *eter-gnin-', 1.0],
          ['particle - preverb - *eter-scarā-', 1.0], ['particle - preverb - *fo-ad-can-', 1.0],
          ['particle - preverb - *fo-ad-logī-', 1.0], ['particle - preverb - *fo-bothā-', 1.0],
          ['particle - preverb - *fo-can-', 1.0], ['particle - preverb - *fo-com-selā-', 1.0],
          ['particle - preverb - *fo-dami-', 1.0], ['particle - preverb - *fo-dālī-', 1.0],
          ['particle - preverb - *fo-ferā-', 1.0], ['particle - preverb - *fo-gnī-', 1.0],
          ['particle - preverb - *fo-luig-', 1.0], ['particle - preverb - *fo-luwā-', 1.0],
          ['particle - preverb - *fo-scochī-', 1.0], ['particle - preverb - *fo-sistī-', 1.0],
          ['particle - preverb - *fo-slig-', 1.0], ['particle - preverb - *fo-sodī-', 1.0],
          ['particle - preverb - *fo-to-imm-di-reth-', 1.0], ['particle - preverb - *fo-uss-anā-', 1.0],
          ['particle - preverb - *for-athi-mani-', 1.0], ['particle - preverb - *for-ber', 1.0],
          ['particle - preverb - *for-cennā-', 0.9996682149966821], ['particle - preverb - *for-com-icc-', 1.0],
          ['particle - preverb - *for-com-ow-', 1.0], ['particle - preverb - *for-con-gari-', 0.9996821360457724],
          ['particle - preverb - *for-de-en-gari-', 0.7954645530603258], ['particle - preverb - *for-fen-', 1.0],
          ['particle - preverb - *for-gellā-', 1.0], ['particle - preverb - *for-tēg- (*for-de-com-wāde-)', 1.0],
          ['particle - preverb - *for-uss-lig- (?)', 1.0], ['particle - preverb - *fo·cerd-', 1.0],
          ['particle - preverb - *fris-to-ber- (*fris-to-ro-ad-dā-)', 1.0], ['particle - preverb - *frith-ber-', 1.0],
          ['particle - preverb - *frith-cori- (*frith-fo-cer-)', 1.0], ['particle - preverb - *frith-gari-', 1.0],
          ['particle - preverb - *frith-gnī-', 1.0], ['particle - preverb - *frith-tēg-', 1.0],
          ['particle - preverb - *frith-āli-', 1.0], ['particle - preverb - *imm-com-arc-', 0.9787556904400607],
          ['particle - preverb - *imm-dī-bina-', 1.0], ['particle - preverb - *imm-fo-longī-', 0.661],
          ['particle - preverb - *imm-imm-gabi-', 0.9974798387096774], ['particle - preverb - *imm-rā-', 1.0],
          ['particle - preverb - *imm-tréni-sagī-', 1.0], ['particle - preverb - *in-com-sech', 0.6398464368551547],
          ['particle - preverb - *in-dlong-', 1.0], ['particle - preverb - *in-dī-con-senī- (?)', 1.0],
          ['particle - preverb - *in-gnin-', 1.0], ['particle - preverb - *in-snad-', 1.0],
          ['particle - preverb - *in-to-in-scanā-', 1.0], ['particle - preverb - *in-togī-', 1.0],
          ['particle - preverb - *inde-ad-ro-uss-ben-', 1.0], ['particle - preverb - *inde-samalī-', 1.0],
          ['particle - preverb - *remi-ess-ber-', 1.0], ['particle - preverb - *remi-sodī-', 1.0],
          ['particle - preverb - *remi-tēg-', 0.9980601357904947], ['particle - preverb - *ro-icc-', 1.0],
          ['particle - preverb - *ro-lam-', 1.0], ['particle - preverb - *ro-sagi-', 1.0],
          ['particle - preverb - *to-ad-fēd-', 0.9116077998528329], ['particle - preverb - *to-ad-selbī-', 1.0],
          ['particle - preverb - *to-air-in-gari-', 1.0], ['particle - preverb - *to-aith-beg-', 1.0],
          ['particle - preverb - *to-aith-cori-', 1.0], ['particle - preverb - *to-ar-(fo-)can-', 1.0],
          ['particle - preverb - *to-ar-ber-', 1.0], ['particle - preverb - *to-ar-decht-', 1.0],
          ['particle - preverb - *to-ari-uss-gabi- (?)', 0.682312925170068],
          ['particle - preverb - *to-athi-mani-', 1.0], ['particle - preverb - *to-ber-', 0.7353149885673737],
          ['particle - preverb - *to-ber- (*to-ro-ad-dā-, *to-ucc-)', 1.0],
          ['particle - preverb - *to-con-sechi-', 0.5202634245187436], ['particle - preverb - *to-cori-', 1.0],
          ['particle - preverb - *to-cori- (*to-ro-lā-)', 1.0],
          ['particle - preverb - *to-de-uss-reg-', 0.6670037074486013], ['particle - preverb - *to-dālī-', 1.0],
          ['particle - preverb - *to-dī-com-wed-', 1.0], ['particle - preverb - *to-dī-fed-', 1.0],
          ['particle - preverb - *to-ellā-', 1.0], ['particle - preverb - *to-ess-ben-', 1.0],
          ['particle - preverb - *to-ess-brenn-', 1.0], ['particle - preverb - *to-fo-bina-', 1.0],
          ['particle - preverb - *to-fo-org- (?)', 1.0], ['particle - preverb - *to-fo-rindā-', 0.9007529463116543],
          ['particle - preverb - *to-fo-uss-lēcī-', 1.0], ['particle - preverb - *to-for-ad-kwis-', 1.0],
          ['particle - preverb - *to-for-ben-', 1.0], ['particle - preverb - *to-for-ess-gabi', 1.0],
          ['particle - preverb - *to-for-mag-', 0.7816854678168547], ['particle - preverb - *to-gaithā-', 1.0],
          ['particle - preverb - *to-iarm-fo-reth-', 0.6276490882207985], ['particle - preverb - *to-icc-', 1.0],
          ['particle - preverb - *to-imm-org-', 1.0], ['particle - preverb - *to-imm-tas- (?)', 1.0],
          ['particle - preverb - *to-in-com-icc-', 0.37687955932708056], ['particle - preverb - *to-in-uss-lā-', 1.0],
          ['particle - preverb - *to-ind-scannā-', 1.0], ['particle - preverb - *to-inde-aneg-', 1.0],
          ['particle - preverb - *to-inde-sow-', 1.0], ['particle - preverb - *to-lin-', 1.0],
          ['particle - preverb - *to-mani-', 1.0], ['particle - preverb - *to-ro-ad-dā-', 1.0],
          ['particle - preverb - *to-sceulī-', 1.0], ['particle - preverb - *to-sow-', 1.0],
          ['particle - preverb - *to-tud- (*to-cer-)', 1.0],
          ['particle - preverb - *to-tēg- (*to-reg-, *to-lud-, *to-di-com-fād-)', 0.999379498634897],
          ['particle - preverb - *to-uss-ber-', 1.0], ['particle - preverb - *to-uss-selī-', 1.0],
          ['particle - preverb - *to-uss-sem-', 0.7998620689655173], ['particle - preverb - *tremi-dī-reg-', 1.0],
          ['particle - preverb - *íarmi-fo-sag-', 1.0], ['particle - preverb - ar·cela', 1.0],
          ['particle - preverb - ar·icc', 1.0], ['particle - preverb - at·baill', 1.0],
          ['particle - preverb - do·ommalgg', 1.0], ['particle - preverb - díxnigidir', 0.7611788617886179],
          ['particle - preverb - díṡruthaigidir', 1.0], ['particle - preverb - ro·finnadar', 1.0],
          ['particle - preverb - sechmo·ella', 1.0], ['particle - preverb - subjunctive ro', 1.0],
          ['particle - preverb - téit (do·coaid)', 1.0], ['particle - relative - ', 1.0],
          ['particle - relative - rel part + a 5', 1.0], ['particle - relative - rel part + ar 1', 1.0],
          ['particle - relative - rel part + co 1', 1.0], ['particle - relative - rel part + de 1', 1.0],
          ['particle - relative - rel part + do 1', 1.0], ['particle - relative - rel part + for 1', 1.0],
          ['particle - relative - rel part + fri', 1.0], ['particle - relative - rel part + i 2', 1.0],
          ['particle - relative - rel part + ro 1', 1.0], ['particle - relative - rel part + tre 1', 1.0],
          ['particle - relative - rel part + ó 1', 1.0], ['particle - relative negative - ', 1.0],
          ['particle - relative negative, with infixed pronouns Class C - ', 1.0], ['particle - vocative - ', 1.0],
          ['particle, emphatic pronominal - 1pl - ', 1.0],
          ['particle, emphatic pronominal - 1sg - ', 0.24316147737299887],
          ['particle, emphatic pronominal - 2pl - ', 1.0], ['particle, emphatic pronominal - 2sg - ', 1.0],
          ['particle, emphatic pronominal - 3pl - ', 0.9033541173941088],
          ['particle, emphatic pronominal - 3sg f - ', 0.8135290616941083],
          ['particle, emphatic pronominal - 3sg m, n - ', 0.04208476226766586],
          ['particle, emphatic pronominal - 3sg m, n - 3sg.masc.', 1.0],
          ['particle, emphatic pronominal - 3sg m, n - masc.', 1.0],
          ['preposition, nominal, with gen - nasalizing - ', 0.20227457351746547],
          ['preposition, with acc -  - acc.', 0.052768510299654126],
          ['preposition, with acc -  - acc. + def.art.sg', 1.0],
          ['preposition, with acc -  - acc. + poss.pron.3pl.', 1.0],
          ['preposition, with acc -  - acc. + poss.pron.3sg.fem.', 1.0],
          ['preposition, with acc -  - acc. + suff.pron.1sg.', 1.0],
          ['preposition, with acc -  - acc. + suff.pron.2sg.', 1.0],
          ['preposition, with acc -  - acc. + suff.pron.3pl.', 0.10076951264199341],
          ['preposition, with acc -  - acc. + suff.pron.3sg.masc./neut.', 1.0],
          ['preposition, with acc -  - eter + suff pron 3sg n', 1.0],
          ['preposition, with acc; and adversative conjunction -  - ', 0.018199411961740297],
          ['preposition, with acc; and adversative conjunction -  - acc.', 1.0],
          ['preposition, with acc; and conjunction -  - ', 0.790580704160951],
          ['preposition, with acc; and conjunction -  - acc.', 0.3624465139692927],
          ['preposition, with acc; geminating -  - ', 1.0],
          ['preposition, with acc; geminating -  - acc.', 0.013757227028742531],
          ['preposition, with acc; geminating -  - acc. + def.art.pl.', 1.0],
          ['preposition, with acc; geminating -  - acc. + def.art.pl. + í 1', 1.0],
          ['preposition, with acc; geminating -  - acc. + def.art.sg', 1.0],
          ['preposition, with acc; geminating -  - acc. + def.art.sg. + í 1', 1.0],
          ['preposition, with acc; geminating -  - acc. + poss.pron.3pl.', 1.0],
          ['preposition, with acc; geminating -  - acc. + poss.pron.3sg.fem.', 1.0],
          ['preposition, with acc; geminating -  - acc. + poss.pron.3sg.masc./neut.', 1.0],
          ['preposition, with acc; geminating -  - acc. + rel.part.', 1.0],
          ['preposition, with acc; geminating -  - acc. + so 1', 1.0],
          ['preposition, with acc; geminating -  - acc. + suff.pron.1pl.', 0.013443246670894103],
          ['preposition, with acc; geminating -  - acc. + suff.pron.1sg.', 0.22425176056338028],
          ['preposition, with acc; geminating -  - acc. + suff.pron.2sg.', 0.11523830834638622],
          ['preposition, with acc; geminating -  - acc. + suff.pron.3pl.', 0.040658499234303216],
          ['preposition, with acc; geminating -  - acc. + suff.pron.3sg.fem.', 0.271135567783892],
          ['preposition, with acc; geminating -  - acc. + suff.pron.3sg.masc./neut.', 0.11208638909741872],
          ['preposition, with acc; leniting -  - acc.', 0.030329495831679237],
          ['preposition, with acc; leniting -  - acc. + def.art.sg', 1.0],
          ['preposition, with acc; leniting -  - acc. + poss.pron.3pl.', 1.0],
          ['preposition, with acc; leniting -  - acc. + poss.pron.3sg.masc./neut.', 1.0],
          ['preposition, with acc; leniting -  - acc. + rel.part.', 1.0],
          ['preposition, with acc; leniting -  - acc. + suff.pron.3pl.', 0.046153846153846156],
          ['preposition, with acc; leniting -  - acc. + suff.pron.3sg.fem.', 1.0],
          ['preposition, with acc; leniting -  - acc. + suff.pron.3sg.masc./neut.', 0.12049585040445425],
          ['preposition, with acc; leniting -  - adverbial form', 1.0],
          ['preposition, with acc; leniting -  - composition form', 1.0],
          ['preposition, with acc; leniting; and conjunction -  - acc.', 1.0],
          ['preposition, with acc; leniting; and conjunction -  - acc. + suff.pron.3sg.masc./neut.',
           0.19194943446440452],
          ['preposition, with dat -  - dat.', 0.2940201302545885],
          ['preposition, with dat -  - dat. + def.art.pl.', 1.0],
          ['preposition, with dat -  - dat. + def.art.sg.', 1.0],
          ['preposition, with dat -  - dat. + poss.pron.3pl.', 1.0],
          ['preposition, with dat -  - dat. + poss.pron.3sg.', 1.0],
          ['preposition, with dat -  - dat. + poss.pron.3sg.masc./neut.', 1.0],
          ['preposition, with dat -  - dat. + suff.pron.3sg.fem.', 1.0],
          ['preposition, with dat -  - dat. + suff.pron.3sg.masc./neut.', 0.5095477386934674],
          ['preposition, with dat and acc; leniting -  - acc.', 0.5134972052845529],
          ['preposition, with dat and acc; leniting -  - acc. + def.art.pl.', 1.0],
          ['preposition, with dat and acc; leniting -  - acc. + def.art.sg', 1.0],
          ['preposition, with dat and acc; leniting -  - acc. + poss.pron.3pl.', 1.0],
          ['preposition, with dat and acc; leniting -  - acc. + poss.pron.3sg.masc./neut.', 1.0],
          ['preposition, with dat and acc; leniting -  - acc. + rel.part.', 1.0],
          ['preposition, with dat and acc; leniting -  - acc. + suff.pron.3pl.', 0.6000828843762951],
          ['preposition, with dat and acc; leniting -  - acc. + suff.pron.3sg.masc./neut.', 0.06413900788725628],
          ['preposition, with dat and acc; leniting -  - acc./dat.', 1.0],
          ['preposition, with dat and acc; leniting -  - acc./dat. + rel.part.', 1.0],
          ['preposition, with dat and acc; leniting -  - dat (?) + poss.pron.3sg.masc./neut.', 1.0],
          ['preposition, with dat and acc; leniting -  - dat.', 0.6530298441395056],
          ['preposition, with dat and acc; leniting -  - dat. (?)', 1.0],
          ['preposition, with dat and acc; leniting -  - dat. + def.art.pl.', 1.0],
          ['preposition, with dat and acc; leniting -  - dat. + def.art.sg.', 1.0],
          ['preposition, with dat and acc; leniting -  - dat. + poss.pron.3pl.', 1.0],
          ['preposition, with dat and acc; leniting -  - dat. + poss.pron.3sg.masc./neut.', 1.0],
          ['preposition, with dat and acc; leniting -  - dat. + rel.part.', 1.0],
          ['preposition, with dat and acc; leniting -  - dat. + suff.pron.3pl.', 0.12337337337337337],
          ['preposition, with dat and acc; leniting -  - dat. + suff.pron.3sg.masc./neut.', 1.0],
          ['preposition, with dat and acc; leniting -  - dat.sg.', 1.0],
          ['preposition, with dat and acc; nasalizing -  - acc.', 1.0],
          ['preposition, with dat and acc; nasalizing -  - acc. + def.art.pl.', 1.0],
          ['preposition, with dat and acc; nasalizing -  - acc. + def.art.sg', 1.0],
          ['preposition, with dat and acc; nasalizing -  - acc. + poss.pron.3sg.masc./neut.', 1.0],
          ['preposition, with dat and acc; nasalizing -  - acc. + rel.part.', 1.0],
          ['preposition, with dat and acc; nasalizing -  - acc. + suff.pron.3pl.', 1.0],
          ['preposition, with dat and acc; nasalizing -  - acc. + suff.pron.3sg.masc./neut.', 1.0],
          ['preposition, with dat and acc; nasalizing -  - acc./dat.', 1.0],
          ['preposition, with dat and acc; nasalizing -  - acc.sg.', 1.0],
          ['preposition, with dat and acc; nasalizing -  - dat.', 0.24134578833558712],
          ['preposition, with dat and acc; nasalizing -  - dat. + def.art.pl.', 1.0],
          ['preposition, with dat and acc; nasalizing -  - dat. + def.art.sg.', 1.0],
          ['preposition, with dat and acc; nasalizing -  - dat. + def.art.sg. + í 1', 1.0],
          ['preposition, with dat and acc; nasalizing -  - dat. + poss.pron.2sg.', 1.0],
          ['preposition, with dat and acc; nasalizing -  - dat. + poss.pron.3pl.', 1.0],
          ['preposition, with dat and acc; nasalizing -  - dat. + poss.pron.3sg.masc./neut.', 1.0],
          ['preposition, with dat and acc; nasalizing -  - dat. + rel.part.', 1.0],
          ['preposition, with dat and acc; nasalizing -  - dat. + suff.pron.3pl.', 0.024850797377947362],
          ['preposition, with dat and acc; nasalizing -  - dat. + suff.pron.3sg.fem.', 0.11688634667993036],
          ['preposition, with dat and acc; nasalizing -  - dat. + suff.pron.3sg.masc./neut.', 0.024617188072386255],
          ['preposition, with dat and acc; nasalizing -  - dat.pl.', 1.0],
          ['preposition, with dat and acc; nasalizing -  - dat.sg.', 1.0],
          ['preposition, with dat and acc; nasalizing -  - i 2 + poss.pron.3sg.fem.', 1.0],
          ['preposition, with dat; geminating -  - dat.', 1.0],
          ['preposition, with dat; geminating -  - dat. + def.art.sg.', 1.0],
          ['preposition, with dat; geminating -  - dat. + poss.pron.3pl.', 1.0],
          ['preposition, with dat; geminating -  - dat. + rel.part.', 1.0],
          ['preposition, with dat; geminating -  - dat. + suff.pron.3pl.', 1.0],
          ['preposition, with dat; geminating -  - dat. + suff.pron.3sg.fem.', 1.0],
          ['preposition, with dat; geminating -  - dat. + suff.pron.3sg.masc./neut.', 0.7256836763462081],
          ['preposition, with dat; leniting -  - composition form', 1.0],
          ['preposition, with dat; leniting -  - dat.', 0.051338855209728786],
          ['preposition, with dat; leniting -  - dat. + alaile', 1.0],
          ['preposition, with dat; leniting -  - dat. + def.art.pl.', 1.0],
          ['preposition, with dat; leniting -  - dat. + def.art.sg.', 0.8905247634263243],
          ['preposition, with dat; leniting -  - dat. + def.art.sg. + í 1', 1.0],
          ['preposition, with dat; leniting -  - dat. + poss.pron.3pl.', 1.0],
          ['preposition, with dat; leniting -  - dat. + poss.pron.3sg', 1.0],
          ['preposition, with dat; leniting -  - dat. + poss.pron.3sg.fem.', 1.0],
          ['preposition, with dat; leniting -  - dat. + poss.pron.3sg.masc./neut.', 1.0],
          ['preposition, with dat; leniting -  - dat. + rel.part.', 1.0],
          ['preposition, with dat; leniting -  - dat. + suff.pron.1pl.', 0.22102747909199522],
          ['preposition, with dat; leniting -  - dat. + suff.pron.2pl.', 1.0],
          ['preposition, with dat; leniting -  - dat. + suff.pron.2sg.', 0.2859598853868195],
          ['preposition, with dat; leniting -  - dat. + suff.pron.3pl.', 0.1504433546341705],
          ['preposition, with dat; leniting -  - dat. + suff.pron.3sg.fem.', 1.0],
          ['preposition, with dat; leniting -  - dat. + suff.pron.3sg.fem. + -si 1', 1.0],
          ['preposition, with dat; leniting -  - dat. + suff.pron.3sg.masc./neut.', 0.5357432275989813],
          ['preposition, with dat; leniting -  - dat.du.', 1.0], ['preposition, with dat; leniting -  - dat.pl.', 1.0],
          ['preposition, with dat; leniting -  - dat.sg.', 1.0],
          ['preposition, with dat; nasalizing -  - composition form', 1.0],
          ['preposition, with dat; nasalizing -  - dat.', 0.3384102234367465],
          ['preposition, with dat; nasalizing -  - dat. + def.art.sg.', 1.0],
          ['preposition, with dat; nasalizing -  - dat. + poss.pron.3pl.', 1.0],
          ['preposition, with dat; nasalizing -  - dat. + poss.pron.3sg.masc./neut.', 1.0],
          ['preposition, with dat; nasalizing -  - dat. + suff.pron.3pl.', 1.0],
          ['preposition, with dat; nasalizing -  - dat. + suff.pron.3sg.fem.', 0.09084836339345358],
          ['preposition, with gen; and conjunction -  - ', 0.3814363143631436],
          ['preposition, with gen; and conjunction -  - gen.', 1.0],
          ['pronoun - interrogative - ', 0.052576235541535225], ['pronoun - negative interrogative - ', 1.0],
          ['pronoun, anaphoric - enclitic - ', 0.6651430506179109],
          ['pronoun, anaphoric - enclitic - acc.pl.fem.', 1.0], ['pronoun, anaphoric - enclitic - acc.sg.', 1.0],
          ['pronoun, anaphoric - enclitic - acc.sg.fem.', 1.0], ['pronoun, anaphoric - enclitic - dat.pl.fem.', 1.0],
          ['pronoun, anaphoric - enclitic - dat.sg.fem', 1.0], ['pronoun, anaphoric - enclitic - gen.sg.', 1.0],
          ['pronoun, anaphoric - enclitic - gen.sg.fem.', 1.0], ['pronoun, anaphoric - enclitic - gen.sg.neut.', 1.0],
          ['pronoun, anaphoric - enclitic - nom.pl.', 0.04131683605832965],
          ['pronoun, anaphoric - enclitic - nom.pl.fem.', 1.0], ['pronoun, anaphoric - enclitic - nom.pl.masc.', 1.0],
          ['pronoun, anaphoric - enclitic - nom.sg.', 1.0],
          ['pronoun, anaphoric - enclitic - nom.sg.fem.', 0.4098169068952084],
          ['pronoun, anaphoric - enclitic - nom.sg.masc.', 1.0],
          ['pronoun, anaphoric - neuter, stressed - acc.sg.', 0.022571071540143706],
          ['pronoun, anaphoric - neuter, stressed - dat.sg.', 0.9989858012170385],
          ['pronoun, anaphoric - stressed - acc.sg.fem.', 0.04136504653567735],
          ['pronoun, anaphoric - stressed - acc.sg.masc.', 0.5019723865877712],
          ['pronoun, anaphoric - stressed - dat.pl.', 0.008241758241758242],
          ['pronoun, anaphoric - stressed - dat.sg.fem.', 1.0], ['pronoun, anaphoric - stressed - dat.sg.masc.', 1.0],
          ['pronoun, anaphoric - stressed - dat.sg.neut.', 0.03357004519044545],
          ['pronoun, demonstrative - neuter, indeclinable - ', 0.20480961923847696],
          ['pronoun, demonstrative - that, those - acc.sg.fem.', 1.0],
          ['pronoun, demonstrative - that, those - acc.sg.masc.', 1.0],
          ['pronoun, demonstrative - that, those - acc.sg.neut.', 1.0],
          ['pronoun, demonstrative - that, those - dat.sg.neut.', 1.0],
          ['pronoun, demonstrative - that, those - nom.pl.', 1.0],
          ['pronoun, demonstrative - that, those - nom.pl.masc.', 1.0],
          ['pronoun, demonstrative - that, those - nom.sg.', 1.0],
          ['pronoun, demonstrative - that, those - nom.sg.fem.', 1.0],
          ['pronoun, demonstrative - that, those - nom.sg.masc.', 1.0],
          ['pronoun, demonstrative - that, those - nom.sg.neut.', 1.0], ['pronoun, indeclinable  -  - ', 1.0],
          ['pronoun, indeclinable  -  - acc.sg.', 0.9639215686274509],
          ['pronoun, indeclinable  -  - acc.sg.neut.', 1.0],
          ['pronoun, indeclinable  -  - dat.sg.', 0.7672456575682383], ['pronoun, indeclinable  -  - gen.sg.', 1.0],
          ['pronoun, indeclinable  -  - nom.sg.', 0.8269373607328546],
          ['pronoun, indeclinable, accented, deictic -  - ', 1.0],
          ['pronoun, indeclinable, accented, deictic -  - acc.pl.', 1.0],
          ['pronoun, indeclinable, accented, deictic -  - acc.pl.masc.', 1.0],
          ['pronoun, indeclinable, accented, deictic -  - acc.pl.neut.', 1.0],
          ['pronoun, indeclinable, accented, deictic -  - acc.sg.', 1.0],
          ['pronoun, indeclinable, accented, deictic -  - acc.sg.fem.', 1.0],
          ['pronoun, indeclinable, accented, deictic -  - acc.sg.masc.', 1.0],
          ['pronoun, indeclinable, accented, deictic -  - acc.sg.neut.', 1.0],
          ['pronoun, indeclinable, accented, deictic -  - dat.pl.', 1.0],
          ['pronoun, indeclinable, accented, deictic -  - dat.pl.masc.', 1.0],
          ['pronoun, indeclinable, accented, deictic -  - dat.pl.neut.', 1.0],
          ['pronoun, indeclinable, accented, deictic -  - dat.sg.', 1.0],
          ['pronoun, indeclinable, accented, deictic -  - dat.sg.fem', 1.0],
          ['pronoun, indeclinable, accented, deictic -  - dat.sg.masc.', 1.0],
          ['pronoun, indeclinable, accented, deictic -  - dat.sg.neut.', 0.10590163934426229],
          ['pronoun, indeclinable, accented, deictic -  - gen.pl.masc.', 1.0],
          ['pronoun, indeclinable, accented, deictic -  - gen.pl.neut.', 1.0],
          ['pronoun, indeclinable, accented, deictic -  - gen.sg.', 1.0],
          ['pronoun, indeclinable, accented, deictic -  - gen.sg.masc.', 1.0],
          ['pronoun, indeclinable, accented, deictic -  - gen.sg.neut.', 1.0],
          ['pronoun, indeclinable, accented, deictic -  - nom.pl.', 1.0],
          ['pronoun, indeclinable, accented, deictic -  - nom.pl.masc.', 1.0],
          ['pronoun, indeclinable, accented, deictic -  - nom.pl.neut.', 1.0],
          ['pronoun, indeclinable, accented, deictic -  - nom.sg.', 1.0],
          ['pronoun, indeclinable, accented, deictic -  - nom.sg.fem.', 1.0],
          ['pronoun, indeclinable, accented, deictic -  - nom.sg.masc.', 1.0],
          ['pronoun, indeclinable, accented, deictic -  - nom.sg.neut.', 0.10173781002193352],
          ['pronoun, indefinite -  - acc.sg.', 1.0], ['pronoun, indefinite - m - acc.sg.', 1.0],
          ['pronoun, indefinite - m - dat.sg.', 0.005422993492407809], ['pronoun, infixed, class A - 1pl - ', 1.0],
          ['pronoun, infixed, class A - 1sg - ', 0.0152], ['pronoun, infixed, class A - 2sg - ', 1.0],
          ['pronoun, infixed, class A - 3pl - ', 0.30683269476372926],
          ['pronoun, infixed, class A - 3sg f (sometimes nasalizing) - ', 1.0],
          ['pronoun, infixed, class A - 3sg m - ', 1.0], ['pronoun, infixed, class A - 3sg n (leniting) - ', 1.0],
          ['pronoun, infixed, class B - 1sg - ', 1.0], ['pronoun, infixed, class B - 3pl - ', 1.0],
          ['pronoun, infixed, class B - 3sg f (geminating) - ', 1.0],
          ['pronoun, infixed, class B - 3sg n (leniting) - ', 0.9964580873671782],
          ['pronoun, infixed, class C - 1pl - ', 1.0],
          ['pronoun, infixed, class C - 3pl (geminating) - ', 0.9889322916666666],
          ['pronoun, infixed, class C - 3sg f (geminating) - ', 1.0], ['pronoun, infixed, class C - 3sg m - ', 1.0],
          ['pronoun, infixed, class C - 3sg n (leniting) - ', 0.7845572807385648],
          ['pronoun, interrogative and indefinite -  - ', 0.7268733072524827],
          ['pronoun, non-neuter -  - acc.sg.', 0.5349753694581281], ['pronoun, non-neuter -  - dat.sg.', 1.0],
          ['pronoun, non-neuter -  - nom.sg.', 1.0], ['pronoun, personal - 1sg - ', 1.0],
          ['pronoun, personal - 2sg - ', 0.04281345565749235], ['pronoun, personal - 2sg - voc.sg.', 1.0],
          ['pronoun, personal - 3pl - ', 0.40944803580308303], ['pronoun, personal - 3sg f - ', 0.05363838090136965],
          ['pronoun, personal - 3sg m - ', 0.6604879088100565], ['pronoun, personal - 3sg n - ', 0.06374775536072673],
          ['pronoun, personal - 3sg n - composition form', 1.0],
          ['pronoun, personal - 3sg n - formal pred, immediately after copula', 1.0],
          ['pronoun, possessive, stressed - 3sg and pl - pl.', 0.27431806484817295],
          ['pronoun, possessive, stressed - 3sg and pl - sg.', 0.4206033010813887],
          ['pronoun, possessive, unstressed - 1pl (nasalizing) - ', 1.0],
          ['pronoun, possessive, unstressed - 1sg (leniting) - ', 0.07982021078735275],
          ['pronoun, possessive, unstressed - 2sg - ', 1.0],
          ['pronoun, possessive, unstressed - 3pl (nasalizing) - ', 1.0],
          ['pronoun, possessive, unstressed - 3sg f - ', 1.0],
          ['pronoun, possessive, unstressed - 3sg m, n (leniting) - ', 0.818394342023496],
          ['pronoun, possessive, unstressed - 3sg m, n (leniting) - 3sg.neut.', 1.0],
          ['pronoun, possessive, unstressed - 3sg m, n (leniting) - neut.', 1.0],
          ['pronoun, reflexive -  - ', 0.7561303325495465], ['pronoun, reflexive -  - 1sg.', 1.0],
          ['pronoun, reflexive -  - 2sg.', 1.0], ['pronoun, reflexive -  - 3pl.', 1.0],
          ['pronoun, reflexive -  - 3sg.', 0.9967145790554415], ['pronoun, reflexive -  - 3sg.fem.', 0.985836627140975],
          ['pronoun, reflexive -  - 3sg.masc.', 1.0], ['pronoun, reflexive -  - 3sg.neut.', 0.23601667032243914],
          ['pronoun, suffixed - 3sg m, n - ', 1.0], ['see amail -  - ', 0.9710884353741497], ['unclear -  - ', 1.0],
          ['verb -  - 3sg.pres.ind.pass.', 1.0], ['verb - AI - 1sg.perf.', 1.0],
          ['verb - AI - 1sg.perf. + infix pron Class C 3sg.neut.', 1.0], ['verb - AI - 1sg.pres.ind.', 1.0],
          ['verb - AI - 1sg.pres.subj.', 1.0], ['verb - AI - 1sg.pret.', 1.0], ['verb - AI - 2sg.impv.', 1.0],
          ['verb - AI - 2sg.pres.ind.', 1.0], ['verb - AI - 3pl.imperf. + infix.pron. Class A 3sg.neut.', 1.0],
          ['verb - AI - 3pl.imperf.pass.', 1.0], ['verb - AI - 3pl.perf.', 1.0],
          ['verb - AI - 3pl.pres.ind.', 0.6096725360529042],
          ['verb - AI - 3pl.pres.ind. + infix.pron. Class C 3sg.masc.', 1.0],
          ['verb - AI - 3pl.pres.ind. + infix.pron. Class C 3sg.neut.', 1.0],
          ['verb - AI - 3pl.pres.ind.pass.', 0.8710336374778701], ['verb - AI - 3pl.pres.ind.pass.rel.', 1.0],
          ['verb - AI - 3pl.pres.ind.rel.', 1.0], ['verb - AI - 3pl.pres.subj.', 1.0],
          ['verb - AI - 3pl.pres.subj.pass.', 1.0], ['verb - AI - 3pl.sec.fut.pass.', 1.0],
          ['verb - AI - 3sg.imperf.subj.pass.', 1.0], ['verb - AI - 3sg.pass.perf.', 1.0],
          ['verb - AI - 3sg.past.subj.', 1.0], ['verb - AI - 3sg.perf.', 0.7853223593964335],
          ['verb - AI - 3sg.pres.ind.', 0.4053470768239652],
          ['verb - AI - 3sg.pres.ind. + inf.pron. class A 1sg.', 1.0],
          ['verb - AI - 3sg.pres.ind. + inf.pron. class A 3sg.neut.', 1.0],
          ['verb - AI - 3sg.pres.ind. + infix.pron. Class C 3pl.', 1.0],
          ['verb - AI - 3sg.pres.ind. + infix.pron. Class C 3sg.fem.', 0.03680981595092025],
          ['verb - AI - 3sg.pres.ind. + infix.pron. Class C 3sg.neut.', 1.0],
          ['verb - AI - 3sg.pres.ind.pass.', 0.6449487554904831],
          ['verb - AI - 3sg.pres.ind.pass. + inf.pron. Class A 1sg.', 1.0],
          ['verb - AI - 3sg.pres.ind.pass. + infix.pron. class A 1sg.', 1.0],
          ['verb - AI - 3sg.pres.ind.pass.rel.', 1.0], ['verb - AI - 3sg.pres.ind.rel.', 0.45377906976744187],
          ['verb - AI - 3sg.pres.ind.rel. + petr.i.nfix.pron.', 1.0], ['verb - AI - 3sg.pres.pass.rel.', 1.0],
          ['verb - AI - 3sg.pres.subj.', 1.0], ['verb - AI - 3sg.pres.subj. + infix.pron. Class A 1sg.', 1.0],
          ['verb - AI - 3sg.pres.subj.pass.', 1.0], ['verb - AI - 3sg.pret.pass.', 1.0],
          ['verb - AI - perf 3pl.perf.rel.', 1.0], ['verb - AII (?) - 1sg.pres.ind.', 1.0],
          ['verb - AII - 1pl.pres.ind.rel.', 1.0], ['verb - AII - 1pl.pret.', 1.0], ['verb - AII - 1sg.pres.ind.', 1.0],
          ['verb - AII - 1sg.pres.ind. + infix.pron. Class A 3pl.', 1.0], ['verb - AII - 1sg.pret.', 1.0],
          ['verb - AII - 2sg.impv.', 1.0], ['verb - AII - 2sg.pres.ind.', 1.0], ['verb - AII - 3pl.fut.pass.', 1.0],
          ['verb - AII - 3pl.imperf.', 1.0], ['verb - AII - 3pl.imperf. + infix.pron. Class C 3pl.', 1.0],
          ['verb - AII - 3pl.perf.', 1.0], ['verb - AII - 3pl.perf. + infix.pron. Class B 3pl.', 1.0],
          ['verb - AII - 3pl.perf.pass.', 1.0], ['verb - AII - 3pl.pres.ind.', 0.8562999619337648],
          ['verb - AII - 3pl.pres.ind. + infix.pron. Class A 3sg.neut.', 1.0],
          ['verb - AII - 3pl.pres.ind. + infix.pron. Class C 3pl.', 1.0],
          ['verb - AII - 3pl.pres.ind. + infix.pron. Class C 3sg.fem.', 1.0], ['verb - AII - 3pl.pres.ind.pass.', 1.0],
          ['verb - AII - 3pl.pres.ind.pass. + infix.pron. class C 3sg.neut.', 1.0],
          ['verb - AII - 3pl.pres.ind.pass.rel.', 1.0], ['verb - AII - 3pl.pres.ind.rel.', 0.6972363748649066],
          ['verb - AII - 3pl.pres.subj.', 1.0], ['verb - AII - 3pl.pres.subj.pass.', 1.0],
          ['verb - AII - 3pl.pret.pass.', 1.0], ['verb - AII - 3sg.fut.pass.', 1.0],
          ['verb - AII - 3sg.imperf.pass.', 1.0], ['verb - AII - 3sg.imperf.subj.pass.', 1.0],
          ['verb - AII - 3sg.pass.perf.', 0.37452948557089083], ['verb - AII - 3sg.past.subj.', 1.0],
          ['verb - AII - 3sg.perf.', 1.0], ['verb - AII - 3sg.pres.ind.', 0.651909307875895],
          ['verb - AII - 3sg.pres.ind. + inf.pron. class A 1sg.', 1.0],
          ['verb - AII - 3sg.pres.ind. + inf.pron. class A 3sg.fem.', 1.0],
          ['verb - AII - 3sg.pres.ind. + infix.pron. Class B 3pl.', 1.0],
          ['verb - AII - 3sg.pres.ind. + infix.pron. Class B 3sg.neut.', 1.0],
          ['verb - AII - 3sg.pres.ind. + infix.pron. Class C 3sg.fem.', 1.0],
          ['verb - AII - 3sg.pres.ind. + infix.pron. Class C 3sg.neut.', 1.0],
          ['verb - AII - 3sg.pres.ind. + suff.pron. 3sg.masc./neut.', 1.0],
          ['verb - AII - 3sg.pres.ind.pass.', 0.7908317929759704],
          ['verb - AII - 3sg.pres.ind.pass. + infix.pron. class A 1sg.', 1.0],
          ['verb - AII - 3sg.pres.ind.pass.rel.', 1.0], ['verb - AII - 3sg.pres.ind.rel.', 0.9633350075339026],
          ['verb - AII - 3sg.pres.pass.rel.', 1.0], ['verb - AII - 3sg.pres.subj.', 1.0],
          ['verb - AII - 3sg.pres.subj.pass.', 1.0], ['verb - AII - 3sg.pres.subj.rel.', 0.9966199903428296],
          ['verb - AII - 3sg.pret.', 1.0], ['verb - AII - 3sg.pret.pass.', 1.0],
          ['verb - AIII - 1pl.imperf.subj.', 1.0], ['verb - AIII - 1pl.past.subj.', 1.0],
          ['verb - AIII - 1pl.pres.ind.', 1.0], ['verb - AIII - 1pl.pres.subj.', 1.0],
          ['verb - AIII - 1sg.pres.ind.', 1.0], ['verb - AIII - 2sg.fut.', 1.0], ['verb - AIII - 2sg.perf.', 1.0],
          ['verb - AIII - 2sg.pres.ind.', 1.0], ['verb - AIII - 3pl.cond.', 1.0],
          ['verb - AIII - 3pl.imperf. + infix.pron. Class A 3sg.neut.', 1.0],
          ['verb - AIII - 3pl.imperf. + infix.pron. Class C 3sg.neut.', 1.0], ['verb - AIII - 3pl.past.subj.', 1.0],
          ['verb - AIII - 3pl.perf.', 1.0], ['verb - AIII - 3pl.perf. + infix.pron. Class A 3sg.neut.', 1.0],
          ['verb - AIII - 3pl.perf.pass.', 1.0], ['verb - AIII - 3pl.pres.ind.', 0.7860199714693296],
          ['verb - AIII - 3pl.pres.ind.pass.', 1.0], ['verb - AIII - 3pl.pres.ind.rel.', 0.05454545454545454],
          ['verb - AIII - 3pl.pret.pass.', 1.0], ['verb - AIII - 3sg.fut.', 1.0], ['verb - AIII - 3sg.fut.pass.', 1.0],
          ['verb - AIII - 3sg.imperf.pass.', 1.0], ['verb - AIII - 3sg.imperf.subj.pass.', 1.0],
          ['verb - AIII - 3sg.pass.perf.', 1.0], ['verb - AIII - 3sg.past.subj.', 1.0],
          ['verb - AIII - 3sg.perf.', 0.6243407707910751],
          ['verb - AIII - 3sg.perf. + infix.pron. Class A 3sg.neut.', 1.0],
          ['verb - AIII - 3sg.pres.ind.', 0.4516404830608101],
          ['verb - AIII - 3sg.pres.ind. + inf.pron. class A 1sg.', 1.0],
          ['verb - AIII - 3sg.pres.ind. + inf.pron. class A 3sg.neut.', 1.0],
          ['verb - AIII - 3sg.pres.ind. + infix.pron. Class B 3sg.neut.', 1.0],
          ['verb - AIII - 3sg.pres.ind. + infix.pron. Class C 3sg.fem.', 1.0],
          ['verb - AIII - 3sg.pres.ind.pass.', 0.7838623156012516],
          ['verb - AIII - 3sg.pres.ind.pass. + infix pron Class B 1sg', 1.0],
          ['verb - AIII - 3sg.pres.ind.pass. + infix.pron. Class B 1sg.', 1.0],
          ['verb - AIII - 3sg.pres.ind.pass.rel.', 0.032], ['verb - AIII - 3sg.pres.ind.rel.', 1.0],
          ['verb - AIII - 3sg.pres.ind.rel. + inf.pron. class C 3sg.', 1.0], ['verb - AIII - 3sg.pres.subj.', 1.0],
          ['verb - AIII - 3sg.pret.', 1.0], ['verb - AIII - 3sg.sec.fut.pass.', 1.0],
          ['verb - BI (?) - 1sg.pres.ind.', 0.05476864966949953], ['verb - BI - *to-in-com-icc-', 1.0],
          ['verb - BI - 1pl.fut.', 1.0], ['verb - BI - 1pl.fut. + infix.pron. Class B 3sg.neut.', 1.0],
          ['verb - BI - 1pl.perf.', 1.0], ['verb - BI - 1pl.perf. + infix.pron. Class C 3sg.masc.', 1.0],
          ['verb - BI - 1pl.pres.ind.', 1.0], ['verb - BI - 1pl.pres.ind. + infix.pron. Class C 3sg.neut.', 1.0],
          ['verb - BI - 1sg.fut.', 1.0], ['verb - BI - 1sg.past.subj.', 1.0], ['verb - BI - 1sg.perf.', 1.0],
          ['verb - BI - 1sg.perf. + infix pron Class C 3sg.neut.', 0.05483207676490747],
          ['verb - BI - 1sg.pres.ind.', 0.7178803451953845],
          ['verb - BI - 1sg.pres.ind. + infix pron Class A 3sg.neut.', 0.25],
          ['verb - BI - 1sg.pres.ind. + infix pron Class C 3sg.neut.', 0.36276522929500343],
          ['verb - BI - 1sg.pres.ind. + infix.pron. Class A 2sg.', 1.0],
          ['verb - BI - 1sg.pres.ind. + infix.pron. Class A 3pl.', 1.0],
          ['verb - BI - 1sg.pres.ind. + infix.pron. Class A 3sg.fem.', 1.0],
          ['verb - BI - 1sg.pres.ind. + infix.pron. Class A 3sg.masc.', 1.0], ['verb - BI - 1sg.pret.', 1.0],
          ['verb - BI - 2sg.fut.', 1.0], ['verb - BI - 2sg.imperf.subj.', 1.0], ['verb - BI - 2sg.pres.ind.', 1.0],
          ['verb - BI - 2sg.pres.ind. + infix.pron. class C 3sg.neut.', 1.0],
          ['verb - BI - 2sg.pres.subj.', 0.6730831973898858], ['verb - BI - 3pl.imperf.', 1.0],
          ['verb - BI - 3pl.imperf.subj.pass.', 1.0], ['verb - BI - 3pl.past.subj.', 1.0],
          ['verb - BI - 3pl.perf.', 1.0], ['verb - BI - 3pl.pres.ind.', 0.6383793465505527],
          ['verb - BI - 3pl.pres.ind. + infix.pron. Class A 3sg.masc.', 1.0],
          ['verb - BI - 3pl.pres.ind. + infix.pron. Class B 3sg.neut.', 1.0],
          ['verb - BI - 3pl.pres.ind. + infix.pron. Class C 3pl.', 1.0],
          ['verb - BI - 3pl.pres.ind.pass.', 0.9927680347134333], ['verb - BI - 3pl.pres.ind.pass.rel.', 1.0],
          ['verb - BI - 3pl.pres.ind.rel.', 0.24923391215526047], ['verb - BI - 3pl.pres.subj.', 1.0],
          ['verb - BI - 3pl.pres.subj.pass.', 0.5187817258883248], ['verb - BI - 3sg.fut.', 1.0],
          ['verb - BI - 3sg.imperf.', 1.0], ['verb - BI - 3sg.imperf.subj.', 1.0],
          ['verb - BI - 3sg.imperf.subj.pass.', 1.0], ['verb - BI - 3sg.imperf.subj.pass. (perfective)', 1.0],
          ['verb - BI - 3sg.pass.perf.', 0.8106069971566324], ['verb - BI - 3sg.past.subj.', 1.0],
          ['verb - BI - 3sg.perf.', 0.5770486581189774], ['verb - BI - 3sg.perf. + infix.pron. Class A 3sg.neut.', 1.0],
          ['verb - BI - 3sg.perf. + infix.pron. Class C 1pl.', 1.0],
          ['verb - BI - 3sg.perf. + infix.pron. Class C 3sg.neut.', 1.0],
          ['verb - BI - 3sg.pres.ind.', 0.5830884753509631],
          ['verb - BI - 3sg.pres.ind. + inf.pron. class A 1sg.', 1.0],
          ['verb - BI - 3sg.pres.ind. + inf.pron. class A 3sg.neut.', 1.0],
          ['verb - BI - 3sg.pres.ind. + infix.pron. Class C 3pl.', 1.0],
          ['verb - BI - 3sg.pres.ind. + infix.pron. Class C 3sg.fem.', 1.0],
          ['verb - BI - 3sg.pres.ind. + infix.pron. Class C 3sg.neut.', 1.0],
          ['verb - BI - 3sg.pres.ind.pass.', 0.3898149711721709],
          ['verb - BI - 3sg.pres.ind.pass. + infix.pron. Class B 1sg.', 1.0],
          ['verb - BI - 3sg.pres.ind.pass.rel.', 1.0], ['verb - BI - 3sg.pres.ind.rel.', 0.3828105075235909],
          ['verb - BI - 3sg.pres.subj.', 1.0], ['verb - BI - 3sg.pres.subj. + infix.pron. Class B 3sg.neut.', 1.0],
          ['verb - BI - 3sg.pres.subj.pass.', 1.0], ['verb - BI - 3sg.pret.', 1.0],
          ['verb - BI - 3sg.pret./perf.', 1.0], ['verb - BI - 3sg.pret./perf. + infix.pron. Class A 1pl.', 1.0],
          ['verb - BII (?) - 3sg.pres.ind.', 1.0], ['verb - BII - 1pl.perf.', 1.0], ['verb - BII - 1sg.fut.', 1.0],
          ['verb - BII - 1sg.pres.ind.', 1.0], ['verb - BII - 1sg.pres.subj.', 1.0], ['verb - BII - 2sg.impv.', 1.0],
          ['verb - BII - 2sg.past.subj.', 1.0], ['verb - BII - 3pl.fut.', 1.0], ['verb - BII - 3pl.perf.', 1.0],
          ['verb - BII - 3pl.perf. + infix.pron. Class C 3sg.neut.', 1.0], ['verb - BII - 3pl.perf.pass.', 1.0],
          ['verb - BII - 3pl.pres.ind.', 1.0], ['verb - BII - 3pl.pres.ind. + infix.pron. Class A 3pl.', 1.0],
          ['verb - BII - 3pl.pres.ind. + infix.pron. Class C 3sg.neut.', 1.0], ['verb - BII - 3pl.pres.ind.pass.', 1.0],
          ['verb - BII - 3pl.pres.subj.', 1.0], ['verb - BII - 3sg.cond.', 1.0], ['verb - BII - 3sg.imperf.', 1.0],
          ['verb - BII - 3sg.imperf.subj.', 1.0], ['verb - BII - 3sg.imperf.subj.pass.', 1.0],
          ['verb - BII - 3sg.pass.perf.', 1.0], ['verb - BII - 3sg.perf.', 1.0],
          ['verb - BII - 3sg.perf. + infix.pron. Class C 3sg.neut.', 0.09167893961708394],
          ['verb - BII - 3sg.pres.ind.', 0.8263300270513977],
          ['verb - BII - 3sg.pres.ind. + suff.pron. 3sg.masc./neut.', 1.0], ['verb - BII - 3sg.pres.ind.pass.', 1.0],
          ['verb - BII - 3sg.pres.ind.pass. + infix.pron. Class B 3sg.', 1.0],
          ['verb - BII - 3sg.pres.ind.rel.', 0.36320434487440595],
          ['verb - BII - 3sg.pret./perf. + infix.pron. Class C 3sg.neut.', 1.0],
          ['verb - BII - 3sg.sec.fut. + infix pron Class C 3sg nt', 1.0], ['verb - BIII - 1sg.pres.ind.', 1.0],
          ['verb - BIII - 3pl.perf.', 1.0], ['verb - BIII - 3pl.pres.ind.', 1.0], ['verb - BIII - 3sg.pres.ind.', 1.0],
          ['verb - BIV - 1sg.pres.ind.', 0.521870286576169], ['verb - BIV - 3pl.pres.ind.', 1.0],
          ['verb - BIV - 3sg.perf.', 1.0], ['verb - BIV - 3sg.perf. + infix.pron. Class A 2sg.', 1.0],
          ['verb - BIV - 3sg.perf. + infix.pron. Class A 3sg.masc.', 1.0], ['verb - BIV - 3sg.pres.ind.', 1.0],
          ['verb - BIV - 3sg.pres.ind.pass.', 1.0], ['verb - BIV - 3sg.pret./perf.', 1.0],
          ['verb - BV - 1pl.pres.ind.', 1.0], ['verb - BV - 1sg.pres.ind.', 1.0], ['verb - BV - 2sg.pres.subj.', 1.0],
          ['verb - BV - 3pl.pres.ind.pass.', 1.0], ['verb - BV - 3pl.pres.subj.pass.', 1.0],
          ['verb - BV - 3sg.imperf.', 1.0], ['verb - BV - 3sg.imperf.subj.', 1.0],
          ['verb - BV - 3sg.imperf.subj.pass.', 1.0], ['verb - BV - 3sg.pres.ind.pass.', 0.46357800725648896],
          ['verb - BV - 3sg.pres.subj.pass.', 1.0], ['verb - copula - 1sg.pres.ind.', 1.0],
          ['verb - copula - 3pl.cond.', 1.0], ['verb - copula - 3pl.fut.', 0.36105476673427994],
          ['verb - copula - 3pl.past.subj.', 1.0], ['verb - copula - 3pl.pres.ind.', 0.08246808243671383],
          ['verb - copula - 3pl.pres.ind.rel.', 0.7697865718096932], ['verb - copula - 3pl.pres.subj.', 1.0],
          ['verb - copula - 3pl.pres.subj.rel.', 0.21182586094866795], ['verb - copula - 3pl.pret.', 1.0],
          ['verb - copula - 3pl.pret.rel.', 1.0], ['verb - copula - 3sg.cond.', 1.0],
          ['verb - copula - 3sg.cons.pres.', 0.9857142857142858], ['verb - copula - 3sg.fut.', 1.0],
          ['verb - copula - 3sg.fut.rel.', 1.0], ['verb - copula - 3sg.imperf.', 1.0],
          ['verb - copula - 3sg.impv.', 0.0039946737683089215], ['verb - copula - 3sg.past.subj.', 0.2705897692207397],
          ['verb - copula - 3sg.past.subj.rel.', 1.0], ['verb - copula - 3sg.perf.', 0.4243415389912205],
          ['verb - copula - 3sg.pres.ind.', 0.2465126030092406],
          ['verb - copula - 3sg.pres.ind. + infix.pron. Class C 3sg.neut.', 1.0],
          ['verb - copula - 3sg.pres.ind. + suff.pron. 3sg.masc./neut.', 1.0],
          ['verb - copula - 3sg.pres.ind.rel.', 0.013877737226277373],
          ['verb - copula - 3sg.pres.subj.', 0.21892547357381634],
          ['verb - copula - 3sg.pres.subj.rel.', 0.3330365093499555], ['verb - copula - 3sg.pret.', 0.9996720236142997],
          ['verb - copula - 3sg.sec.fut.', 1.0], ['verb - defective - 3pl.pres.ind.', 1.0],
          ['verb - defective - 3sg.pres.ind.', 1.0], ['verb - inflexion not clear - 3sg.pres.ind.', 1.0],
          ['verb - substantive verb (compound) - 3pl.pres.ind.', 1.0],
          ['verb - substantive verb (compound) - 3sg.cons.pres.', 1.0],
          ['verb - substantive verb (compound) - 3sg.pres.ind.', 1.0], ['verb - substantive verb - 1sg.pres.ind.', 1.0],
          ['verb - substantive verb - 1sg.pret.', 1.0], ['verb - substantive verb - 2pl.impv.', 1.0],
          ['verb - substantive verb - 3pl.cons.pres.', 0.2831597382247212],
          ['verb - substantive verb - 3pl.cons.pres.rel.', 0.19631454114212735],
          ['verb - substantive verb - 3pl.fut.', 1.0], ['verb - substantive verb - 3pl.fut.rel.', 1.0],
          ['verb - substantive verb - 3pl.imperf.', 1.0],
          ['verb - substantive verb - 3pl.past.subj.', 0.0020297699594046007],
          ['verb - substantive verb - 3pl.perf.', 1.0],
          ['verb - substantive verb - 3pl.pres.ind.', 0.16314167286640452],
          ['verb - substantive verb - 3pl.pres.ind. + infix.pron. Class A 3pl.', 1.0],
          ['verb - substantive verb - 3pl.pres.ind.rel.', 1.0], ['verb - substantive verb - 3pl.pres.subj.', 1.0],
          ['verb - substantive verb - 3pl.pret.', 1.0], ['verb - substantive verb - 3sg.cond.', 1.0],
          ['verb - substantive verb - 3sg.cons.pres.', 0.2970096474061867],
          ['verb - substantive verb - 3sg.cons.pres.rel.', 0.07700646704796082],
          ['verb - substantive verb - 3sg.fut.', 0.620366598778004], ['verb - substantive verb - 3sg.fut.rel.', 1.0],
          ['verb - substantive verb - 3sg.imperf.', 0.24284997491219268], ['verb - substantive verb - 3sg.impv.', 1.0],
          ['verb - substantive verb - 3sg.past.subj.', 0.6849972319616165],
          ['verb - substantive verb - 3sg.perf.', 0.17739887538545257],
          ['verb - substantive verb - 3sg.pres.ind.', 0.37113366710102186],
          ['verb - substantive verb - 3sg.pres.ind. + inf.pron. class A 3sg.neut.', 1.0],
          ['verb - substantive verb - 3sg.pres.ind. + inf.pron. class C 3sg.neut.', 1.0],
          ['verb - substantive verb - 3sg.pres.ind. + infix.pron. Class A 3pl.', 1.0],
          ['verb - substantive verb - 3sg.pres.ind. + infix.pron. Class C 3sg.neut.', 1.0],
          ['verb - substantive verb - 3sg.pres.ind.rel.', 0.019329098233653547],
          ['verb - substantive verb - 3sg.pres.subj.', 0.427584463729042],
          ['verb - substantive verb - 3sg.pres.subj.rel.', 1.0], ['verb - substantive verb - 3sg.pret.', 1.0],
          ['verb - unclear - 2sg.impv.', 1.0], ['verb - unclear - 3sg.pres.ind.', 1.0],
          ['verbal of necessity -  - *ad-āgi-', 1.0], ['verbal of necessity -  - *com-uss-scochī-', 1.0],
          ['verbal of necessity -  - *ess-ber-', 1.0], ['verbal of necessity -  - *in-gnin-', 1.0],
          ['verbal of necessity -  - verbal of necessity: *ar·eim', 1.0],
          ['verbal of necessity -  - verbal of necessity: *as·gleinn', 1.0],
          ['verbal of necessity -  - verbal of necessity: *do·edbair', 1.0],
          ['verbal of necessity -  - verbal of necessity: caraid', 1.0],
          ['verbal of necessity -  - verbal of necessity: con·certa', 1.0],
          ['verbal of necessity -  - verbal of necessity: fo-dáli', 1.0],
          ['verbal of necessity -  - verbal of necessity: sernaid', 1.0],
          ['verbal of necessity -  - verbal of necessity: sásaid', 1.0],
          ['verbal of necessity -  - verbal of necessity: techtaid', 1.0]
         ]
         ),
        (0.6860614248686578, [
            ['Precedes and forms compd. with qualified noun', 1.0], ['adjective', 0.5233596629957831],
            ['adjective, demonstrative', 0.9586206896551724],
            ['adjective, demonstrative pronominal', 0.7969671988892746],
            ['adjective, indefinite pronominal', 0.6808547106210364],
            ['adjective, pronominal (preceding noun)', 0.9771401438068105],
            ['adverb', 0.7100918890966228],
            ['adverb; preposition, with accusative', 0.6177836761778368],
            ['article', 0.7883524492065065], ['conjunction', 0.7057686706394503],
            ['conjunction (disjunct) and discourse marker', 0.9595790157192716],
            ['conjunction (leniting)', 1.0],
            ['conjunction (nasalizing, conjunct)', 0.8423907707412862],
            ['conjunction and adverb (conjunctive)', 0.9735473159933592],
            ['conjunction and preposition', 0.7449443882709808],
            ['emphasizing particle', 0.9200847585893749], ['noun', 0.6109297414610098],
            ['noun and adjective', 0.44165733482642777], ['noun, proper', 0.12470875402196827],
            ['number', 0.7236902949303559], ['particle', 0.6319688180822618],
            ['particle, emphatic pronominal', 0.620567677420452],
            ['preposition, nominal, with gen', 0.7977254264825345],
            ['preposition, with acc', 0.8821685202984119],
            ['preposition, with acc; and adversative conjunction', 0.9833435520130799],
            ['preposition, with acc; and conjunction', 0.7702168443752246],
            ['preposition, with acc; geminating', 0.9343927916543621],
            ['preposition, with acc; leniting', 0.886693703074478],
            ['preposition, with acc; leniting; and conjunction', 0.9727541022311416],
            ['preposition, with dat', 0.7858525048376693],
            ['preposition, with dat and acc; leniting', 0.7656295273381871],
            ['preposition, with dat and acc; nasalizing', 0.757940089742008],
            ['preposition, with dat; geminating', 0.0422419032734219],
            ['preposition, with dat; leniting', 0.9696272343126947],
            ['preposition, with dat; nasalizing', 0.7619186835675653],
            ['preposition, with gen; and conjunction', 0.9395181957970271],
            ['pronoun', 0.4702505219206681], ['pronoun, anaphoric', 0.9734140278828488],
            ['pronoun, demonstrative', 0.9927643667236901],
            ['pronoun, indeclinable ', 0.9952038369304557],
            ['pronoun, indeclinable, accented, deictic', 0.9292718812783342],
            ['pronoun, indefinite', 0.9620868869936035],
            ['pronoun, infixed, class A', 0.45229901539049805],
            ['pronoun, infixed, class C', 0.18616397582754576],
            ['pronoun, interrogative and indefinite', 0.27312669274751733],
            ['pronoun, non-neuter', 0.7254901960784313], ['pronoun, personal', 0.935793030111319],
            ['pronoun, possessive, stressed', 0.7759170653907496],
            ['pronoun, possessive, unstressed', 0.9321134247024053],
            ['pronoun, reflexive', 0.7931554215799272], ['see amail', 0.02891156462585034],
            ['verb', 0.5916506564323053]
        ],
         [
             ['', 1.0], ['abbreviation', 1.0], ['adjective', 0.4766403370042169], ['adjective and noun', 1.0],
             ['adjective, demonstrative', 0.041379310344827586],
             ['adjective, demonstrative pronominal', 0.20303280111072544],
             ['adjective, indefinite pronominal', 0.3191452893789636],
             ['adjective, pronominal (preceding noun)', 0.022859856193189528], ['adverb', 0.2899081109033772],
             ['adverb; preposition, with accusative', 0.38221632382216325], ['article', 0.21164755079349354],
             ['conjunction', 0.2942313293605498], ['conjunction (disjunct) and discourse marker', 0.040420984280728336],
             ['conjunction (leniting, non-conjunct particle)', 1.0], ['conjunction (nasalizing)', 1.0],
             ['conjunction (nasalizing, conjunct)', 0.1576092292587138],
             ['conjunction and adverb (conjunctive)', 0.02645268400664084],
             ['conjunction and preposition', 0.2550556117290192], ['conjunction w/ subordinate negation', 1.0],
             ['emphasizing particle', 0.0799152414106251], ['exclamation form', 1.0], ['interjection', 1.0],
             ['noun', 0.38907025853899024], ['noun and adjective', 0.5583426651735722],
             ['noun, proper', 0.8752912459780318], ['number', 0.27630970506964414], ['particle', 0.36803118191773826],
             ['particle, emphatic pronominal', 0.37943232257954795],
             ['preposition, nominal, with gen', 0.20227457351746547], ['preposition, with acc', 0.11783147970158818],
             ['preposition, with acc; and adversative conjunction', 0.01665644798692009],
             ['preposition, with acc; and conjunction', 0.22978315562477536],
             ['preposition, with acc; geminating', 0.06560720834563798],
             ['preposition, with acc; leniting', 0.11330629692552201],
             ['preposition, with acc; leniting; and conjunction', 0.027245897768858458],
             ['preposition, with dat', 0.21414749516233067],
             ['preposition, with dat and acc; leniting', 0.23437047266181285],
             ['preposition, with dat and acc; nasalizing', 0.24205991025799203],
             ['preposition, with dat; geminating', 0.9577580967265781],
             ['preposition, with dat; leniting', 0.030372765687305334],
             ['preposition, with dat; nasalizing', 0.2380813164324347],
             ['preposition, with gen; and conjunction', 0.06048180420297283], ['pronoun', 0.5297494780793319],
             ['pronoun, anaphoric', 0.026585972117151194], ['pronoun, demonstrative', 0.007235633276309954],
             ['pronoun, indeclinable ', 0.004796163069544364],
             ['pronoun, indeclinable, accented, deictic', 0.0707281187216658],
             ['pronoun, indefinite', 0.03791311300639659], ['pronoun, infixed, class A', 0.547700984609502],
             ['pronoun, infixed, class B', 1.0], ['pronoun, infixed, class C', 0.8138360241724543],
             ['pronoun, interrogative and indefinite', 0.7268733072524827],
             ['pronoun, non-neuter', 0.27450980392156865], ['pronoun, personal', 0.06420696988868099],
             ['pronoun, possessive, stressed', 0.2240829346092504],
             ['pronoun, possessive, unstressed', 0.06788657529759468], ['pronoun, reflexive', 0.2068445784200727],
             ['pronoun, suffixed', 1.0], ['see amail', 0.9710884353741497], ['unclear', 1.0],
             ['verb', 0.4083493435676947], ['verbal of necessity', 1.0]
         ]
         ),
        (0.7089022125393927, [
            ['ADJ', 0.5178149975960239], ['ADP', 0.8671954594869719], ['ADV', 0.9807337944962649],
            ['AUX', 0.8037397766157157], ['CCONJ', 0.9713900200374895], ['DET', 0.7913001851392581],
            ['INTJ', 0.6631395221991928], ['NOUN', 0.6083242766085344], ['NUM', 0.7728146520765559],
            ['PART', 0.8843356242172943], ['PRON', 0.8449821763706427], ['PROPN', 0.12536237270497286],
            ['PUNCT', 1.0], ['SCONJ', 0.7598595874481869], ['VERB', 0.47998031090150794], ['X', 0.5521739051824048]
        ],
         [
             ['ADJ', 0.48218500240397616], ['ADP', 0.1328045405130281], ['ADV', 0.019266205503735125],
             ['AUX', 0.19626022338428423], ['CCONJ', 0.028609979962510503], ['DET', 0.20869981486074182],
             ['INTJ', 0.33686047780080725], ['NOUN', 0.39167572339146567], ['NUM', 0.22718534792344416],
             ['PART', 0.11566437578270573], ['PRON', 0.15501782362935734], ['PROPN', 0.8746376272950271],
             ['SCONJ', 0.2401404125518131], ['VERB', 0.520019689098492], ['X', 0.44782609481759517]
         ]
         ),
        (0.6977989312968103, [
            ['ADJ', 0.5233434120093587], ['ADP', 0.8670220987916845], ['ADV', 0.9815915649196774],
            ['AUX', 0.817395833708821], ['CCONJ', 0.9713900200374895], ['DET', 0.788567752486434],
            ['INTJ', 0.6631395221991928], ['NOUN', 0.6107361201267972], ['NUM', 0.76287549114876],
            ['PART', 0.6159903177713305], ['PRON', 0.7905606619440704], ['PROPN', 0.12536237270497286],
            ['PUNCT', 1.0], ['SCONJ', 0.7475991869229247], ['VERB', 0.5267538929205717], ['X', 0.5415135302500039]
        ],
         [
             ['ADJ', 0.4766565879906413], ['ADP', 0.1329779012083155], ['ADV', 0.01840843508032269],
             ['AUX', 0.18260416629117898], ['CCONJ', 0.028609979962510503], ['DET', 0.21143224751356604],
             ['INTJ', 0.33686047780080725], ['NOUN', 0.38926387987320277], ['NUM', 0.23712450885124],
             ['PART', 0.38400968222866944], ['PRON', 0.2094393380559296], ['PROPN', 0.8746376272950271],
             ['SCONJ', 0.2524008130770753], ['VERB', 0.4732461070794282], ['X', 0.458486469749996]
         ]
         )
    ]

    # # Output the overall accuracy over 10,000 passes, and percentage of all unique POS-tags occurring in test-set
    # # Also output percentage of unique POS-tags both correctly and incorrectly assigned
    # ten_thou_percentages = pos_percent(ten_thousand_pass_test_results, sorted_pos_totals)
    # print(f"N-gram tagging with {num_passes} passes and n=10,000.")
    # for tok_style_indx, output in enumerate(ten_thousand_pass_test_results):
    #     print(
    #         f"Accuracy: {output[0]},\n"
    #         f"  Unique POS-tags occurring in test-set: {ten_thou_percentages[tok_style_indx][0]}%\n"
    #         f"  Unique POS-tags occurring in test-set correctly tagged: {ten_thou_percentages[tok_style_indx][1]}%\n"
    #         f"  Unique POS-tags occurring in test-set incorrectly tagged: {ten_thou_percentages[tok_style_indx][2]}%"
    #     )
