# -*- coding: utf-8 -*-
"""Copy of SVM.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/17W7JwY9EyDaTfrCTwFYNWKeSFKz8i-jd
"""

+from google.colab import drive
drive.mount('/content/drive')

import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import glob
import cv2
import os
import sklearn
import pandas as pd
import xgboost
from skimage import io, filters, feature
from skimage.filters import sobel
from skimage.feature import greycomatrix, greycoprops
from skimage.measure import shannon_entropy
from sklearn import preprocessing
from sklearn import svm
from sklearn import metrics
from sklearn.model_selection import KFold
from sklearn.model_selection import cross_val_score, cross_validate
from sklearn.metrics import confusion_matrix
from sklearn.metrics import classification_report
import random
from sklearn import preprocessing
from sklearn.model_selection import StratifiedKFold

"""# New section"""

SIZE = 128
#creating empty lists.
train_images = []
train_labels = []

for directory_path in glob.glob('/content/drive/MyDrive/Images/plant-growth-estimator-for-hydroponics-main/half F/canola_training/training/*'):
    label = directory_path.split("/")[-1]
    #print(label)
    for img_path in glob.glob(os.path.join(directory_path, "*.bmp")):
        #print(img_path)
        orig_img   = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)

        orig_img   =cv2.resize(orig_img, (SIZE, SIZE))

        train_images.append(orig_img)
        train_labels.append(label)

train_images = np.array(train_images)
train_labels = np.array(train_labels)

#Testing images into a list
test_images = []
test_labels = []

for directory_path in glob.glob('/content/drive/MyDrive/Images/plant-growth-estimator-for-hydroponics-main/half F/canola_test/test/*'):
    label = directory_path.split("/")[-1]
    #print(label)
    for img_path in glob.glob(os.path.join(directory_path, "*.bmp")):
        #print(img_path)
        orig_img   = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
        orig_img   =cv2.resize(orig_img, (SIZE, SIZE))
        #orig_img = cv2.cvtColor(orig_img, cv2.COLOR_RGB2BGR)
        test_images.append(orig_img)
        test_labels.append(label)

test_images = np.array(test_images)
test_labels  = np.array(test_labels)

from sklearn import preprocessing
#label encorder
le = preprocessing.LabelEncoder()
le.fit(test_labels)
test_labels_encoded = le.transform(test_labels)
le.fit(train_labels)
train_labels_encoded = le.transform(train_labels)

#Assigning the dataset into meaningful convention
x_train, y_train, x_test, y_test = train_images, train_labels_encoded, test_images, test_labels_encoded

x_train, x_test = x_train / 255.0, x_test / 255.0

def feature_extractor(dataset):
    x_train = dataset
    image_dataset = pd.DataFrame()
    for image in range(x_train.shape[0]):  #iterate through each image

        df = pd.DataFrame()  #Store the feature information itno a temporary data frame

        input_img = x_train[image, :,:]
        img = input_img
        pixel_values = img.reshape(-1)
        df['Pixel_Value'] = pixel_values   #The first feature is the pixel value

        # FEATURE 2 - Gabor filter responses
        #Generating Gabor kernels
        num = 1  #Starting a counter to give Gabor features a lable in the data frame
        kernels = []
        for theta in range(4):   #Defining the number of thetas
            theta = theta / 4. * np.pi
            for lamda in np.arange(np.pi/10, np.pi / 8):   #Range of wavelengths
                gamma = 0.5
                sigma = 0.5
                #phi = 0
                gabor_label = 'Gabor' + str(num)  #Label Gabor columns as Gabor1, Gabor2, etc.
                ksize=9
                kernel = cv2.getGaborKernel((ksize, ksize), sigma, theta, lamda, gamma, 0, ktype=cv2.CV_32F)
                kernels.append(kernel)
                #filtering the image and adding values to a new column
                fimg = cv2.filter2D(img, cv2.CV_8UC3, kernel)
                filtered_img = fimg.reshape(-1)
                df[gabor_label] = filtered_img  #Labeling columns as Gabor1, Gabor2,Gabor3, and Gabor4
                #print(gabor_label, ': theta=', theta, ': sigma=', sigma, ': lamda=', lamda, ': gamma=', gamma)
                num += 1  #Increment for gabor column label

        # FEATURE 3 Sobel
        edge_sobel = sobel(img)
        edge_sobel1 = edge_sobel.reshape(-1)
        df['Sobel'] = edge_sobel1

        image_dataset = image_dataset.append(df)

    return image_dataset

