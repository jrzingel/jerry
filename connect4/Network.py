# d7137

# The real brains of the creatures; use per generation per round per game per move
import logging
import tensorflow as tf
import numpy as np
from scipy.sparse import random
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'  # ignore warnings.
log = logging.getLogger(__name__)  # Inherits main config

"""
STRUCTURE
- Allow dynamic structure of creatures (ie chance of them mutating to get another layer)
- But MUST have a normal input of 6x7 and output of softmax 7x1.
"""

BASE_DIMS = [42, 10, 12, 7]


def new_wb(dims):
    """Make some new weights and biases"""
    w = []
    b = []
    for layer in range(1, len(dims)):
        w.append(tf.random.uniform((dims[layer], dims[layer-1]), minval=0, maxval=1))
        b.append(tf.random.uniform((dims[layer], 1), minval=0, maxval=1))
    return w, b


class DNA:
    """The DNA of a creature"""
    def __init__(self, d=None, w=None, b=None):
        if d is None:
            d = BASE_DIMS
        self.dims = d  # Dimensions of layers. Layer 0 is input, layer -1 is output.

        if w is not None:  # Load the weights if necessary
            assert b is not None
            self.weights = w
            self.biases = b
        else:
            self.weights, self.biases = new_wb(self.dims)

    def copy(self):
        """Return a copy of the DNA (unlinked)"""
        return DNA(d=self.dims.copy(), w=self.weights.copy(), b=self.biases.copy())

    def forward(self, state):
        """Feed forward the state to output"""
        a = state.reshape((42,1))
        for l in range(len(self.weights)):  # l is hidden weight layer (or final layer)
            z = tf.math.add(tf.matmul(self.weights[l], a), self.biases[l])
            a = tf.nn.relu(z)  # TODO: Allow customisation of this function
        yh = tf.nn.softmax(a, axis=0)
        return tf.argmax(yh).numpy()

    def merge(self, other, weigh=True):
        """Merge two sets of DNA together. Weighted towards self (Against other)"""
        # Take a mask of each weights and add them together
        weights = []
        biases = []

        if weigh:  # Should the network be weighed towards self. Default yes. (66/33)
            peak = 3
        else:
            peak = 2
        for i, l in enumerate(self.weights):  # Cycle through weights
            mask = np.random.randint(0, peak, l.shape)
            mask[mask == 2] = 1
            a = mask*l
            b = (np.ones(l.shape)-mask).astype('int64')*other.weights[i]  # Invert the mask
            weights.append(a + b)

        for i, l in enumerate(self.biases):  # Cycle through biases
            mask = np.random.randint(0, peak, l.shape)
            mask[mask == 2] = 1
            a = mask*l
            b = (np.ones(l.shape)-mask).astype('int64')*other.biases[i]  # Invert the mask
            biases.append(a + b)

        return DNA(d=self.dims.copy(), w=weights.copy(), b=biases.copy())  # Return the new DNA

    def noise(self, density, std):
        """Add some noise to the weights"""
        for i, l in enumerate(self.biases):
            locs = random(l.shape[0], l.shape[1], density).A
            locs[locs != 0] = 1
            muts = np.random.normal(0, std, l.shape)
            muts = np.multiply(muts, locs)
            l += muts

        for i, l in enumerate(self.weights):
            locs = random(l.shape[0], l.shape[1], density).A
            locs[locs != 0] = 1
            muts = np.random.normal(0, std, l.shape)
            muts = np.multiply(muts, locs)
            l += muts

    def change_node(self):
        """Add a new node somewhere to the network"""
        layer = np.random.randint(1, len(self.dims)-1)  # Only hidden layers can change
        self.dims[layer] += int((np.random.randint(0, 2)-.5)*2)
        # Restructure the weights and biases.
        w_ = []
        b_ = []
        for layer in range(1, len(self.dims)):
            w = self.weights[layer-1][tf.newaxis, ..., tf.newaxis]  # Make a 4D tensor
            b = self.biases[layer-1][tf.newaxis, ..., tf.newaxis]

            w_.append(tf.image.resize(w, (self.dims[layer], self.dims[layer-1]))[0, ..., 0])  # Resize and drop to 2D
            b_.append(tf.image.resize(b, (self.dims[layer], 1))[0, ..., 0])

        self.weights = w_
        self.biases = b_


if __name__ == '__main__':
    d = DNA()
    print(d.forward(np.ones((6,7))))
    d.noise(0.5, 1)

