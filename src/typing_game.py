import asyncio
import platform
import pygame
import sys
import random
import time
import math

# Pygame 初始化
pygame.init()
pygame.mixer.init()  # 初始化音频

# 窗口和网格设置
CHAR_WIDTH_ESTIMATE = 10
CHAR_HEIGHT_ESTIMATE = 20
GRID_WIDTH = 60
GRID_HEIGHT = 25
CASTLE_BOTTOM_GRID_ROW = GRID_HEIGHT - 1  # Not directly used, but good for context
CASTLE_INITIAL_HEIGHT_GRID = 3  # Refers to the height of initial_castle_art

WINDOW_PIXEL_WIDTH = GRID_WIDTH * CHAR_WIDTH_ESTIMATE
WINDOW_PIXEL_HEIGHT = GRID_HEIGHT * CHAR_HEIGHT_ESTIMATE

screen = pygame.display.set_mode((WINDOW_PIXEL_WIDTH, WINDOW_PIXEL_HEIGHT))
pygame.display.set_caption("Typing Game")

# 字体设置
font = None
CHAR_WIDTH = CHAR_WIDTH_ESTIMATE
CHAR_HEIGHT = CHAR_HEIGHT_ESTIMATE
font_names_to_try = ["Consolas", "Courier New", "Lucida Console", "DejaVu Sans Mono", "Liberation Mono", "Arial"]

for font_name in font_names_to_try:
    try:
        font = pygame.font.SysFont(font_name, CHAR_HEIGHT_ESTIMATE, bold=False)
        if font:
            # Check if font actually rendered something (some systems return a default)
            if font.size(" ")[0] > 0:  # Check width of a space
                break
            else:
                font = None  # Reset if it's a bad font
    except pygame.error:
        pass  # Font not found or error loading

if not font:
    font = pygame.font.Font(None, CHAR_HEIGHT_ESTIMATE)  # Pygame's default font

char_size = font.size(" ")  # Use a space to determine default char size
CHAR_WIDTH = char_size[0]
CHAR_HEIGHT = char_size[1]

# Recalculate window size based on actual font metrics
WINDOW_PIXEL_WIDTH = GRID_WIDTH * CHAR_WIDTH
WINDOW_PIXEL_HEIGHT = GRID_HEIGHT * CHAR_HEIGHT
screen = pygame.display.set_mode((WINDOW_PIXEL_WIDTH, WINDOW_PIXEL_HEIGHT))

# 颜色定义
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)
BLUE = (0, 0, 255)
GRAY = (128, 128, 128)
PURPLE = (128, 0, 128)

# --- Enhanced Bonus Word Settings ---
BONUS_SPEED_MULTIPLIER = 10.0  # Increased speed for bonus words
BONUS_SCORE_MULTIPLIER = 3  # Increased score for bonus words
BONUS_DAMAGE_MULTIPLIER = 3  # Increased damage by bonus words


