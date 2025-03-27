import numpy as np

def compute_dist_angle(hyp, y_offset, y_pos):
    """Computes the distance on x as well as the angle of XXX 

    Args:
        hyp (float): Hypothenuse of the triangle
        y_offset (float): Position on y of the horizontal line (adjacent)
        y_pos (float): Position of the target (x, y), the end position of the hypotenuse

    Returns:
        dist(float), angle(float): Returns the distance on x and the angle of the hypotenuse
    """
    delta_y = y_pos - y_offset
    xProj = np.sqrt(hyp**2 - (delta_y)**2)
    angle = np.arcsin(delta_y/ hyp)
    return xProj, angle


def interpolate_circle(diameter:float, nbPoints:int):
    """Interpolates a circle with a given radius, and a given number of points

    Args:
        diamater (float): diameter of the circle
        nbPoints (int): Number of points to interpolate

    Returns:
        np.array: Returns an array of size nbPoints x 2, with the x and y coordinates of the circle
    """
    circle = np.zeros((nbPoints, 2))
    radius = diameter / 2
    for i in range(nbPoints):
        circle[i,0] = radius * np.cos(2*np.pi*i/nbPoints)
        circle[i,1] = radius * np.sin(2*np.pi*i/nbPoints)
    return circle


def interpolate_line(length:float, nbPoints:int):
    """Interpolates a line with a given length, and a given number of points

    Args:
        length (float): Length of the line
        nbPoints (int): Number of points to interpolate

    Returns:
        np.array: Returns an array of size nbPoints x 2, with the x and y coordinates of the line
    """
    line = np.zeros((nbPoints, 2))
    for i in range(nbPoints):
        line[i,0] = i * length / nbPoints
        line[i,1] = 0
    line[:,0] -= length/2 # center the line
    return line


def interpolate_square(side:float, nbPoints:int):
    """Interpolates a square with a given side, and a given number of points

    Args:
        side (float): Side of the square
        nbPoints (int): Number of points to interpolate

    Returns:
        np.array: Returns an array of size nbPoints x 2, with the x and y coordinates of the square
    """
    square = np.zeros((nbPoints, 2))
    for i in range(nbPoints):
        if i < nbPoints/4:
            square[i,0] = i * side / nbPoints*4
            square[i,1] = 0
        elif i < nbPoints/2:
            square[i,0] = side
            square[i,1] = (i - nbPoints/4) * side / nbPoints*4
        elif i < 3*nbPoints/4:
            square[i,0] = side - (i - nbPoints/2) * side / nbPoints*4
            square[i,1] = side
        else:
            square[i,0] = 0
            square[i,1] = side - (i - 3*nbPoints/4) * side / nbPoints*4
    square -= (side/2, side/2)
    return square