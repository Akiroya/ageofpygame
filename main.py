import pygame
import random
import sys
from pygame import mixer

# Инициализация Pygame и звука
pygame.init()
mixer.init()

# Константы
WIDTH, HEIGHT = 1200, 800
GRID_SIZE = 40
UNIT_COSTS = {'warrior': 40, 'scout': 30, 'knight': 60}
FPS = 60
REGION_UPGRADE_COST = 100
COLORS = {
    "neutral": (150, 150, 150),
    "country1": (255, 120, 120),
    "country2": (120, 255, 120),
    "country3": (120, 120, 255),
    "selected": (255, 255, 0),
    "highlight": (255, 200, 100),
    "treasure": (255, 215, 0),
    "upgraded": (200, 160, 60),
}

# Инициализация экрана
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Strategy Game")
font = pygame.font.Font(None, 36)
clock = pygame.time.Clock()

class Region:
    def __init__(self, x, y, size, country="neutral"):
        self.x = x
        self.y = y
        self.size = size
        self.country = country
        self.unit = None
        self.has_treasure = False
        self.upgrade_level = 0
        self.rect = pygame.Rect(x, y, size, size)
        
    def draw(self, screen):
        base_color = COLORS[self.country]
        if self.upgrade_level > 0:
            base_color = tuple(min(c + 40, 255) for c in base_color)
        pygame.draw.rect(screen, base_color, self.rect)
        
        if self.has_treasure:
            pygame.draw.circle(screen, COLORS['treasure'], self.rect.center, 8)
        if self.upgrade_level > 0:
            pygame.draw.rect(screen, COLORS['upgraded'], self.rect.inflate(-4, -4), 3)
        
        pygame.draw.rect(screen, (50, 50, 50), self.rect, 1)
        if self.unit:
            self.unit.draw(screen)

class Unit:
    def __init__(self, region, owner, unit_type='warrior'):
        self.region = region
        self.owner = owner
        self.unit_type = unit_type
        self.moves_left = self.get_max_moves()
        self.health = 100
        self.strength = self.get_strength()
        self.radius = 12
        self.anim_progress = 0
        
    def get_max_moves(self):
        return {'warrior': 1, 'scout': 3, 'knight': 2}[self.unit_type]
    
    def get_strength(self):
        return {'warrior': 80, 'scout': 40, 'knight': 100}[self.unit_type]
    
    def move_to(self, new_region, game):
        dx = new_region.x - self.region.x
        dy = new_region.y - self.region.y
        distance = abs(dx) + abs(dy)
        required_moves = distance // GRID_SIZE
        
        if self.moves_left >= required_moves:
            self.moves_left -= required_moves
            self.anim_progress = 0
            start_pos = self.region.rect.center
            end_pos = new_region.rect.center
            
            while self.anim_progress < 1:
                self.anim_progress += 0.1
                current_x = start_pos[0] + (end_pos[0] - start_pos[0]) * self.anim_progress
                current_y = start_pos[1] + (end_pos[1] - start_pos[1]) * self.anim_progress
                self.center = (int(current_x), int(current_y))
                pygame.time.wait(30)
                game.draw_game()
                
            self.finalize_move(new_region, game)
            
    def finalize_move(self, new_region, game):
        if new_region.unit:
            if self.resolve_combat(new_region.unit):
                new_region.unit = None
            else:
                return
                
        self.region.unit = None
        self.region = new_region
        new_region.unit = self
        self.center = new_region.rect.center
        
        if new_region.country != self.owner:
            new_region.country = self.owner
            gold_gain = 10 + (5 * new_region.upgrade_level)
            if new_region.has_treasure:
                gold_gain += 50
                new_region.has_treasure = False
            game.countries[self.owner]["gold"] += gold_gain
            
        if new_region.upgrade_level > 0:
            self.health = min(self.health + 20, 100)
            
        game.check_victory()
        
    def resolve_combat(self, defender):
        attacker_power = self.strength * (self.health / 100)
        defender_power = defender.strength * (defender.health / 100)
        
        if attacker_power > defender_power:
            defender.health -= (attacker_power - defender_power) * 2
            if defender.health <= 0:
                return True
        else:
            self.health -= (defender_power - attacker_power) * 2
            if self.health <= 0:
                return False
        return None
        
    def draw(self, screen):
        color = COLORS["unit_player"] if self.owner == "country1" else COLORS["unit_enemy"]
        if self.anim_progress < 1:
            pygame.draw.circle(screen, color, self.center, self.radius)
        else:
            pygame.draw.circle(screen, color, self.region.rect.center, self.radius)
            
        # Health bar
        pygame.draw.rect(screen, (255,0,0), (self.region.rect.centerx-15, self.region.rect.centery+15, 30, 5))
        pygame.draw.rect(screen, (0,255,0), (self.region.rect.centerx-15, self.region.rect.centery+15, 30*(self.health/100), 5))