# 爆炸效果类
class Explosion:
    def __init__(self, x, y):
        self.x = x  # Center x of explosion
        self.y = y  # Center y of explosion
        self.start_time = time.time()
        self.duration = 0.4  # Slightly longer for more visibility
        self.particles = []
        num_particles = random.randint(10, 15)  # More particles
        for _ in range(num_particles):
            speed = random.uniform(60, 120)  # pixels/sec, slightly faster particles
            angle = random.uniform(0, 2 * math.pi)
            vx = speed * math.cos(angle)
            vy = speed * math.sin(angle)
            self.particles.append({
                'x': self.x,  # Start particles at explosion center
                'y': self.y,
                'vx': vx,
                'vy': vy,
                'radius': random.uniform(3, 6),  # Slightly larger particles
                'color': (random.randint(200, 255), random.randint(50, 200), 0)  # Orange/Yellow tones
            })

    def update(self, dt):
        active_particles = 0
        for particle in self.particles:
            particle['x'] += particle['vx'] * dt
            particle['y'] += particle['vy'] * dt
            particle['radius'] *= (0.98 - dt * 2)  # Shrink faster, factor in dt
            if particle['radius'] < 0.5:
                particle['radius'] = 0  # Mark for removal
            else:
                active_particles += 1

        self.particles = [p for p in self.particles if p['radius'] > 0]
        return time.time() - self.start_time < self.duration or active_particles > 0

    def draw(self, surface):
        current_time_elapsed = time.time() - self.start_time
        if current_time_elapsed > self.duration:
            return

        for particle in self.particles:
            if particle['radius'] <= 0:
                continue
            # Fade out alpha based on particle radius or overall duration
            alpha_factor = min(1, particle['radius'] / 5)  # Fade as it shrinks
            alpha = max(0, 255 * (1 - (current_time_elapsed / self.duration)) * alpha_factor)

            # Particle color (already set in init, but could be modified here)
            # For simplicity, using the pre-set particle color with alpha
            try:
                # Create a temporary surface for alpha blending if color doesn't have alpha
                # Or draw directly if color has alpha (pygame.Color supports it)
                # For simple circles, direct drawing with alpha in color tuple might not work well.
                # A common way is to draw on a separate surface then blit with special_flags=pygame.BLEND_RGBA_MULT
                # Or, more simply, just vary brightness/color over time.
                # Let's make color fade to darker

                r, g, b = particle['color']
                fade_factor = (1 - (current_time_elapsed / self.duration))
                final_color = (int(r * fade_factor), int(g * fade_factor), int(b * fade_factor))

                pygame.draw.circle(surface, final_color, (int(particle['x']), int(particle['y'])),
                                   int(particle['radius']))
            except TypeError:  # If color is not suitable
                pygame.draw.circle(surface, YELLOW, (int(particle['x']), int(particle['y'])), int(particle['radius']))


# FallingObject 类
class FallingObject:
    def __init__(self, text, speed_grid_per_sec=0.5, color=WHITE, is_bonus=False):
        self.text = text.upper()
        self.color = color
        self.is_bonus = is_bonus
        # Speed is pixels per second, then converted to per frame in move()
        self.speed_pixel_per_sec = speed_grid_per_sec * CHAR_HEIGHT
        self.pixel_y_float = 0.0  # Use float for y position for smoother movement

        # Ensure objects don't spawn beyond screen width
        max_grid_x = max(0, GRID_WIDTH - len(self.text))
        grid_x = random.randint(0, max_grid_x) if max_grid_x > 0 else 0

        self.pixel_x = grid_x * CHAR_WIDTH
        self.active = True
        self.progress = 0

    def draw(self, surface, font_to_use):  # Renamed font parameter
        if not self.active:
            return
        inputted_text = self.text[:self.progress]
        remaining_text = self.text[self.progress:]

        current_x = self.pixel_x
        if inputted_text:
            input_surface = font_to_use.render(inputted_text, True, GREEN)
            surface.blit(input_surface, (current_x, int(self.pixel_y_float)))
            current_x += input_surface.get_width()  # Advance x by width of rendered inputted text

        if remaining_text:
            # Determine color: if bonus, always YELLOW, else self.color
            draw_color = YELLOW if self.is_bonus else self.color
            remaining_surface = font_to_use.render(remaining_text, True, draw_color)
            surface.blit(remaining_surface, (current_x, int(self.pixel_y_float)))

    def move(self, dt):  # dt is delta time in seconds
        if self.active:
            self.pixel_y_float += self.speed_pixel_per_sec * dt

    def handle_input(self, typed_char):
        if not self.active or self.progress >= len(self.text):
            return False  # Should not happen if current_target logic is correct

        expected_char = self.text[self.progress].upper()
        typed_char_upper = typed_char.upper()

        if typed_char_upper == expected_char:
            self.progress += 1
            if self.progress == len(self.text):
                self.active = False  # Word completed
                return True  # Indicates completion
            return False  # Correct char, but word not finished
        else:
            # Incorrect char typed
            self.progress = 0  # Reset progress on this word
            # Optionally, could add a small penalty or visual feedback here
            return False  # Indicates incorrect char / reset

    def reset_progress(self):  # Not currently used, but good to have
        self.progress = 0

    def get_bottom_pixel_y(self):
        return self.pixel_y_float + CHAR_HEIGHT

    def get_center_position(self):
        # Center of the word's bounding box
        center_x = self.pixel_x + (len(self.text) * CHAR_WIDTH) / 2
        center_y = self.pixel_y_float + CHAR_HEIGHT / 2
        return center_x, center_y


