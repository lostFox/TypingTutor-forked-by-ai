import asyncio
import platform
import pygame
import sys
import random
import time

# Pygame 初始化
pygame.init()

# 窗口和网格设置
CHAR_WIDTH_ESTIMATE = 10
CHAR_HEIGHT_ESTIMATE = 20
GRID_WIDTH = 60
GRID_HEIGHT = 25
CASTLE_BOTTOM_GRID_ROW = GRID_HEIGHT - 1
CASTLE_INITIAL_HEIGHT_GRID = 3

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
            break
    except pygame.error:
        pass

if not font:
    font = pygame.font.Font(None, CHAR_HEIGHT_ESTIMATE)

char_size = font.size(" ")
CHAR_WIDTH = char_size[0]
CHAR_HEIGHT = char_size[1]
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

# FallingObject 类
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

    def draw(self, surface, font):
        if not self.active:
            return
        text_surface = font.render(self.text, True, self.color)
        surface.blit(text_surface, (self.pixel_x, int(self.pixel_y)))

    def move(self):
        if self.active:
            self.pixel_y += self.speed_pixel_per_frame

    def get_bottom_pixel_y(self):
        return self.pixel_y + CHAR_HEIGHT

    def get_center_position(self):
        grid_x = int(self.pixel_x / CHAR_WIDTH)
        grid_y = int(self.pixel_y / CHAR_HEIGHT)
        center_x = (grid_x + len(self.text) / 2) * CHAR_WIDTH
        center_y = grid_y * CHAR_HEIGHT + CHAR_HEIGHT / 2
        return center_x, center_y

# 难度定义
difficulty_levels = [
    {
        'level': 1,
        'items': ['F', 'G', 'H', 'J'],
        'speed_grid_per_sec': 0.3,
        'generate_interval': 2.0,
        'score_threshold': 50
    },  # 食指基准键（中间排）[[5]][[9]]

    {
        'level': 2,
        'items': ['T', 'Y', 'U', 'B', 'N', 'M'],
        'speed_grid_per_sec': 0.35,
        'generate_interval': 1.8,
        'score_threshold': 150
    },  # 食指扩展（上排T/Y/U + 下排B/N/M）[[5]][[8]]

    {
        'level': 3,
        'items': ['D', 'K', 'R', 'E'],
        'speed_grid_per_sec': 0.4,
        'generate_interval': 1.6,
        'score_threshold': 300
    },  # 中指基准键（中间排D/K）+ 上排R/E[[5]][[3]]

    {
        'level': 4,
        'items': ['S', 'L', 'W', 'Q'],
        'speed_grid_per_sec': 0.45,
        'generate_interval': 1.4,
        'score_threshold': 500
    },  # 无名指基准键（中间排S/L）+ 上排W/Q[[5]][[4]]

    {
        'level': 5,
        'items': ['A', ';', 'Z', 'X'],
        'speed_grid_per_sec': 0.5,
        'generate_interval': 2.5,
        'score_threshold': 800
    },  # 小指基准键（中间排A/;）+ 下排Z/X[[5]][[9]]

    {
        'level': 6,
        'items': ['THE', 'AND', 'FOR', 'ARE', 'BUT'],
        'speed_grid_per_sec': 0.55,
        'generate_interval': 2.2,
        'score_threshold': 1200
    },  # 单词入门（高频短词）[[7]][[4]]

    {
        'level': 7,
        'items': ['THIS', 'THAT', 'WITH', 'FROM', 'HAVE'],
        'speed_grid_per_sec': 0.6,
        'generate_interval': 2.0,
        'score_threshold': 1800
    },  # 中等长度单词[[7]][[4]]

    {
        'level': 8,
        'items': ['PROGRAMMING', 'DEVELOPMENT', 'COMPUTER', 'SCIENCE', 'INTELLIGENCE'],
        'speed_grid_per_sec': 0.65,
        'generate_interval': 1.8,
        'score_threshold': 2500
    }  # 长单词与技术术语[[7]][[4]]
]

def get_level_settings(level):
    index = max(0, min(level - 1, len(difficulty_levels) - 1))
    return difficulty_levels[index]

# 城堡艺术字和状态
initial_castle_art = [
    "############################################################",
    "============================================================",
    "||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||",
]
castle_art = []

# 游戏状态变量
falling_objects = []
current_target = None
score = 0
current_level = 1
game_over = False
last_generate_time = time.time()
show_red_line = False
red_line_target = None
red_line_timer = 0
RED_LINE_DURATION = 0.1  # 红线显示0.1秒

# 奖励物品设置
BONUS_CHANCE = 0.1
BONUS_SPEED_MULTIPLIER = 8.0
BONUS_SCORE_MULTIPLIER = 2
BONUS_DAMAGE_MULTIPLIER = 2

# 生成掉落物体
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
        speed = base_speed * (BONUS_SPEED_MULTIPLIER if is_bonus else 1.0)
        new_object = FallingObject(item, speed_grid_per_sec=speed, color=color, is_bonus=is_bonus)
        falling_objects.append(new_object)
        last_generate_time = now

