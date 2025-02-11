# -*- coding: utf-8 -*-
"""lab2.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1ho3SarkeMexJ9NxZQxDMFLCxSIV_oujs

**Серебрянский Александр 18-АС** \
**DEEP WEEDS AND VGG16**

В соответствии с csv файлом распределим фотографии по папкам-классам (делал не в colab)
"""

import shutil
import csv
import pandas as pd

def copy_pictures(file, tt):
    src = "C:\\Users\\parti\\Desktop\\deep_weeds\\DeepWeeds_Images_256\\" + str(file[0])
    dst = "C:\\Users\\parti\\Desktop\\deep_weeds\\" + str(ttv) + "\\" + str(file[1]) + "\\" + str(file[0])
    shutil.copyfile(src, dst, follow_symlinks=True)
    print("File " + str(file[0]) + " placed in " + str(file[1]))

def csv_reader(name):
    df = pd.read_csv(name+'_set_labels.csv', sep=',')
    return df

def df_parser(i,df):
    file = []
    name = df.iloc[i]['Label']
    label = df.iloc[i]['Species']
    file.append(name)
    file.append(label)
    return file

if __name__ == "__main__":
    train = csv_reader('train')
    for i in range (0,train.shape[0]):
        file = df_parser(i,train)
        copy_pictures(file, 'train')
    test = csv_reader('test')
    for i in range (0,test.shape[0]):
        file = df_parser(i,test)
        copy_pictures(file, 'test')
    val = csv_reader('validation')
    for i in range (0,test.shape[0]):
        file = df_parser(i,test)
        copy_pictures(file, 'validation')

"""Установим keras и подключим библиотеки"""

!pip install keras-tuner

import os
import random
import numpy as np
import cv2
import keras
import matplotlib.pyplot as plt
from keras.models import Model
from keras.preprocessing.image import ImageDataGenerator, load_img, img_to_array, array_to_img
from keras.callbacks import Callback, ModelCheckpoint, EarlyStopping
from tensorflow.python.keras.models import Sequential
from tensorflow.python.keras.layers import (Activation, Flatten, MaxPooling2D, BatchNormalization, Conv2D, Dense,
                                            DepthwiseConv2D, Dropout, GlobalAveragePooling2D)
from kerastuner.tuners import Hyperband
import IPython
import tensorflow as tf
from google.colab.patches import cv2_imshow
import keras.regularizers as regularizers
from keras.applications import VGG16
from keras.optimizers import Adam

"""Зададим глобальные переменные и директории"""

from google.colab import drive
drive.mount('/content/drive')

os.environ['LAB_ROOT'] = '/content/drive/My Drive/labs/deep_weeds'
!mkdir -p "$LAB_ROOT/images"
OUTPUT_DIRECTORY = "./outputs/"

img_width = 224
img_height = 224
MAX_EPOCH = 1000
batch_size = 256

lab_root = os.getenv('LAB_ROOT')

train_dir = os.path.join(lab_root, 'train')
validation_dir = os.path.join(lab_root, 'validation')
test_dir = os.path.join(lab_root, 'test')

"""Добавим генераторы для тренировки, теста, валидации"""

datagen = ImageDataGenerator(rescale=1./255)

train_generator = datagen.flow_from_directory(
    train_dir,
    target_size=(img_width, img_height),
    batch_size=batch_size,
)
train_generator.class_indices

validation_generator = datagen.flow_from_directory(
    validation_dir,
    target_size=(img_width, img_height),
    batch_size=batch_size,
)

test_generator = datagen.flow_from_directory(
    test_dir,
    target_size=(img_width, img_height),
    batch_size=batch_size,
)

"""Выведем по одному изображению для каждого класса"""

image_dirs = [
              os.path.join(train_dir, '0'),
              os.path.join(train_dir, '1'),
              os.path.join(train_dir, '2'),
              os.path.join(train_dir, '3'),
              os.path.join(train_dir, '4'),
              os.path.join(train_dir, '5'),
              os.path.join(train_dir, '6'),
              os.path.join(train_dir, '7'),
              os.path.join(train_dir, '8'),
]

