import tensorflow as tf
import numpy as np


class Permutation(tf.keras.layers.Layer):
    def __init__(self, seed=None, **kwargs):
        super().__init__(**kwargs)
        self.permutation = None
        self.seed = seed

    def get_config(self):
        conf = super().get_config()
        conf.update({'seed': self.seed})
        return conf

    def compute_output_shape(self, input_shape):
        return input_shape

    def build(self, input_shape):
        dim = input_shape[-1]
        if self.seed:
            np.random.seed(self.seed)
        self.permutation = np.random.permutation(dim)
        super().build(input_shape)

    def call(self, inputs, **kwargs):
        return tf.gather(inputs, self.permutation, axis=-1)


class Rotation(tf.keras.layers.Layer):
    def __init__(self, theta_initializer='uniform', **kwargs):
        super().__init__(**kwargs)
        self.units = None
        self.theta = None
        self.theta_initializer = theta_initializer

    def get_config(self):
        conf = super().get_config()
        conf.update({'theta_initializer': self.theta_initializer})
        return conf

    def compute_output_shape(self, input_shape):
        return input_shape

    def build(self, input_shape):
        self.units = input_shape[-1]
        if self.units % 2 == 1:
            raise ValueError('Rotation layer only works on an even number of inputs')
        self.theta = self.add_weight(name='theta',
                                     initializer=self.theta_initializer,
                                     shape=(self.units//2,))
        super().build(input_shape)

    def call(self, inputs, **kwargs):
        cos = tf.cos(self.theta)
        sin = tf.sin(self.theta)
        xi = inputs[..., ::2]
        xj = inputs[..., 1::2]
        yi = cos * xi - sin * xj
        yj = cos * xj + sin * xi
        return tf.reshape(tf.stack([yi, yj], axis=-1), tf.shape(inputs))


class Diagonal(tf.keras.layers.Layer):
    def __init__(self, t_initializer='uniform', function=None, **kwargs):
        super().__init__(**kwargs)
        self.units = None
        self.t = None
        self.t_initializer = t_initializer
        self.function = function or tf.nn.sigmoid

    def get_config(self):
        conf = super().get_config()
        conf.update({'t_initializer': self.t_initializer,
                     'function': self.function})
        return conf

    def compute_output_shape(self, input_shape):
        return input_shape

    def build(self, input_shape):
        self.units = input_shape[-1]
        self.t = self.add_weight(name='t',
                                 initializer=self.t_initializer,
                                 shape=(self.units,))
        super().build(input_shape)

    def call(self, inputs, **kwargs):
        f = self.function(self.t)
        vec = f / tf.roll(f, -1, 0)
        return inputs * vec


class Bias(tf.keras.layers.Layer):
    def __init__(self, bias_initializer='uniform', **kwargs):
        super().__init__(**kwargs)
        self.bias = None
        self.units = None
        self.bias_initializer = bias_initializer

    def get_config(self):
        conf = super().get_config()
        conf.update({'bias_initializer': self.bias_initializer})
        return conf

    def compute_output_shape(self, input_shape):
        return input_shape

    def build(self, input_shape):
        self.units = input_shape[-1]
        self.bias = self.add_weight(name='bias',
                                    initializer=self.bias_initializer,
                                    shape=(self.units,))
        super().build(input_shape)

    def call(self, inputs, **kwargs):
        return inputs + self.bias


class SVDDownsize(tf.keras.layers.Layer):
    def __init__(self, units, **kwargs):
        self.Z = None
        self.units = units
        super().__init__(**kwargs)

    def get_config(self):
        conf = super().get_config()
        conf.update({'units': self.units})
        return conf

    def compute_output_shape(self, input_shape):
        return input_shape[:-1] + (self.units,)

    def build(self, input_shape):
        v = np.random.normal(size=(input_shape[-1], self.units))
        z = np.linalg.svd(v, full_matrices=False)[0]
        self.Z = tf.Variable(z, dtype=tf.float32, trainable=False)
        super().build(input_shape)

    def call(self, inputs, **kwargs):
        return tf.matmul(inputs, self.Z)