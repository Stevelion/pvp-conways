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
        """partially copy and pasted code from old Grid class, however it now only runs on cells that become alive, not all cells that could
        change state"""
        self.new_living_indices = np.nonzero(self.become_living) # get indices of cells becoming alive
        self.new_array = self.array.copy() * self.new_living.astype(int) # remove dying cells from new array
        for n in range(len(self.new_living_indices[0])): # for each cell, create a 3x3 kernel around it, then use it to determine colour
            kernel = self.array[self.new_living_indices[0][n]-1:self.new_living_indices[0][n]+2, self.new_living_indices[1][n]-1:self.new_living_indices[1][n]+2]
            nonzero = np.nonzero(kernel)
            # # if all neighbors the same, return it
            if len(set([kernel[nonzero[0][n], nonzero[1][n]] for n in range(len(nonzero[0]))])) == 1:
                self.new_array[self.new_living_indices[0][n], self.new_living_indices[1][n]] = np.max(kernel)
            else: # if not all neighbors the same, return 3 (debris)
                self.new_array[self.new_living_indices[0][n], self.new_living_indices[1][n]] = 3
        self.array = self.new_array
        self.damaged_base = np.logical_xor(self.bases, np.equal(self.array, 4)) # True if any base cell changed from init mask to now