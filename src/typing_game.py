import asyncio
import platform
import pygame
import sys
import random
import time

# --- Pygame 初始化 ---
pygame.init()

# --- 窗口和网格设置 ---
CHAR_WIDTH_ESTIMATE = 10
CHAR_HEIGHT_ESTIMATE = 20
GRID_WIDTH = 60
GRID_HEIGHT = 25
CASTLE_BOTTOM_GRID_ROW = GRID_HEIGHT - 1
CASTLE_INITIAL_HEIGHT_GRID = 3

WINDOW_PIXEL_WIDTH = GRID_WIDTH * CHAR_WIDTH_ESTIMATE
WINDOW_PIXEL_HEIGHT = GRID_HEIGHT * CHAR_HEIGHT_ESTIMATE

screen = pygame.display.set_mode((WINDOW_PIXEL_WIDTH, WINDOW_PIXEL_HEIGHT))
pygame.display.set_caption("This is tt game")

# --- 字体设置 ---
font = None
CHAR_WIDTH = CHAR_WIDTH_ESTIMATE
CHAR_HEIGHT = CHAR_HEIGHT_ESTIMATE
loaded_font_name = "Default"
font_names_to_try = ["Consolas", "Courier New", "Lucida Console", "DejaVu Sans Mono", "Liberation Mono", "Arial"]

try:
    for font_name in font_names_to_try:
        try:
            test_font = pygame.font.SysFont(font_name, CHAR_HEIGHT_ESTIMATE, bold=False)
            if test_font is not None:
                font = test_font
                loaded_font_name = font_name
                break
        except pygame.error:
            pass

    if font is None:
        print("警告: 未找到合适的系统字体. 使用默认 Pygame 字体.")
        font = pygame.font.Font(None, CHAR_HEIGHT_ESTIMATE)
        loaded_font_name = "Default Pygame Font"

    char_size = font.size(" ")
    CHAR_WIDTH = char_size[0]
    CHAR_HEIGHT = char_size[1]

    WINDOW_PIXEL_WIDTH = GRID_WIDTH * CHAR_WIDTH
    WINDOW_PIXEL_HEIGHT = GRID_HEIGHT * CHAR_HEIGHT
    screen = pygame.display.set_mode((WINDOW_PIXEL_WIDTH, WINDOW_PIXEL_HEIGHT))

    print(f"最终使用字体: {font.get_name() if hasattr(font, 'get_name') else loaded_font_name}, 字符尺寸: {CHAR_WIDTH}x{CHAR_HEIGHT}, 窗口尺寸: {WINDOW_PIXEL_WIDTH}x{WINDOW_PIXEL_HEIGHT}")

except pygame.error as e:
    print(f"严重错误: 字体加载或尺寸计算失败: {e}. 尝试使用估算尺寸.")
    font = pygame.font.Font(None, CHAR_HEIGHT_ESTIMATE)
    CHAR_WIDTH = CHAR_WIDTH_ESTIMATE
    CHAR_HEIGHT = CHAR_HEIGHT_ESTIMATE
    print(f"使用默认字体 (Fallback Error), 字符尺寸: {CHAR_WIDTH}x{CHAR_HEIGHT}, 窗口尺寸: {WINDOW_PIXEL_WIDTH}x{WINDOW_PIXEL_HEIGHT}")

if font is None:
    print("严重错误: 无法加载任何字体。程序将退出。")
    pygame.quit()
    sys.exit()

# --- 颜色定义 ---
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)
BLUE = (0, 0, 255)
GRAY = (128, 128, 128)

# --- FallingObject 类 ---
class FallingObject:
    def __init__(self, text, speed_grid_per_sec=0.5, color=WHITE, is_bonus=False):
        self.text = text.upper()
        self.color = color
        self.is_bonus = is_bonus
        self.speed_pixel_per_frame = speed_grid_per_sec * CHAR_HEIGHT / 60.0
        grid_x = random.randint(0, GRID_WIDTH - len(self.text))
        self.pixel_x = grid_x * CHAR_WIDTH
        self.pixel_y = 0
        self.active = True
        self.progress = 0

    def draw(self, surface, font):
        if not self.active:
            return
        inputted_text = self.text[:self.progress]
        if inputted_text:
            input_surface = font.render(inputted_text, True, GREEN)
            surface.blit(input_surface, (self.pixel_x, int(self.pixel_y)))
        remaining_text = self.text[self.progress:]
        if remaining_text:
            remaining_surface = font.render(remaining_text, True, self.color)
            surface.blit(remaining_surface, (self.pixel_x + self.progress * CHAR_WIDTH, int(self.pixel_y)))

    def move(self):
        if self.active:
            self.pixel_y += self.speed_pixel_per_frame

    def handle_input(self, typed_char):
        if not self.active or self.progress >= len(self.text):
            return False
        expected_char = self.text[self.progress].upper()
        typed_char_upper = typed_char.upper()
        if typed_char_upper == expected_char:
            self.progress += 1
            if self.progress == len(self.text):
                self.active = False
                return True
            return False
        else:
            self.progress = 0
            return False

    def reset_progress(self):
        self.progress = 0

    def get_bottom_pixel_y(self):
        return self.pixel_y + CHAR_HEIGHT

    def get_center_position(self):
        grid_x = int(self.pixel_x / CHAR_WIDTH)
        grid_y = int(self.pixel_y / CHAR_HEIGHT)
        center_x = (grid_x + len(self.text) / 2) * CHAR_WIDTH
        center_y = grid_y * CHAR_HEIGHT + CHAR_HEIGHT / 2
        return center_x, center_y

