import os
import cv2
import numpy as np
from os import listdir
from os.path import isfile, join
from tensorflow.keras.applications.mobilenet import MobileNet
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout, Activation, Flatten, GlobalAveragePooling2D
from tensorflow.keras.layers import Conv2D, MaxPooling2D, ZeroPadding2D
from tensorflow.keras.layers import BatchNormalization
from tensorflow.keras.models import Model
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.optimizers import RMSprop
from tensorflow.keras.callbacks import ModelCheckpoint, EarlyStopping
from tensorflow.keras.models import load_model

# MobileNet works on 224 x 224 pixel input images sizes
img_rows, img_cols = 224, 224 

# Re-loads the MobileNet model without the top or FC layers
MobileNet = MobileNet(weights = 'imagenet', 
                 include_top = False, 
                 input_shape = (img_rows, img_cols, 3))

for layer in MobileNet.layers:
    layer.trainable = False
    

# Print the layers 
for (i,layer) in enumerate(MobileNet.layers):
    print(str(i) + " "+ layer.__class__.__name__, layer.trainable)

def lw(bottom_model, num_classes):
    """creates the top or head of the model that will be 
    placed ontop of the bottom layers"""

    top_model = bottom_model.output
    top_model = GlobalAveragePooling2D()(top_model)
    top_model = Dense(1024,activation='relu')(top_model)
    top_model = Dense(1024,activation='relu')(top_model)
    top_model = Dense(512,activation='relu')(top_model)
    top_model = Dense(num_classes,activation='softmax')(top_model)
    return top_model

# Set the class number to 5
num_classes = 5

FC_Head = lw(MobileNet, num_classes)

model = Model(inputs = MobileNet.input, outputs = FC_Head)

print(model.summary())

train_data_dir = '/home/pi/Desktop/Face_Recognition/train/'
validation_data_dir = '/home/pi/Desktop/Face_Recognition/validation/'

train_datagen = ImageDataGenerator(
      rescale=1./255,
      rotation_range=45,
      width_shift_range=0.3,
      height_shift_range=0.3,
      horizontal_flip=True,
      fill_mode='nearest')
 
validation_datagen = ImageDataGenerator(rescale=1./255)
 
# Set the batch size 
batch_size = 5
 
train_generator = train_datagen.flow_from_directory(
        train_data_dir,
        target_size=(img_rows, img_cols),
        batch_size=batch_size,
        class_mode='categorical')
 
validation_generator = validation_datagen.flow_from_directory(
        validation_data_dir,
        target_size=(img_rows, img_cols),
        batch_size=batch_size,
        class_mode='categorical')
                     
checkpoint = ModelCheckpoint("Facial_recogNet.h5",
                             monitor="val_loss", 
                             mode="min",
                             save_best_only = True,
                             verbose=1)

earlystop = EarlyStopping(monitor = 'val_loss', 
                          min_delta = 0, 
                          patience = 30,   
                          verbose = 1,
                          restore_best_weights = True)

# The callbacks are put into a callback list
callbacks = [earlystop, checkpoint]

# Set a small learning rate 
model.compile(loss = 'categorical_crossentropy',
              optimizer = RMSprop(lr = 0.0001), #initial 0.001
              metrics = ['accuracy'])

# Set the number of training and validation samples 
nb_train_samples = 35
nb_validation_samples = 10

# Set the number of epochs
epochs = 60
batch_size = 5

