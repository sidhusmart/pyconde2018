import time
import struct
import numpy as np
import os

from pynput import keyboard

import actionCNN as myNN
import time

import pyscreenshot as ImageGrab
from pykeyboard import PyKeyboard
from PIL import Image

from selenium import webdriver

# Object that is used to capture the screenshot
class ScreenCapture(object):

    numOfSamples = 300
    # The Snapshot Region size is hard coded, please change it
    # based on the setting of your display window.
    # It actually took a bit of trial and error t arrive the bbox
    # in my case - should be a way to automate

    def __init__(self, x1, y1, x2, y2, folderPath):
        self.X1 = x1
        self.Y1 = y1
        self.X2 = x2
        self.Y2 = y2
        self.folderPath = folderPath
    
    def capture(self):

        im=ImageGrab.grab(bbox=(self.X1,self.Y1,self.X2,self.Y2))

        if im.width % 2 > 0:
            # Capture region should be even sized else
            # you will see wrongly strided images i.e corrupted
            emsg = "Capture region width should be even (was %s)" % (region.size.width)
            raise ValueError(emsg)
           
        # Get width/height of image
        self.width = im.width
        self.height = im.height

        return im

    def saveROIImg(self, name, img, counter):
        if counter <= self.numOfSamples:
            counter = counter + 1
            name = name + str(counter)
            print ("Saving img:",name)
        img.save(self.folderPath + name + ".png")
    
        return counter

# Globals
isEscape = False
sp = ScreenCapture(380, 150, 800, 300, './imgfolder-201810201450/')
counter1 = 0
counter2 = 0
banner =  '''\nWhat would you like to do ?
    1- Use pretrained model for gesture recognition & layer visualization
    2- Train the model (you will require image samples for training under .\imgfolder)
    3- Generate training image samples. Note: You need to be in 'sudo' i.e admin mode.
    '''


# This function gets called when user presses any keyboard key
def on_press(key):
    global isEscape, sp, counter1, counter2
    
    # Pressing 'UP arrow key' will initiate saving provided capture region images
    if key == keyboard.Key.up:
        img = sp.capture()
        counter1 = sp.saveROIImg("jump", img, counter1)
    
    # Pressing 'Right arrow key' will initiate saving provided capture region images
    if key == keyboard.Key.right:
        img = sp.capture()
        counter2 = sp.saveROIImg("nojump", img, counter2)

# This function gets called when user releases the keyboard key previously pressed
def on_release(key):
    global isEscape, sp, counter1
    if key == keyboard.Key.esc:
        isEscape = True
        # Stop listener
        return False

# This function keeps listening for any keyboard input and takes actions defined in on_press/on_releast functions
def listen():

    global isEscape, sp, counter1, counter2

    driver = webdriver.Chrome('/home/sidharth/Downloads/ChromeDriver/chromedriver')
    driver.maximize_window()
    driver.get('http://www.google.com/')
    time.sleep(5) # Let the user actually see something!

    outer_width = driver.execute_script("return screen.width")
    outer_height = driver.execute_script("return screen.height")
    print (outer_width, outer_height)

    inner_height = driver.execute_script("return window.innerHeight")
    inner_width = driver.execute_script("return window.innerWidth")
    print (inner_width, inner_height)

    element = driver.find_element_by_xpath("/html/body/div[1]/div[4]/canvas[1]")
    location = element.location
    size = element.size
    titleBarSize = outer_height - inner_height
    print (titleBarSize)

    X1 = location['x']
    Y1 = location['y']+titleBarSize
    X2 = location['x']+size['width']
    Y2 = location['y']+size['height']+titleBarSize

    print (X1, Y1, X2, Y2)

    sp = ScreenCapture(X1, Y1, X2, Y2, './imgfolder-201810201450/')

    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()

    driver.quit()

# This functions is used to actually play the game by reading in image from the browser
# and asking the Neural Network what the action should be 
# and passing this action to the browser
def playGame(mod):

    guess = True

    global isEscape, sp, counter1, counter2

    driver = webdriver.Chrome('/home/sidharth/Downloads/ChromeDriver/chromedriver')
    driver.maximize_window()
    driver.get('http://www.google.com/')
    time.sleep(5)

    outer_width = driver.execute_script("return screen.width")
    outer_height = driver.execute_script("return screen.height")
    print (outer_width, outer_height)

    inner_height = driver.execute_script("return window.innerHeight")
    inner_width = driver.execute_script("return window.innerWidth")
    print (inner_width, inner_height)

    element = driver.find_element_by_xpath("/html/body/div[1]/div[4]/canvas[1]")
    location = element.location
    size = element.size
    titleBarSize = outer_height - inner_height
    print (titleBarSize)

    X1 = location['x']
    Y1 = location['y']+titleBarSize
    X2 = location['x']+size['width']
    Y2 = location['y']+size['height']+titleBarSize

    print (X1, Y1, X2, Y2)

    sp = ScreenCapture(X1, Y1, X2, Y2, './imgfolder-201810201450/')
    print ("The program will start the game play in 5 seconds, please ALT-TAB to your offline Chrome window")
    time.sleep(15)

    ## Pressing the UP arrow key to start the T-Rex
    k = PyKeyboard()
    k.tap_key(k.up_key)
    counter3 = 0

    ## Now you need to start capturing the images based on which predictions will be made
    while guess:

        img = sp.capture()
        counter3 = sp.saveROIImg("test", img, counter3)
        imgData = np.array((img.resize((myNN.img_rows,myNN.img_cols))).convert('L')).flatten()
        
        #imgData = np.asarray(img)
        # r, g, b = cv2.split(imgData)
        # inputData = cv2.merge([b, g, r])

        if myNN.img_channels == 1:
            #image = cv2.cvtColor(inputData, cv2.COLOR_BGR2GRAY)

            # Resize as per our need
            # rimage = cv2.resize(imgData, (myNN.img_rows, myNN.img_cols))
            retvalue = myNN.guessAction(mod, imgData)
            print (str(retvalue) + ' ' + str(counter3))

            ## If the NN says that jump is required then send jump command
            if retvalue == 0:
                k.tap_key(k.up_key)
            else:
                ## Adding a small delay to actual key press - this seemed to work better to coordinate actions
                ## Though I did have some trouble with some intermediate images
                #time.sleep(0.35)
                continue



def main():
    global sp
 
    guess = False
    lastAction = -1
    mod = 0

    #Call CNN model loading callback
    while True:
        ans = int(input( banner))
        if ans == 1:
            # Possible to load multiple model parameters, right now using only the one I trained
            mod = myNN.loadCNN(1) 
            playGame(mod)
        elif ans == 2:
            mod = myNN.loadCNN(1)
            myNN.trainModel(mod)
            input("Press any key to continue")
            break
        elif ans == 3:
            listen()
            break
        else:
            print ("Get out of here!!!")
            return 0

if __name__ == '__main__':
    main()