# 难度定义
difficulty_levels = [
    {'level': 1, 'items': ['F', 'G', 'H', 'J'], 'speed_grid_per_sec': 0.3, 'generate_interval': 2.0,
     'score_threshold': 50},
    {'level': 2, 'items': ['R', 'T', 'Y', 'V', 'U', 'B', 'N', 'M'], 'speed_grid_per_sec': 0.35,
     'generate_interval': 1.8, 'score_threshold': 150},
    {'level': 3, 'items': ['D', 'K', 'I', 'E', 'C', ','], 'speed_grid_per_sec': 0.4, 'generate_interval': 1.6,
     'score_threshold': 300},
    {'level': 4, 'items': ['S', 'L', 'W', 'Q', '.'], 'speed_grid_per_sec': 0.45, 'generate_interval': 1.4,
     'score_threshold': 500},  # Added '.'
    {'level': 5, 'items': ['A', 'Z', 'X', ';'], 'speed_grid_per_sec': 0.5, 'generate_interval': 1.5,
     'score_threshold': 800},  # Adjusted interval
    {'level': 6, 'items': ['THE', 'AND', 'FOR', 'ARE', 'BUT'], 'speed_grid_per_sec': 0.55, 'generate_interval': 2.2,
     'score_threshold': 1200},
    {'level': 7, 'items': ['THIS', 'THAT', 'WITH', 'FROM', 'HAVE'], 'speed_grid_per_sec': 0.6, 'generate_interval': 2.0,
     'score_threshold': 1800},
    {'level': 8, 'items': ['PYTHON', 'PYGAME', 'CODING', 'TYPING', 'CASTLE'], 'speed_grid_per_sec': 0.65,
     'generate_interval': 2.5, 'score_threshold': 2500},  # Longer interval for longer words
    {'level': 9, 'items': ['PROGRAM', 'DEVELOP', 'KEYBOARD', 'ACCURACY', 'CHALLENGE'], 'speed_grid_per_sec': 0.7,
     'generate_interval': 2.3, 'score_threshold': 3200},
    {'level': 10, 'items': ['INTELLIGENCE', 'COMMUNICATION', 'ENVIRONMENT', 'FRAMEWORK'], 'speed_grid_per_sec': 0.75,
     'generate_interval': 3.0, 'score_threshold': 4000}
]

# --- Automate memory_items population ---
all_previous_items_for_memory = []
for i in range(len(difficulty_levels)):
    current_level_settings = difficulty_levels[i]
    # Memory items are all unique items from all *previous* levels' 'items' lists
    current_level_settings['memory_items'] = list(set(all_previous_items_for_memory))

    # Add current level's 'items' to the accumulator for the *next* level's memory list
    all_previous_items_for_memory.extend(current_level_settings['items'])


def get_level_settings(level):
    index = max(0, min(level - 1, len(difficulty_levels) - 1))  # Ensure level is within bounds
    return difficulty_levels[index]


# 城堡艺术字和状态
initial_castle_art = [
    "############################################################",  # GRID_WIDTH = 60
    "============================================================",
    "##########**********####################**********##########",  # Core is '*'
    "#########==* *==##################==* *==#########",
    "########=#**#====#**#==================#**#====#**#=########",
]
castle_art = []  # Current state of the castle

# --- Castle Metrics (initialized once) ---
CORE_CHAR = '*'
# Use a clean copy of initial_castle_art for metrics; it's a list of strings, so direct use is fine.
INITIAL_CASTLE_ART_FOR_METRICS = initial_castle_art

INITIAL_CORE_ROW_INDEX_FROM_TOP = -1
INITIAL_CASTLE_MASS = 0
INITIAL_CORE_CHAR_COUNT = 0  # Total number of CORE_CHAR in the designated core line


