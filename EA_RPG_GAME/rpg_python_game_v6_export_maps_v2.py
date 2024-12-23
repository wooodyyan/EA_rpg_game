"""

Author: Woody
Date:   Dec 23, 2024
"""

import pygame
import sys
import random

pygame.init()

MAP_ROWS = 15
MAP_COLS = 20

# Weighted random tiles
WEIGHTED_TILES = (["0","1","2","3","4"], [0.05,0.05,0.70,0.05,0.15])

# EA parameters
POPULATION_SIZE   = 6
NUM_GENERATIONS   = 4
MUTATION_RATE     = 0.05

CENTER_ZONE_RADIUS = 3  # force center to grass

TILE_WIDTH  = 32
TILE_HEIGHT = 32

NUM_SLIMES  = 4
NUM_DRAGONS = 2


mountain_img  = pygame.image.load("mountain.png")
river_img     = pygame.image.load("river.png")
grass_img     = pygame.image.load("grass.png")
rock_img      = pygame.image.load("rock.png")
riverrock_img = pygame.image.load("riverstone.png")
empty_img     = pygame.image.load("empty.png")

mountain_img  = pygame.transform.scale(mountain_img,  (TILE_WIDTH, TILE_HEIGHT))
river_img     = pygame.transform.scale(river_img,     (TILE_WIDTH, TILE_HEIGHT))
grass_img     = pygame.transform.scale(grass_img,     (TILE_WIDTH, TILE_HEIGHT))
rock_img      = pygame.transform.scale(rock_img,      (TILE_WIDTH, TILE_HEIGHT))
riverrock_img = pygame.transform.scale(riverrock_img, (TILE_WIDTH, TILE_HEIGHT))
empty_img     = pygame.transform.scale(empty_img,     (TILE_WIDTH, TILE_HEIGHT))


slime_img = pygame.image.load("angry_slime.png")
dragon_img= pygame.image.load("dragon.png")

slime_img  = pygame.transform.scale(slime_img,  (TILE_WIDTH, TILE_HEIGHT))
dragon_img = pygame.transform.scale(dragon_img, (TILE_WIDTH, TILE_HEIGHT))


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

def random_weighted_map(rows, cols):
    tiles, weights = WEIGHTED_TILES
    data = []
    for _ in range(rows):
        row_list = random.choices(tiles, weights=weights, k=cols)
        data.append("".join(row_list))
    return data

def seed_center_with_grass(map_data, radius=CENTER_ZONE_RADIUS):
    rows = len(map_data)
    cols = len(map_data[0])
    mid_r = rows//2
    mid_c = cols//2
    r_min = max(mid_r - radius, 0)
    r_max = min(mid_r + radius, rows-1)
    c_min = max(mid_c - radius, 0)
    c_max = min(mid_c + radius, cols-1)

    new_map = []
    for r in range(rows):
        row_list = list(map_data[r])
        for c in range(cols):
            if r_min <= r <= r_max and c_min <= c <= c_max:
                row_list[c] = '2'
        new_map.append("".join(row_list))
    return new_map


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
            if tile.blocked:
                blocked+=1
            else:
                walkable+=1
    walkable_ratio = walkable/total
    blocked_ratio  = blocked/total

    desired = 0.75
    dist = abs(walkable_ratio - desired)
    score = (1.0 - dist) - 0.3*blocked_ratio
    return score

def generate_map_ea(rows, cols):
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

        pA = scored[0][1]
        pB = scored[1][1]

        new_pop = [pA, pB]  # elitism
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


def place_slimes_and_dragons(map_data):

    rows = len(map_data)
    cols = len(map_data[0])


    monster_positions = []

    # Helper: check blocked
    def is_blocked(r, c):
        if r<0 or r>=rows or c<0 or c>=cols:
            return True
        tile = RPGTile.get_tile(map_data[r][c])
        return tile.blocked

    # place slimes
    slimes_placed = 0
    while slimes_placed < NUM_SLIMES:
        r = random.randint(0, rows-1)
        c = random.randint(0, cols-1)
        if not is_blocked(r,c):
            monster_positions.append((c, r, slime_img))  # x=c, y=r
            slimes_placed +=1

    # place dragons
    dragons_placed = 0
    while dragons_placed < NUM_DRAGONS:
        r = random.randint(0, rows-1)
        c = random.randint(0, cols-1)
        if not is_blocked(r,c):
            monster_positions.append((c, r, dragon_img))
            dragons_placed +=1

    return monster_positions


def render_map_with_monsters(map_data, monsters):

    rows = len(map_data)
    cols = len(map_data[0])
    surf_width  = cols * TILE_WIDTH
    surf_height = rows * TILE_HEIGHT

    surface = pygame.Surface((surf_width, surf_height))

    # Draw terrain
    for r in range(rows):
        for c in range(cols):
            ch = map_data[r][c]
            tile = RPGTile.get_tile(ch)
            x_draw = c*TILE_WIDTH
            y_draw = r*TILE_HEIGHT
            surface.blit(tile.image, (x_draw, y_draw))

    # Draw monsters
    for (mx, my, mimg) in monsters:
        x_draw = mx * TILE_WIDTH
        y_draw = my * TILE_HEIGHT
        surface.blit(mimg, (x_draw, y_draw))

    return surface


def main():
    for i in range(10):
        print(f"\n=== Generating map #{i} ===")
        final_map = generate_map_ea(MAP_ROWS, MAP_COLS)

        # Place monsters (slimes & dragons) on walkable tiles
        monsters = place_slimes_and_dragons(final_map)

        # Render
        surf = render_map_with_monsters(final_map, monsters)

        # Save
        filename = f"landscape_{i}.png"
        pygame.image.save(surf, filename)
        print(f"Saved: {filename}")

    print("All done! 10 landscapes generated and saved as PNGs (with monsters).")
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