# 绘制城堡
def draw_castle(surface, font, castle_art_lines):
    current_castle_height_grid = len(castle_art_lines)
    if current_castle_height_grid == 0:
        return
    castle_top_pixel_y = (GRID_HEIGHT - current_castle_height_grid) * CHAR_HEIGHT
    for i, line in enumerate(castle_art_lines):
        line_surface = font.render(line, True, BLUE)
        surface.blit(line_surface, (0, castle_top_pixel_y + i * CHAR_HEIGHT))

# 破坏城堡
def damage_castle(amount):
    global castle_art, game_over
    for _ in range(amount):
        if castle_art:
            castle_art.pop(0)
        else:
            game_over = True
            break

# 检查升级
def check_for_level_up():
    global current_level
    if current_level < len(difficulty_levels):
        current_level_settings = get_level_settings(current_level)
        if score >= current_level_settings.get('score_threshold', float('inf')):
            current_level += 1

# 绘制游戏结束
def draw_game_over(surface, font):
    screen.fill(BLACK)
    game_over_text = "GAME OVER"
    score_text = f"Final Score: {score}"
    restart_text = "Press any key to quit"
    game_over_surface = font.render(game_over_text, True, RED)
    score_surface = font.render(score_text, True, WHITE)
    restart_surface = font.render(restart_text, True, GRAY)
    surface.blit(game_over_surface, (WINDOW_PIXEL_WIDTH // 2 - game_over_surface.get_width() // 2, WINDOW_PIXEL_HEIGHT // 3))
    surface.blit(score_surface, (WINDOW_PIXEL_WIDTH // 2 - score_surface.get_width() // 2, WINDOW_PIXEL_HEIGHT // 3 + CHAR_HEIGHT * 2))
    surface.blit(restart_surface, (WINDOW_PIXEL_WIDTH // 2 - restart_surface.get_width() // 2, WINDOW_PIXEL_HEIGHT // 2))

# 游戏主循环
async def run_game():
    global falling_objects, current_target, score, current_level, game_over, castle_art, last_generate_time, show_red_line, red_line_target, red_line_timer
    clock = pygame.time.Clock()
    castle_art = list(initial_castle_art)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            elif event.type == pygame.KEYDOWN:
                if game_over:
                    return
                else:
                    typed_char = event.unicode
                    if typed_char and (typed_char.isalnum() or typed_char in ';'):
                        typed_char_upper = typed_char.upper()
                        for obj in falling_objects:
                            if obj.active and obj.text.startswith(typed_char_upper):
                                current_target = obj
                                show_red_line = True
                                red_line_target = obj
                                red_line_timer = time.time()
                                points = len(obj.text) * 10 * (BONUS_SCORE_MULTIPLIER if obj.is_bonus else 1)
                                score += points
                                obj.active = False
                                break

        if not game_over:
            check_for_level_up()
            generate_falling_object()
            active_objects_next_frame = []
            current_castle_height_grid = len(castle_art)
            castle_top_pixel_y = (GRID_HEIGHT - current_castle_height_grid) * CHAR_HEIGHT if current_castle_height_grid > 0 else WINDOW_PIXEL_HEIGHT
            for obj in falling_objects:
                if obj.active:
                    obj.move()
                    if current_castle_height_grid > 0 and obj.get_bottom_pixel_y() >= castle_top_pixel_y:
                        obj.active = False
                        damage_amount = BONUS_DAMAGE_MULTIPLIER if obj.is_bonus else 1
                        damage_castle(damage_amount)
                if obj.active:
                    active_objects_next_frame.append(obj)
            falling_objects = active_objects_next_frame

        # 检查红线显示时间
        if show_red_line and time.time() - red_line_timer > RED_LINE_DURATION:
            show_red_line = False
            red_line_target = None

        # 绘制
        screen.fill(BLACK)
        if game_over:
            draw_game_over(screen, font)
        else:
            for obj in falling_objects:
                obj.draw(screen, font)
            draw_castle(screen, font, castle_art)
            if show_red_line and red_line_target:
                target_center_x, target_center_y = red_line_target.get_center_position()
                castle_center_x = WINDOW_PIXEL_WIDTH / 2
                castle_bottom_y = WINDOW_PIXEL_HEIGHT - CHAR_HEIGHT * len(castle_art) if castle_art else WINDOW_PIXEL_HEIGHT
                pygame.draw.line(screen, RED, (castle_center_x, castle_bottom_y), (target_center_x, target_center_y), 2)
            score_text = f"Score: {score} Level: {current_level}"
            score_surface = font.render(score_text, True, WHITE)
            screen.blit(score_surface, (WINDOW_PIXEL_WIDTH - score_surface.get_width() - 10, 10))

        pygame.display.flip()
        clock.tick(60)
        await asyncio.sleep(1.0 / 60)

# Pyodide 兼容性处理
async def main():
    await run_game()

if platform.system() == "Emscripten":
    asyncio.ensure_future(main())
else:
    if __name__ == "__main__":
        asyncio.run(main())