import platform
from sklearn.feature_extraction import DictVectorizer
from sklearn.preprocessing import LabelEncoder
from keras.utils import np_utils
from tensorflow.keras.utils import Sequence
from keras.models import Sequential
from keras.layers import Dense, Dropout, Activation
from keras.callbacks import EarlyStopping
import matplotlib.pyplot as plt
import numpy as np
from numpy import argmax as am
import os
from keras.utils import plot_model
import keras.backend as K
import tensorflow as tf
import random


op_sys = platform.system()
if op_sys == "Windows":
    slash = "\\"
else:
    slash = "/"


def get_postags(conllu_sentences):
    """Takes a parsed conllu file and returns a list of sentences, containing token/POS tuples"""

    tag_list = [[(token.get("form"), token.get("upos")) for token in sentence] for sentence in conllu_sentences]

    return tag_list


def split_tokmorphs(sentence_lists):
    """Takes a list of sentences, where each sentence is a list of token/morphology-label tuples
       returns a list of tokens and a separate list of matched morphological labels"""

    token_list = [[tok_data[0] for tok_data in sent] for sent in sentence_lists]
    morph_list = [[tok_data[1] for tok_data in sent] for sent in sentence_lists]

    return [token_list, morph_list]


def transform_words(sentence_lists):
    """Buffers words in sentence lists so that they are all the same length"""

    unique_words = sorted(list(set([item[0] for sublist in sentence_lists for item in sublist])))
    longest_word = sorted([len(word) for word in unique_words])[-1]

    # Make the buffer size for the language equal to the length of the longest word in the training data plus 5
    # Then round up to the nearest ten
    multiples_of_ten = [10*n for n in range(1, 21)]
    buffer_size = longest_word + 5
    for decimal in multiples_of_ten:
        if decimal >= buffer_size:
            buffer_size = decimal
            break

    buffered_sentences = list()
    buffer_character = "☘"
    for sublist in sentence_lists:
        buffered_sentence = list()
        for item in sublist:
            token = item[0]
            pos_tag = item[1]
            buffer_length = buffer_size - len(token)
            new_token = buffer_length*buffer_character + token
            buffered_sentence.append((new_token, pos_tag))
        buffered_sentences.append(buffered_sentence)

    return buffered_sentences


def get_word_features(words, word_index):
    """Return a dictionary of important word features for an individual word in the context of its sentence"""
    word = words[word_index]
    buffer_character = "☘"
    unbuffered_word = word.strip(buffer_character)
    empty_token = buffer_character*len(word)
    return {
        'word': word.lower(),
        'sent_len': len(words),
        'word_len': len(unbuffered_word),
        'first_word': word_index == 0,
        'last_word': word_index == len(words) - 1,
        'capitalised': unbuffered_word[0].upper() == unbuffered_word[0] if len(unbuffered_word) > 0 else False,
        'all_caps': unbuffered_word.upper() == unbuffered_word,
        'all_lower': unbuffered_word.lower() == unbuffered_word,
        'start_letter': unbuffered_word[0] if len(unbuffered_word) > 0 else "",
        'start_letters-2': unbuffered_word[:2] if len(unbuffered_word) > 1 else "",
        'start_letters-3': unbuffered_word[:3] if len(unbuffered_word) > 2 else "",
        'start_letters-4': unbuffered_word[:4] if len(unbuffered_word) > 3 else "",
        'start_letters-5': unbuffered_word[:5] if len(unbuffered_word) > 4 else "",
        'end_letter': unbuffered_word[-1] if len(unbuffered_word) > 0 else "",
        'end_letters-2': unbuffered_word[-2:] if len(unbuffered_word) > 1 else "",
        'end_letters-3': unbuffered_word[-3:] if len(unbuffered_word) > 2 else "",
        'end_letters-4': unbuffered_word[-4:] if len(unbuffered_word) > 3 else "",
        'end_letters-5': unbuffered_word[-5:] if len(unbuffered_word) > 4 else "",
        'previous_word': empty_token if word_index == 0 else words[word_index - 1].lower(),
        'previous_word2': empty_token if word_index <= 1 else words[word_index - 2].lower(),
        'following_word': empty_token if word_index == len(words) - 1 else words[word_index + 1].lower(),
        'following_word2': empty_token if word_index >= len(words) - 2 else words[word_index + 2].lower()
    }


def generate_xy_dataset(sentence_lists):
    """Returns a split of token data (word-feature dictionary objects) and token morphology data (POS, lemmata, etc.)"""

    sentence_lists = transform_words(sentence_lists)
    morph_split = split_tokmorphs(sentence_lists)

    X, y = list(), list()

    for sentnum, sentence in enumerate(morph_split[0]):
        sent_morphology = morph_split[1][sentnum]
        for index, token in enumerate(sentence):
            X.append(get_word_features(sentence, index))
            y.append(sent_morphology[index])

    return [X, y]


