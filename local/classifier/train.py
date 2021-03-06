import json
import numpy as np
from sklearn.model_selection import train_test_split
import tensorflow as tf
from tensorflow import keras


DATA_PATH = "local/classifier/data.json"
SAVED_MODEL_PATH = r"/Users/James/Documents/Python/MachineLearningProjects/DeepLearning_Deployment/server/flask/model.h5"
EPOCHS = 40
BATCH_SIZE = 32
PATIENCE = 5
LEARNING_RATE = 0.0001


def load_data(data_path):

    with open(data_path, "r") as fp:
        data = json.load(fp)

    X = np.array(data["MFCCs"])
    y = np.array(data["labels"])
    print("Training sets loaded!")
    return X, y


def prepare_dataset(data_path, test_size=0.2, validation_size=0.2):

    # load dataset
    X, y = load_data(data_path)

    # create train, validation, test split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size)
    X_train, X_validation, y_train, y_validation = train_test_split(
        X_train, y_train, test_size=validation_size
    )

    # add an axis to nd array
    X_train = X_train[..., np.newaxis]
    X_test = X_test[..., np.newaxis]
    X_validation = X_validation[..., np.newaxis]

    return X_train, y_train, X_validation, y_validation, X_test, y_test


def build_model(
    input_shape, loss="sparse_categorical_crossentropy", learning_rate=0.0001
):

    # build network architecture using convolutional layers
    model = keras.models.Sequential()

    # 1st conv layer
    model.add(
        keras.layers.Conv2D(
            64,
            (3, 3),
            activation="relu",
            input_shape=input_shape,
            kernel_regularizer=keras.regularizers.l2(0.001),
        )
    )
    model.add(keras.layers.BatchNormalization())
    model.add(keras.layers.MaxPooling2D((3, 3), strides=(2, 2), padding="same"))

    # 2nd conv layer
    model.add(
        keras.layers.Conv2D(
            32,
            (3, 3),
            activation="relu",
            kernel_regularizer=keras.regularizers.l2(0.001),
        )
    )
    model.add(keras.layers.BatchNormalization())
    model.add(keras.layers.MaxPooling2D((3, 3), strides=(2, 2), padding="same"))

    # 3rd conv layer
    model.add(
        keras.layers.Conv2D(
            32,
            (2, 2),
            activation="relu",
            kernel_regularizer=keras.regularizers.l2(0.001),
        )
    )
    model.add(keras.layers.BatchNormalization())
    model.add(keras.layers.MaxPooling2D((2, 2), strides=(2, 2), padding="same"))

    # flatten output and feed into dense layer
    model.add(keras.layers.Flatten())
    model.add(keras.layers.Dense(64, activation="relu"))
    keras.layers.Dropout(0.3)

    # softmax output layer
    model.add(keras.layers.Dense(10, activation="softmax"))

    optimiser = tf.optimizers.Adam(learning_rate=learning_rate)

    # compile model
    model.compile(optimizer=optimiser, loss=loss, metrics=["accuracy"])

    # print model parameters on console
    model.summary()

    # plot model image
    dot_img_file = "model_figure.png"
    keras.utils.plot_model(model, to_file=dot_img_file, show_shapes=True)

    return model


def train(
    model, epochs, batch_size, patience, X_train, y_train, X_validation, y_validation
):

    earlystop_callback = keras.callbacks.EarlyStopping(
        monitor="accuracy", min_delta=0.001, patience=patience
    )

    # train model
    history = model.fit(
        X_train,
        y_train,
        epochs=epochs,
        batch_size=batch_size,
        validation_data=(X_validation, y_validation),
        callbacks=[earlystop_callback],
    )
    return history


def main():
    # generate train, validation and test sets
    X_train, y_train, X_validation, y_validation, X_test, y_test = prepare_dataset(
        DATA_PATH
    )

    # create network
    input_shape = (X_train.shape[1], X_train.shape[2], 1)
    model = build_model(input_shape, learning_rate=LEARNING_RATE)

    # train network
    history = train(
        model,
        EPOCHS,
        BATCH_SIZE,
        PATIENCE,
        X_train,
        y_train,
        X_validation,
        y_validation,
    )

    # evaluate network on test set
    test_loss, test_acc = model.evaluate(X_test, y_test)
    print("\nTest loss: {}, test accuracy: {}".format(test_loss, 100 * test_acc))

    save model
    model.save(SAVED_MODEL_PATH)


if __name__ == "__main__":
    main()