#Starting and timing the Feature extraction using the Feature extractor defined in the feature extraction stage
def timer(start_time=None):
    if not start_time:
        start_time = datetime.now()
        return start_time
    elif start_time:
        thour, temp_sec = divmod((datetime.now() - start_time).total_seconds(), 3600)
        tmin, tsec = divmod(temp_sec, 60)
        print('\n Time taken: %i hours %i minutes and %s seconds.' % (thour, tmin, round(tsec, 2)))

from datetime import datetime
start_time = timer(None) # timing starts
image_features = feature_extractor(x_train)
timer(start_time) # timing ends

#Checking of NaN in the features
np.isnan(image_features)
np.where(np.isnan(image_features))
np.nan_to_num(image_features)

#Reshaping image features to a vector for SVM
n_features = image_features.shape[1]
image_features = np.expand_dims(image_features, axis=0)
X_for_SVM = np.reshape(image_features, (x_train.shape[0], -1))  #Reshape to #images, features

#Classifier
SVM_model= svm.SVC(kernel='rbf', random_state=1, gamma=0.00001, C=32)

#CROSS VALIDATION ON TRAINING DATASET X_for_SVM
X = X_for_SVM
y= train_labels

classifier=SVM_model

# Capturing the fitting time
start_time = timer(None) # timing starts
classifier.fit(X_for_SVM, train_labels)
timer(start_time) # timing ends


# Capturing the cross validation time (Traning)
start_time = timer(None)
n_splits = 3
kf = StratifiedKFold(n_splits=n_splits, shuffle=True)
# Print Accuracy, Confusion Matrix, Classification Report
for train_index, val_index in kf.split(X_for_SVM, y):
    classifier.fit(X_for_SVM[train_index], y[train_index])
    train_prediction = classifier.predict(X_for_SVM[val_index])
    #train_prediction = le.inverse_transform(train_prediction)
    print ("Accuracy = ", metrics.accuracy_score(y[val_index], train_prediction))
    print(confusion_matrix(y[val_index], train_prediction))
    print(classification_report(y[val_index], train_prediction))
timer(start_time) # timing ends

#Predict on Test images

#Extracting features from test set and reshape
start_time = timer(None) # timing starts
test_features = feature_extractor(x_test)
test_features = np.expand_dims(test_features, axis=0)
test_for_SVM = np.reshape(test_features, (x_test.shape[0], -1))
timer(start_time) # timing ends

np.isnan(test_for_SVM)
c=np.where(~np.isnan(test_for_SVM), test_for_SVM, 0)

#Predict on test
start_time = timer(None)
test_prediction = classifier.predict(test_for_SVM)
timer(start_time) # timing ends
#Overall accuracy without cross validation
print ("Accuracy = ", metrics.accuracy_score(test_labels, test_prediction))

#Predicting on the whole TEST SET
X = test_for_SVM
y= test_labels

start_time = timer(None)
n_splits = 3
kf = StratifiedKFold(n_splits=n_splits, shuffle=True)
# Printing Accuracy, Confusion Matrix, Classification Report
for test_index, vali_index in kf.split(test_for_SVM, y):
    #classifier.fit(test_for_SVM[test_index], y[test_index])
    test_prediction = classifier.predict(test_for_SVM[vali_index])
    #train_prediction = le.inverse_transform(train_prediction)
    print ("Accuracy = ", metrics.accuracy_score(y[vali_index], test_prediction))
    print(confusion_matrix(y[vali_index], test_prediction))
    print(classification_report(y[vali_index], test_prediction))
timer(start_time) # timing ends

#Check prediction on random images
start_time = timer(None)
n=random.randint(0, x_test.shape[0]-1) #Selecting the index of image to be loaded for testing
img = x_test[n]
plt.imshow(img)

#Extracting features and reshape to the right dimensions
input_img = np.expand_dims(img, axis=0) #Expanding dimensions so the input is (num images, x, y, c)
input_img_features=feature_extractor(input_img)
input_img_features = np.expand_dims(input_img_features, axis=0)
input_img_for_SVM = np.reshape(input_img_features, (input_img.shape[0], -1))
prediction_SVM = classifier.predict(input_img_for_SVM)
print("The prediction for this image is: ", prediction_SVM)
print("The actual label for this image is: ", test_labels[n])
timer(start_time) # timing ends