def vectorise_x(train_tokens):
    """Returns vectoriser fitted to all x data"""

    # Fit the vectoriser to the token data
    dict_vectoriser = DictVectorizer(sparse=False)
    dict_vectoriser.fit(train_tokens)

    return dict_vectoriser


def encode_y(encode_labels, all_labels):
    """Returns encodings for labels"""

    # Fit the encoder to the label data
    label_encoder = LabelEncoder()
    label_encoder.fit(all_labels)
    tag_classes = len(sorted(list(set(all_labels))))

    # Encode label data
    y_data = label_encoder.transform(encode_labels)

    # Convert encodings to one-hot encodings
    y_data = np_utils.to_categorical(y_data, num_classes=tag_classes)

    return y_data


def decode_y(encoded_predictions, all_labels):
    """Returns encodings for labels"""

    # Fit the encoder to the label data
    label_encoder = LabelEncoder()
    label_encoder.fit(all_labels)

    # Convert encodings back from one-hot encodings
    y_test = [am(item) for item in encoded_predictions]

    # Decode label data
    decoded = label_encoder.inverse_transform(y_test)

    return decoded


class DataGenerator(Sequence):
    def __init__(self, x_set, y_set, batch_size, x_vec):
        self.x, self.y = x_set, y_set
        self.batch_size = batch_size
        self.x_vec = x_vec

    def __len__(self):
        return int(np.ceil(len(self.x) / float(self.batch_size)))

    def __getitem__(self, idx):
        batch_x = self.x_vec.transform(self.x[idx * self.batch_size:(idx + 1) * self.batch_size])
        batch_y = self.y[idx * self.batch_size:(idx + 1) * self.batch_size]
        return batch_x, batch_y


class TestGenerator(Sequence):
    def __init__(self, x_set, batch_size, x_vec):
        self.x = x_set
        self.batch_size = batch_size
        self.x_vec = x_vec

    def __len__(self):
        return int(np.ceil(len(self.x) / float(self.batch_size)))

    def __getitem__(self, idx):
        batch_x = self.x_vec.transform(self.x[idx * self.batch_size:(idx + 1) * self.batch_size])
        return batch_x


def construct_model(input_dim, hidden_neurons, output_dim):
    """Returns a Keras model which will be used to predict parts-of-speech"""

    pos_model = Sequential([
        Dense(hidden_neurons, input_dim=input_dim),
        Activation('relu'),
        Dropout(0.2),
        Dense(hidden_neurons),
        Activation('relu'),
        Dropout(0.2),
        Dense(output_dim, activation='softmax')
    ])
    pos_model.compile(loss='categorical_crossentropy', optimizer='adam', metrics=['accuracy'])

    return pos_model


def plot_model_performance(train_loss, train_acc, train_val_loss, train_val_acc, model_name, save_dir):
    """Plot model loss and accuracy as it trains"""

    blue = '#34495E'
    green = '#2ECC71'
    orange = '#E23B13'

    # Plot model loss
    fig, (ax1, ax2) = plt.subplots(2, figsize=(10, 8))

    fig.suptitle(f'Loss and accuracy through #epochs for model: {model_name}', color=orange, fontweight='bold')

    ax1.plot(range(1, len(train_loss) + 1), train_loss, blue, linewidth=5, label='training')
    ax1.plot(range(1, len(train_val_loss) + 1), train_val_loss, green, linewidth=5, label='validation')
    ax1.set_xlabel('# epoch')
    ax1.set_ylabel('loss')
    ax1.tick_params('y')
    ax1.legend(loc='upper right', shadow=False)

    # Plot model accuracy
    ax2.plot(range(1, len(train_acc) + 1), train_acc, blue, linewidth=5, label='training')
    ax2.plot(range(1, len(train_val_acc) + 1), train_val_acc, green, linewidth=5, label='validation')
    ax2.set_xlabel('# epoch')
    ax2.set_ylabel('accuracy')
    ax2.tick_params('y')
    ax2.legend(loc='lower right', shadow=False)

    plt.savefig(f"{save_dir}{slash}{model_name}_training_data.png")


def create_val_data(train_data, val_percentage=10):
    """Create a random validation split from a selected percentage of provided training data"""

    val_size = int(len(train_data) / val_percentage)
    usable_indices = [index for index in range(len(train_data))]
    random.seed(15)
    random_indices = sorted(random.sample(usable_indices, val_size))
    new_val = [train_data[i] for i in random_indices]
    new_train = [j for i, j in enumerate(train_data) if i not in random_indices]

    return [new_train, new_val]