plt.figure(figsize=[12, 12])
for i, path in enumerate([os.path.join(dir, random.choice(os.listdir(dir))) for dir in image_dirs]):
  plt.subplot(3, 3, i+1)
  plt.title(path.split('/')[-2])
  plt.imshow(load_img(path))
plt.show()

"""За основу модели возьмем предобученную VGG16. Заморозим все обученные слои. Заменим слои вывода."""

base_model = VGG16(
    include_top=False,
    weights='imagenet',
    input_tensor=None,
    input_shape=(224, 224, 3),
    pooling=None,
    classifier_activation="softmax",
)
for layer in base_model.layers:
    layer.trainable = False
x = base_model.output
x = GlobalAveragePooling2D(name='avg_pool')(x)
x = Dense(512, activation='relu', name = 'dense_1')(x)
x = Dense(9, name = 'dense_2')(x)
outputs = Activation(activation='softmax')(x)
model = Model(inputs=base_model.input, outputs=outputs)

"""Добавим сохранение лучшей эпохи и защиту от переобучения"""

callbacks_list = [
    EarlyStopping(monitor='val_accuracy', mode='max',
                  patience=40, 
                  verbose=0),
    ModelCheckpoint(
    os.path.join(lab2_root, 'best_epoch.h5'),
    save_best_only=True,
    monitor='val_accuracy',
    mode='max',
    verbose=2)
]

model.compile(loss='categorical_crossentropy', optimizer='rmsprop', metrics=['accuracy'])

model.summary()

"""Обучим нашу модель"""

history = model.fit(
    train_generator,
    steps_per_epoch=train_generator.n // batch_size,
    validation_data = validation_generator,
    validation_steps=validation_generator.n // batch_size,
    epochs= MAX_EPOCH,
    verbose=1,
    callbacks = callbacks_list
    )

"""Сохраним модель"""

model.save('/content/drive/My Drive/labs/VGG16_model.h5')

model.save_weights('/content/drive/My Drive/labs/VGG16_model_wieghts.h5')

"""Нарисуем графики"""

def draw_graphics(history):
    history = history.history
    loss = history['loss']
    val_loss = history["val_loss"]
    accuracy = history['accuracy']
    val_accuracy = history['val_accuracy']
    epochs = range(1, len(loss) + 1)

    plt.plot(epochs, loss, 'r', label='Training loss')
    plt.plot(epochs, val_loss, 'b', label='Validation loss')
    plt.title('Training and validation loss')
    plt.xlabel('epochs')
    plt.ylabel('loss')
    plt.legend()
    plt.show()

    plt.plot(epochs, accuracy, 'r', label='Training accuracy')
    plt.plot(epochs, val_accuracy, 'b', label='Validation accuracy')
    plt.title('Training and validation accuracy')
    plt.xlabel('epochs')
    plt.ylabel('accuracy')
    plt.legend()
    plt.show()

draw_graphics(history)

"""Проведем тестирование обученной модели"""

def preprocess_image(image):
  return np.expand_dims(img_to_array(image), axis=0) / 255.

image_paths = [os.path.join(dir, random.choice(os.listdir(dir))) for dir in image_dirs * 1]
classes = ['0',
          '1',
          '2',
          '3',
          '4',
          '5',
          '6',
          '7',
          '8']

for path in image_paths:
  out = model.predict(preprocess_image(load_img(path)))[0]
  print(dict(zip(classes,[round(x, 4) for x in out])), path.split('/')[-2])

"""Добавим шумы и протестируем сеть на изображениях с шумом"""

S = 1

def get_normal_noise(image):
  noise = np.random.normal(128, 20, (image.shape[0], image.shape[1]))
  return np.dstack((noise, noise, noise)).astype(np.uint8)

