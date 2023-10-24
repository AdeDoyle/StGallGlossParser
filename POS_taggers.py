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
        if tagger_style != "all":
            tagger = train_pos_tagger(train_set, tagger_style, ngram)
        elif tagger_style == "all":
            unigram_tagger = train_pos_tagger(train_set, "n-gram", 1)
            ngram_tagger = train_pos_tagger(train_set, "n-gram", ngram)
            brill_tagger = train_pos_tagger(train_set, "brill", ngram)
            hmm_tagger = train_pos_tagger(train_set, "HMM", ngram)
            perceptron_tagger = train_pos_tagger(train_set, "perceptron", ngram)

        # Evaluate POS tagger on the test files
        correct = list()
        incorrect = list()
        # Test the tagger on each gloss, and compile a list of POS "guesses" for each gloss in the test set
        for gloss_indx, test_gloss in enumerate(test_toks):
            # If only one tagger is being tested
            if tagger_style != "all":
                guesses = tagger.tag(test_gloss)
                guesses = [guess[1] if guess[1] else "No Guess" for guess in guesses]
            # If all taggers are being combined
            elif tagger_style == "all":
                uni_guesses = unigram_tagger.tag(test_gloss)
                uni_guesses = [guess[1] if guess[1] else "No Guess" for guess in uni_guesses]
                ngram_guesses = ngram_tagger.tag(test_gloss)
                ngram_guesses = [guess[1] if guess[1] else "No Guess" for guess in ngram_guesses]
                brill_guesses = brill_tagger.tag(test_gloss)
                brill_guesses = [guess[1] if guess[1] else "No Guess" for guess in brill_guesses]
                hmm_guesses = hmm_tagger.tag(test_gloss)
                hmm_guesses = [guess[1] if guess[1] else "No Guess" for guess in hmm_guesses]
                perceptron_guesses = perceptron_tagger.tag(test_gloss)
                perceptron_guesses = [guess[1] if guess[1] else "No Guess" for guess in perceptron_guesses]
                guesses = list()
                # Identify POS accuracies for different taggers
                uni_accs = {"ADV": 0.982, "CCONJ": 0.971}
                ngram_accs = {"NUM": 0.790}
                brill_accs = {"PRON": 0.817, "PROPN": 0.840}
                hmm_accs = {"DET": 0.928, "PART": 0.971}
                perceptron_accs = {"ADJ": 0.694, "ADP": 0.893, "ADV": 0.974, "AUX": 0.910, "CCONJ": 0.956, "DET": 0.922,
                                   "INTJ": 0.678, "NOUN": 0.899, "NUM": 0.724, "PART": 0.833, "PRON": 0.814,
                                   "PROPN": 0.055, "PUNCT": 1.0, "SCONJ": 0.861, "VERB": 0.814, "X": 0.846}
                # Using perceptron tagger as the base tagger (as it is te best performing model in isolation)
                # substitute in POS-tags from other taggers where those other taggers are better than the perceptron
                # tagger at identifying those specific parts-of-speech
                for guess_num, guess in enumerate(perceptron_guesses):
                    uni_tagcheck = uni_guesses[guess_num]
                    ngram_tagcheck = ngram_guesses[guess_num]
                    brill_tagcheck = brill_guesses[guess_num]
                    hmm_tagcheck = hmm_guesses[guess_num]
                    if guess == "No Guess" and hmm_tagcheck != "No Guess":
                        guess = hmm_tagcheck
                    elif guess == "No Guess" and brill_tagcheck != "No Guess":
                        guess = brill_tagcheck
                    elif guess == "No Guess" and ngram_tagcheck != "No Guess":
                        guess = ngram_tagcheck
                    elif guess == "No Guess" and uni_tagcheck != "No Guess":
                        guess = uni_tagcheck
                    if guess != "No Guess":
                        if uni_tagcheck in uni_accs and guess != uni_tagcheck:
                            guess_acc = perceptron_accs.get(guess)
                            alt_acc = uni_accs.get(uni_tagcheck)
                            if guess_acc < alt_acc:
                                guess = uni_tagcheck
                        elif ngram_tagcheck in ngram_accs and guess != ngram_tagcheck:
                            guess_acc = perceptron_accs.get(guess)
                            alt_acc = ngram_accs.get(ngram_tagcheck)
                            if guess_acc < alt_acc:
                                guess = ngram_tagcheck
                        elif brill_tagcheck in brill_accs and guess != brill_tagcheck:
                            guess_acc = perceptron_accs.get(guess)
                            alt_acc = brill_accs.get(brill_tagcheck)
                            if guess_acc < alt_acc:
                                guess = brill_tagcheck
                        elif hmm_tagcheck in hmm_accs and guess != hmm_tagcheck:
                            guess_acc = perceptron_accs.get(guess)
                            alt_acc = hmm_accs.get(hmm_tagcheck)
                            if guess_acc < alt_acc:
                                guess = hmm_tagcheck
                    guesses.append(guess)
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
    tagger_n = 3

    # *** UNIGRAM TAGGER ***

    # Train n-gram taggers and test on random selection of glosses multiple times
    ngram_multi_pass = multi_test_random(combined_corpora, 5, num_passes, "n-gram", 1)

    print()
    print(f"Unigram tagging with {num_passes} passes.")

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

    # *** N-GRAM TAGGER ***

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

    # *** BRILL TAGGER ***

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

    # *** HMM TAGGER ***

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

    # *** PERCEPTRON TAGGER ***

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

    # *** COMBINATION TAGGER ***

    # Train a combination of taggers and test on random selection of glosses multiple times
    combination_multi_pass = multi_test_random(combined_corpora, 5, num_passes, "all", tagger_n)

    print()
    print(f"Combination Model tagging with {num_passes} passes and n={tagger_n}.")

    # Print average score for each corpus tested
    for i in combination_multi_pass[2:]:
        print(i)
        # print(i[0])

    # Output the overall accuracy over multiple passes, and percentage of all unique POS-tags occurring in test-set
    # Also output percentage of unique POS-tags both correctly and incorrectly assigned
    multi_pass_percentages = pos_percent(combination_multi_pass, sorted_pos_totals)
    for tok_style_indx, output in enumerate(combination_multi_pass):
        print(
            f"Accuracy: {output[0]},\n"
            f"  Unique POS-tags occurring in test-set: {multi_pass_percentages[tok_style_indx][0]}%\n"
            f"  Unique POS-tags occurring in test-set correctly tagged: {multi_pass_percentages[tok_style_indx][1]}%\n"
            f"  Unique POS-tags occurring in test-set incorrectly tagged: {multi_pass_percentages[tok_style_indx][2]}%"
        )
    print()