def initialize_global_castle_metrics():
    global INITIAL_CORE_ROW_INDEX_FROM_TOP, INITIAL_CASTLE_MASS, INITIAL_CORE_CHAR_COUNT

    found_core_line = False
    for i, row_str in enumerate(INITIAL_CASTLE_ART_FOR_METRICS):
        if CORE_CHAR in row_str and not found_core_line:  # Designate the first row with '*' as the core line
            INITIAL_CORE_ROW_INDEX_FROM_TOP = i
            INITIAL_CORE_CHAR_COUNT = row_str.count(CORE_CHAR)
            found_core_line = True  # Stop after finding the first core line
            # If multiple lines have '*', this logic picks the topmost one as "the" core line.
            # For this game, the 3rd line is the intended core.
            if i == 2:  # Explicitly target the 3rd line (index 2) as the primary core.
                INITIAL_CORE_CHAR_COUNT = INITIAL_CASTLE_ART_FOR_METRICS[2].count(CORE_CHAR)
                INITIAL_CORE_ROW_INDEX_FROM_TOP = 2

    if INITIAL_CORE_ROW_INDEX_FROM_TOP == -1:  # Fallback if core char not in expected line
        print("WARNING: Core char '*' not found in the designated core line of initial_castle_art!")
        INITIAL_CORE_CHAR_COUNT = 0  # No specific core to track if not found

    INITIAL_CASTLE_MASS = sum(
        sum(1 for char_in_row in row if char_in_row != ' ') for row in INITIAL_CASTLE_ART_FOR_METRICS)
    if INITIAL_CASTLE_MASS == 0:
        print("WARNING: Initial castle mass is zero. Game over conditions might be affected.")


# Call this once at startup
initialize_global_castle_metrics()

# 游戏状态变量
falling_objects = []
current_target = None  # The FallingObject the player is currently typing
score = 0
current_level = 1
game_over = False
last_generate_time = 0  # Initialize to 0 to allow immediate first generation
show_red_line = False
red_line_target = None
red_line_timer = 0
RED_LINE_DURATION = 0.1  # Seconds for the "laser" line
MEMORY_ITEM_CHANCE = 0.35  # Slightly higher chance for memory items
BONUS_CHANCE = 0.15  # Slightly higher chance for bonus words
explosions = []

# 音频初始化
try:
    # Assuming 'res' folder is in the same directory as the script or accessible
    # pygame.mixer.music.load("res/background.mid") # Use forward slashes for paths
    # pygame.mixer.music.set_volume(0.3) # Quieter background
    # pygame.mixer.music.play(-1)
    print("Background music loading skipped for now. Uncomment to enable.")
except pygame.error as e:
    print(f"Warning: Could not load background music. {e}")

try:
    # hit_sound = pygame.mixer.Sound("res/hit.wav")
    # hit_sound.set_volume(0.6)
    print("Hit sound loading skipped for now. Uncomment to enable.")
    hit_sound = None  # Placeholder if not loaded
except pygame.error as e:
    print(f"Warning: Could not load hit sound. {e}")
    hit_sound = None


# 生成掉落物体
def generate_falling_object():
    global falling_objects, last_generate_time
    now = time.time()
    level_settings = get_level_settings(current_level)
    generate_interval = level_settings['generate_interval']

    if not level_settings['items'] and not level_settings['memory_items']:
        # No items to generate for this level, perhaps an issue with config or max level reached
        return

    if now - last_generate_time > generate_interval:
        item_text = None
        is_bonus = random.random() < BONUS_CHANCE

        # Determine if it's a memory item or a new item for the level
        use_memory_item = random.random() < MEMORY_ITEM_CHANCE and level_settings['memory_items']

        if use_memory_item:
            item_text = random.choice(level_settings['memory_items'])
        elif level_settings['items']:  # Fallback to current level's new items
            item_text = random.choice(level_settings['items'])
        elif level_settings['memory_items']:  # If no new items, but memory items exist
            item_text = random.choice(level_settings['memory_items'])

        if item_text:  # Ensure an item was actually chosen
            base_speed = level_settings['speed_grid_per_sec']
            final_speed = base_speed * (BONUS_SPEED_MULTIPLIER if is_bonus else 1.0)

            new_object = FallingObject(item_text,
                                       speed_grid_per_sec=final_speed,
                                       color=WHITE,  # Bonus color handled in FallingObject.draw
                                       is_bonus=is_bonus)
            falling_objects.append(new_object)

        last_generate_time = now