def encode_test(test_data, all_tags):
    """Encodes test data so that it can be tagged using a DNN POS-tagger"""

    test_dataset = generate_xy_dataset(test_data)
    test_labels = encode_y(test_dataset[1], all_tags)

    return test_labels


def trainDNN(pos_set, save_model=False, mod_name="DNN_tagger"):
    """Trains the DNN POS-tagger"""

    train_gen, val_gen, input_dim, output_dim, batch_size = pos_set[0], pos_set[1], pos_set[2], pos_set[3], pos_set[4]

    # Create and train model
    early_stopping = EarlyStopping(monitor="val_loss", mode='min', patience=7, restore_best_weights=True, verbose=1)
    model_params = {
        'input_dim': input_dim,
        'hidden_neurons': 64,
        'output_dim': output_dim,
        'epochs': 50,
        'batch_size': batch_size,
        'callbacks': [early_stopping],
        'verbose': 1,
        'shuffle': True
    }

    pos_model = construct_model(
        input_dim=model_params.get("input_dim"),
        hidden_neurons=model_params.get("hidden_neurons"),
        output_dim=model_params.get("output_dim")
    )

    hist = pos_model.fit(
        train_gen,
        batch_size=model_params.get("batch_size"),
        epochs=model_params.get("epochs"),
        callbacks=model_params.get("callbacks"),
        verbose=model_params.get("verbose"),
        validation_data=val_gen,
        shuffle=model_params.get("shuffle")
    )

    if save_model:

        # Create all necessary directories if they do not already exist
        cur_dir = os.getcwd()
        pos_dir = f"{cur_dir}{slash}DNN_models"
        models_dir = f"{pos_dir}{slash}models"
        vis_dir = f"{pos_dir}{slash}model_visualisations"
        training_dir = f"{pos_dir}{slash}training_data"

        for folder in [pos_dir, models_dir, vis_dir, training_dir]:
            if not os.path.exists(folder):
                os.mkdir(folder)

        # Plot the model's validation loss and accuracy during training
        # and save this graph to the training data directory
        print("\nPlotting model performance during training")
        plot_model_performance(
            train_loss=hist.history.get('loss', []),
            train_acc=hist.history.get('accuracy', []),
            train_val_loss=hist.history.get('val_loss', []),
            train_val_acc=hist.history.get('val_accuracy', []),
            model_name=mod_name,
            save_dir=training_dir
        )

        # Save the model to the models directory
        print(f"Saving model: {mod_name}")
        pos_model.save(f"{models_dir}{slash}{mod_name}.h5")

        # Save a visualisation of the model to the training data directory
        print(f"    Saving visualisation for model: {mod_name}")
        plot_model(pos_model, to_file=f"{vis_dir}{slash}{mod_name}_model.png", show_shapes=True)

        print(f"Created and saved model: {mod_name}\n")

    else:
        print(f"Created model: {mod_name}\n")

    return pos_model


def dnn_tag(test_set, tagger, batch_size, x_vectoriser, tag_set, intj_split=False, prop_split=False, punct_split=False):
    """Uses a tagger model to POS-tag list of sentences"""

    # Turn list of sentences into a single list of tokens, then use this to create data generator
    test_sentences = [[token[0] for token in sent] for sent in test_set]
    test_toks = generate_xy_dataset(test_set)[0]
    test_gen = TestGenerator(test_toks, batch_size, x_vectoriser)

    # Try to make predictions using GPU first
    K.clear_session()
    try:
        with tf.device('/gpu:0'):
            predictions = tagger.predict(test_gen)
    # If this fails (eg. due to memory error) attempt using CPU
    except:
        print(f"Error making predictions using GPU\n    Switching to CPU")
        with tf.device('/cpu:0'):
            predictions = tagger.predict(test_gen)

    # Decode model predictions
    decoded_labels = decode_y(predictions, tag_set)
    labels_gen = iter(decoded_labels)
    tagged_sentences = [[(word, next(labels_gen)) for word in sent] for sent in test_sentences]

    if intj_split:
        intj_dict = {tok[0].lower(): tok[1] for tok in intj_split}
        tagged_sentences = [
            [
                tok if tok[0].lower() not in intj_dict else (tok[0], intj_dict.get(tok[0].lower())) for tok in sent
            ] for sent in tagged_sentences
        ]

    if prop_split:
        prop_dict = {tok[0].lower(): tok[1] for tok in prop_split}
        tagged_sentences = [
            [
                tok if tok[0].lower() not in prop_dict else (tok[0], prop_dict.get(tok[0].lower())) for tok in sent
            ] for sent in tagged_sentences
        ]

    if punct_split:
        punct_dict = {tok[0]: tok[1] for tok in punct_split}
        tagged_sentences = [
            [
                tok if tok[0] not in punct_dict else (tok[0], punct_dict.get(tok[0])) for tok in sent
            ] for sent in tagged_sentences
        ]

    return tagged_sentences