# --- 难度定义 ---
difficulty_levels = [
    {'level': 1, 'items': ['F', 'J', 'G', 'H'], 'speed_grid_per_sec': 0.3, 'generate_interval': 2.0, 'score_threshold': 50},
    {'level': 2, 'items': ['D', 'K', 'S', 'L'], 'speed_grid_per_sec': 0.35, 'generate_interval': 1.8, 'score_threshold': 150},
    {'level': 3, 'items': ['A', ';'], 'speed_grid_per_sec': 0.4, 'generate_interval': 1.6, 'score_threshold': 300},
    {'level': 4, 'items': list('QWERTYUIOPASDFGHJKLZXCVBNM'), 'speed_grid_per_sec': 0.45, 'generate_interval': 1.4, 'score_threshold': 500},
    {'level': 5, 'items': ['THE', 'AND', 'FOR', 'ARE', 'BUT'], 'speed_grid_per_sec': 0.5, 'generate_interval': 2.5, 'score_threshold': 800},
    {'level': 6, 'items': ['THIS', 'THAT', 'WITH', 'FROM', 'HAVE'], 'speed_grid_per_sec': 0.55, 'generate_interval': 2.2, 'score_threshold': 1200},
    {'level': 7, 'items': ['LEARN', 'PYTHON', 'GAME', 'TYPING', 'KEYBOARD'], 'speed_grid_per_sec': 0.6, 'generate_interval': 2.0, 'score_threshold': 1800},
    {'level': 8, 'items': ['PROGRAMMING', 'DEVELOPMENT', 'COMPUTER', 'SCIENCE', 'INTELLIGENCE'], 'speed_grid_per_sec': 0.65, 'generate_interval': 1.8, 'score_threshold': 2500},
]

def get_level_settings(level):
    index = max(0, min(level - 1, len(difficulty_levels) - 1))
    return difficulty_levels[index]

# --- 城堡艺术字和状态 ---
initial_castle_art = [
    "############################################################",
    "============================================================",
    "||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||",
]
for line in initial_castle_art:
    assert len(line) == GRID_WIDTH, f"城堡艺术字长度错误! 期望 {GRID_WIDTH}, 实际 {len(line)}"
castle_art = []

# --- 游戏状态变量 ---
falling_objects = []
current_target = None
score = 0
current_level = 1
game_over = False
last_generate_time = time.time()

# --- 奖励物品设置 ---
BONUS_CHANCE = 0.1
BONUS_SPEED_MULTIPLIER = 2.0  # 增加到2.0以加快速度
BONUS_SCORE_MULTIPLIER = 2
BONUS_DAMAGE_MULTIPLIER = 2

# --- 生成掉落物体 ---
def generate_falling_object():
    global falling_objects, last_generate_time
    now = time.time()
    level_settings = get_level_settings(current_level)
    generate_interval = level_settings['generate_interval']
    if level_settings['items'] and now - last_generate_time > generate_interval:
        item = random.choice(level_settings['items'])
        base_speed = level_settings['speed_grid_per_sec']
        is_bonus = random.random() < BONUS_CHANCE
        color = YELLOW if is_bonus else WHITE
        speed = base_speed
        if is_bonus:
            speed *= BONUS_SPEED_MULTIPLIER
            speed = max(speed, base_speed * 1.5)  # 确保至少1.5倍基本速度
        new_object = FallingObject(item, speed_grid_per_sec=speed, color=color, is_bonus=is_bonus)
        falling_objects.append(new_object)
        last_generate_time = now

# --- 绘制城堡 ---
def draw_castle(surface, font, castle_art_lines):
    current_castle_height_grid = len(castle_art_lines)
    if current_castle_height_grid == 0:
        return
    castle_top_pixel_y = (GRID_HEIGHT - current_castle_height_grid) * CHAR_HEIGHT
    for i, line in enumerate(castle_art_lines):
        line_surface = font.render(line, True, BLUE)
        surface.blit(line_surface, (0, castle_top_pixel_y + i * CHAR_HEIGHT))

# --- 破坏城堡 ---
def damage_castle(amount):
    global castle_art, game_over
    damage_done = 0
    for _ in range(amount):
        if castle_art:
            castle_art.pop(0)
            damage_done += 1
        else:
            game_over = True  # 确保城堡全毁时触发游戏结束
            break
    return damage_done

