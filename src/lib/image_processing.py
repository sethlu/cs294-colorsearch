import numpy as np
#import matplotlib.pyplot as plt
import pickle
import skimage
import os
import operator
from imageio import imread
from skimage import data
import skimage.color
from PIL import Image

from utils import eprint

# NB: When printing messages for debugging, please use eprint instead of print!
# This avoids clogging the stdout that we use to pass the results back to the parent process


def split(img, newDim):
    # For now, assumes dimensions of img are divisible by newDim for convenience

    result = np.empty((newDim, newDim, 3))
    horizBlockSize = img.shape[0] / newDim
    vertBlockSize = img.shape[1] / newDim
    for i in range(newDim):
        for j in range(newDim):
            startHorizIdx = int(i * horizBlockSize)
            endHorizIdx = int((i + 1) * horizBlockSize)
            startVertIdx = int(j * vertBlockSize)
            endVertIdx = int((j + 1) * vertBlockSize)
            result[i][j] = img[startHorizIdx:endHorizIdx][startVertIdx:endVertIdx]
    return result


def computeAllColorScores(img, split_dim, color_functions):
    # Returns a matrix of dimensions newDim x newDim called result, where result[i][j][k] corresponds to
    # the color score for color k of the (i, j)th subsection, where (0, 0) is the top left.

    #eprint("Computing all color scores", flush=True)

    result = np.zeros((split_dim, split_dim, len(color_functions)))
    horizBlockSize = img.shape[0] / split_dim
    vertBlockSize = img.shape[1] / split_dim
    for i in range(split_dim):
        for j in range(split_dim):
            startHorizIdx = int(i * horizBlockSize)
            endHorizIdx = int((i + 1) * horizBlockSize)
            startVertIdx = int(j * vertBlockSize)
            endVertIdx = int((j + 1) * vertBlockSize)
            for x in range(startHorizIdx, endHorizIdx):
                for y in range(startVertIdx, endVertIdx):
                    for k in range(len(color_functions)):
                        color_f = color_functions[k]
                        result[i][j][k] += color_f(img[x][y])

    return result


def findBestMatches(normalized_color_scores, input_profile, split_dim):
    bestScoreSoFar = -1
    stuff = np.empty(normalized_color_scores.shape[0])
    k = 0
    for img in normalized_color_scores:
        totalScore = 0
        for i in range(split_dim):
            for j in range(split_dim):
                totalScore += img[i][j][np.argmax(input_profile[i][j])]

        if (totalScore > bestScoreSoFar):
            bestSoFar = img
            bestScoreSoFar = totalScore
        stuff[k] = totalScore
        k += 1

    # display(stuff)
    # display (np.argmax(stuff))
    # display(np.argsort(stuff))
    return np.argsort(stuff)


def sortImagesByMatch(imgs, input_profile, split_dim, color_functions):
    all_color_scores = [computeAllColorScores(
        img, split_dim, color_functions) for img in imgs]
    normalized_color_scores = np.copy(all_color_scores)
    for i in range(len(imgs)):
        normalized_color_scores[i] /= (imgs[i].shape[0] * imgs[i].shape[1])
    """for x in range(len(imgs)) :
        for i in range(normalized_color_scores.shape[1]) :
            for j in range(normalized_color_scores.shape[2]) :
                normalized_color_scores[x][i][j] /= (imgs[x].shape[0] * imgs[x].shape[1])
                """
    # display(normalized_color_scores)
    #eprint(normalized_color_scores, flush=True)
    return [imgs[i] for i in reversed(findBestMatches(normalized_color_scores, input_profile, split_dim))]


def sortImagesByMatchAndMatrix(imgs, input_profile, color_score_matrix, split_dim):
    # Assumes color score matrix is normalized
    return [imgs[i] for i in reversed(findBestMatches(color_score_matrix, input_profile, split_dim))]


def calcNormalizedColorScoreMatrix(imgs, split_dim, color_functions):
    # Calculates normalized color score matrix for the given images.
    color_scores = np.array([computeAllColorScores(
        img, split_dim, color_functions) / (img.shape[0] * img.shape[1]) for img in imgs])
    for i in range(color_scores.shape[0]):
        for j in range(color_scores.shape[1]):
            for k in range(color_scores.shape[2]):
                norm = np.linalg.norm(color_scores[i][j][k])
                color_scores[i][j][k] /= norm if norm != 0 else 1


