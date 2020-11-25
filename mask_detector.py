# import the necessary packages
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.layers import AveragePooling2D
from tensorflow.keras.layers import Dropout
from tensorflow.keras.layers import Flatten
from tensorflow.keras.layers import Dense
from tensorflow.keras.layers import Input
from tensorflow.keras.models import Model
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input
from tensorflow.keras.preprocessing.image import img_to_array
from tensorflow.keras.preprocessing.image import load_img
from tensorflow.keras.utils import to_categorical
from sklearn.preprocessing import LabelBinarizer
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
from imutils import paths
import matplotlib.pyplot as plt
import numpy as np
import os

# initialize the initial learning rate, number of epochs to train for,
# and batch size
INIT_LR = 1e-4 #initial Learning rate make sure learning rate is less your loss will be calculated properly which means u will get the better accuracy soon 0.0001
EPOCHS = 20
BS = 32 #batch size

DIRECTORY = r"D:\Projects\Data Sciences\Mask Dedection on Face\Face-Mask-Detection-master\dataset"
CATEGORIES = ["with_mask", "without_mask"]

# grab the list of images in our dataset directory, then initialize
# the list of data (i.e., images) and class images
print("[INFO] loading images...")

data = []
labels = []

for category in CATEGORIES:
    path = os.path.join(DIRECTORY, category)
    for img in os.listdir(path):
    	img_path = os.path.join(path, img)
    	image = load_img(img_path, target_size=(224, 224)) #coming from keras.preprocessing (224,224) is the size of the image
    	image = img_to_array(image)
    	image = preprocess_input(image) #it is used in mobilenets we have to use this preprocessinput

    	data.append(image) #images in Data
    	labels.append(category) #their category in labels

# perform one-hot encoding on the labels
lb = LabelBinarizer() #coming from sklearn.preprocessing
labels = lb.fit_transform(labels)
labels = to_categorical(labels) 

#right now our dataand labels are list we have to convert them to array
data = np.array(data, dtype="float32")
labels = np.array(labels)

(trainX, testX, trainY, testY) = train_test_split(data, labels,
	test_size=0.20, stratify=labels, random_state=42)

#mobile Nets Tend to be less Accurate when compared to others
#but it faster 

# construct the training image generator for data augmentation
#it create it many images with a single image by changing some of the properties rotating fliping 
aug = ImageDataGenerator(
	rotation_range=20,
	zoom_range=0.15,
	width_shift_range=0.2,
	height_shift_range=0.2,
	shear_range=0.15,
	horizontal_flip=True,
	fill_mode="nearest")

# load the MobileNetV2 network, ensuring the head FC layer sets are
# left off
#there are some pretrained model for which weights are already assigned so we gonna use imagenet here which will give us better result
baseModel = MobileNetV2(weights="imagenet", include_top=False, #include_top we will connect the fully connected top layer by ourselves thats why we have set it to false
	input_tensor=Input(shape=(224, 224, 3))) #shape of the image going thorugh

# construct the head of the model that will be placed on top of the
# the base model
headModel = baseModel.output
headModel = AveragePooling2D(pool_size=(7, 7))(headModel)
headModel = Flatten(name="flatten")(headModel)
headModel = Dense(128, activation="relu")(headModel) #goto activation fucntion 'relu' whenver u deal with images
headModel = Dropout(0.5)(headModel) #using dropout to avoid overfitting of our models
#our output is 2 layers one with mask one without max
headModel = Dense(2, activation="softmax")(headModel) #since we are dealing with binary classification,As they are probability based fucntions


# place the head FC model on top of the base model (this will become
# the actual model we will train)
model = Model(inputs=baseModel.input, outputs=headModel)

# loop over all layers in the base model and freeze them so they will
# *not* be updated during the first training process
for layer in baseModel.layers:
	layer.trainable = False
#here we are giving the inital learning model for our model 
# compile our model
print("[INFO] compiling model...")
opt = Adam(lr=INIT_LR, decay=INIT_LR / EPOCHS)#it is the go to optimiser for any image prediction
model.compile(loss="binary_crossentropy", optimizer=opt, 
	metrics=["accuracy"]) #accuracy metric is the only metric we are going to track for

#fit the model
# train the head of the network
print("[INFO] training head...")
H = model.fit(
	aug.flow(trainX, trainY, batch_size=BS), #imageDatagenerator is flowing here so that we get more data here as we have less images to work with
	steps_per_epoch=len(trainX) // BS,
	validation_data=(testX, testY), #for validation we will be using testX,Testy
	validation_steps=len(testX) // BS,
	epochs=EPOCHS)

# make predictions on the testing set
# We are going to evaluate our network by model.predict method
print("[INFO] evaluating network...")
predIdxs = model.predict(testX, batch_size=BS)

# for each image in the testing set we need to find the index of the
# label with corresponding largest predicted probability
predIdxs = np.argmax(predIdxs, axis=1)

# show a nicely formatted classification report
print(classification_report(testY.argmax(axis=1), predIdxs,
	target_names=lb.classes_))

# serialize the model to disk
print("[INFO] saving mask detector model...")
model.save("mask_detector.model", save_format="h5") #saving the model with h5 format

# plot the training loss and accuracy
N = EPOCHS
plt.style.use("ggplot")
plt.figure()
plt.plot(np.arange(0, N), H.history["loss"], label="train_loss")
plt.plot(np.arange(0, N), H.history["val_loss"], label="val_loss")
plt.plot(np.arange(0, N), H.history["accuracy"], label="train_acc")
plt.plot(np.arange(0, N), H.history["val_accuracy"], label="val_acc")
plt.title("Training Loss and Accuracy")
plt.xlabel("Epoch #")
plt.ylabel("Loss/Accuracy")
plt.legend(loc="lower left")
plt.savefig("plot.png")