# --- 检查升级 ---
def check_for_level_up():
    global current_level
    if current_level < len(difficulty_levels):
        current_level_settings = get_level_settings(current_level)
        if score >= current_level_settings.get('score_threshold', float('inf')):
            current_level += 1
            print(f"Level Up! Current Level: {current_level}.")
            next_level_settings = get_level_settings(current_level)
            if next_level_settings['items']:
                print(f"  新物品示例: {next_level_settings['items'][:min(3, len(next_level_settings['items']))]}...")

# --- 绘制游戏结束 ---
def draw_game_over(surface, font):
    screen.fill(BLACK)
    game_over_text = "game over"
    score_text = f"final score: {score}"
    restart_text = "pass anykey 2 quit"
    game_over_surface = font.render(game_over_text, True, RED)
    score_surface = font.render(score_text, True, WHITE)
    restart_surface = font.render(restart_text, True, GRAY)
    game_over_rect = game_over_surface.get_rect(center=(WINDOW_PIXEL_WIDTH // 2, WINDOW_PIXEL_HEIGHT // 3))
    score_rect = score_surface.get_rect(center=(WINDOW_PIXEL_WIDTH // 2, WINDOW_PIXEL_HEIGHT // 3 + CHAR_HEIGHT * 2))
    restart_rect = restart_surface.get_rect(center=(WINDOW_PIXEL_WIDTH // 2, WINDOW_PIXEL_HEIGHT // 2))
    surface.blit(game_over_surface, game_over_rect)
    surface.blit(score_surface, score_rect)
    surface.blit(restart_surface, restart_rect)

# --- 游戏主循环 ---
async def run_game():
    global running, falling_objects, current_target, score, current_level, game_over, castle_art, last_generate_time
    running = True
    clock = pygame.time.Clock()
    castle_art = list(initial_castle_art)
    FPS = 60

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if game_over:
                    running = False
                else:
                    typed_char = event.unicode
                    if typed_char and (typed_char.isalnum() or typed_char in ';'):
                        typed_char_upper = typed_char.upper()
                        target_switched = False
                        if current_target and current_target.active:
                            is_completed = current_target.handle_input(typed_char)
                            if is_completed:
                                points = len(current_target.text) * 10
                                if current_target.is_bonus:
                                    points *= BONUS_SCORE_MULTIPLIER
                                score += points
                                current_target = None
                                continue
                            found_alternative = None
                            for obj in falling_objects:
                                if obj.active and obj != current_target and obj.text.startswith(typed_char_upper):
                                    found_alternative = obj
                                    break
                            if found_alternative:
                                current_target.reset_progress()
                                current_target = found_alternative
                                target_switched = True
                        if current_target is None and not target_switched:
                            for obj in falling_objects:
                                if obj.active and obj.text.startswith(typed_char_upper):
                                    current_target = obj
                                    break
                        if current_target and current_target.active and current_target.progress == len(current_target.text):
                            current_target = None

        if not game_over:
            check_for_level_up()
            generate_falling_object()
            active_objects_next_frame = []
            current_castle_height_grid = len(castle_art)
            current_castle_top_pixel_y = (GRID_HEIGHT - current_castle_height_grid) * CHAR_HEIGHT if current_castle_height_grid > 0 else WINDOW_PIXEL_HEIGHT
            for obj in falling_objects:
                if obj.active:
                    obj.move()
                    if current_castle_height_grid > 0 and obj.get_bottom_pixel_y() >= current_castle_top_pixel_y:
                        obj.active = False
                        damage_amount = 1
                        if obj.is_bonus:
                            damage_amount *= BONUS_DAMAGE_MULTIPLIER
                        damage_castle(damage_amount)
                        if obj == current_target:
                            current_target = None
                if obj.active:
                    active_objects_next_frame.append(obj)
            falling_objects = active_objects_next_frame

        screen.fill(BLACK)
        if game_over:
            draw_game_over(screen, font)
        else:
            for obj in falling_objects:
                obj.draw(screen, font)
            draw_castle(screen, font, castle_art)
            # 绘制火力动画
            if current_target and current_target.active:
                target_center_x, target_center_y = current_target.get_center_position()
                castle_center_x = WINDOW_PIXEL_WIDTH / 2
                castle_bottom_y = WINDOW_PIXEL_HEIGHT - CHAR_HEIGHT * len(castle_art) if castle_art else WINDOW_PIXEL_HEIGHT
                pygame.draw.line(screen, RED, (castle_center_x, castle_bottom_y), (target_center_x, target_center_y), 2)
            score_text = f"score: {score} level: {current_level}"
            score_surface = font.render(score_text, True, WHITE)
            score_rect = score_surface.get_rect()
            score_rect.topright = (WINDOW_PIXEL_WIDTH - 10, 10)
            screen.blit(score_surface, score_rect)

        pygame.display.flip()
        clock.tick(FPS)
        await asyncio.sleep(1.0 / FPS)

if platform.system() == "Emscripten":
    asyncio.ensure_future(run_game())
else:
    if __name__ == "__main__":
        asyncio.run(run_game())