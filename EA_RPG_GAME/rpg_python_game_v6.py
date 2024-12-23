# rpg_ea_pde.py
# -*- coding: utf-8 -*-
"""
A small PDE-style Python + Pygame RPG with:
 - Weighted random map generation (favoring grass).
 - Guaranteed grass zone in the center.
 - Partial "view radius" around the player (like PDE).
 - Slimes & Dragons spawn on walkable tiles.
 - The avatar can move and is visible.

Author: Woody
Date:   December 23, 2024
"""

import pygame
import sys
import random

pygame.init()

SCREEN_WIDTH   = 800
SCREEN_HEIGHT  = 600

MAP_ROWS = 15
MAP_COLS = 20


RADIUS = 4
VIEW_SIZE = RADIUS * 2 + 1  # total tiles horizontally & vertically


TILE_WIDTH  = SCREEN_WIDTH  // VIEW_SIZE
TILE_HEIGHT = SCREEN_HEIGHT // VIEW_SIZE

# Weighted random tiles
#  0=mountain,1=river,2=grass,3=rock,4=riverrock

WEIGHTED_TILES = (["0","1","2","3","4"], [0.05,0.05,0.70,0.05,0.15])

# Entity types
ENTITY_PLAYER = "player"
ENTITY_SLIME  = "slime"
ENTITY_DRAGON = "dragon"


POPULATION_SIZE   = 6
NUM_GENERATIONS   = 4
MUTATION_RATE     = 0.05

CENTER_ZONE_RADIUS = 3


mountain_img  = pygame.image.load("mountain.png")
river_img     = pygame.image.load("river.png")
grass_img     = pygame.image.load("grass.png")
rock_img      = pygame.image.load("rock.png")
riverrock_img = pygame.image.load("riverstone.png")
empty_img     = pygame.image.load("empty.png")
avatar_img    = pygame.image.load("avatar.png")
slime_img     = pygame.image.load("angry_slime.png")
dragon_img    = pygame.image.load("dragon.png")


mountain_img  = pygame.transform.scale(mountain_img,  (TILE_WIDTH, TILE_HEIGHT))
river_img     = pygame.transform.scale(river_img,     (TILE_WIDTH, TILE_HEIGHT))
grass_img     = pygame.transform.scale(grass_img,     (TILE_WIDTH, TILE_HEIGHT))
rock_img      = pygame.transform.scale(rock_img,      (TILE_WIDTH, TILE_HEIGHT))
riverrock_img = pygame.transform.scale(riverrock_img, (TILE_WIDTH, TILE_HEIGHT))
empty_img     = pygame.transform.scale(empty_img,     (TILE_WIDTH, TILE_HEIGHT))
avatar_img    = pygame.transform.scale(avatar_img,    (TILE_WIDTH, TILE_HEIGHT))
slime_img     = pygame.transform.scale(slime_img,     (TILE_WIDTH, TILE_HEIGHT))
dragon_img    = pygame.transform.scale(dragon_img,    (TILE_WIDTH, TILE_HEIGHT))


class RPGTile:
    def __init__(self, image, blocked=False):
        self.image = image
        self.blocked = blocked

    @staticmethod
    def get_tile(ch):
        if ch == '0':   # Mountain
            return MOUNTAIN
        elif ch == '1': # River
            return RIVER
        elif ch == '2': # Grass
            return GRASS
        elif ch == '3': # Rock
            return ROCK
        elif ch == '4': # Riverrock
            return RIVERROCK
        else:
            return EMPTY

MOUNTAIN   = RPGTile(mountain_img,  blocked=True)
RIVER      = RPGTile(river_img,     blocked=True)
GRASS      = RPGTile(grass_img,     blocked=False)
ROCK       = RPGTile(rock_img,      blocked=True)
RIVERROCK  = RPGTile(riverrock_img, blocked=False)
EMPTY      = RPGTile(empty_img,     blocked=False)

# -----------------------------------------------------------------------------
# Weighted random map creation + "center grass zone"
# -----------------------------------------------------------------------------
def random_weighted_map(rows, cols):

    tiles, weights = WEIGHTED_TILES
    data = []
    for r in range(rows):
        row_list = random.choices(tiles, weights=weights, k=cols)
        data.append("".join(row_list))
    return data

def seed_center_with_grass(map_data, radius=CENTER_ZONE_RADIUS):

    rows = len(map_data)
    cols = len(map_data[0])
    row_mid = rows // 2
    col_mid = cols // 2

    r_min = max(row_mid - radius, 0)
    r_max = min(row_mid + radius, rows - 1)
    c_min = max(col_mid - radius, 0)
    c_max = min(col_mid + radius, cols - 1)

    out = []
    for r in range(rows):
        row_list = list(map_data[r])
        for c in range(cols):
            if r_min <= r <= r_max and c_min <= c <= c_max:
                row_list[c] = '2'
        out.append("".join(row_list))
    return out

