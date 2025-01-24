
import pygame
import random
import sys
import math

# --- Constants ---
WIDTH, HEIGHT = 1000, 700
GRID_SIZE = 30
NUM_REGIONS = 30
COLORS = {
    "neutral": (100, 100, 100),
    "country1": (255, 100, 100),
    "country2": (100, 255, 100),
    "country3": (100, 100, 255),
    "unit": (255, 255, 255),
    "selected": (255, 255, 0),
    "unit_enemy": (200, 0, 0),
    "unit_player": (0, 200, 0)
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
        color = COLORS[self.country]
        pygame.draw.rect(screen, color, self.rect)
        
        if self.unit:
           self.unit.draw(screen)

class Unit:
    def __init__(self, region, owner):
        self.region = region
        self.owner = owner
        self.radius = 10
        self.center = (region.rect.center)
    
    def move_to(self, new_region, game):
      if self.region.unit is self:
         self.region.unit = None
      self.region = new_region
      self.center = (new_region.rect.center)
      new_region.unit = self

      self.handle_combat(game)

    def handle_combat(self, game):
      if self.region.unit and self.region.unit != self and self.region.unit.owner != self.owner:
        self.fight(game, self.region.unit)

    def fight(self, game, other_unit):
        if self.owner == game.player_country:
            other_unit.region.unit = None
            game.units.remove(other_unit)
        else:
            self.region.unit = None
            game.units.remove(self)

        
    def draw(self, screen):
        if self.owner == game.player_country:
          color = COLORS['unit_player']
        else:
          color = COLORS['unit_enemy']

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
        self.player_country = random.choice(self.countries)
        self.units = []
        self.selected_unit = None
        self.message = ""
        self.ai_turn = False
        self.current_turn = self.player_country

        self.generate_map()

    def generate_map(self):
      """Generate the map regions with random borders using a random walk algorithm."""
      # Initialize a grid with neutral regions
      for y in range(0, HEIGHT, GRID_SIZE):
        for x in range(0, WIDTH, GRID_SIZE):
          self.regions.append(Region(x,y,GRID_SIZE))

      # Generate random walks for each region and assign a country to each
      for country in self.countries:
        start_x = random.randint(0, (WIDTH // GRID_SIZE) - 1) * GRID_SIZE
        start_y = random.randint(0, (HEIGHT // GRID_SIZE) - 1) * GRID_SIZE
        start_region = self.get_region_at_pos(start_x, start_y)
        if start_region is None:
          continue

        self.assign_region_to_country(start_region, country)
        current_x, current_y = start_x, start_y
        for _ in range(100):
          dx, dy = random.choice([(GRID_SIZE, 0), (-GRID_SIZE, 0), (0, GRID_SIZE), (0, -GRID_SIZE)])
          new_x, new_y = current_x + dx, current_y + dy
          if 0 <= new_x < WIDTH and 0 <= new_y < HEIGHT:
            new_region = self.get_region_at_pos(new_x,new_y)
            if new_region is not None and new_region.country == 'neutral':
               self.assign_region_to_country(new_region, country)
            current_x, current_y = new_x, new_y

      self.create_starting_units()

    def assign_region_to_country(self, region, country):
      region.country = country

    def get_region_at_pos(self, x, y):
      """Returns the region object at given coordinates, None if no region is found."""
      for region in self.regions:
        if region.rect.collidepoint(x, y):
          return region
      return None
    
    def create_starting_units(self):
        for country in self.countries:
          regions = [region for region in self.regions if region.country == country]
          if regions:
            start_region = random.choice(regions)
            unit = Unit(start_region, country)
            start_region.unit = unit
            self.units.append(unit)

    def handle_input(self):
        if self.current_turn != self.player_country:
            return
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                x, y = event.pos
                region = self.get_region_at_pos(x,y)
                if region:
                    if region.unit and region.unit.owner == self.player_country:
                        self.selected_unit = region.unit
                    elif self.selected_unit:
                        self.handle_unit_move(region)
                else:
                    self.selected_unit = None
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
              self.current_turn = "ai_turn"
              self.ai_turn = True
              self.message = ""


    def handle_unit_move(self, target_region):
      if target_region and self.selected_unit:
         if self.is_adjacent(self.selected_unit.region, target_region):
            self.selected_unit.move_to(target_region, self)
            
            if target_region.country != self.player_country:
              target_region.country = self.player_country

            self.message = ""
         else:
           self.message = "You can't move there!"
         self.selected_unit = None # Deselect unit after move

    def is_adjacent(self, region1, region2):
        """Checks if two regions are adjacent."""
        dx = abs(region1.x - region2.x)
        dy = abs(region1.y - region2.y)
        return (dx <= region1.size and dy == 0) or (dy <= region1.size and dx == 0)
    
    def ai_move(self):
        for country in self.countries:
            if country == self.player_country:
                continue

            units = [unit for unit in self.units if unit.owner == country]
            for unit in units:
                available_regions = [region for region in self.regions if self.is_adjacent(unit.region, region)]
                if available_regions:
                    target_region = self.find_ai_target(available_regions, unit)
                    if target_region:
                        unit.move_to(target_region, self)
                        if target_region.country != country:
                          target_region.country = country
                
        self.current_turn = self.player_country
        self.ai_turn = False
    
    def find_ai_target(self, available_regions, unit):
      """Find target for AI Unit: try to capture new territory"""
      enemy_regions = [region for region in available_regions if region.country != unit.owner and region.country != 'neutral']
      if enemy_regions:
        return random.choice(enemy_regions)

      neutral_regions = [region for region in available_regions if region.country == 'neutral']
      if neutral_regions:
        return random.choice(neutral_regions)
      
      return random.choice(available_regions)
      
    def draw(self):
        self.screen.fill((0, 0, 0))
        for region in self.regions:
          region.draw(self.screen)
        
        if self.selected_unit:
          pygame.draw.rect(self.screen, COLORS['selected'], self.selected_unit.region.rect, 3)
        
        text_surface = self.font.render(self.message, True, (255, 255, 255))
        self.screen.blit(text_surface, (10, 10))

        pygame.display.flip()

    def run(self):
        while self.running:
            self.handle_input()
            if self.ai_turn:
              self.ai_move()
            self.draw()

        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = Game()
    game.run()