history = model.fit_generator(
    train_generator,
    steps_per_epoch = nb_train_samples // batch_size,
    epochs = epochs,
    callbacks = callbacks,
    validation_data = validation_generator,
    validation_steps = nb_validation_samples // batch_size)

classifier = load_model('Facial_recogNet.h5')

# Mexican People Face Recognition
facial_recog_dict = {"[0]": "1_Salma Hayek",
                     "[1]": "2_Chicarito Hernandez",
                     "[2]": "3_Carlos Slim",
                     "[3]": "4_Guillermo del Toro",
                     "[4]": "5_Oscar De La Hoya"}

facial_recog_dict_n = {"Chicarito Hernandez": "2_Chicarito Hernandez",
                       "Guillermo del Toro": "4_Guillermo del Toro",
                       "Salma Hayek": "1_Salma Hayek",
                       "Oscar De La Hoya": "5_Oscar De La Hoya",
                       "Carlos Slim": "3_Carlos Slim"}

def draw_test(name, pred, im):
    facial = facial_recog_dict[str(pred)]
    BLACK = [0,0,0]
    expanded_image = cv2.copyMakeBorder(im, 80, 0, 0, 100 ,cv2.BORDER_CONSTANT,value=BLACK)
    cv2.putText(expanded_image, facial, (20, 60) , cv2.FONT_HERSHEY_SIMPLEX,1, (0,0,255), 2)
    cv2.imshow(name, expanded_image)

def getRandomImage(path):
    """function loads a random images from a random folder in our test path """
    folders = list(filter(lambda x: os.path.isdir(os.path.join(path, x)), os.listdir(path)))
    random_directory = np.random.randint(0,len(folders))
    path_class = folders[random_directory]
    print("Class - " + facial_recog_dict_n[str(path_class)])
    file_path = path + path_class
    file_names = [f for f in listdir(file_path) if isfile(join(file_path, f))]
    random_file_index = np.random.randint(0,len(file_names))
    image_name = file_names[random_file_index]
    return cv2.imread(file_path+"/"+image_name)    

'''
probability_images_dictionary = {}
for class_item in range(0, 5):
    dir_path = "validation/"+facial_recog_dict["[{}]".format(class_item)]
    for image_index in range (1,3):
        print(dir_path+"/{}.jpg".format(image_index))
        input_im = cv2.imread(dir_path+"/{}.jpg".format(image_index))
        
        input_original = input_im.copy()
        input_original = cv2.resize(input_original, None, fx=0.5, fy=0.5, interpolation=cv2.INTER_LINEAR)
        input_im = cv2.resize(input_im, (224,224), interpolation = cv2.INTER_LINEAR)
        input_im = input_im /255.
        input_im = input_im.reshape(1,224,224,3)
        
        result_array = classifier.predict(input_im,1,verbose=0)
        # Get Prediction
        result = np.argmax(result_array, axis=1)

        input_original = cv2.resize(input_original, (224,224), interpolation = cv2.INTER_LINEAR)
        draw_test("Prediction", result, input_original)
        
        probability_images_dictionary = {}
        for train_classes in range(0, 5):
            file_path = "train/"+facial_recog_dict["[{}]".format(train_classes)]
            
            for j in range (1,8):
                train_image = cv2.imread(file_path+"/{}".format(j)+".jpg")
                train_image = cv2.resize(train_image, (224,224), interpolation = cv2.INTER_LINEAR)
                train_image = input_im /255.
                train_image = input_im.reshape(1,224,224,3)
            
                results = classifier.predict(train_image,1,verbose=0)
                norm = np.linalg.norm(results)
                results = results/norm;
                probability_images_dictionary[results[0][result[0]]] = file_path+"/{}".format(j)+".jpg"
            
        index = 0
        print(probability_images_dictionary)
        for key in sorted(probability_images_dictionary.keys(), reverse = True):
            index = index+1
            image = cv2.imread(probability_images_dictionary[key])
            image = cv2.resize(image, (224,224), interpolation = cv2.INTER_LINEAR)
            cv2.imshow("{} - Result {}".format(facial_recog_dict[str(result)],index),image)
            if index > 2:
                break
        cv2.waitKey(0)  
        cv2.destroyAllWindows()      
        
'''
# Iterate through each validation images
probability_images_dictionary = {}
for class_item in range(0, 5):
    dir_path = "validation/"+facial_recog_dict["[{}]".format(class_item)]
    for image_index in range (1,3):
        print(dir_path+"/{}.jpg".format(image_index))
        input_im = cv2.imread(dir_path+"/{}.jpg".format(image_index))
        
        input_original = input_im.copy()
        input_original = cv2.resize(input_original, None, fx=0.5, fy=0.5, interpolation=cv2.INTER_LINEAR)
        input_im = cv2.resize(input_im, (224,224), interpolation = cv2.INTER_LINEAR)
        input_im = input_im /255.
        input_im = input_im.reshape(1,224,224,3)
        
        result_array = classifier.predict(input_im,1,verbose=0)
        # Get the predictions
        result = np.argmax(result_array, axis=1)

        input_original = cv2.resize(input_original, (224,224), interpolation = cv2.INTER_LINEAR)
        draw_test("Prediction", result, input_original)
        
        probability_images_dictionary = {}
        for train_classes in range(0, 5):
            file_path = "train/"+facial_recog_dict["[{}]".format(train_classes)]
            
            for j in range (1,8):
                train_image = cv2.imread(file_path+"/{}".format(j)+".jpg")
                train_image = cv2.resize(train_image, (224,224), interpolation = cv2.INTER_LINEAR)
                train_image = input_im /255.
                train_image = input_im.reshape(1,224,224,3)
            
                results = classifier.predict(train_image,1,verbose=0)
                norm = np.linalg.norm(results)
                results = results/norm;
                probability_images_dictionary[results[0][result[0]]] = file_path+"/{}".format(j)+".jpg"
        cv2.waitKey(0)  
        cv2.destroyAllWindows()            
'''                
for i in range(0,10):
    input_im = getRandomImage("/home/pi/Desktop/Face_Recognition/validation/")
    input_original = input_im.copy()
    input_original = cv2.resize(input_original, None, fx=0.5, fy=0.5, interpolation = cv2.INTER_LINEAR)
    
    input_im = cv2.resize(input_im, (224, 224), interpolation = cv2.INTER_LINEAR)
    input_im = input_im / 255.
    input_im = input_im.reshape(1,224,224,3) 
    
    # Get Prediction
    res = np.argmax(classifier.predict(input_im, 1, verbose = 0), axis=1)
    
    # Show image with predicted class
    draw_test("Prediction", res, input_original)
    cv2.waitKey(0)

cv2.destroyAllWindows()
'''