# -----------------------------------------------------------------------------
# EA: generate, mutate, etc.
# -----------------------------------------------------------------------------
def mutate(map_data):
    rows = len(map_data)
    cols = len(map_data[0])
    tiles, weights = WEIGHTED_TILES
    new_map = []
    for r in range(rows):
        row_list = list(map_data[r])
        for c in range(cols):
            if random.random() < MUTATION_RATE:
                row_list[c] = random.choices(tiles, weights=weights, k=1)[0]
        new_map.append("".join(row_list))
    return new_map

def crossover(map_a, map_b):
    rows = len(map_a)
    child = []
    for r in range(rows):
        if r < rows//2:
            child.append(map_a[r])
        else:
            child.append(map_b[r])
    return child

def fitness_function(map_data):

    total = len(map_data)*len(map_data[0])
    walkable=0
    blocked=0
    for row in map_data:
        for ch in row:
            tile = RPGTile.get_tile(ch)
            if not tile.blocked:
                walkable+=1
            if tile.blocked:
                blocked+=1
    walkable_ratio = walkable/total
    blocked_ratio  = blocked/total

    # aim for ~75% walkable
    desired = 0.75
    dist = abs(walkable_ratio - desired)

    score = (1.0 - dist) - 0.3*blocked_ratio
    return score

def generate_map_ea(rows, cols):

    # Initial pop
    population = []
    for _ in range(POPULATION_SIZE):
        rm = random_weighted_map(rows, cols)
        rm = seed_center_with_grass(rm)
        population.append(rm)

    for gen in range(NUM_GENERATIONS):
        scored = [(fitness_function(m), m) for m in population]
        scored.sort(key=lambda x: x[0], reverse=True)
        best_fit, best_map = scored[0]
        print(f"Gen {gen}, best fit={best_fit:.3f}")
        # top 2
        pA = scored[0][1]
        pB = scored[1][1]

        new_pop=[]
        # elitism
        new_pop.append(pA)
        new_pop.append(pB)
        while len(new_pop)<POPULATION_SIZE:
            child = crossover(pA, pB)
            child = mutate(child)
            child = seed_center_with_grass(child)
            new_pop.append(child)
        population = new_pop

    final_scored = [(fitness_function(m), m) for m in population]
    final_scored.sort(key=lambda x: x[0], reverse=True)
    best_fit, final_map = final_scored[0]
    print("Final best fitness=", best_fit)
    return final_map

class Entity:
    def __init__(self, x, y, image, e_type):
        self.x = x
        self.y = y
        self.image = image
        self.type = e_type
        self.hp = 10