# 绘制城堡
def draw_castle(surface, font_to_use, castle_art_lines):  # Renamed font parameter
    current_castle_height_grid = len(castle_art_lines)
    if current_castle_height_grid == 0:
        return

    # Castle is drawn from the bottom of its art upwards, positioned at bottom of game grid
    castle_top_on_screen_grid_y = GRID_HEIGHT - current_castle_height_grid

    for i, line_str in enumerate(castle_art_lines):
        # y_pixel is the top of the current castle line being drawn
        y_pixel = (castle_top_on_screen_grid_y + i) * CHAR_HEIGHT
        for j, char_in_line in enumerate(line_str):
            if char_in_line == ' ':  # Don't draw spaces
                continue

            color = PURPLE if char_in_line == CORE_CHAR else BLUE  # Core parts are purple
            if char_in_line == '=':
                color = GRAY  # Different color for '=' parts

            char_surface = font_to_use.render(char_in_line, True, color)
            surface.blit(char_surface, (j * CHAR_WIDTH, y_pixel))


# 破坏城堡
def damage_castle(destruction_width_chars, obj_pixel_x, hit_row_in_current_castle):
    global castle_art, game_over, explosions  # Access global game_over flag

    if game_over: return  # No action if game is already over
    if not castle_art:  # Should be caught by game_over, but as a safeguard
        game_over = True
        return

    # Validate hit_row_in_current_castle
    if not (0 <= hit_row_in_current_castle < len(castle_art)):
        # This implies a hit on a non-existent part, possibly due to timing or extreme shrinkage
        # If the castle is tiny, this could mean game over.
        if len(castle_art) <= 1: game_over = True  # Or some small threshold
        return

    castle_height_at_impact = len(castle_art)  # For explosion Y calculation

    # --- Apply Damage to Castle Row ---
    grid_x_of_impact_start = int(obj_pixel_x / CHAR_WIDTH)
    damage_start_col = max(0, grid_x_of_impact_start)
    # destruction_width_chars is how many character cells the damage spans
    damage_end_col = min(GRID_WIDTH, damage_start_col + destruction_width_chars)

    target_row_as_list = list(castle_art[hit_row_in_current_castle])
    chars_actually_damaged = 0
    for col in range(damage_start_col, damage_end_col):
        if col < len(target_row_as_list) and target_row_as_list[col] != ' ':
            target_row_as_list[col] = ' '
            chars_actually_damaged += 1

    if chars_actually_damaged > 0:  # Only if actual damage occurred
        castle_art[hit_row_in_current_castle] = "".join(target_row_as_list)

        # --- Create Explosion (as per original structure) ---
        # Explosion centered on the damaged segment of the castle row
        explosion_center_x_px = (damage_start_col + (damage_end_col - damage_start_col) / 2) * CHAR_WIDTH

        # Y-coordinate of the center of the affected castle row on screen
        castle_top_on_screen_grid_y = GRID_HEIGHT - castle_height_at_impact
        hit_row_on_screen_grid_y = castle_top_on_screen_grid_y + hit_row_in_current_castle
        explosion_center_y_px = (hit_row_on_screen_grid_y * CHAR_HEIGHT) + CHAR_HEIGHT / 2

        explosions.append(Explosion(explosion_center_x_px, explosion_center_y_px))

        if hit_sound:
            hit_sound.play()

    # --- Remove Empty Top Rows of Castle ---
    # This happens after damage and potential explosion/sound for this hit
    rows_shrunk_this_step = 0
    while castle_art and all(c == ' ' for c in castle_art[0]):
        castle_art.pop(0)
        rows_shrunk_this_step += 1

    # --- Game Over Checks ---
    if not castle_art:  # Castle completely destroyed (all rows gone)
        game_over = True
        return

    # 1. Core Destruction Check (Specific characters in the core line)
    # This check is only relevant if a core was defined and still potentially exists.
    if INITIAL_CORE_CHAR_COUNT > 0 and INITIAL_CORE_ROW_INDEX_FROM_TOP != -1:
        # Calculate where the original core line *would be* in the current, possibly shrunk, castle
        # num_rows_shrunk_from_original_top = original_height - current_height
        num_rows_shrunk_from_original_top = len(INITIAL_CASTLE_ART_FOR_METRICS) - len(castle_art)

        # Index of the original core line, relative to the current castle_art's top (0-indexed)
        current_expected_core_row_idx_in_art = INITIAL_CORE_ROW_INDEX_FROM_TOP - num_rows_shrunk_from_original_top

        if current_expected_core_row_idx_in_art < 0:
            # The castle has shrunk so much that the entire original core line (and layers above it) is gone.
            game_over = True
        elif current_expected_core_row_idx_in_art < len(castle_art):
            # The line where the core was originally located still exists in the current castle_art.
            # Check if all CORE_CHAR are gone from this line.
            core_line_string = castle_art[current_expected_core_row_idx_in_art]
            if core_line_string.count(CORE_CHAR) == 0:
                game_over = True  # All '*' are gone from the core line
        # If current_expected_core_row_idx_in_art >= len(castle_art), it means the core line
        # should exist but castle is shorter - implies core line is gone. Covered by < 0 effectively.

    if game_over: return

    # 2. Mass Loss Check (e.g., 80% loss means current mass <= 20% of initial)
    if INITIAL_CASTLE_MASS > 0:  # Avoid division by zero if castle started empty
        current_mass = sum(sum(1 for char_in_row in row if char_in_row != ' ') for row in castle_art)
        if current_mass <= INITIAL_CASTLE_MASS * 0.20:  # Lost 80% or more
            game_over = True


