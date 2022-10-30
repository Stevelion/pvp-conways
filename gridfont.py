import numpy as np

# Font characters courtesy of my boyfriend

class Font:
    """turns characters and strings into 12 tall (including 3 underline spaces for p, g, q) characters
    all coordinates are read (x, y)
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
        self.inventory = 'Aa Bb Cc Dd Ee Ff Gg Hh Ii Jj Kk Ll Mm Nn Oo Pp Qq Rr Ss Tt Uu Vv Ww Xx Yy Zz 0123456789'

    def arrange(self, text = str, width = int, spacing = 1, centered = False):
        """takes a text input, translates to gridfont, and adds text wrapping for large bodies of text
        width is the maximum width of a line, spacing is the amount of cells in the gap between lines"""
        text = text.split()
        body = np.zeros((1, width)) # initialize an array to append to, will be removed later
        n = 0
        while n < len(text): # each loop creates a new row of text then appends it to the bottom
            row = self.as_grid(text[n])
            if row.shape[1] > width: # if a word in the text is too large for size, return a blank array
                row = np.zeros((12, width)) # of the correct size to prevent crashing
                break
            n += 1
            if not row.shape[1] > width - 3: # add a space if there is room (a space is 3 wide)
                row = np.append(row, np.zeros((12,3)), 1)
            while row.shape[1] < width and n < len(text):
                word = self.as_grid(text[n])
                if row.shape[1] + word.shape[1] > width: # if no room for next word
                    break                                # break to end of line logic
                row = np.append(row, word, 1) # add word to row
                n += 1
                if row.shape[1] > width - 3: # break if no room for space
                    break
                row = np.append(row, np.zeros((12,3)), 1) # add a space
            if not centered and row.shape[1] < width: # fill in remaining whitespace at end
                row = np.append(row, np.zeros((12, width - row.shape[1])), 1)
            elif centered:
                while not np.sum(row[:,-1]): # repeat until last column is not empty
                    row = np.delete(row, -1, 1) # delete last column
                row = self.expand_grid(row, (width, 0)) # fill in whitespace on both sides
            body = np.append(body, row, 0) # append row to body
            body = np.append(body, np.zeros((spacing, width)), 0) # add whitespace between rows
        body = np.delete(body, 0, 0) # remove initialization row
        for r in range(spacing): # remove final row of spacing
            body = np.delete(body, -1, 0)
        return body

    def as_grid(self, input = str):
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
        return array

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


font = Font()
