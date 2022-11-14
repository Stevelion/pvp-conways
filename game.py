import numpy as np
import pygame
import time
import json
from grid import ColouredGrid
from math import ceil
from lifegui import PrefabButton


# owner: 0 = dead, 1 = player, 2 = enemy, 3 = shrapnel, 4 = what to defend/attack
# some temporary colour definitions for easier GUI dev
BUILD_COLOUR = (30, 240, 80)
DEFAULT_BUTTON_COLOUR = (180,180,180)
BACKGROUND_COLOUR = (240,240,240)
BLACK, RED, GREEN, BLUE = (0,0,0), (255, 0, 0), (0,255,0), (0,0,255)


class Game:
    """Main game class to handle events and general gameplay.
    surface: surface to draw onto
    array: array of cells to initialize with
    tickrate: delay between grid.update() calls in seconds
    cell_size: default size of cells in pixels (may be removed later if zooming is added)
    border_width: size of gap between window border and grid in pixels (may be removed later if resizing is added)"""
    def __init__(self, surface, array, tickrate = 0.1, cell_size = 20, rect = (30, 30, 600, 600), build_area = None):
        self.surface = surface # what to draw on
        self.grid = ColouredGrid(array) # get Grid object
        self.tickrate = tickrate # how often in seconds to call grid.update()
        self.cell_size = cell_size # starting size of cells in pixels
        self.rect = pygame.Rect(rect) # rect the the game is inside of
        self.build_rects = build_area
        if build_area:
            self.build_area = np.zeros(self.grid.array.shape, dtype=bool)
            for rectangle in build_area:
                self.build_area[rectangle[0][0] : rectangle[1][0], rectangle[0][1] : rectangle[1][1]] = True
        else:
            self.build_area = np.ones(self.grid.array.shape, dtype=bool) # allow building everywhere, only really meant for sandbox
        self.time_on = False # is time running
        self.ingame = True # when to end game loop and return to menu
        self.game_over = False # if a base has been destroyed
        self.cycles = 1 # counter for tickrate math
        self.colours = {0 : (0, 0, 0), 1 : (0, 0, 255), 2 : (255, 0, 0), 3 : (225, 115, 20), 4 : (140, 0, 200), 5 : (10, 10, 10), 6 : (50, 90, 255)} # colour dict for draw()
        self.background = BACKGROUND_COLOUR
        self.rect_surface = pygame.Surface((self.rect[2], self.rect[3])) # intermediate surface to hide rolling edge of draw()
        self.view_coords = [(self.grid.array.shape[1]*cell_size - self.rect[3]) // 2,
                            (self.grid.array.shape[0]*cell_size - self.rect[2]) // 2] # list of top left viewable cell x,y coordinates
        self.MOVES = {pygame.K_UP : (0, -1),
                      pygame.K_DOWN : (0, 1),
                      pygame.K_LEFT : (-1, 0),
                      pygame.K_RIGHT : (1, 0)} # dict for how directions affect coords
        self.DIRECTIONS = {pygame.K_UP : False,
                           pygame.K_DOWN : False,
                           pygame.K_LEFT : False,
                           pygame.K_RIGHT : False} # dict for whether a direction is held
        self.buttons = [PrefabButton('Glider', (660, 200, 144, 100), np.genfromtxt('prefab/glider.csv', delimiter=','), parent=self, cell_size=12),
                        PrefabButton('Glider Gun', (660, 300, 144, 100), np.genfromtxt('prefab/gun.csv', delimiter=','), parent=self, cell_size=4)]
        self.selected_pattern = np.zeros((1,1))
        self.prefab_todraw_array = np.zeros(self.grid.array.shape, bool)
        self.last_grid = np.zeros(self.grid.array.shape) # initialize undo array to allow for checking in undo method


    def main(self):
        self.start_time = time.perf_counter()
        self.surface.fill(BACKGROUND_COLOUR)
        while self.ingame:
            # get events
            self.handle_events(pygame.event.get())
            if time.perf_counter() - self.start_time - self.cycles * self.tickrate > 0: # true every 'tickrate' seconds
                self.cycles += 1
                if self.time_on: # only run update logic if time is turned on
                    self.grid.update()
                    self.check_bases()
                for button in self.buttons:
                    if button.hovered: # update all buttons that are ticked as hovered, should only ever be 1
                        button.update()
            for direction in self.DIRECTIONS:  # check if each direction is held
                if self.DIRECTIONS[direction]: # if it is, scroll that way
                    self.move(direction)
            self.draw()
            time.sleep(0.01)
    

    def handle_events(self, events):
        """top level function to delegate events"""
        for event in events:
            if event.type == pygame.MOUSEMOTION: # find if mouse motion involved hovering or unhovering a button
                for button in self.buttons:
                    button.hover(event) # pass to each button, they turn flip a var that says whether to update at update step
                if np.any(self.selected_pattern) and self.rect.collidepoint(event.pos): # if a pattern is selected and mouse is over grid
                    self.draw_prefab()

            if event.type in (pygame.MOUSEBUTTONUP, pygame.MOUSEBUTTONDOWN):
                if event.button in (1, 3): # left/right click
                    self.handle_click(event)
                elif event.button in (4, 5): # scroll
                    self.handle_scroll(event)

            elif event.type == pygame.KEYDOWN: # various keys
                if event.key in (self.DIRECTIONS):
                    self.handle_direction_key(event)
                elif event.key == pygame.K_SPACE:
                    self.handle_space()
                elif event.key == pygame.K_ESCAPE:
                    self.handle_escape()
                elif event.key == pygame.K_s:
                    self.handle_s_key()
                elif event.key == pygame.K_r:
                    self.rotate_prefab()
                elif event.key in (pygame.K_t, pygame.K_f):
                    self.flip_prefab(event)
                elif event.key == pygame.K_z and pygame.key.get_mods() & pygame.KMOD_CTRL: # get_mods() returns a bitmask, must be bitwise &
                    self.undo()
            elif event.type == pygame.KEYUP:
                if event.key in (self.DIRECTIONS):
                    self.handle_direction_key(event)
            elif event.type == pygame.QUIT: # if x is clicked on top right of window
                pygame.quit()
                quit()


    def rotate_prefab(self):
        """rotates currently selected prefab clockwise"""
        if not np.any(self.selected_pattern): # no prefab selected
            return
        self.selected_pattern = np.rot90(self.selected_pattern, k=1, axes=(1, 0))
        self.draw_prefab() # update draw
    
    
    def flip_prefab(self, event):
        """flip currently selected prefab"""
        if not np.any(self.selected_pattern): # no prefab selected
            return
        if event.key == pygame.K_f: # key to flip vertically
            self.selected_pattern = np.flipud(self.selected_pattern)
        elif event.key == pygame.K_t: # key to flip horizontally
            self.selected_pattern = np.fliplr(self.selected_pattern)
        self.draw_prefab() # update draw


    def handle_direction_key(self, event):
        """toggle whether a key is pressed for move check"""
        if event.type == pygame.KEYDOWN:
            self.DIRECTIONS[event.key] = True
        else:
            self.DIRECTIONS[event.key] = False

    
    def undo(self):
        """takes the grid back one state, only works if time has not been turned on"""
        if np.any(self.last_grid) and not self.time_on: # if grid has been saved and time is off
            self.grid.array = self.last_grid


    def handle_scroll(self, event):
        """turn scroll wheel events into zooming in and out"""
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pixel = [self.view_coords[n] + event.pos[n] - self.rect[n] for n in range(2)] # store current center
            total_pixel = [(self.grid.array.shape[int(not n)]) * self.cell_size for n in range(2)] # store current bottom right pixel
            if event.button == 4: # mouse wheel scroll up
                self.cell_size += 5
            elif event.button == 5: # mouse wheel scroll down
                self.cell_size -= 5
                # catch zooming too far out (far enough that the grid can't cover the full rect)
                self.cell_size = max(5, self.cell_size, max(ceil(self.rect[2] / (self.grid.array.shape[1] - 4)), ceil(self.rect[3] / (self.grid.array.shape[0] - 4))))
            new_total_pixel = [(self.grid.array.shape[int(not n)]) * self.cell_size for n in range(2)] # get new bottom right pixel
            # multiply old center/total ratio by new total to get new center, then subtract half of rect size to find top left
            new_mouse_pixel = [int(mouse_pixel[n] / total_pixel[n] * new_total_pixel[n]) - event.pos[n] + self.rect[n] for n in range(2)]
            # catch overhang when zooming out next to border
            self.view_coords = [max(2 * self.cell_size, min(new_mouse_pixel[n], new_total_pixel[n] - self.rect[2+n] - 2 * self.cell_size)) for n in range(2)]
            if np.any(self.selected_pattern): # adjust prefab if needed
                self.draw_prefab()

    def handle_space(self):
        """flip time_on on space press"""
        if not self.game_over:
            self.time_on = not self.time_on
        self.last_grid = np.zeros(self.grid.array.shape) # clear undo array when time turns on or off


    def handle_escape(self):
        """currently returns to menu, eventually run open_escape()"""
        self.ingame = False

    
    def handle_s_key(self):
        """dummy method to be used as save hotkey by LevelEditor child"""
        pass

    
    def handle_click(self, event):
        """intermediary function to pass to various parts of game screen"""
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.last_grid = self.grid.array.copy() # save grid before click for undo if needed
            for button in self.buttons:
                if button.rect.collidepoint(event.pos):
                    button.function()
                    return
            if np.any(self.selected_pattern): # if there is a pattern selected
                self.handle_prefab_click(event)
                return
            if self.rect.collidepoint(event.pos):
                self.handle_grid_click(event)


    def handle_prefab_click(self, event):
        """what do do if player clicks while a prefab is selected"""
        if event.button == 1 and not self.time_on and not self.game_over: # if left click:
            self.grid.array = sum((self.grid.array, self.prefab_todraw_array)) # put pattern into grid
            self.selected_pattern = np.zeros((1,1)) # clear selected pattern
            self.prefab_todraw_array = np.zeros(self.grid.array.shape, bool) # clear draw array
        elif event.button == 3: # if right click
            self.selected_pattern = np.zeros((1,1)) # clear selected pattern
            self.prefab_todraw_array = np.zeros(self.grid.array.shape, bool) # clear draw array


    def handle_grid_click(self, event):
        """for clicks inside grid, translate click coords to grid coords, then translate to global array
        then interact appropriately with clicked cell"""
        if not self.time_on and not self.game_over: # only do if time is stopped
            # translate to global array coords (also needs to be y,x for numpy)
            coords = [(event.pos[n] - self.rect[n] + self.view_coords[n]) // self.cell_size for n in range(2)][::-1]
            if self.in_build_area(coords): # make sure player is allowed to change cell
            # interact with clicked cell
                if event.button == 1 and self.grid.array[coords[0], coords[1]] == 0: # on left click
                    self.grid.array[coords[0], coords[1]] = 1 # if the clicked cell is dead, make it a player owned cell
                elif event.button == 3 and self.grid.array[coords[0], coords[1]] == 1: # on right click
                        self.grid.array[coords[0], coords[1]] = 0 # if the clicked cell is player owned, make it dead


    def in_build_area(self, cell):
        """returns whether a cell is in the build area"""
        return self.build_area[cell[0], cell[1]] # return false if the cell is not in any rectangle of the build area


    def check_bases(self):
        """checks bases to see if any have been damaged and the game ends"""
        if np.any(self.grid.damaged_base):
            # convert to list of tuples
            damaged = [(np.nonzero(self.grid.damaged_base)[0][n], np.nonzero(self.grid.damaged_base)[1][n]) for n in range(len(np.nonzero(self.grid.damaged_base)[0]))]
            for cell in damaged:
                if self.in_build_area(cell): # if inside build area (therefore owned by player)
                    print('You lost') # TODO replace later with ingame message
                    break
            else: # if loop terminates normally (none owned by player)
                print('You won!') # TODO replace later with ingame message
            self.game_over = True
            self.time_on = False


    def move(self, direction, size = 10):
        self.view_coords = [self.view_coords[n] + (self.MOVES[direction][n] * size) for n in range(2)] # shift view in direction
        # catch view going past edge of array
        self.view_coords = [min(max(2 * self.cell_size, self.view_coords[n]), (self.grid.array.shape[int(not n)] - 2) * self.cell_size - self.rect[n+2]) for n in range(2)]
        if np.any(self.selected_pattern): # adjust prefab if needed
            self.draw_prefab()
    

    def draw_prefab(self):
        """check whether do draw prefab and create array to draw later"""
        # translate to global array coords (also needs to be y,x for numpy) uses mouse.get_pos() instead of an event to handle scrolling and zoom
        coords = [(pygame.mouse.get_pos()[n] - self.rect[n] + self.view_coords[n]) // self.cell_size for n in range(2)][::-1]
        if coords[0] - self.selected_pattern.shape[0] < 1 or coords[1] + self.selected_pattern.shape[1] > self.grid.array.shape[1] - 2:
            self.prefab_todraw_array = np.zeros(self.grid.array.shape, bool) # if bounding box goes outside of grid
            return
        self.bounding_mask = np.ones(self.selected_pattern.shape, bool) # create array of trues the size of the pattern bounding box
        self.bounding_mask = np.append(np.zeros((coords[0] - self.bounding_mask.shape[0] + 1, self.bounding_mask.shape[1]), bool), self.bounding_mask, 0) # expand top
        self.bounding_mask = np.append(np.zeros((self.bounding_mask.shape[0], coords[1]), bool), self.bounding_mask, 1) # expand left
        self.bounding_mask = np.append(self.bounding_mask, np.zeros((self.grid.array.shape[0] - self.bounding_mask.shape[0], self.bounding_mask.shape[1]), bool), 0) # expand bottom
        self.bounding_mask = np.append(self.bounding_mask, np.zeros((self.bounding_mask.shape[0], self.grid.array.shape[1] - self.bounding_mask.shape[1]), bool), 1) # expand right
        if np.max(np.logical_xor(np.logical_and(self.bounding_mask, self.build_area), self.bounding_mask)): # combine bounding mask and build area, returns fewer trues if bounding box is outside
            self.prefab_todraw_array = np.zeros(self.grid.array.shape, bool) # only if bounding box goes outside of build area
            return
        # create a boolean mask out of the pattern as an intermediate step to check for cell collisions
        self.pattern_mask = self.selected_pattern.astype(bool)
        self.pattern_mask = np.append(np.zeros((coords[0] - self.pattern_mask.shape[0] + 1, self.pattern_mask.shape[1]), bool), self.pattern_mask, 0) # expand top
        self.pattern_mask = np.append(np.zeros((self.pattern_mask.shape[0], coords[1]), bool), self.pattern_mask, 1) # expand left
        self.pattern_mask = np.append(self.pattern_mask, np.zeros((self.grid.array.shape[0] - self.pattern_mask.shape[0], self.pattern_mask.shape[1]), bool), 0) # expand bottom
        self.pattern_mask = np.append(self.pattern_mask, np.zeros((self.pattern_mask.shape[0], self.grid.array.shape[1] - self.pattern_mask.shape[1]), bool), 1) # expand right
        if np.max(np.logical_and(self.pattern_mask, self.grid.array.astype(bool))): # if any cells are already living and part of the pattern
            self.prefab_todraw_array = np.zeros(self.grid.array.shape, bool)
            return
        else: # if it reaches this, pattern is within grid, within build area, and doesn't collide with any current cells
            self.prefab_todraw_array = self.pattern_mask.copy() # finally make the todraw array the pattern
            return


    def draw(self):
        """draw visible grid on pygame window"""
        # add in build area cosmetically
        self.grid_and_prefab = sum((self.grid.array, self.prefab_todraw_array * 6)) # add prefab cells, should already be checked for cell collisions
        self.draw_grid = sum((self.grid_and_prefab, (np.logical_and(self.build_area, np.logical_not(self.grid_and_prefab.astype(bool))) * 5)))
        # slice array to only operate on visible part of grid
        self.viewable_grid = self.draw_grid[self.view_coords[1] // self.cell_size : (self.view_coords[1] + self.rect[3]) // self.cell_size + 1,
                                       self.view_coords[0] // self.cell_size : (self.view_coords[0] + self.rect[2]) // self.cell_size + 1]
        mask_list = [np.equal(self.viewable_grid, n) for n in range(7)] # create boolean masks for each type of cell (0 through 4)
        # the next line is very densely packed to avoid wasteful memory intensive copies of potentially million item arrays. There is an explanation for how it works in commit Alpha v1.6
        self.pixel_array = sum([np.asarray(self.colours[n]) * np.transpose(np.broadcast_to(mask_list[n][:,:,None], (mask_list[n].shape[0], mask_list[n].shape[1], 3)), (1,0,2)) for n in range(7)])
        self.pixel_surf = pygame.surfarray.make_surface(self.pixel_array) # make surface
        self.pixel_surf = pygame.transform.scale(self.pixel_surf, (self.pixel_surf.get_size()[0]*self.cell_size, self.pixel_surf.get_size()[1]*self.cell_size)) # scale by cell size
        self.pixel_surf.scroll(-(self.view_coords[0] % self.cell_size), -(self.view_coords[1] % self.cell_size)) # scroll surface by the offset (I think it just shifts all pixels in a direction)
        self.surface.blit(self.rect_surface, self.rect) # draw intermediate surface to hide hanging pixels at edge
        self.rect_surface.blit(self.pixel_surf, (0,0)) # draw
        for button in self.buttons:
            button.draw(self.surface)
        pygame.display.update()




class LevelEditor(Game):
    """Child class for the level editor
    works very similarly to Game except for some functionality to help with level building and a save function"""
    def __init__(self, surface, array, build_area=(((0,0),(0,0)),), cell_size=20):
        Game.__init__(self, surface, array, build_area=build_area, cell_size=cell_size)

    def handle_space(self):
        if self.time_on == False:
            self.placeholder_grid = self.grid.array.copy()
        else:
            self.grid.array = self.placeholder_grid
        self.time_on = not self.time_on
    
    def handle_s_key(self):
        if self.time_on:
            np.savetxt('savedgrid.csv', self.placeholder_grid, '%1.0f', delimiter=",")
            with open('savedgrid.json', 'w') as f:
                json.dump({'array' : 'savedgrid.csv',
                            'build_area' : self.build_rects}, f)
        else:
            np.savetxt('savedgrid.csv', self.grid.array, '%1.0f', delimiter=",")
            with open('savedgrid.json', 'w') as f:
                json.dump({'array' : 'savedgrid.csv',
                            'build_area' : self.build_rects}, f)

    def handle_grid_click(self, event):
        """for clicks inside grid, translate click coords to grid coords, then translate to global array
        then interact appropriately with clicked cell"""
        if not self.time_on: # only do if time is stopped
            # translate to global array coords (also needs to be y,x for numpy)
            coords = [(event.pos[n] - self.rect[n] + self.view_coords[n]) // self.cell_size for n in range(2)][::-1]
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.grid.array[coords[0], coords[1]] < 4:
                self.grid.array[coords[0], coords[1]] += 1 # increment when left click
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3 and self.grid.array[coords[0], coords[1]] > 0:
                self.grid.array[coords[0], coords[1]] -= 1 # decrement when right click
    
    def check_bases(self):
        """don't check bases in the editor"""
        pass