# 检查升级
def check_for_level_up():
    global current_level, score  # Ensure score is accessible
    if current_level < len(difficulty_levels):  # Max level is len(difficulty_levels)
        current_level_settings = get_level_settings(current_level)  # Settings for current level
        # Threshold to reach *next* level is in current level's settings
        if score >= current_level_settings.get('score_threshold', float('inf')):
            current_level += 1
            # Optionally, add a visual/audio cue for leveling up


# 绘制游戏结束
def draw_game_over(surface, font_to_use):  # Renamed font parameter
    # Optional: Fade out effect or a solid color overlay
    overlay = pygame.Surface((WINDOW_PIXEL_WIDTH, WINDOW_PIXEL_HEIGHT))
    overlay.set_alpha(180)  # Semi-transparent
    overlay.fill(BLACK)
    surface.blit(overlay, (0, 0))

    game_over_text = "GAME OVER"
    score_text = f"Final Score: {score}"  # score is global
    level_text = f"Reached Level: {current_level}"  # current_level is global
    restart_text = "Press ANY KEY to quit"  # Changed from "restart" to "quit" as per loop logic

    # Use a slightly larger font for "GAME OVER" if available, or scale up
    try:
        game_over_font = pygame.font.SysFont(font.name, CHAR_HEIGHT * 2, bold=True)
    except:
        game_over_font = pygame.font.Font(None, CHAR_HEIGHT * 2)

    game_over_surf = game_over_font.render(game_over_text, True, RED)
    score_surf = font_to_use.render(score_text, True, WHITE)
    level_surf = font_to_use.render(level_text, True, WHITE)
    restart_surf = font_to_use.render(restart_text, True, GRAY)

    # Centering text
    def blit_center(target_surface, text_surf, y_offset_factor):
        x = WINDOW_PIXEL_WIDTH // 2 - text_surf.get_width() // 2
        y = WINDOW_PIXEL_HEIGHT * y_offset_factor - text_surf.get_height() // 2
        target_surface.blit(text_surf, (x, y))

    blit_center(surface, game_over_surf, 0.35)
    blit_center(surface, score_surf, 0.50)
    blit_center(surface, level_surf, 0.58)
    blit_center(surface, restart_surf, 0.75)


