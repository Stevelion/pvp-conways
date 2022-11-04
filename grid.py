import numpy as np



class Grid:
    """Abstract class that evaluates CGoL logic on an array"""
    def __init__(self, array):
        self.array = array

    def update(self):
        self.bool_array = self.array.astype(bool)
        self.living = self.bool_array.astype(int) # convert to binary
        self.neighbors = self.get_neighbors(self.living) # get neighbors
        self.has_3 = np.equal(self.neighbors, 3)
        self.has_2or3 = np.logical_or(self.has_3, np.equal(self.neighbors, 2))
        self.become_living = np.logical_and(self.has_3, np.logical_not(self.living.astype(bool))) # find dead cells that turn living
        self.stay_living = np.logical_and(self.living.astype(bool), self.has_2or3) # find living cells that stay living
        self.new_living = np.logical_or(self.become_living, self.stay_living) # add together (important they stay seperate for child class usage)
        self.update_cell()
        # clean up edges
        for n in range(2):
            self.array[n, :] = self.array[n, :] * 0
            self.array[-n-1, :] = self.array[-n-1, :] * 0
            self.array[:, n] = self.array[:, n] * 0
            self.array[:, -n-1] = self.array[:, -n-1] * 0
    
    def get_neighbors(self, array): 
        """rolling algorithm to find neighbors"""
        self.top = np.roll(array, 1, 0)
        self.bottom = np.roll(array, -1, 0)
        # packed together to avoid unnecessary large array storage, only rolls that need to be reused are top and bottom
        return self.top + self.bottom + np.roll(array, 1, 1) + np.roll(array, -1, 1) + np.roll(self.top, 1, 1) + np.roll(self.top, -1, 1) + np.roll(self.bottom, 1, 1) + np.roll(self.bottom, -1, 1)

    def update_cell(self):
        """dummy function to allow child classes to handle final array differently
        takes boolean array of living, returns 0s and 1s, prossibly not even necessary"""
        self.array = self.new_living.astype(int)



class ColouredGrid(Grid):
    """child grid function to handle 5 cell types instead of only 2"""
    def __init__(self, array):
        Grid.__init__(self, array)
        self.bases = np.equal(self.array, 4) # create a mask of all base cells
    
    def update_cell(self):
        """new colouring logic handled by numpy instead of python"""
        self.mask_list = [np.equal(self.array, n) for n in range(5)] # create masks of each type from old array
        self.mask_neighbors = {} # initialize dict of masks of whether a cell has a neighbor of type n
        for n in range(1, 5): # fill aforementioned dict
            self.mask_top = np.roll(self.mask_list[n], 1, 0)
            self.mask_bottom = np.roll(self.mask_list[n], -1, 0)
            # create dicts of neighbor types
            self.mask_neighbors[n] = (sum((self.mask_top, self.mask_bottom, np.roll(self.mask_list[n], 1, 1), np.roll(self.mask_list[n], -1, 1),
                                     np.roll(self.mask_top, 1, 1), np.roll(self.mask_top, -1, 1), np.roll(self.mask_bottom, 1, 1), np.roll(self.mask_bottom, -1, 1)))).astype(bool)
        # create type masks
        self.single_neighbor_mask = np.equal(sum(self.mask_neighbors.values()), 1) # has exactly 1 type of living neighbor
        self.mult_neighbor_mask = np.greater(sum(self.mask_neighbors.values()), 1) # has more than 1 type of neighbor
        # create masks of whether a cell should be coloured that type
        self.type_masks = {n : np.logical_or(self.mask_list[n], np.logical_and(self.mask_neighbors[n], self.single_neighbor_mask)) for n in (1, 2, 4)}
        self.type_masks[3] = np.logical_or(self.mask_list[3], np.logical_and(np.logical_not(self.bool_array), np.logical_or(self.mask_neighbors[3], self.mult_neighbor_mask)))
        # to remove overlap if orange cell alive but has only 1 neighbor type
        self.not_3 = np.logical_not(self.type_masks[3])
        for n in (1,2,4):
            self.type_masks[n] = self.type_masks[n] * self.not_3
        # combine type masks into a colour field to be masked by Grid.new_living
        self.colour_field = sum([self.type_masks[n] * n for n in range(1,5)])
        self.array = self.colour_field * self.new_living
        self.damaged_base = np.logical_xor(self.bases, np.equal(self.array, 4)) # True if any base cell changed from init mask to now