class PDEView:

    def __init__(self, player, entities, game_map):
        self.player   = player
        self.entities = entities
        self.map_data = game_map

        self.rows = len(game_map)
        self.cols = len(game_map[0])

        self.margin_x = (SCREEN_WIDTH  - TILE_WIDTH  * VIEW_SIZE)//2
        self.margin_y = (SCREEN_HEIGHT - TILE_HEIGHT * VIEW_SIZE)//2
        if self.margin_x < 0: self.margin_x=0
        if self.margin_y < 0: self.margin_y=0

    def draw(self, screen):

        x_min = self.player.x - RADIUS
        y_min = self.player.y - RADIUS

        for row in range(VIEW_SIZE):
            for col in range(VIEW_SIZE):
                mx = x_min + col
                my = y_min + row
                tile = self.get_tile_at(mx, my)
                dx = self.margin_x + col*TILE_WIDTH
                dy = self.margin_y + row*TILE_HEIGHT
                screen.blit(tile.image, (dx, dy))


        for ent in self.entities:
            if x_min <= ent.x < x_min+VIEW_SIZE and y_min <= ent.y < y_min+VIEW_SIZE:
                dx = self.margin_x + (ent.x - x_min)*TILE_WIDTH
                dy = self.margin_y + (ent.y - y_min)*TILE_HEIGHT
                screen.blit(ent.image, (dx, dy))

    def get_tile_at(self, x, y):
        if x<0 or x>=self.cols or y<0 or y>=self.rows:
            return EMPTY
        ch = self.map_data[y][x]
        return RPGTile.get_tile(ch)

    def is_blocked(self, x, y):
        if x<0 or y<0 or x>=self.cols or y>=self.rows:
            return True
        tile = self.get_tile_at(x, y)
        return tile.blocked

    def move_player(self, dx, dy):
        nx = self.player.x + dx
        ny = self.player.y + dy
        if not self.is_blocked(nx, ny):
            self.player.x = nx
            self.player.y = ny

        # collision with slimes/dragons
        for e in self.entities:
            if e.x==self.player.x and e.y==self.player.y and e!=self.player:
                if e.type == ENTITY_SLIME:
                    self.player.hp -=1
                    print("Player attacked by Slime! HP=", self.player.hp)
                elif e.type == ENTITY_DRAGON:
                    self.player.hp -=2
                    print("Player attacked by Dragon! HP=", self.player.hp)

    def update_monsters(self):
        # move each monster
        for e in self.entities:
            if e.type==ENTITY_SLIME:
                self.update_slime(e)
            elif e.type==ENTITY_DRAGON:
                self.update_dragon(e)

        # check Slime<->Dragon collisions
        for i in range(len(self.entities)):
            for j in range(i+1, len(self.entities)):
                e1 = self.entities[i]
                e2 = self.entities[j]
                if e1.x==e2.x and e1.y==e2.y:
                    # dragon attacks slime
                    if e1.type==ENTITY_DRAGON and e2.type==ENTITY_SLIME:
                        e2.hp-=2
                        print("Dragon attacks Slime!")
                    elif e1.type==ENTITY_SLIME and e2.type==ENTITY_DRAGON:
                        e1.hp-=2
                        print("Dragon attacks Slime!")

        # remove dead
        self.entities = [e for e in self.entities if e.hp>0]

    def update_slime(self, slime):
        # see if dragon is near
        danger = False
        for e in self.entities:
            if e.type==ENTITY_DRAGON:
                dist = abs(e.x - slime.x)+abs(e.y - slime.y)
                if dist<=2:
                    danger=True
                    break
        if danger:
            # run to water
            directions=[(-1,0),(1,0),(0,-1),(0,1)]
            random.shuffle(directions)
            for dx,dy in directions:
                nx = slime.x+dx
                ny = slime.y+dy
                if not self.is_blocked(nx, ny):
                    t = self.get_tile_at(nx, ny)
                    if t == RIVER or t==RIVERROCK:
                        slime.x=nx
                        slime.y=ny
                        return
            self.move_randomly(slime)
        else:
            self.move_randomly(slime)

    def update_dragon(self, dragon):
        self.move_randomly(dragon)

    def move_randomly(self, e):
        directions=[(-1,0),(1,0),(0,-1),(0,1)]
        dx,dy = random.choice(directions)
        nx = e.x+dx
        ny = e.y+dy
        if not self.is_blocked(nx, ny):
            e.x=nx
            e.y=ny

def main():
    # 1) EA-generate a map
    final_map = generate_map_ea(MAP_ROWS, MAP_COLS)

    # 2) Place player in the center
    px = MAP_COLS//2
    py = MAP_ROWS//2
    # Ensure it's walkable
    # If it's blocked, do a quick fallback random search
    if RPGTile.get_tile(final_map[py][px]).blocked:
        found = False
        for _ in range(100):
            rx = random.randint(0, MAP_COLS-1)
            ry = random.randint(0, MAP_ROWS-1)
            if not RPGTile.get_tile(final_map[ry][rx]).blocked:
                px, py = rx, ry
                found=True
                break
        if not found:
            print("No walkable tile found for the player!")
            sys.exit()

    player = Entity(px, py, avatar_img, ENTITY_PLAYER)

    # 3) Create slimes & dragons on walkable tiles
    entities = []
    # Slimes
    for _ in range(4):
        while True:
            sx = random.randint(0, MAP_COLS-1)
            sy = random.randint(0, MAP_ROWS-1)
            if not RPGTile.get_tile(final_map[sy][sx]).blocked:
                entities.append(Entity(sx, sy, slime_img, ENTITY_SLIME))
                break
    # Dragons
    for _ in range(2):
        while True:
            dx = random.randint(0, MAP_COLS-1)
            dy = random.randint(0, MAP_ROWS-1)
            if not RPGTile.get_tile(final_map[dy][dx]).blocked:
                entities.append(Entity(dx, dy, dragon_img, ENTITY_DRAGON))
                break

    # 4) Initialize PDE-style view
    view = PDEView(player, entities, final_map)

    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("PDE-Style EA RPG (More Grass, Less Empty)")
    clock = pygame.time.Clock()

    running = True
    while running:
        clock.tick(10)  # ~10 FPS

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running=False

        # Player movement
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            view.move_player(-1, 0)
        if keys[pygame.K_RIGHT]:
            view.move_player(1, 0)
        if keys[pygame.K_UP]:
            view.move_player(0, -1)
        if keys[pygame.K_DOWN]:
            view.move_player(0, 1)

        # Update monsters
        view.update_monsters()

        # Check if player died
        if player.hp <=0:
            print("Game Over! Player died.")
            running=False

        # Draw
        screen.fill((0,0,0))
        view.draw(screen)
        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__=="__main__":
    main()
