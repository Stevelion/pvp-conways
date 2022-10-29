import numpy as np

# Font characters courtesy of my boyfriend

class Font:
    """turns characters and strings into 12 tall (including 3 underline spaces for p, g, q) characters
    must be initialized first by creating a font object"""
    def __init__(self):
        uppers = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        lowers = 'abcdefghijklmnopqrstuvwxyz'
        numbers = '0123456789'
        self.font = {}
        for char in uppers:
            self.font[char] = np.genfromtxt('font/uppers/' + char + '.csv', delimiter=',')
        for char in lowers:
            self.font[char] = np.genfromtxt('font/lowers/' + char + '.csv', delimiter=',')
        for char in numbers:
            self.font[char] = np.genfromtxt('font/numbers/' + char + '.csv', delimiter=',')
        self.font[' '] = np.zeros((12,1))
        self.chars = uppers + lowers + numbers + ' '

    def as_grid(self, input = str, size = tuple):
        """returns input as an array of 1s and 0s drawing the characters
        size is minimum size of return array, passing (0,0) ignores this"""
        if input[0] in self.chars:
            array = self.font[input[0]] # begin array
        else:
            array = np.zeros((12,1)) # begin array
        if len(input) > 1:
            for char in input[1:]: # if input is longer than 1 character, add each character to array
                if char in self.chars:
                    array = np.append(array, np.zeros((12,1)), 1)
                    array = np.append(array, self.font[char], 1)
                else:
                    array = np.append(array, np.zeros((12,1)), 1)
        return self.expand_grid(array, size) # expand array with 0s to minimum size if necessary

    def expand_grid(self, array = np.ndarray, size = tuple):
        """expands array with 0s in all directions"""
        x_expand, y_expand = 0, 0
        new_array = array.copy()
        if size[0] > array.shape[1]: # if min x not met
            x_expand += (size[0] - array.shape[1]) // 2
            if x_expand: # if min x not met
                new_array = np.append(np.zeros((new_array.shape[0], x_expand)), new_array, 1) # expand x axis in both directions with 0s
                new_array = np.append(new_array, np.zeros((new_array.shape[0], x_expand)), 1)
            if x_expand * 2 != (size[0] - array.shape[1]): # check for odd lost in int division
                new_array = np.append(np.zeros((new_array.shape[0], 1)), new_array, 1)
        if size[1] > array.shape[0]: # if min y not met
            y_expand += (size[1] - array.shape[0]) // 2
            if y_expand: # if min y not met
                new_array = np.append(np.zeros((y_expand + 1, new_array.shape[1])), new_array, 0) # expand y axis in both directions with 0s
                new_array = np.append(new_array, np.zeros((y_expand - 1, new_array.shape[1])), 0)
            if y_expand * 2 != (size[1] - array.shape[0]): # check for odd lost in int division
                new_array = np.append(new_array, np.zeros((1, new_array.shape[1])), 0)
        return new_array
