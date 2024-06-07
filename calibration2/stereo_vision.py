


import sys
import cv2
import numpy as np
import time
import imutils
from matplotlib import pyplot as plt
from picamera2 import Picamera2

# Function for stereo vision and depth estimation
import disparitymap as dismap
import triangulation as tri
import imageprocessor as calibration

# Mediapipe for face detection
import mediapipe as mp
import time

mp_facedetector = mp.solutions.face_detection
mp_draw = mp.solutions.drawing_utils

# Open both cameras
cap_right = Picamera2(1)                 
cap_left =  Picamera2(0)

cap_right.start()
cap_left.start()


# Stereo vision setup parameters
frame_rate = 120    #Camera frame rate (maximum at 120 fps)
B = 6               #Distance between the cameras [cm]
f = 2.6             #Camera lense's focal length [mm]
alpha = 70        #Camera field of view in the horisontal plane [degrees]




# Main program loop with face detector and depth estimation using stereo vision
with mp_facedetector.FaceDetection(min_detection_confidence=0.7) as face_detection:

    while True:

        frame_right = cap_right.capture_array()
        frame_left = cap_left.capture_array()

    ################## CALIBRATION #########################################################

        frame_right, frame_left = calibration.undistortRectify(frame_right, frame_left)

    ########################################################################################
        
        
        # If cannot catch any frame, break
        if frame_right is None or frame_left is None:                    
            break

        else:

            start = time.time()
            
            # Convert the BGR image to RGB
            frame_right = cv2.cvtColor(frame_right, cv2.COLOR_BGR2RGB)
            frame_left = cv2.cvtColor(frame_left, cv2.COLOR_BGR2RGB)

            # Process the image and find faces
            results_right = face_detection.process(frame_right)
            results_left = face_detection.process(frame_left)

            # Convert the RGB image to BGR
            frame_right = cv2.cvtColor(frame_right, cv2.COLOR_RGB2BGR)
            frame_left = cv2.cvtColor(frame_left, cv2.COLOR_RGB2BGR)


            ################## CALCULATING DEPTH #########################################################

            center_right = 0
            center_left = 0

            if results_right.detections:
                for id, detection in enumerate(results_right.detections):
                    mp_draw.draw_detection(frame_right, detection)

                    bBox = detection.location_data.relative_bounding_box

                    h, w, c = frame_right.shape

                    boundBox = int(bBox.xmin * w), int(bBox.ymin * h), int(bBox.width * w), int(bBox.height * h)

                    center_point_right = (boundBox[0] + boundBox[2] / 2, boundBox[1] + boundBox[3] / 2)

                    cv2.putText(frame_right, f'{int(detection.score[0]*100)}%', (boundBox[0], boundBox[1] - 20), cv2.FONT_HERSHEY_SIMPLEX, 2, (0,255,0), 2)


            if results_left.detections:
                for id, detection in enumerate(results_left.detections):
                    mp_draw.draw_detection(frame_left, detection)

                    bBox = detection.location_data.relative_bounding_box

                    h, w, c = frame_left.shape

                    boundBox = int(bBox.xmin * w), int(bBox.ymin * h), int(bBox.width * w), int(bBox.height * h)

                    center_point_left = (boundBox[0] + boundBox[2] / 2, boundBox[1] + boundBox[3] / 2)

                    cv2.putText(frame_left, f'{int(detection.score[0]*100)}%', (boundBox[0], boundBox[1] - 20), cv2.FONT_HERSHEY_SIMPLEX, 2, (0,255,0), 2)




            # If no ball can be caught in one camera show text "TRACKING LOST"
            if not results_right.detections or not results_left.detections:
                cv2.putText(frame_right, "TRACKING LOST", (75,50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255),2)
                cv2.putText(frame_left, "TRACKING LOST", (75,50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255),2)

            else:
                # Function to calculate depth of object. Outputs vector of all depths in case of several balls.
                # All formulas used to find depth is in video presentaion
                depth = tri.find_depth(center_point_right, center_point_left, frame_right, frame_left, B, f, alpha)
                disparitymap = dismap.compute_disparity_map(frame_left, frame_right)
                depthmap = dismap.find_depth_map(disparitymap, B , alpha)

                cv2.putText(frame_right, "Distance: " + str(round(depth,1)), (50,50), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0,255,0),3)
                cv2.putText(frame_left, "Distance: " + str(round(depth,1)), (50,50), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0,255,0),3)
                # Multiply computer value with 205.8 to get real-life depth in [cm]. The factor was found manually.
                print("Depth: ", str(round(depth,1)))



            end = time.time()
            totalTime = end - start

            fps = 1 / totalTime
            #print("FPS: ", fps)

            cv2.putText(frame_right, f'FPS: {int(fps)}', (20,450), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0,255,0), 2)
            cv2.putText(frame_left, f'FPS: {int(fps)}', (20,450), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0,255,0), 2)                                   


            # Show the frames
            frame_right= cv2.cvtColor(frame_right,cv2.COLOR_BGR2RGB)
            frame_left= cv2.cvtColor(frame_left,cv2.COLOR_BGR2RGB)
            cv2.imshow("frame right",frame_right )
            cv2.imshow("frame left", frame_left)
            depth_map_normalized = cv2.normalize(depthmap, None, 0, 255, cv2.NORM_MINMAX)
            depth_map_normalized = np.uint8(depth_map_normalized)

# Display the depth map using OpenCV
            cv2.imshow('Depth Map', depth_map_normalized)
            



            # Hit "q" to close the window
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break


# Release and destroy all windows before termination
cap_right.release()
cap_left.release()

cv2.destroyAllWindows()