"""All random generators for Terrain class."""

from terrain import Terrain
import random
import abc
import math


class TerrainGenerator(object):
    """Abstract noise generator that makes a Terrain with heights produced from noise."""

    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def __call__(self, *args, **kwargs):
        """Generate a Terrain with heights corresponding to noise.

        Returns:
            Terrain: New Terrain with heights corresponding to noise.

        """


class DiamondSquareGenerator(TerrainGenerator):
    """Terrain generator that used diamond-square algorithm."""

    def __init__(self, amp_from_freq):
        """

        Args:
            amp_from_freq (function): Function that converts frequency to maximum amplitude.

        """
        self.amp_from_freq = amp_from_freq

    def __call__(self, side_exp):
        """Generate a Terrain with heights corresponding to noise.

        Used diamond-square algorithm, with frequency of noise at each step doubling.
        Colored_noise will use the frequency to generate the offset noise.

        Width and length are equal, and length must be of form 2**n + 1 (n >= 0).

        Args:
            side_exp (int): Exponent of side length. Length of side is 2**side_exp + 1.

        Returns:
            Terrain: New Terrain with heights corresponding to noise.

        """
        side_len = (2 ** side_exp) + 1
        ter = Terrain(side_len, side_len)
        return self._divide(self._initialize_corners(ter, 0.5), side_len-1)

    def _initialize_corners(self, terrain, init_val):
        """Initialize corner values of terrain.

        Args:
            terrain (Terrain): Terrain to initialize edges of.
            init_val (float): Initial value to set all corners to, between 0 and 1.

        Returns:
            Terrain: Terrain with corners set to init_val.

        """
        terrain[0, 0] = init_val
        terrain[0, terrain.length-1] = init_val
        terrain[terrain.width-1, 0] = init_val
        terrain[terrain.width-1, terrain.length-1] = init_val
        return terrain

    def _divide(self, terrain, square_len):
        """Divide terrain into squares and process each square recursively.

        Goes through each square, altering midpoint. After this, go through each diamond, altering edges.
        (Altering constitutes setting the value to an average of adjacent values and adding a noise offset.)
        Once all are done, halve size of each square and do _divide again on half-size squares.
        Once square size goes below 1, finish.

        Args:
            terrain (Terrain): Terrain to manipulate. Must have corners initialized.
            square_len (int): Current length of one side of a square.

        Returns:
            Terrain: New terrain with generated values.

        """
        half = square_len / 2

        if half < 1:
            return terrain
        else:
            # loop through all squares
            for y in range(half, terrain.length, square_len):
                for x in range(half, terrain.width, square_len):
                    terrain = self._update_square(terrain, x, y, square_len)
            # loop through all diamonds
            for y in range(0, terrain.length, half):
                for x in range((y + half) % square_len, terrain.width, square_len):
                    terrain = self._update_diamond(terrain, x, y, square_len)
            return self._divide(terrain, half)

    def _update_square(self, terrain, x, y, square_len):
        """Update the midpoint of a square.

        Midpoint becomes average of square corners plus a random offset determined by noise.

        Args:
            terrain (Terrain): Terrain to update.
            x (int): X coordinate of center of square.
            y (int): Y coordinate of center of square.
            square_len (int): Length of one side of square.

        Returns:
            Terrain: New terrain with updated square center.

        """
        half_len = square_len / 2
        # Impossible to attempt to access neighbours out of terrain bounds
        mean_height = sum([terrain[x - half_len, y - half_len],
                           terrain[x - half_len, y + half_len],
                           terrain[x + half_len, y - half_len],
                           terrain[x + half_len, y + half_len]]) / 4.0
        frequency = terrain.length / square_len
        offset = (random.random() - 0.5) * self.amp_from_freq(frequency)
        if not 0 <= mean_height + offset <= 1:
            if mean_height + offset > 1:
                terrain[x, y] = 1
            else:
                terrain[x, y] = 0
        else:
            terrain[x, y] = mean_height + offset
        return terrain

    def _update_diamond(self, terrain, x, y, diamond_len):
        """Update the midpoint of a diamond.

        Midpoint becomes average of diamond corners plus a random offset determined by noise.

        Args:
            terrain (Terrain): Terrain to update.
            x (int): X coordinate of center of diamond.
            y (int): Y coordinate of center of diamond.
            diamond_len (int): Length of one corner of diamond to other.

        Returns:
            Terrain: New terrain with updated square center.

        """
        half_len = diamond_len / 2
        # If on edge of terrain, only access 3 neighbours to avoid leaving terrain bounds
        neighbours = []
        if x != 0:
            neighbours.append(terrain[x - half_len, y])
        if y != 0:
            neighbours.append(terrain[x, y - half_len])
        if x != terrain.width - 1:
            neighbours.append(terrain[x + half_len, y])
        if y != terrain.length - 1:
            neighbours.append(terrain[x, y + half_len])
        mean_height = sum(neighbours) / float(len(neighbours))
        frequency = terrain.length / diamond_len
        offset = (random.random() - 0.5) * self.amp_from_freq(frequency)
        if not 0 <= mean_height + offset <= 1:
            if mean_height + offset > 1:
                terrain[x, y] = 1
            else:
                terrain[x, y] = 0
        else:
            terrain[x, y] = mean_height + offset
        return terrain


