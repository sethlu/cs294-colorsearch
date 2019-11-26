import numpy as np
import matplotlib.pyplot as plt
import skimage
import os
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


def computeAllColorScores(img, splitDim, color_functions):
    # Returns a matrix of dimensions newDim x newDim called result, where result[i][j][k] corresponds to
    # the color score for color k of the (i, j)th subsection, where (0, 0) is the top left.

    eprint("Computing all color scores", flush=True)

    result = np.zeros((splitDim, splitDim, len(color_functions)))
    horizBlockSize = img.shape[0] / splitDim
    vertBlockSize = img.shape[1] / splitDim
    for i in range(splitDim):
        for j in range(splitDim):
            startHorizIdx = int(i * horizBlockSize)
            endHorizIdx = int((i + 1) * horizBlockSize)
            startVertIdx = int(j * vertBlockSize)
            endVertIdx = int((j + 1) * vertBlockSize)
            for x in range(startHorizIdx, endHorizIdx):
                for y in range(startVertIdx, endVertIdx):
                    for k in range(len(color_functions)):
                        color_f = color_functions[k]
                        if (color_f(img[x][y])):
                            result[i][j][k] += 1

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
    eprint(normalized_color_scores, flush=True)
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
    for filename in os.listdir(directory):
        if filename.endswith(".jpg"):
            img = Image.open(os.path.join(directory, filename))
            img.thumbnail((16, 16), Image.ANTIALIAS) # @sethlu: I scaled the dimensions down for performance boost in debugging lol
            imgs.append(np.asarray(img))
            # eprint(os.path.join(directory, filename))
            continue
        else:
            continue
    return imgs
