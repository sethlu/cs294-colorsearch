import json

import os
import numpy as np
import skimage.color

from utils import eprint


# Perceptron

def make_perceptron_classifier(coefs=None, intercepts=None, mean=None, scale=None, **kwargs):
    # coefs = np.array(coefs)
    # intercepts = np.array(intercepts)
    mean = np.array(mean)
    scale = np.array(scale)

    def classifier(RGB):
        XYZ = skimage.color.convert_colorspace([[RGB]], 'RGB', 'XYZ')[0][0]
        XYZsum = XYZ[0] + XYZ[1] + XYZ[2]
        xyY = np.array([0, 0, 0]) if XYZsum == 0 else np.array(
            [XYZ[0] / XYZsum, XYZ[1] / XYZsum, XYZ[1]])

        a = (xyY - mean) / scale

        # Intercepts
        b = np.array(intercepts[0])
        # Weights
        for i, ai in enumerate(a):
            b += ai * np.array(coefs[0][i])
        # Activation
        b = np.maximum(np.zeros(b.shape), b)  # ReLU

        # Intercepts
        z = np.array(intercepts[1])
        # Weights
        for i, bi in enumerate(b):
            z += bi * np.array(coefs[1][i])
        # Activation
        z = 1 / (1 + np.exp(-z))  # Logistic

        return z[0]
    return classifier


# Query Handling

def handle_query(directory, palette, canvas):
    """
    Parameters
        directory: folder containing images
        palette: maps color ids to functions
        canvas: list of color ids

    Return value
        list of strings (file names)
    """

    split_dim = 4

    from image_processing import load_images, sortImagesByMatchRevised
    
    imgs = load_images(directory)
    result = sortImagesByMatchRevised(imgs, canvas, split_dim, palette)

    # result_imgs = []
    # for filename in result:
    #     result_imgs.append(Image.open(os.path.join(directory, filename)))

    return result


# Request Parsing

query = json.loads(input())

directory = query['directory']
palette = {color_id: make_perceptron_classifier(
    **color['perceptron']) for color_id, color in query['palette'].items()}
canvas = query['canvas']

eprint("Directory:", directory, flush=True)
eprint("Palette:", palette, flush=True)
eprint("Canvas:", canvas, flush=True)

# Pass back the search results

print(json.dumps(handle_query(directory, palette, canvas)))
