import cv2
from realsense_depth import *
import math
import time
from datetime import datetime
import numpy as np
from DepthMap import * 
from Contours import *
from PointCloud import *
from MonocularDepthEstimation import *
from upload_to_gdrive import *
import os
import json
import matplotlib.pyplot as plt

#Initializing Camera and getting intrinsic parameters
camera = DepthCamera()
camera_intrinsics = [camera.intrinsics_width, camera.intrinsics_height, camera.intrinsics_fx, camera.intrinsics_fy, camera.intrinsics_ppx, camera.intrinsics_ppy]

#Skipping initial frames
time.sleep(3)

#Control how often an image is taken in minutes (interval = number of minutes)
interval = 1
wait = math.floor(interval*60)

#Expected minimum and maximum distances for the camera/image (in mm)
min_dist = 0
max_dist = 2000

#Online upload
online_upload = False

#Generate Point Clouds
pcd_gen = False


#Path under which images are saved
path = r'./Image_Capture//'
#Checking that path folder exists to save images locally. Otherwise create the pathway.
if not os.path.exists(path):
    os.mkdir(path)
if not os.path.exists(path+'Picture//'):
    os.mkdir(path+'Picture//')
if not os.path.exists(path+'StereoDepthMap//'):
    os.mkdir(path+'StereoDepthMap//')
if not os.path.exists(path+'EstimatedDepthMap//'):
    os.mkdir(path+'EstimatedDepthMap//')
if not os.path.exists(path+'Contours//'):
    os.mkdir(path+'Contours//')
if not os.path.exists(path+'ContoursForeground//'):
    os.mkdir(path+'ContoursForeground//')
if not os.path.exists(path+'EstimatedPCD//'):
    os.mkdir(path+'EstimatedPCD//')
if not os.path.exists(path+'NormalizedStereoPCD//'):
    os.mkdir(path+'NormalizedStereoPCD//')

with open("config.json", "r") as config_file:
    config = json.load(config_file)