# if __name__ == "__main__":
#
#     # Create all necessary directories if they do not already exist
#     cur_dir = os.getcwd()
#     pos_dir = f"{cur_dir}{slash}DNN_models"
#     models_dir = f"{pos_dir}{slash}models"
#     scores_dir = f"{pos_dir}{slash}model_scores"
#     vis_dir = f"{pos_dir}{slash}model_visualisations"
#     training_dir = f"{pos_dir}{slash}training_data"
#
#     for folder in [pos_dir, models_dir, scores_dir, vis_dir, training_dir]:
#         if not os.path.exists(folder):
#             os.mkdir(folder)
#
#     language = "Old Irish"
#
#     print(f"Training tagger for language: {language}")
#
#     # Load and process training, validation and test datasets
#     train_data = load_trainfiles("morph", language, verbose=1)
#     train_sent_lists = get_postags(train_data.get(language))
#     train_dataset = generate_xy_dataset(train_sent_lists)
#
#     val_data = load_valfiles("morph", language, verbose=1)
#     val_sent_lists = get_postags(val_data.get(language))
#     val_dataset = generate_xy_dataset(val_sent_lists)
#
#     test_data = load_test_json("pos", language, verbose=1)
#     test_dataset = generate_xy_dataset(test_data.get(language))
#
#     x_data = [train_dataset[0], val_dataset[0], test_dataset[0]]
#     x_vec = vectorise_x(train_dataset[0])
#     y_data = encode_y(train_dataset[1], val_dataset[1], test_dataset[1])
#
#     batch_size = 256
#
#     train_gen = DataGenerator(x_data[0], y_data[0], batch_size, x_vec)
#     val_gen = DataGenerator(x_data[1], y_data[1], batch_size, x_vec)
#     test_gen = DataGenerator(x_data[2], y_data[2], batch_size, x_vec)
#
#     # Create and train model
#     early_stopping = EarlyStopping(monitor="val_loss", mode='min', patience=7, restore_best_weights=True, verbose=1)
#     model_params = {
#         'input_dim': len(x_vec.get_feature_names_out()),
#         'hidden_neurons': 64,
#         'output_dim': y_data[0].shape[1],
#         'epochs': 50,
#         'batch_size': batch_size,
#         'callbacks': [early_stopping],
#         'verbose': 1,
#         'shuffle': True
#     }
#
#     pos_model = construct_model(
#         input_dim=model_params.get("input_dim"),
#         hidden_neurons=model_params.get("hidden_neurons"),
#         output_dim=model_params.get("output_dim")
#     )
#
#     hist = pos_model.fit(
#         train_gen,
#         batch_size=model_params.get("batch_size"),
#         epochs=model_params.get("epochs"),
#         callbacks=model_params.get("callbacks"),
#         verbose=model_params.get("verbose"),
#         validation_data=val_gen,
#         shuffle=model_params.get("shuffle")
#     )
#
#     # Plot the model's validation loss and accuracy during training
#     # and save this graph to the training data directory
#     print("\nPlotting model performance during training")
#     plot_model_performance(
#         train_loss=hist.history.get('loss', []),
#         train_acc=hist.history.get('accuracy', []),
#         train_val_loss=hist.history.get('val_loss', []),
#         train_val_acc=hist.history.get('val_accuracy', []),
#         this_lang=language,
#         this_dir=cur_dir,
#         save_dir=training_dir
#     )
#
#     # Save the model to the models directory
#     print(f"Saving model for language: {language}")
#     os.chdir(models_dir)
#     pos_model.save(f"{language}_Alt_tagger.h5")
#     os.chdir(cur_dir)
#
#     # Save a visualisation of the model to the training data directory
#     print(f"    Saving model visualisation for language: {language}")
#     os.chdir(vis_dir)
#     plot_model(pos_model, to_file=f"{language}_Alt_model.png", show_shapes=True)
#     os.chdir(cur_dir)
#
#     # Calculate the model's score and save it to a text file in the scores directory
#     print(f"    Evaluating model for language: {language}")
#     score = pos_model.evaluate(test_gen)
#
#     with open(f"{scores_dir}{slash}{language}_Alt_score.txt", "w") as f:
#         f.write(f"Model score for {language}:\n    test loss = {score[0]}\n    test accuracy = {score[1]}")
#
#     print(f"Model created, evaluated and saved for language: {language}\n")