def load_images(directory):
    # Specify a directory to look for an images. Returns all of the images (.jpg) files as a list of numpy matrices.
    imgs = []
    filename_to_img = {}
    for filename in os.listdir(directory):
        if filename.endswith(".jpg"):
            img = Image.open(os.path.join(directory, filename))
            img.thumbnail((16, 16), Image.ANTIALIAS) # @sethlu: I scaled the dimensions down for performance boost in debugging lol
            imgs.append(np.asarray(img))
            filename_to_img[filename] = np.asarray(img)
            # eprint(os.path.join(directory, filename))
            continue
        else:
            continue
    #eprint("HI")
    #eprint(filename_to_img)
    return filename_to_img #imgs


def computeSingleImageColorScores(img, split_dim, color_name_to_functions) :
    result = {}
    horizBlockSize = img.shape[0] / split_dim
    vertBlockSize = img.shape[1] / split_dim
    for color_name in color_name_to_functions.keys() :
        result[color_name] = np.zeros((split_dim, split_dim))
        for i in range(split_dim) :
            for j in range(split_dim) :
                startHorizIdx = int(i * horizBlockSize)
                endHorizIdx = int((i + 1) * horizBlockSize)
                startVertIdx = int(j * vertBlockSize)
                endVertIdx = int((j + 1) * vertBlockSize)
                for x in range(startHorizIdx, endHorizIdx) :
                    for y in range(startVertIdx, endVertIdx) :
                        result[color_name][i][j] += color_name_to_functions[color_name](img[x][y])
        result[color_name] /= (img.shape[0] * img.shape[1])
    #eprint("COLOR SCORES:")
    #eprint(result)
    return result

def computeSingleImageSingleColorScore(img, split_dim, color_name, color_function) :
    horizBlockSize = img.shape[0] / split_dim
    vertBlockSize = img.shape[1] / split_dim
    result = np.zeros((split_dim, split_dim))
    for i in range(split_dim) :
        for j in range(split_dim) :
            startHorizIdx = int(i * horizBlockSize)
            endHorizIdx = int((i + 1) * horizBlockSize)
            startVertIdx = int(j * vertBlockSize)
            endVertIdx = int((j + 1) * vertBlockSize)
            for x in range(startHorizIdx, endHorizIdx) :
                for y in range(startVertIdx, endVertIdx) :
                    result[i][j] += color_function(img[x][y])
    return result / (img.shape[0] * img.shape[1])

def sortImagesByMatchRevised(filename_to_imgs, input_profile, split_dim, color_name_to_functions) :
    all_color_scores = {}
    for filename, img in filename_to_imgs.items() :
        all_color_scores[filename] = computeSingleImageColorScores(img, split_dim, color_name_to_functions)
    return findBestMatchesRevised(all_color_scores, input_profile, split_dim) 

def findBestMatchesRevised(color_scores, input_profile, split_dim) :
    bestScoreSoFar = -1
    stuff = {}     #np.empty(color_scores.shape[0])
    k = 0
    for file_name, scores in color_scores.items():
        totalScore = 0
        for i in range(split_dim) :
            for j in range(split_dim) :
                color = input_profile[j + split_dim * i]
                if color is not None:
                    totalScore += scores[color][i][j]
        if totalScore != 0:
            stuff[file_name] = totalScore
        k += 1
    return sorted(stuff, key=stuff.get, reverse=True)

# Writes the info stored in image_color_info (map of filename -> color -> 2d color score matrix)
# into a file called filename
def image_color_info_to_file(image_color_info, filename) :
    pickle.dump(image_color_info, open(filename, "wb"))

# Loads the info stored in file called filename, where info should be a 
# map of filename -> color -> 2d color score matrix
def image_color_info_from_file(filename) :
    return pickle.load(open(filename, "rb"))
    
# Takes a user specified directory and filename for the image (img_name), and an existing
# image-color-info map called image_color_info,  and returns the result of adding the additional
# information to the existing information.
def add_image_to_info(directory, img_name, image_color_info, split_dim, color_name_to_functions) :
    img = Image.open(os.path.join(directory, img_name)) 
    image_color_info[img_name] = computeSingleImageColorScores(img, split_dim, color_name_to_functions)
    return image_color_info

# Adds the information encoded by the TUPLE color_name_to_function (String color name -> function)
# to the existing information in image_color_info, and returns the updated info.
def add_color_to_info(directory, image_color_info, split_dim, color_name_to_function) :
    for filename, img in image_color_info.items() :
        image_color_info[filename][color_name_to_function] = computeSingleImageSingleColorScore(img, split_dim, color_name_to_function[0], color_name_to_function[1])
    return image_color_info 