while True:
    try:
        #Start measuring time needed for image processing and upload
        start_time = time.time() 

        #Getting photo footage
        ret, depth_frames, color_frames = camera.get_frame()

        cam_number = 1
        for i in range(len(camera.pipeline)):

            #Getting date and time
            now = datetime.now()
            now_str = f"{now.timestamp().__ceil__()}_Camera_{cam_number}"
            #Formatting date and time to be saved in the file name
            #NOTE: The time format is changed to use ";" instead of ":" to avoid issues with file names
            #      and Google Drive uploads

            #now_str = now.strftime("Date %Y-%m-%d Time %H;%M;%S Camera {}".format(cam_number))

            #Getting the color and depth frames from each individual camera
            depth_frame = depth_frames[i]
            color_frame = color_frames[i]
            #Getting the parameters of each individual camera
            camera_intrinsic = [parameter[i] for parameter in camera_intrinsics]

            #Resizing the actual depth frame due to "decimation" post-processing and filtering techniqe in camera.get_frame()
            depth_frame = cv2.resize(depth_frame, (640,480), cv2.INTER_CUBIC)
            depth_file = f"./Image_Capture/StereoDepthMap/StereoDepthMap_{now_str}.csv"
            with open(depth_file, "w") as file:
                for row in depth_frame:
                    file.write(",".join(map(str,row)) + "/n")

            #Estimating the depth frame from the color_frame image
            # monocular_depth_frame = MonocularDepthEstimation(color_frame, min_dist, max_dist)

            #Saving image
            written = cv2.imwrite(path+"Picture/Picture_{}.png".format(now_str), color_frame)
            uploader = GoogleDriveUploader("credentials.json", config["googleDrive"]["parentIds"]["Picture"])
            try:
                uploader.upload_photo(path+"Picture/Picture_{}.png".format(now_str))
            except Exception as e:
                print(f"An error occurred: {e}")

            #Generating and saving the stereo depth map
            depth_img = DepthMap(depth_frame, min_dist, max_dist)
            depth_img.save(path+"StereoDepthMap/StereoDepthMap_{}.png".format(now_str))
            uploader = GoogleDriveUploader("credentials.json", config["googleDrive"]["parentIds"]["StereoDepthMap"])
            try:
                uploader.upload_photo(path+"StereoDepthMap/StereoDepthMap_{}.png".format(now_str))
            except Exception as e:
                print(f"An error occurred: {e}")
            
            #Generating and saving the estimated depth map
            # estimated_depth_img = DepthMap(monocular_depth_frame, min_dist, max_dist)
            # estimated_depth_img.save(path+"EstimatedDepthMap/EstimatedDepthMap_{}.png".format(now_str))
            # uploader = GoogleDriveUploader("credentials.json", config["googleDrive"]["parentIds"]["EstimatedDepthMap"])
            # try:
            #     uploader.upload_photo(path+"EstimatedDepthMap/EstimatedDepthMap_{}.png".format(now_str))
            # except Exception as e:
            #     print(f"An error occurred: {e}")

            #Generating the contouors image for the foreground
            contour_img_foreground, contour_img = Contours(color_frame, 100, 200)
            #Saving the contoured image to the folder
            contour_img.save(path+"Contours/Contours_{}.png".format(now_str))
            #Uploading the contoured image to Google Drive
            uploader = GoogleDriveUploader("credentials.json", config["googleDrive"]["parentIds"]["Contours"])
            try:
                uploader.upload_photo(path+"Contours/Contours_{}.png".format(now_str))
            except Exception as e:
                print(f"An error occurred: {e}")
            
            
            #Generating point clouds from color and estimated depth images
            # if pcd_gen:
            #     estimated_pcd = PointCloud(color_frame,monocular_depth_frame.astype('uint16'), camera_intrinsic)
            #     o3d.io.write_point_cloud(path+"EstimatedPCD/EstimatedPCD_{}.pcd".format(now_str), estimated_pcd)
            #     #Making a copy of the camera depth frame and nomalizing it between 0-2000 for point cloud plotting
            #     depth_frame_copy = np.copy(depth_frame)
            #     depth_frame_copy = (max_dist - min_dist)*((depth_frame_copy - np.min(depth_frame_copy))/(np.max(depth_frame_copy) - np.min(depth_frame_copy)))
            #     depth_frame_copy = depth_frame_copy.astype('uint16')
            #     #Uploading the point cloud to Google Drive
            #     uploader = GoogleDriveUploader("credentials.json", config["googleDrive"]["parentIds"]["EstimatedPCD"])
            #     try:
            #         uploader.upload_photo(path+"EstimatedPCD/EstimatedPCD_{}.pcd".format(now_str))      
            #     except Exception as e:
            #         print(f"An error occurred: {e}")


                
            #     #Generating point cloud from color and RealSense camera normalized depth images
            #     normalized_stereo_pcd = PointCloud(color_frame,depth_frame_copy, camera_intrinsic)
            #     o3d.io.write_point_cloud(path+"NormalizedStereoPCD//NormalizedStereoPCD_{}.pcd".format(now_str), normalized_stereo_pcd)

            #     uploader = GoogleDriveUploader("credentials.json", config["googleDrive"]["parentIds"]["NormalizedStereoPCD"])
            #     try:
            #         uploader.upload_photo(path+"NormalizedStereoPCD//NormalizedStereoPCD_{}.pcd".format(now_str))
            #     except Exception as e:
            #         print(f"An error occurred: {e}")


            contour_img_foreground.save(path+"ContoursForeground/ContoursForeground_{}.png".format(now_str)) 
            #Uploading files to Google Drive.
            uploader = GoogleDriveUploader("credentials.json", config["googleDrive"]["parentIds"]["ContoursForeground"])
            try:
                uploader.upload_photo(path+"ContoursForeground/ContoursForeground_{}.png".format(now_str))
            except Exception as e:
                print(f"An error occurred: {e}")
            
            cam_number +=1

        #Complete measuring time needed for image processing and upload
        end_time = time.time()
        elapsed_time = end_time - start_time

        #Change wait time to account for image processing and upload
        waittime = math.floor(wait - elapsed_time)
        #For processing time greater than wait time
        if waittime < 0:
            waittime = 0

        #Waiting to take another image
        time.sleep(waittime)

    #Press Ctrl+C in terminal to stop the program
    except KeyboardInterrupt:
        print("exit")
        break