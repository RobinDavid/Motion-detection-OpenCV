import cv2.cv as cv
from datetime import datetime
import time

class MotionDetector():
    
    def onChange(self, val): #callback when the user change the ceil
        self.ceil = val
    
    def __init__(self,ceil=8, doRecord=True, showWindows=True):
        self.writer = None
        self.font = None
        self.doRecord=doRecord #Either or not record the moving object
        self.show = showWindows #Either or not show the 2 windows
        self.frame = None
    
        self.capture=cv.CaptureFromCAM(0)
        self.frame = cv.QueryFrame(self.capture) #Take a frame to init recorder
        if doRecord:
            self.initRecorder()
        
        self.frame1gray = cv.CreateMat(self.frame.height, self.frame.width, cv.CV_8U) #Gray frame at t-1
        cv.CvtColor(self.frame, self.frame1gray, cv.CV_RGB2GRAY)
        
        #Will hold the thresholded result
        self.res = cv.CreateMat(self.frame.height, self.frame.width, cv.CV_8U)
        
        self.frame2gray = cv.CreateMat(self.frame.height, self.frame.width, cv.CV_8U) #Gray frame at t
        
        self.width = self.frame.width
        self.height = self.frame.height
        self.nb_pixels = self.width * self.height
        self.ceil = ceil
        self.isRecording = False
        self.trigger_time = 0 #Hold timestamp of the last detection
        
        if showWindows:
            cv.NamedWindow("Image")
            cv.CreateTrackbar("Mytrack", "Image", self.ceil, 100, self.onChange)
        
    def initRecorder(self): #Create the recorder
        codec = cv.CV_FOURCC('D', 'I', 'V', 'X')
        #codec = cv.CV_FOURCC("D", "I", "B", " ")
        self.writer=cv.CreateVideoWriter(datetime.now().strftime("%b-%d_%H:%M:%S")+".avi", codec, 15, cv.GetSize(self.frame), 1)
        #FPS set at 15 because it seems to be the fps of my cam but should be ajusted to your needs
        self.font = cv.InitFont(cv.CV_FONT_HERSHEY_SIMPLEX, 1, 1, 0, 2, 8) #Creates a font

    def run(self):
        started = time.time()
        while True:
            
            curframe = cv.QueryFrame(self.capture)
            instant = time.time() #Get timestamp o the frame
            
            self.processImage(curframe) #Process the image
            
            if not self.isRecording:
                if self.somethingHasMoved():
                    self.trigger_time = instant #Update the trigger_time
                    if instant > started +5:#Wait 5 second after the webcam start for luminosity adjusting etc..
                        print "Something is moving !"
                        if self.doRecord: #set isRecording=True only if we record a video
                            self.isRecording = True
            else:
                if instant >= self.trigger_time +10: #Record during 10 seconds
                    print "Stop recording"
                    self.isRecording = False
                else:
                    cv.PutText(curframe,datetime.now().strftime("%b %d, %H:%M:%S"), (25,30),self.font, 0) #Put date on the frame
                    cv.WriteFrame(self.writer, curframe) #Write the frame
            
            if self.show:
                cv.ShowImage("Image", curframe)
                cv.ShowImage("Res", self.res)
                
            cv.Copy(self.frame2gray, self.frame1gray)
            c=cv.WaitKey(1)
            if c==27 or c == 1048603: #Break if user enters 'Esc'.
                break            
    
    def processImage(self, frame):
        cv.CvtColor(frame, self.frame2gray, cv.CV_RGB2GRAY)
        
        #Absdiff to get the difference between to the frames
        cv.AbsDiff(self.frame1gray, self.frame2gray, self.res)
        
        #Remove the noise and do the threshold
        cv.Smooth(self.res, self.res, cv.CV_BLUR, 5,5)
        element = cv.CreateStructuringElementEx(5*2+1, 5*2+1, 5, 5,  cv.CV_SHAPE_RECT)
        cv.MorphologyEx(self.res, self.res, None, None, cv.CV_MOP_OPEN)
        cv.MorphologyEx(self.res, self.res, None, None, cv.CV_MOP_CLOSE)
        cv.Threshold(self.res, self.res, 10, 255, cv.CV_THRESH_BINARY_INV)

    def somethingHasMoved(self):
        nb=0 #Will hold the number of black pixels

        for y in range(self.height): #Iterate the hole image
            for x in range(self.width):
                if self.res[y,x] == 0.0: #If the pixel is black keep it
                    nb += 1
        avg = (nb*100.0)/self.nb_pixels #Calculate the average of black pixel in the image
        #print "Average: ",avg, "%\r",
        if avg > self.ceil:#If over the ceil trigger the alarm
            return True
        else:
            return False
        
if __name__=="__main__":
    detect = MotionDetector(doRecord=False)
    detect.run()