class Game:
    def __init__(self):
        self.running = True
        self.in_menu = True
        self.regions = []
        self.countries = {c: {"gold": 100, "income": 0} for c in ["country1", "country2", "country3"]}
        self.player_country = "country1"
        self.selected_unit = None
        self.hovered_region = None
        self.current_turn_index = 0
        self.turn_counter = 1
        self.events = []
        
    def generate_map(self):
        self.regions = []
        for y in range(0, HEIGHT, GRID_SIZE):
            for x in range(0, WIDTH, GRID_SIZE):
                self.regions.append(Region(x, y, GRID_SIZE))
                
        for country in self.countries:
            for _ in range(8):
                region = random.choice([r for r in self.regions if r.country == "neutral"])
                region.country = country
                if random.random() < 0.2:
                    region.has_treasure = True
                    
        for _ in range(5):
            region = random.choice(self.regions)
            region.upgrade_level = 1
            
    def create_starting_units(self):
        for country in self.countries:
            for _ in range(3):
                regions = [r for r in self.regions if r.country == country]
                if regions:
                    region = random.choice(regions)
                    unit_type = random.choice(['warrior', 'scout', 'knight'])
                    region.unit = Unit(region, country, unit_type)
                    
    def handle_input(self):
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
                        self.selected_unit = None
                        self.next_turn()
                        
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_b:
                    self.build_unit()
                elif event.key == pygame.K_u:
                    self.upgrade_region()
                elif event.key == pygame.K_r:
                    self.restart_game()
                    
    def next_turn(self):
        self.current_turn_index = (self.current_turn_index + 1) % 3
        self.turn_counter += 1
        self.update_incomes()
        self.reset_moves()
        self.spawn_treasure()
        
        if self.current_turn() != self.player_country:
            self.ai_turn()
            
    def update_incomes(self):
        for country in self.countries:
            owned_regions = sum(1 for r in self.regions if r.country == country)
            self.countries[country]["income"] = owned_regions * 5
            self.countries[country]["gold"] += self.countries[country]["income"]
            
    def spawn_treasure(self):
        if random.random() < 0.1:
            neutral_regions = [r for r in self.regions if r.country == "neutral"]
            if neutral_regions:
                region = random.choice(neutral_regions)
                region.has_treasure = True
                
    def build_unit(self):
        if self.countries[self.player_country]["gold"] >= UNIT_COSTS['warrior']:
            regions = [r for r in self.regions if r.country == self.player_country and r.unit is None]
            if regions:
                region = random.choice(regions)
                unit_type = random.choice(['warrior', 'scout', 'knight'])
                region.unit = Unit(region, self.player_country, unit_type)
                self.countries[self.player_country]["gold"] -= UNIT_COSTS[unit_type]
                
    def upgrade_region(self):
        if self.selected_unit and self.countries[self.player_country]["gold"] >= REGION_UPGRADE_COST:
            region = self.selected_unit.region
            if region.country == self.player_country:
                region.upgrade_level += 1
                self.countries[self.player_country]["gold"] -= REGION_UPGRADE_COST
                
    def restart_game(self):
        self.generate_map()
        self.create_starting_units()
        self.countries = {c: {"gold": 100, "income": 0} for c in ["country1", "country2", "country3"]}
        self.selected_unit = None
        self.current_turn_index = 0
        self.turn_counter = 1
        
    def ai_turn(self):
        for unit in [u for u in self.regions if u.unit and u.unit.owner == self.current_turn()]:
            adjacent_regions = [r for r in self.regions if self.is_adjacent(unit.region, r)]
            if adjacent_regions:
                target_region = random.choice(adjacent_regions)
                unit.unit.move_to(target_region, self)
                
    def check_victory(self):
        player_regions = sum(1 for r in self.regions if r.country == self.player_country)
        if player_regions == len(self.regions):
            self.show_message("Victory!")
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
    
    def reset_moves(self):
        for region in self.regions:
            if region.unit:
                region.unit.moves_left = region.unit.get_max_moves()
                
    def draw_interface(self):
        pygame.draw.rect(screen, (40, 40, 40), (0, HEIGHT-100, WIDTH, 100))
        gold_text = font.render(f"Gold: {self.countries[self.player_country]['gold']} (+{self.countries[self.player_country]['income']}/turn)", 
                              True, (255, 255, 255))
        screen.blit(gold_text, (20, HEIGHT-80))
        
    def draw_game(self):
        screen.fill((30, 30, 30))
        for region in self.regions:
            region.draw(screen)
        self.draw_interface()
        pygame.display.flip()
        
    def run(self):
        self.generate_map()
        self.create_starting_units()
        while self.running:
            self.handle_input()
            self.draw_game()
            clock.tick(FPS)
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = Game()
    game.run()
