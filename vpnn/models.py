import tensorflow as tf
import numpy as np
from typing import List, Callable, Union

from .layers import Rotation, Permutation, Diagonal, Bias, SVDDownsize
from . import activations


def vpnn(input_dim: int = 2,
         n_layers: int = 1,
         n_rotations: int = 1,
         theta_initializer: str = 'uniform',
         t_initializer: str = 'uniform',
         bias_initializer: str = 'uniform',
         output_dim: int = None,
         use_bias: bool = True,
         use_permutations: bool = True,
         use_diagonals: bool = True,
         diagonal_fn: Callable = None,
         output_activation: Union[str, Callable] = 'linear',
         hidden_activation: Union[str, Callable] = 'relu',
         M_initializer='ones',
         M_init=1.3,
         trainable_M=False):
    """
    builds a VPNN model (just volume preserving kernels)
    :param M_initializer: passed to `Chebyshev` constructors
    :param M_init: passed to `Chebyshev` constructors
    :param trainable_M: passed as `trainable` to `Chebyshev` constructors
    :param input_dim: the input dimension to the model
    :param n_layers: the number of hidden layers of the model
    :param n_rotations: the number of rotations to use (k/2 if you read the paper)
    :param theta_initializer: initializer for angles of rotations
    :param t_initializer: initializer for t parameter of diagonals
    :param bias_initializer: initializer for bias vectors
    :param output_dim: if not None, the output dimension for an SVDDownsize
    :param use_bias: if False, no bias vectors are used
    :param use_permutations: if False, no permutations are used
    :param use_diagonals: if False, no diagonals are used
    :param diagonal_fn: a callable for the diagonal
    :param output_activation: activation for the output layer (the SVD if applicable)
    :param hidden_activation: activation for hidden layers (all but the last if no SVD)
    :return: a tf.keras.Model
    """

    # if input_dim % 2 != 0:
    #     raise ValueError('input dimension must be even')

    # input_tensor = tf.keras.Input(shape=(None,))
    model = tf.keras.Sequential()
    # current_output = input_tensor

    for k in range(n_layers):
        for j in range(n_rotations):
            if use_permutations:
                # current_output = Permutation()(current_output)
                model.add(Permutation())
            # current_output = Rotation(theta_initializer=theta_initializer)(current_output)
            model.add(Rotation(theta_initializer=theta_initializer))

        if use_diagonals:
            # current_output = Diagonal(t_initializer=t_initializer, function=diagonal_fn)(current_output)
            model.add(Diagonal(t_initializer=t_initializer, function=diagonal_fn))

        for j in range(n_rotations):
            if use_permutations:
                # current_output = Permutation()(current_output)
                model.add(Permutation())
            # current_output = Rotation(theta_initializer=theta_initializer)(current_output)
            model.add(Rotation(theta_initializer=theta_initializer))

        if use_bias:
            # current_output = Bias(
            #     bias_initializer=bias_initializer)(current_output)
            model.add(Bias(bias_initializer=bias_initializer))
        if k != n_layers - 1:
            # current_output = activations.get(hidden_activation,
            #                                  trainable=trainable_M,
            #                                  M_init=M_init,
            #                                  M_initializer=M_initializer)(current_output)
            model.add(tf.keras.layers.Lambda(activations.get(hidden_activation,
                                                             trainable=trainable_M,
                                                             M_init=M_init,
                                                             M_initializer=M_initializer)))

    if output_dim:
        # current_output = SVDDownsize(output_dim)(current_output)
        model.add(SVDDownsize(output_dim))
    # current_output = activations.get(output_activation,
    #                                  trainable=trainable_M,
    #                                  M_init=M_init,
    #                                  M_initializer=M_initializer)(current_output)
    model.add(tf.keras.layers.Lambda(activations.get(output_activation,
                                                     trainable=trainable_M,
                                                     M_init=M_init,
                                                     M_initializer=M_initializer)))
    # return tf.keras.Model(input_tensor, current_output)
    return model
