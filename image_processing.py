import numpy as np
import matplotlib.pyplot as plt
import skimage
import os
from imageio import imread
from skimage import data
from PIL import Image

# For now, assumes dimensions of img are divisible by newDim for convenience
def split(img, newDim) :
    result = np.empty((newDim, newDim, 3))
    horizBlockSize = img.shape[0] / newDim
    vertBlockSize = img.shape[1] / newDim
    for i in range(newDim) :
        for j in range(newDim) :
            startHorizIdx = int(i * horizBlockSize)
            endHorizIdx = int((i + 1) * horizBlockSize)
            startVertIdx = int(j * vertBlockSize)
            endVertIdx = int((j + 1) * vertBlockSize)
            result[i][j] = img[startHorizIdx:endHorizIdx][startVertIdx:endVertIdx]
    return result


# Returns a matrix of dimensions newDim x newDim called result, where result[i][j][k] corresponds to 
# the color score for color k of the (i, j)th subsection, where (0, 0) is the top left.
def computeAllColorScores(img, splitDim) :
    result = np.zeros((splitDim, splitDim, len(color_fs)))
    horizBlockSize = img.shape[0] / splitDim
    vertBlockSize = img.shape[1] / splitDim
    for i in range(splitDim) :
        for j in range(splitDim) :
            startHorizIdx = int(i * horizBlockSize)
            endHorizIdx = int((i + 1) * horizBlockSize)
            startVertIdx = int(j * vertBlockSize)
            endVertIdx = int((j + 1) * vertBlockSize)
            for x in range(startHorizIdx, endHorizIdx) :
                for y in range(startVertIdx, endVertIdx) :
                    for k in range(len(color_fs)) :
                        color_f = color_fs[k]
                        if (color_f(img[x][y])) :
                            result[i][j][k] += 1

    return result

def findBestMatches(normalized_color_scores, input_profile, split_dim) :
    bestScoreSoFar = -1
    stuff = np.empty(normalized_color_scores.shape[0])
    k = 0
    for img in normalized_color_scores :
        totalScore = 0
        for i in range(split_dim) :
            for j in range(split_dim) :
                totalScore += img[i][j][np.argmax(input_profile[i][j])]
            
        if (totalScore > bestScoreSoFar) :
            bestSoFar = img
            bestScoreSoFar = totalScore
        stuff[k] = totalScore
        k += 1
        
    #display(stuff)
    #display (np.argmax(stuff))
    #display(np.argsort(stuff))
    return np.argsort(stuff)

def sortImagesByMatch(imgs, input_profile, split_dim) :
    all_color_scores = [computeAllColorScores(img, split_dim) for img in imgs]
    normalized_color_scores = np.copy(all_color_scores)
    for i in range(len(imgs)) : 
        normalized_color_scores[i] /= (imgs[i].shape[0] * imgs[i].shape[1])
    """for x in range(len(imgs)) :
        for i in range(normalized_color_scores.shape[1]) :
            for j in range(normalized_color_scores.shape[2]) :
                normalized_color_scores[x][i][j] /= (imgs[x].shape[0] * imgs[x].shape[1])
                """
    #display(normalized_color_scores)
    return [imgs[i] for i in reversed(findBestMatches(normalized_color_scores, input_profile, split_dim))]

# Assumes color score matrix is normalized
def sortImagesByMatchAndMatrix(imgs, input_profile, color_score_matrix) :
    return [imgs[i] for i in reversed(findBestMatches(color_score_matrix, input_profile, split_dim))]

# Calculates normalized color score matrix for the given images.
def calcNormalizedColorScoreMatrix(imgs, split_dim) :
    color_scores = np.array([computeAllColorScores(img, split_dim) / (img.shape[0] * img.shape[1]) for img in imgs])
    for i in range(test_sky_matrix.shape[0]) :
        for j in range(test_sky_matrix.shape[1]) :
            for k in range(test_sky_matrix.shape[2]) :
                norm = np.linalg.norm(test_sky_matrix[i][j][k])
                test_sky_matrix[i][j][k] /= norm if norm != 0 else 1


# Specify a directory to look for an images. Returns all of the images (.jpg) files as a list of numpy matrices.
def load_images(directory) :
    imgs = []
    for filename in os.listdir(directory):
        if filename.endswith(".jpg") :
            img = Image.open(os.path.join(directory, filename))
            img.thumbnail((100, 100), Image.ANTIALIAS)
            imgs.append(np.asarray(img))
             # print(os.path.join(directory, filename))
            continue
        else:
            continue
    return imgs


# EXAMPLE EXECUTION 

# EXAMPLE CLASSIFIER FUNCTIONS 
def isBlack(pixel) :
    return np.max(pixel) < 30 #pixel[0] == pixel[1] and pixel[1] == pixel[2] and pixel[0] < 128

def isWhite(pixel) :
    return np.min(pixel) > 220 #pixel[0] == pixel[1] and pixel[1] == pixel[2] and pixel[0] >= 128

def isRed(pixel) :
    return np.argmax(pixel) == 0 and pixel[0] != pixel[1] and not isBlack(pixel) and not isWhite(pixel) and np.max(pixel) - np.min(pixel) > 50 # and np.max(pixel) - np.min(pixel) >= 20
def isGreen(pixel) :
    return np.argmax(pixel) == 1 and pixel[0] != pixel[1] and not isBlack(pixel) and not isWhite(pixel) and np.max(pixel) - np.min(pixel) > 50 # and np.max(pixel) - np.min(pixel) >= 20
def isBlue(pixel) :
    return np.argmax(pixel) == 2 and pixel[0] != pixel[2] and not isBlack(pixel) and not isWhite(pixel) and np.max(pixel) - np.min(pixel) > 50 # and np.max(pixel) - np.min(pixel) >= 20

color_fs = [isRed, isGreen, isBlue, isBlack, isWhite]

# EXAMPLE INPUTS
WHITE_BLACK = np.zeros((4, 4, 5))
WHITE_BLACK[0][0][4] = 1
for i in range(0, 2) :
    for j in range(0, 4) :
        WHITE_BLACK[i][j][0] = 1
        
for i in range(2, 4) :
    for j in range (0, 4) :
        WHITE_BLACK[i][j][3] = 1
#display(WHITE_BLACK)

RED_BLACK = np.zeros((4, 4, 5))

for i in range(0, 2) :
    for j in range(0, 4) :
        RED_BLACK[i][j][0] = 1
        
for i in range(2, 4) :
    for j in range (0, 4) :
        RED_BLACK[i][j][3] = 1
#display(RED_BLACK)
# RED TOP, BLACK BOTTOM

BLUE_BLACK = np.zeros((4, 4, 5))

for i in range(0, 2) :
    for j in range(0, 4) :
        BLUE_BLACK[i][j][2] = 1
        
for i in range(2, 4) :
    for j in range (0, 4) :
        BLUE_BLACK[i][j][3] = 1
#display(BLUE_BLACK)
# BLUE TOP, BLACK BOTTOM

img_directory = "./images/sky"
imgs = load_images(img_directory)
result = sortImagesByMatch(imgs, RED_BLACK, 4)
fig=plt.figure(figsize=(8, 8))
columns = 4
rows = 5
for i in range(1, columns*rows +1):
    img = result[i - 1]
    fig.add_subplot(rows, columns, i)
    plt.imshow(img)
plt.show()

