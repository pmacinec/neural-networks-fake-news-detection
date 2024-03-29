import gc
from os import makedirs
from os.path import dirname, join
import datetime
import numpy as np
from config import parse_input_parameters, get_config
from model import FakeNewsDetectionNet
from preprocessing import read_data, get_sequences_and_word_index, split_data,\
    get_embeddings_matrix
from fasttext import read_fasttext_model
import tensorflow.keras as keras
import pickle


def get_model(
        dim_input,
        dim_embeddings,
        embeddings, optimizer,
        lstm_units=64,
        num_hidden_layers=1):
    """
    Function to get compiled model, ready for training.

    :param dim_input: int, input dimension (vocabulary size).
    :param dim_embeddings: int, dimension of embeddings (e.g. 300 for
        pre-trained fastText embeddings).
    :param embeddings: np.ndarray, matrix of pre-trained embeddings.
    :param optimizer: str|keras.optimizers.Optimizer, optimizer to be
        used in training.
    :param lstm_units: int, number of units in LSTM layer.
    :param num_hidden_layers: int, number of hidden dense layers.
    :return: FakeNewsDetectionNet, compiled Keras model.
    """
    model = FakeNewsDetectionNet(
        dim_input=dim_input,
        dim_embeddings=dim_embeddings,
        embeddings=embeddings,
        lstm_units=lstm_units,
        num_hidden_layers=num_hidden_layers
    )

    model.compile(
        optimizer=optimizer,
        loss='binary_crossentropy',
        metrics=['accuracy']
    )

    return model


def prepare_data(
        data_path=None,
        max_words=None,
        test_size=0.15,
        max_seq_len=None,
        samples=None
):
    """
    Function to load and prepare data for training.

    :param data_path: str, path where csv file is stored.
    :param max_words: int, maximum number of top words in vocabulary.
    :param test_size: float, train test split rate.
    :param max_seq_len: int, maximum length of all sequences.
    :param samples: int, number of samples from data to choose.
    :return: list, list of data and word index in format:
        x_train, x_test, y_train, y_test, word_index
    """
    data = read_data(data_path, samples)

    labels = np.asarray(data['label'])
    sequences, word_index = get_sequences_and_word_index(
        data['body'], max_words, max_seq_len
    )

    print(f'Sequences shape: {sequences.shape}')

    x_train, x_test, y_train, y_test = split_data(sequences, labels, test_size)

    return x_train, x_test, y_train, y_test, word_index


def get_callbacks(training_name):
    """
    Function to get callbacks for training.

    :param training_name: str, name of current training (also the folder
        name for both, logs and checkpoint model).
    :return: list, list of callbacks.
    """
    tensorboard = keras.callbacks.TensorBoard(
        log_dir=join(dirname(__file__), f'../../logs/{training_name}'),
        histogram_freq=1,
        profile_batch=0
    )

    checkpoint_filepath = join(
        dirname(__file__),
        f'../../models/{training_name}/model'
    )
    checkpoint = keras.callbacks.ModelCheckpoint(
        filepath=checkpoint_filepath,
        save_weights_only=False,
        verbose=1,
        monitor='val_accuracy',
        save_best_only=True,
        mode='max'
    )

    early_stopping = keras.callbacks.EarlyStopping(
        monitor='val_accuracy', 
        patience=3
    )

    return [tensorboard, checkpoint, early_stopping]


def train(config):
    """
    Function to train prepared model on chosen data.

    :param config: dict, configuration to be used.
    :return: FakeNewsDetectionNet, trained model.
    """
    training_name = config.get('name', None)
    if training_name is None:
        training_name = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    makedirs(join(
        dirname(__file__),
        f'../../models/{training_name}'
    ))

    # Read the data and get word index
    print('Preparing data...')
    x_train, x_test, y_train, y_test, word_index = prepare_data(
        data_path=config.get('data_file', None),
        max_words=config.get('max_words', None),
        test_size=config.get('test_size', None),
        max_seq_len=config.get('max_seq_len', None),
        samples=config.get('num_samples', None)
    )
    print(f'Data prepared. Vocabulary size: {len(word_index)}.')
    print('Serializing word index table...')
    pickle.dump(
        word_index,
        open(
            join(
                dirname(__file__),
                f'../../models/{training_name}/word_index.obj'
            ),
            'wb'
        )
    )

    print('Reading fastText model...')
    # Read pre-trained fasttext embeddings
    fasttext = read_fasttext_model(
        join(dirname(__file__), '../../models/fasttext/wiki-news-300d-1M.vec')
    )

    print('Creating embeddings matrix...')
    # Get filtered embeddings matrix
    embeddings_matrix = get_embeddings_matrix(
        word_index,
        fasttext,
        300
    )

    vocabulary_size = len(word_index)

    del fasttext
    del word_index
    gc.collect()

    optimizer = keras.optimizers.Adam(learning_rate=config['learning_rate'])

    model = get_model(
        vocabulary_size,
        300,
        embeddings_matrix,
        optimizer,
        int(config.get('lstm_units')),
        int(config.get('num_hidden_layers'))
    )

    print('Training the model...')
    model.fit(
        x=x_train,
        y=y_train,
        batch_size=int(config.get('batch_size', 0)),
        validation_data=(x_test, y_test),
        callbacks=get_callbacks(training_name),
        epochs=int(config.get('epochs', 0))
    )

    model.summary()

    return model


if __name__ == "__main__":
    args = parse_input_parameters()

    config = get_config(args)
    print(f'Config for this training: {config}')

    train(config)
    print('Model training ended.')
