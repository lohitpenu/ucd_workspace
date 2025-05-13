import cv2
from PIL import Image
from rembg import remove

#Find the contour edges from an image
#Lighting Threshholds (integer from 0 - 255)
def Contours(image, threshold1, threshold2):

    #Converting from a color image to greyscale for canny algorithm
    img_gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    #Canny edge detection to generate edges from the greyscale image 
    edges = cv2.Canny(img_gray,threshold1,threshold2)

    #Generating image from the image array
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGBA)
    base = Image.fromarray(image_rgb)
    #Generating edge image and converting to "RGBA" mode to be compatible for blending
    overlay = Image.fromarray(edges)
    overlay = overlay.convert('RGBA')
    #Loading the pixel values of the overlay image
    pixels = overlay.load()
    #Change the alpha/transparency over all the black pixels to 0 (white pixels alpha remains 255)
    for x in range(overlay.size[0]):
       for y in range(overlay.size[1]):
           if pixels[x,y][0] <= 126:
               pixels[x,y] = (0, 0, 0, 0)

    #Overlaying the edges on top of the original image
    base.paste(overlay, (0,0), overlay)

    #Removing background from the contoured image
    img_foreground = remove(base)

    return img_foreground, base