def add_normal_noise(image):
  noise = get_normal_noise(image) * S
  noise_image = cv2.add(image.astype(np.float64), noise.astype(np.float64))
  cv2.normalize(noise_image, noise_image, 0, 255, cv2.NORM_MINMAX)
  return noise_image

def get_uniform_noise(image):
  noise = np.random.uniform(0, 255, (image.shape[0], image.shape[1]))
  return np.dstack((noise, noise, noise)).astype(np.uint8)

def add_uniform_noise(image):
  noise = get_uniform_noise(image) * S
  noise_image = cv2.add(image.astype(np.float64), noise.astype(np.float64))
  cv2.normalize(noise_image, noise_image, 0, 255, cv2.NORM_MINMAX)
  return noise_image

test_generator_with_normal_noise = ImageDataGenerator(rescale=1./255, preprocessing_function=add_normal_noise).flow_from_directory(
    test_dir,
    target_size=(img_width, img_height),
    batch_size=batch_size,
)

test_generator_with_uniform_noise = ImageDataGenerator(rescale=1./255, preprocessing_function=add_uniform_noise).flow_from_directory(
    test_dir,
    target_size=(img_width, img_height),
    batch_size=batch_size,
)

"""Нормальный шум"""

for i, path in zip(list(range(0, 9, 3)),[os.path.join(dir, random.choice(os.listdir(dir))) for dir in image_dirs]):
  image = cv2.resize(cv2.imread(path), (255, 255))
  cv2_imshow(np.concatenate((image, get_normal_noise(image), add_normal_noise(image)), axis=1))

loss, accuracy = model.evaluate(test_generator_with_normal_noise)

"""Равномерный шум"""

for i, path in zip(list(range(0, 9, 3)),[os.path.join(dir, random.choice(os.listdir(dir))) for dir in image_dirs]):
  image = cv2.resize(cv2.imread(path), (250, 250))
  cv2_imshow(np.concatenate((image, get_uniform_noise(image), add_uniform_noise(image)), axis=1))

loss, accuracy = model.evaluate(test_generator_with_uniform_noise)

"""Выведем фильтры входного слоя"""

def draw_layer_filters(layer_index):
  filters, biases = model.layers[layer_index].get_weights()
  print(filters.shape)

  filter_list = [filters[:, :, j, i] for i, j in zip(sorted(list(range(filters.shape[-1])) * filters.shape[-2]), list(range(filters.shape[-2])) * filters.shape[-1])]
  rows = filters.shape[-1] if filters.shape[-1] != 1 else 8
  cols = filters.shape[-2] if filters.shape[-1] != 1 else filters.shape[-2] // 8

  plt.figure(figsize=[100, 100])
  for i in range(len(filter_list)):
    plt.subplot(rows, cols, i+1, xticks=([]), yticks=([]))
    plt.imshow(filter_list[i], cmap='gray')
  plt.show()

draw_layer_filters(1)

def get_feature_maps(original_model, image_tensor, layer_index):
  model = keras.models.Model(inputs=original_model.inputs, outputs=original_model.layers[layer_index].output)
  print(original_model.layers[layer_index].name)
  return model.predict(image_tensor)

def draw_feature_maps(feature_maps):
  plt.figure(figsize=[64, 64])
  for i, feature_map in enumerate([feature_maps[0, :, :, j] for j in range(3)]):
    plt.subplot(8, 8, i+1, xticks=([]), yticks=([]))
    plt.imshow(feature_map, cmap='gray')
  plt.show()

image_path = '/content/drive/My Drive/labs/deep_weeds/test/3/20170811-104056-2.jpg'

image = load_img(image_path)
image_tensor = preprocess_image(image)
plt.imshow(image)

"""Выведем карты признаков для нескольких слоев"""

blocks = []
for i, layer in enumerate(model.layers):
  if 'conv' in layer.name:
      blocks.append(i)
for i in blocks:
  feature_maps = get_feature_maps(model, image_tensor, i)
  draw_feature_maps(feature_maps)