import pygame
import random
import sys

WIDTH, HEIGHT = 1000, 700
GRID_SIZE = 30
GOLD_PER_REGION = 10
UNIT_COST = 30
FPS = 60

COLORS = {
    "neutral": (150, 150, 150),
    "country1": (255, 120, 120),
    "country2": (120, 255, 120),
    "country3": (120, 120, 255),
    "unit_player": (0, 200, 0),
    "unit_enemy": (200, 0, 0),
    "selected": (255, 255, 0),
}

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
font = pygame.font.Font(None, 24)
menu_font = pygame.font.Font(None, 48)


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
        pygame.draw.rect(screen, (50, 50, 50), self.rect, 1)
        if self.unit:
            self.unit.draw(screen)


class Unit:
    def __init__(self, region, owner):
        self.region = region
        self.owner = owner
        self.radius = 10
        self.center = region.rect.center

    def move_to(self, new_region, game):
        if new_region.unit and new_region.unit.owner != self.owner:
            new_region.unit.owner = self.owner
            game.countries[self.owner]["gold"] += 5
        else:
            self.region.unit = None
            self.region = new_region
            self.center = new_region.rect.center
            new_region.unit = self
            game.countries[self.owner]["gold"] += 5
        game.check_victory()

    def draw(self, screen):
        color = COLORS["unit_player"] if self.owner == "country1" else COLORS["unit_enemy"]
        pygame.draw.circle(screen, color, self.center, self.radius)


class Game:
    def __init__(self):
        self.running = True
        self.in_menu = True
        self.in_instructions = False
        self.regions = []
        self.countries = {c: {"gold": 50} for c in ["country1", "country2", "country3"]}
        self.player_country = "country1"
        self.units = []
        self.selected_unit = None
        self.message = ""
        self.current_turn_index = 0
        self.play_button = None
        self.instructions_button = None

    def generate_map(self):
        self.regions = []
        for y in range(0, HEIGHT, GRID_SIZE):
            for x in range(0, WIDTH, GRID_SIZE):
                self.regions.append(Region(x, y, GRID_SIZE))
        for country in self.countries.keys():
            for _ in range(10):
                region = random.choice([r for r in self.regions if r.country == "neutral"])
                region.country = country

    def create_starting_units(self):
        self.units = []
        for country in self.countries.keys():
            for _ in range(3):
                regions = [r for r in self.regions if r.country == country and r.unit is None]
                if regions:
                    region = random.choice(regions)
                    unit = Unit(region, country)
                    region.unit = unit
                    self.units.append(unit)

    def handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            if self.in_menu:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    x, y = event.pos
                    if self.play_button.collidepoint(x, y):
                        self.start_game()
                    elif self.instructions_button.collidepoint(x, y):
                        self.in_menu = False
                        self.in_instructions = True

            elif self.in_instructions:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.in_instructions = False
                    self.in_menu = True

            else:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.in_menu = True
                    elif event.key == pygame.K_r:
                        self.restart_game()
                    elif event.key == pygame.K_b:
                        self.build_unit()

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

    def start_game(self):
        self.generate_map()
        self.create_starting_units()
        self.in_menu = False

    def build_unit(self):
        gold = self.countries[self.player_country]["gold"]
        if gold >= UNIT_COST:
            regions = [r for r in self.regions if r.country == self.player_country and r.unit is None]
            if regions:
                region = random.choice(regions)
                unit = Unit(region, self.player_country)
                region.unit = unit
                self.units.append(unit)
                self.countries[self.player_country]["gold"] -= UNIT_COST

    def restart_game(self):
        self.generate_map()
        self.create_starting_units()
        self.countries = {c: {"gold": 50} for c in ["country1", "country2", "country3"]}
        self.selected_unit = None
        self.message = ""
        self.current_turn_index = 0

    def current_turn(self):
        return list(self.countries.keys())[self.current_turn_index]

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

    def check_victory(self):
        if all(unit.owner == self.player_country for unit in self.units):
            self.message = "Victory! All enemies converted!"
            self.running = False

    def get_region_at_pos(self, x, y):
        for region in self.regions:
            if region.rect.collidepoint(x, y):
                return region
        return None

    def is_adjacent(self, region1, region2):
        dx = abs(region1.x - region2.x)
        dy = abs(region1.y - region2.y)
        return (dx == GRID_SIZE and dy == 0) or (dx == 0 and dy == GRID_SIZE)

    def draw_menu(self):
        screen.fill((30, 30, 30))

        # Кнопка "Играть"
        self.play_button = pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2 - 60, 200, 50)
        pygame.draw.rect(screen, (0, 150, 0), self.play_button)
        text = menu_font.render("Играть", True, (255, 255, 255))
        screen.blit(text, (WIDTH // 2 - 50, HEIGHT // 2 - 50))

        # Кнопка "Инструкции"
        self.instructions_button = pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2 + 20, 200, 50)
        pygame.draw.rect(screen, (0, 0, 150), self.instructions_button)
        text = menu_font.render("Инструкции", True, (255, 255, 255))
        screen.blit(text, (WIDTH // 2 - 85, HEIGHT // 2 + 30))

        pygame.display.flip()

    def draw_instructions(self):
        screen.fill((30, 30, 30))
        lines = [
            "Инструкции:",
            "ЛКМ — выбрать юнит / переместить его",
            "B — создать юнита за золото",
            "R — перезапуск игры",
            "ESC — выйти в меню",
            "",
            "Нажмите ESC для возврата в меню"
        ]

        y = 50
        for line in lines:
            text = font.render(line, True, (255, 255, 255))
            screen.blit(text, (50, y))
            y += 40

        pygame.display.flip()

    def draw_game(self):
        screen.fill((30, 30, 30))
        for region in self.regions:
            region.draw(screen)
        text = font.render(f"Золото: {self.countries[self.player_country]['gold']}", True, (255, 255, 255))
        screen.blit(text, (10, 10))
        pygame.display.flip()

    def run(self):
        clock = pygame.time.Clock()
        while self.running:
            self.handle_input()

            if self.in_menu:
                self.draw_menu()
            elif self.in_instructions:
                self.draw_instructions()
            else:
                self.draw_game()

            clock.tick(FPS)

        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    game = Game()
    game.run()
