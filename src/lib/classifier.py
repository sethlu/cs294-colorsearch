import json

import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.neural_network import MLPClassifier


class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super(NumpyEncoder, self).default(obj)


datapoints = json.loads(input())

X = [datapoint[:-1] for datapoint in datapoints]
y = [datapoint[-1] for datapoint in datapoints]

ss = StandardScaler()
X = ss.fit_transform(X)

clf = MLPClassifier(solver='adam', alpha=1e-5, max_iter=1000, hidden_layer_sizes=(100,))
clf.fit(X, y)

print(json.dumps({
    'mean': ss.mean_,
    'scale': ss.scale_,
    'coefs': clf.coefs_,
    'intercepts': clf.intercepts_,
    'out_activation': clf.out_activation_,
    'loss': clf.loss_,
    'classes': clf.classes_,
}, cls=NumpyEncoder))
