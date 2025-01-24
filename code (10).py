import pygame
import random
import sys

WIDTH, HEIGHT = 1000, 700
GRID_SIZE = 30
COLORS = {
    "neutral": (100, 100, 100),
    "country1": (255, 100, 100),
    "country2": (100, 255, 100),
    "country3": (100, 100, 255),
    "unit_player": (0, 200, 0),
    "unit_enemy": (200, 0, 0),
    "selected": (255, 255, 0),
}

class Region:
    def __init__(self, x, y, size, country="neutral"):
        self.x = x
        self.y = y
        self.size = size
        self.country = country
        self.unit = None
        self.rect = pygame.Rect(x, y, size, size)

    def draw(self, screen):
        pygame.draw.rect(screen, COLORS[self.country], self.rect)
        if self.unit:
            self.unit.draw(screen)

class Unit:
    def __init__(self, region, owner):
        self.region = region
        self.owner = owner
        self.radius = 10
        self.center = region.rect.center

    def move_to(self, new_region, game):
        self.region.unit = None
        self.region = new_region
        self.center = new_region.rect.center
        new_region.unit = self
        self.handle_combat(game)

    def handle_combat(self, game):
        if self.region.unit and self.region.unit != self and self.region.unit.owner != self.owner:
            game.units.remove(self.region.unit)
            self.region.unit = self

    def draw(self, screen):
        color = COLORS["unit_player"] if self.owner == game.player_country else COLORS["unit_enemy"]
        pygame.draw.circle(screen, color, self.center, self.radius)

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Age of Pygame")
        self.font = pygame.font.Font(None, 24)
        self.running = True
        self.regions = []
        self.countries = ["country1", "country2", "country3"]
        self.player_country = "country1"
        self.units = []
        self.selected_unit = None
        self.message = ""
        self.current_turn_index = 0
        self.generate_map()
        self.create_starting_units()

    def generate_map(self):
        for y in range(0, HEIGHT, GRID_SIZE):
            for x in range(0, WIDTH, GRID_SIZE):
                self.regions.append(Region(x, y, GRID_SIZE))
        for country in self.countries:
            for _ in range(10):
                region = random.choice([r for r in self.regions if r.country == "neutral"])
                region.country = country

    def create_starting_units(self):
        for country in self.countries:
            for _ in range(3):
                region = random.choice([r for r in self.regions if r.country == country and r.unit is None])
                unit = Unit(region, country)
                region.unit = unit
                self.units.append(unit)

    def handle_input(self):
        if self.current_turn() != self.player_country:
            return
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                x, y = event.pos
                region = self.get_region_at_pos(x, y)
                if region:
                    if region.unit and region.unit.owner == self.player_country:
                        self.selected_unit = region.unit
                    elif self.selected_unit and self.is_adjacent(self.selected_unit.region, region):
                        self.selected_unit.move_to(region, self)
                        if region.country != self.player_country:
                            region.country = self.player_country
                        self.selected_unit = None
                        self.next_turn()

    def current_turn(self):
        return self.countries[self.current_turn_index]

    def next_turn(self):
        self.current_turn_index = (self.current_turn_index + 1) % len(self.countries)
        if self.current_turn() != self.player_country:
            self.ai_turn()

    def ai_turn(self):
        for unit in [u for u in self.units if u.owner == self.current_turn()]:
            adjacent_regions = [r for r in self.regions if self.is_adjacent(unit.region, r)]
            if adjacent_regions:
                target_region = random.choice(adjacent_regions)
                unit.move_to(target_region, self)
                if target_region.country != unit.owner:
                    target_region.country = unit.owner
        self.next_turn()

    def get_region_at_pos(self, x, y):
        for region in self.regions:
            if region.rect.collidepoint(x, y):
                return region
        return None

    def is_adjacent(self, region1, region2):
        dx = abs(region1.x - region2.x)
        dy = abs(region1.y - region2.y)
        return (dx == GRID_SIZE and dy == 0) or (dx == 0 and dy == GRID_SIZE)

    def check_victory(self):
        player_regions = [r for r in self.regions if r.country == self.player_country]
        if len(player_regions) == len(self.regions) - len([r for r in self.regions if r.country == "neutral"]):
            self.message = "Victory! You conquered all enemy territories!"
            self.running = False

    def draw(self):
        self.screen.fill((0, 0, 0))
        for region in self.regions:
            region.draw(self.screen)
        if self.selected_unit:
            pygame.draw.rect(self.screen, COLORS["selected"], self.selected_unit.region.rect, 3)
        text_surface = self.font.render(self.message, True, (255, 255, 255))
        self.screen.blit(text_surface, (10, 10))
        pygame.display.flip()

    def run(self):
        while self.running:
            self.handle_input()
            self.check_victory()
            self.draw()
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = Game()
    game.run()