class RedNoiseGenerator(DiamondSquareGenerator):
    """Diamond square terrain generator with red noise (amplitude = 1 / (frequency^2))."""

    def __new__(cls, *args, **kwargs):
        return DiamondSquareGenerator(lambda f: f ** -2)


class PinkNoiseGenerator(DiamondSquareGenerator):
    """Diamond square terrain generator with pink noise (amplitude = 1 / frequency)."""

    def __new__(cls, *args, **kwargs):
        return DiamondSquareGenerator(lambda f: f ** -1)


class WhiteNoiseGenerator(DiamondSquareGenerator):
    """Diamond square terrain generator with white noise (amplitude = 1)."""

    def __new__(cls, *args, **kwargs):
        return DiamondSquareGenerator(lambda f: 1)


class BlueNoiseGenerator(DiamondSquareGenerator):
    """Diamond square terrain generator with blue noise (amplitude = frequency)."""

    def __new__(cls, *args, **kwargs):
        return DiamondSquareGenerator(lambda f: f)


class VioletNoiseGenerator(DiamondSquareGenerator):
    """Diamond square terrain generator with violet noise (amplitude = frequency^2)."""

    def __new__(cls, *args, **kwargs):
        return DiamondSquareGenerator(lambda f: f ** 2)


class PerlinGenerator(TerrainGenerator):
    """Terrain generator that uses Perlin noise algorithm."""

    def __init__(self, square_len, width_in_squares, length_in_squares):
        """

        Args:
            square_len (int): Length of one side of a square in Perlin noise grid. Is > 0.
            width_in_squares (int): Width of generated terrain in grid squares. Is > 0.
            length_in_squares (int): Length of generated terrain in grid squares. Is > 0.

        """
        self._square_len = square_len
        self._width_in_squares = width_in_squares
        self._length_in_squares = length_in_squares
        self.terr = Terrain(square_len * self._width_in_squares, square_len * self._length_in_squares)

    def _init_gradients(self, vec_magnitude):
        """Initialize all gradient vectors.

        Args:
            vec_magnitude (float): Magnitude of all gradient vectors.

        """
        self._grad_vecs = [[(0, 0) for _ in range(self._width_in_squares)] for _ in range(self._length_in_squares)]
        """list[list[tuple(float, float)]]: Grid of gradient vectors."""
        for x in range(self._width_in_squares):
            for y in range(self._length_in_squares):
                x_val = random.random() * vec_magnitude
                y_val = math.sqrt(vec_magnitude**2 - x_val**2)
                self._grad_vecs[y][x] = (x_val, y_val)

    def __call__(self, interp_func=None):
        """Generate terrain via Perlin noise.

        Does this by choosing a random gradient vector for each grid corner
        and taking their dot products with the displacement vectors to each point in the grid.
        The generated values are added onto each point within each grid square,
        and then interpolated between.

        Args:
            interp_func (function): Function to specify linear interpolation.

        Returns:
            Terrain: Generated terrain.

        """
        pass