# 游戏主循环
async def run_game():
    global falling_objects, current_target, score, current_level, game_over, castle_art
    global last_generate_time, show_red_line, red_line_target, red_line_timer, explosions

    # Reset game state variables for a new game
    falling_objects = []
    current_target = None
    score = 0
    current_level = 1
    game_over = False
    castle_art = list(initial_castle_art)  # Fresh copy of the castle
    explosions = []
    last_generate_time = time.time()  # Start generating objects after a short delay from game start

    # Ensure global castle metrics are initialized (should be called once outside if game can restart)
    # If run_game can be called multiple times, metrics should not be re-initialized here
    # but once globally. Assuming they are already set by initialize_global_castle_metrics().

    clock = pygame.time.Clock()
    running = True

    while running:
        dt = clock.tick(60) / 1000.0  # Delta time in seconds (e.g., 0.0166 for 60 FPS)
        # Cap dt to prevent large jumps if game hangs
        dt = min(dt, 0.1)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                # For Emscripten, sys.exit() might be needed or a different quit mechanism
                if platform.system() == "Emscripten":
                    # Emscripten doesn't handle sys.exit well in async loops sometimes.
                    # Just breaking the loop is often enough.
                    pass
                else:
                    pygame.quit()
                    sys.exit()


            elif event.type == pygame.KEYDOWN:
                if game_over:
                    running = False  # Any key quits after game over
                    # Similar exit logic as QUIT
                    if platform.system() != "Emscripten":
                        pygame.quit()
                        sys.exit()
                    return  # Exit run_game function

                else:  # Game is active
                    typed_char = event.unicode
                    # Allow alphanumeric and some punctuation relevant to typing
                    if typed_char and (typed_char.isalnum() or typed_char in ';.,'):
                        typed_char_upper = typed_char.upper()

                        # If already targeting an object
                        if current_target and current_target.active:
                            completed_word = current_target.handle_input(typed_char)
                            if completed_word:
                                show_red_line = True  # Visual feedback for completion
                                red_line_target = current_target  # Store for drawing laser
                                red_line_timer = time.time()  # Start laser timer

                                points = len(current_target.text) * 10
                                if current_target.is_bonus:
                                    points *= BONUS_SCORE_MULTIPLIER
                                score += points

                                # Word completed, current_target becomes inactive in handle_input
                                current_target = None  # Stop targeting it
                            elif current_target.progress == 0:  # Incorrect char typed, progress reset
                                current_target = None  # Player needs to re-target or pick new one

                        # If not targeting, or target was reset due to mistype
                        if not current_target:
                            # Find a new target that starts with the typed character
                            # Prioritize objects lower on the screen or closer to castle? (Optional enhancement)
                            # For now, first match from the list.
                            best_match = None
                            for obj in falling_objects:
                                if obj.active and obj.text.startswith(typed_char_upper):
                                    # Simple first match, could be improved (e.g. lowest obj)
                                    if best_match is None or obj.pixel_y_float > best_match.pixel_y_float:
                                        best_match = obj

                            if best_match:
                                current_target = best_match
                                completed_word_on_first_char = current_target.handle_input(
                                    typed_char)  # Process the first char
                                if completed_word_on_first_char:  # Single-letter word completed
                                    show_red_line = True
                                    red_line_target = current_target
                                    red_line_timer = time.time()
                                    points = len(current_target.text) * 10
                                    if current_target.is_bonus:
                                        points *= BONUS_SCORE_MULTIPLIER
                                    score += points
                                    current_target = None  # Already completed

        if not game_over:
            check_for_level_up()
            generate_falling_object()

            active_objects_next_frame = []
            current_castle_height_grid = len(castle_art)

            if current_castle_height_grid == 0 and not game_over:  # Should be caught by damage_castle
                game_over = True

            if not game_over:  # Double check before processing objects
                for obj in falling_objects:
                    if obj.active:
                        obj.move(dt)  # Pass delta time for frame-rate independent speed

                        # --- Collision Detection with Castle ---
                        # Determine the part of the castle the object might hit
                        obj_grid_x_start = int(obj.pixel_x / CHAR_WIDTH)
                        obj_grid_x_end = int((obj.pixel_x + len(obj.text) * CHAR_WIDTH) / CHAR_WIDTH)

                        # Find the highest solid castle block below the object's span
                        highest_impact_y_pixel = WINDOW_PIXEL_HEIGHT  # Assume hits bottom of screen if no castle
                        hit_castle_row_idx = -1

                        if current_castle_height_grid > 0:
                            castle_top_on_screen_grid_y = GRID_HEIGHT - current_castle_height_grid

                            min_hit_y_for_this_obj = WINDOW_PIXEL_HEIGHT  # Reset for each obj

                            for col_idx in range(max(0, obj_grid_x_start), min(GRID_WIDTH, obj_grid_x_end)):
                                for row_in_art_idx in range(current_castle_height_grid):  # Iterate castle art rows
                                    if col_idx < len(castle_art[row_in_art_idx]) and \
                                            castle_art[row_in_art_idx][col_idx] != ' ':

                                        # This is a solid castle part at (col_idx, row_in_art_idx)
                                        # Its top Y pixel on screen:
                                        current_part_top_y_px = (
                                                                            castle_top_on_screen_grid_y + row_in_art_idx) * CHAR_HEIGHT
                                        if current_part_top_y_px < min_hit_y_for_this_obj:
                                            min_hit_y_for_this_obj = current_part_top_y_px
                                            hit_castle_row_idx = row_in_art_idx  # Store the index within castle_art
                                        break  # Found highest block in this column, move to next column
                            highest_impact_y_pixel = min_hit_y_for_this_obj

                        if obj.get_bottom_pixel_y() >= highest_impact_y_pixel:
                            obj.active = False  # Object hits something (castle or ground)
                            if obj == current_target:
                                current_target = None  # Stop targeting if it hits

                            if hit_castle_row_idx != -1:  # It hit a valid castle row
                                destruction_width = len(obj.text)
                                if obj.is_bonus:
                                    destruction_width *= BONUS_DAMAGE_MULTIPLIER

                                damage_castle(destruction_width, obj.pixel_x, hit_castle_row_idx)
                                # Explosion and sound are handled inside damage_castle
                            # If hit_castle_row_idx is -1, it means it hit "ground" (below castle)
                            # game_over is handled by damage_castle if castle is destroyed.

                    if obj.active:  # If still active after move and collision checks
                        active_objects_next_frame.append(obj)

                falling_objects = active_objects_next_frame

            # Update explosions
            explosions[:] = [exp for exp in explosions if exp.update(dt)]

        # --- Drawing ---
        screen.fill(BLACK)

        if game_over:
            draw_game_over(screen, font)
        else:
            # Draw castle first (background element)
            draw_castle(screen, font, castle_art)

            # Draw falling objects
            for obj in falling_objects:
                obj.draw(screen, font)

            # Draw explosions on top
            for exp in explosions:
                exp.draw(screen)

            # Draw "laser" line if active
            if show_red_line and red_line_target:
                if time.time() - red_line_timer <= RED_LINE_DURATION:
                    target_center_x, target_center_y = red_line_target.get_center_position()

                    # Laser origin: center of the top of the highest castle part, or screen bottom if no castle
                    laser_origin_x = WINDOW_PIXEL_WIDTH / 2
                    if castle_art:
                        castle_top_on_screen_grid_y = GRID_HEIGHT - len(castle_art)
                        laser_origin_y = castle_top_on_screen_grid_y * CHAR_HEIGHT
                    else:  # No castle left
                        laser_origin_y = WINDOW_PIXEL_HEIGHT

                    pygame.draw.line(screen, RED,
                                     (laser_origin_x, laser_origin_y),
                                     (target_center_x, target_center_y), 2)
                else:
                    show_red_line = False  # Duration ended
                    red_line_target = None

            # Draw Score and Level
            score_text_str = f"Score: {score}  Level: {current_level}"
            score_surface = font.render(score_text_str, True, WHITE)
            screen.blit(score_surface, (WINDOW_PIXEL_WIDTH - score_surface.get_width() - 10, 10))

            # Highlight current target (optional)
            if current_target and current_target.active:
                pygame.draw.rect(screen, YELLOW,
                                 (current_target.pixel_x - 2, int(current_target.pixel_y_float) - 2,
                                  len(current_target.text) * CHAR_WIDTH + 4, CHAR_HEIGHT + 4), 1)

        pygame.display.flip()
        await asyncio.sleep(0)  # Yield control for web environment / async

    # After running loop finishes (e.g., game over and key press, or QUIT)
    # For non-Emscripten, pygame.quit() and sys.exit() are handled above.
    # For Emscripten, just returning from run_game is often sufficient.


async def main():
    # This function is the main entry point for the asyncio loop.
    # Initialize Pygame components that are safe to init once globally (like mixer, font)
    # The main game logic is encapsulated in run_game.
    await run_game()


if __name__ == "__main__":
    if platform.system() == "Emscripten":
        # For web environment (e.g., Pygbag)
        asyncio.run(main())  # Use asyncio.run for the main async function
    else:
        # For desktop environment
        # Pygame's event loop is typically synchronous.
        # If using asyncio for other reasons on desktop, this is fine.
        # Otherwise, a standard synchronous Pygame loop would also work.
        # Given the `await asyncio.sleep(0)` in run_game, using asyncio.run is consistent.
        asyncio.run(main())
