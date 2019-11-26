import json

import numpy as np
import skimage.color


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

def handle_query(palette, canvas):
    """
    Parameters
        palette: list of functions
        canvas: list of palette indexes

    Return value
        list of strings (file names)
    """

    #canvas_matrix = np.reshape(canvas, (4, 4))
    split_dim = 4
    canvas_matrix = np.zeros((split_dim, split_dim, len(palette)))
    canvas_idx = 0
    for i in range(split_dim):
        for j in range(split_dim):
            canvas_matrix[i][j][canvas[canvas_idx]] = 1
            canvas_idx += 1

    # TODO: Will need to return the matching images instead of displaying them with matplotlib

    from image_processing import load_images, sortImagesByMatch
    import matplotlib.pyplot as plt

    img_directory = "./images/sky-reduced"
    imgs = load_images(img_directory)
    result = sortImagesByMatch(imgs, canvas_matrix, split_dim, palette)
    fig = plt.figure(figsize=(8, 8))
    columns = 5
    rows = 1
    for i in range(1, columns*rows + 1):
        img = result[i - 1]
        fig.add_subplot(rows, columns, i)
        plt.imshow(img)
    plt.show()

    # TODO: To return a list of images in sorted order
    return []


# Request Parsing

query = json.loads(input())

palette = []

color_id_to_index = {}

for color_id, color in query['palette'].items():
    index = len(palette)
    palette.append(make_perceptron_classifier(**color['perceptron']))
    color_id_to_index[color_id] = index

canvas = [color_id_to_index[color_id] for color_id in query['canvas']]

# Pass back the search results

print(json.dumps(handle_query(palette, canvas)))
