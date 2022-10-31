import numpy as np
import pygame
import time
from grid import Grid, ColouredGrid


# owner: 0 = dead, 1 = player, 2 = enemy, 3 = shrapnel, 4 = what to defend/attack
COLOURS = {0 : (0, 0, 0), 1 : (0, 0, 255), 2 : (255, 0, 0), 3 : (225, 115, 20), 4 : (140, 0, 200)}
# some temporary colour definitions for easier GUI dev
BUILD_COLOUR = (30, 240, 80)
DEFAULT_BUTTON_COLOUR = (180,180,180)
BACKGROUND_COLOUR = (240,240,240)
BLACK, RED, GREEN, BLUE = (0,0,0), (255, 0, 0), (0,255,0), (0,0,255)


class Game:
    """Main game class to handle events and general gameplay"""
    def __init__(self, surface, grid, build_area, tickrate = 0.1, cell_size = 20, border_width = 30):
        self.surface = surface
        self.grid = ColouredGrid(grid) # get Grid object
        self.build_area = build_area
        self.time_on = False
        self.ingame = True
        self.cycles = 1
        self.cell_size = cell_size
        self.tickrate = tickrate
        self.border_width = border_width
        self.colours = COLOURS

    def main(self):
        self.start_time = time.perf_counter()
        self.surface.fill(BACKGROUND_COLOUR)
        pygame.draw.rect(self.surface, BUILD_COLOUR, self.build_area) # region where you are allowed to build
        while self.ingame:
            # get events
            self.handle_events(pygame.event.get())
            if time.perf_counter() - self.start_time - self.cycles * self.tickrate > 0: # true every 'tickrate' seconds
                self.cycles += 1
                if self.time_on: # only run update logic if time is turned on
                    self.grid.update_grid()
            self.draw()
            time.sleep(0.01)
    
    def handle_events(self, events):
        """top level function to delegate events"""
        for event in events:
            if event.type in (pygame.MOUSEBUTTONUP, pygame.MOUSEBUTTONDOWN) and event.button in (1, 3): # left/right click
                self.handle_click(event)
            elif event.type == pygame.KEYDOWN: # various keys
                if event.key == pygame.K_SPACE:
                    self.time_on = not self.time_on # flip time_on on space press
                elif event.key == pygame.K_ESCAPE: # currently returns to menu, eventually run open_escape()
                    self.ingame = False
            elif event.type == pygame.QUIT: # if x is clicked on top right of window
                pygame.quit()
                quit()
    
    def handle_click(self, click):
        """Find click target and execute"""
        # determine what was clicked
        # only do if time is stopped
        if not self.time_on:
            # if click is within build area
            if self.build_area.collidepoint(click.pos):
                coords = [int((axis - self.border_width)/self.cell_size + 2) for axis in click.pos[::-1]] # convert mouse click to numpy coords
                if click.type == pygame.MOUSEBUTTONDOWN and click.button == 1 and self.grid.array[coords[0], coords[1]] == 0: # when left click
                    self.grid.array[coords[0], coords[1]] = 1 # if the clicked cell is dead, make it a player owned cell
                if click.type == pygame.MOUSEBUTTONDOWN and click.button == 3:
                    if self.grid.array[coords[0], coords[1]] == 1: # if the clicked cell is player owned, make it dead
                        self.grid.array[coords[0], coords[1]] = 0

    def draw(self):
        """draw visible grid on pygame window"""
        mask_list = [np.equal(self.grid.array, n) for n in range(5)] # create boolean masks for each type of cell (0 through 4)
        # the next line is very densely packed to avoid wasteful memory intensive copies of potentially million item arrays. There is an explanation for how it works in commit Alpha v1.6
        pixel_array = sum([np.asarray(self.colours[n]) * np.transpose(np.broadcast_to(mask_list[n][:,:,None], (mask_list[n].shape[0], mask_list[n].shape[1], 3)), (1,0,2)) for n in range(5)])
        pixel_surf = pygame.surfarray.make_surface(pixel_array[2:-2,2:-2,:]) # make surface, excluding outer 5 rows/columns
        pixel_surf = pygame.transform.scale(pixel_surf, (pixel_surf.get_size()[0]*self.cell_size, pixel_surf.get_size()[1]*self.cell_size)) # scale by cell size
        self.surface.blit(pixel_surf, (self.border_width, self.border_width)) # draw
        pygame.display.update()




class LevelEditor(Game):
    """Please dear god for your sanity and mine don't try to figure this mess out
    it spent 30 minutes trying to refactor it, because it's copy and pasted code from like 3 different stages of developement"""
    def __init__(self, surface, grid, build_area):
        Game.__init__(self, surface, grid, build_area)

    def main(self):
        self.surface.fill(BACKGROUND_COLOUR)
        pygame.draw.rect(self.surface, BUILD_COLOUR, self.build_area)
        self.start_time = time.perf_counter()
        while self.ingame:
            # get events
            self.handle_events(pygame.event.get())

            if time.perf_counter() - self.start_time - self.cycles * self.tickrate > 0: # true every 'tickrate' seconds
                self.cycles += 1
                if self.time_on: # only run update logic if time is turned on
                    self.grid.update_grid()
            self.draw()
            time.sleep(0.01)

    def handle_events(self, events):
        """I would strongly recommend not looking too hard at this. It's copy and pasted
        code from like 3 stages of developement and has almost no comments"""
        for event in events:
            if event.type in (pygame.MOUSEBUTTONUP, pygame.MOUSEBUTTONDOWN) and event.button in (1, 3):
                mouse_x, mouse_y = event.pos
                # if click is within grid bounds
                if self.border_width < mouse_x < self.border_width + (self.grid.array.shape[1] - 4) * self.cell_size and self.border_width < mouse_y < self.border_width + (self.grid.array.shape[0] - 4) * self.cell_size:
                    coords = [int((axis - self.border_width)/self.cell_size + 2) for axis in event.pos[::-1]]
                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.grid.array[coords[0], coords[1]] < 4: # increment when left click
                        self.grid.array[coords[0], coords[1]] += 1
                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3 and self.grid.array[coords[0], coords[1]] > 0: # decrement when right click
                        self.grid.array[coords[0], coords[1]] -= 1
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    if self.time_on == False:
                        self.placeholder_grid = self.grid.array.copy()
                    else:
                        self.grid.array = self.placeholder_grid
                    self.time_on = not self.time_on
                elif event.key == pygame.K_ESCAPE:
                    self.ingame = False
                elif event.key == pygame.K_s: # save as csv
                    if self.time_on:
                        np.savetxt('savedgrid.csv', self.placeholder_grid, '%1.0f', delimiter=",")
                    else:
                        np.savetxt('savedgrid.csv', self.grid.array, '%1.0f', delimiter=",")
            elif event.type == pygame.QUIT:
                pygame.quit()
                quit()
