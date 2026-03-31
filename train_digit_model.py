import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Conv2D, MaxPooling2D, Flatten, Dense, Dropout
import matplotlib.pyplot as plt

print("[INFO] Downloading and loading the original MNIST digit dataset...")
mnist = tf.keras.datasets.mnist
(x_train, y_train), (x_test, y_test) = mnist.load_data()

print("[INFO] Normalizing and reshaping images for the CNN...")
# Normalize pixels to [0,1] and reshape to (num_samples, 28, 28, 1)
x_train = x_train.reshape(x_train.shape[0], 28, 28, 1).astype('float32') / 255.0
x_test = x_test.reshape(x_test.shape[0], 28, 28, 1).astype('float32') / 255.0

print(f"[INFO] Prepared {x_train.shape[0]} training images and {x_test.shape[0]} test images.")

print("[INFO] Stacking the Convolutional Neural Network architecture...")
model = Sequential([
    Conv2D(32, kernel_size=(3, 3), activation='relu', input_shape=(28, 28, 1)),
    MaxPooling2D(pool_size=(2, 2)),
    
    Conv2D(64, kernel_size=(3, 3), activation='relu'),
    MaxPooling2D(pool_size=(2, 2)),
    
    Flatten(),
    
    Dense(128, activation='relu'),
    Dropout(0.5), # Prevent overfitting
    
    Dense(10, activation='softmax') # 10 outputs for digits 0-9
])

model.compile(optimizer='adam',
              loss='sparse_categorical_crossentropy',
              metrics=['accuracy'])

print("[INFO] Initializing Training phase!")
print("[INFO] This might take a minute or two depending on your CPU...")
model.fit(x_train, y_train, epochs=5, validation_data=(x_test, y_test), batch_size=128)

print("\n[INFO] Evaluating accuracy on unseen test data...")
loss, accuracy = model.evaluate(x_test, y_test)
print(f"Test Accuracy: {accuracy*100:.2f}%")

model.save("digit_model.h5")
print("\n[SUCCESS] Custom CNN model trained and securely saved to 'digit_model.h5'!")
