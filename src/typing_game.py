import asyncio
import platform
import pygame
import sys
import random
import time
import math  # 新增 math 模块导入

# Pygame 初始化
pygame.init()
pygame.mixer.init()  # 初始化音频

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
PURPLE = (128, 0, 128)

# 爆炸效果类
class Explosion:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.start_time = time.time()
        self.duration = 0.3  # 持续0.3秒
        self.particles = []
        for _ in range(8):
            speed = random.uniform(50, 100)  # 像素/秒
            angle = random.uniform(0, 2 * 3.14159)
            vx = speed * math.cos(angle)  # 修复：random.cos -> math.cos
            vy = speed * math.sin(angle)  # 修复：random.sin -> math.sin
            self.particles.append({
                'x': x,
                'y': y,
                'vx': vx,
                'vy': vy,
                'radius': random.uniform(2, 5)
            })

    def update(self, dt):
        for particle in self.particles:
            particle['x'] += particle['vx'] * dt
            particle['y'] += particle['vy'] * dt
            particle['radius'] *= 0.95  # 逐渐缩小
        return time.time() - self.start_time < self.duration

    def draw(self, surface):
        for particle in self.particles:
            alpha = 255 * (1 - (time.time() - self.start_time) / self.duration)
            color = (255, max(0, int(255 - alpha)), 0)  # 红到黄渐变
            pygame.draw.circle(surface, color, (int(particle['x']), int(particle['y'])), int(particle['radius']))

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
        self.progress = 0

    def draw(self, surface, font):
        if not self.active:
            return
        inputted_text = self.text[:self.progress]
        remaining_text = self.text[self.progress:]
        if inputted_text:
            input_surface = font.render(inputted_text, True, GREEN)
            surface.blit(input_surface, (self.pixel_x, int(self.pixel_y)))
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

# 难度定义
difficulty_levels = [
    {
        'level': 1,
        'items': ['F', 'G', 'H', 'J'],
        'speed_grid_per_sec': 0.3,
        'generate_interval': 2.0,
        'score_threshold': 50,
        'memory_items': []
    },
    {
        'level': 2,
        'items': ['T', 'Y', 'U', 'B', 'N', 'M'],
        'speed_grid_per_sec': 0.35,
        'generate_interval': 1.8,
        'score_threshold': 150,
        'memory_items': ['F', 'G', 'H', 'J']
    },
    {
        'level': 3,
        'items': ['D', 'K', 'R', 'E'],
        'speed_grid_per_sec': 0.4,
        'generate_interval': 1.6,
        'score_threshold': 300,
        'memory_items': ['F', 'G', 'H', 'J', 'T', 'Y', 'U', 'B', 'N', 'M']
    },
    {
        'level': 4,
        'items': ['S', 'L', 'W', 'Q'],
        'speed_grid_per_sec': 0.45,
        'generate_interval': 1.4,
        'score_threshold': 500,
        'memory_items': ['F', 'G', 'H', 'J', 'T', 'Y', 'U', 'B', 'N', 'M', 'D', 'K', 'R', 'E']
    },
    {
        'level': 5,
        'items': ['A', ';', 'Z', 'X'],
        'speed_grid_per_sec': 0.5,
        'generate_interval': 2.5,
        'score_threshold': 800,
        'memory_items': ['F', 'G', 'H', 'J', 'T', 'Y', 'U', 'B', 'N', 'M', 'D', 'K', 'R', 'E', 'S', 'L', 'W', 'Q']
    },
    {
        'level': 6,
        'items': ['THE', 'AND', 'FOR', 'ARE', 'BUT'],
        'speed_grid_per_sec': 0.55,
        'generate_interval': 2.2,
        'score_threshold': 1200,
        'memory_items': ['F', 'G', 'H', 'J', 'T', 'Y', 'U', 'B', 'N', 'M', 'D', 'K', 'R', 'E', 'S', 'L', 'W', 'Q', 'A', ';', 'Z', 'X']
    },
    {
        'level': 7,
        'items': ['THIS', 'THAT', 'WITH', 'FROM', 'HAVE'],
        'speed_grid_per_sec': 0.6,
        'generate_interval': 2.0,
        'score_threshold': 1800,
        'memory_items': ['THE', 'AND', 'FOR', 'ARE', 'BUT']
    },
    {
        'level': 8,
        'items': ['PROGRAMMING', 'DEVELOPMENT', 'COMPUTER', 'SCIENCE', 'INTELLIGENCE'],
        'speed_grid_per_sec': 0.65,
        'generate_interval': 1.8,
        'score_threshold': 2500,
        'memory_items': ['THIS', 'THAT', 'WITH', 'FROM', 'HAVE']
    }
]

def get_level_settings(level):
    index = max(0, min(level - 1, len(difficulty_levels) - 1))
    return difficulty_levels[index]

# 城堡艺术字和状态
initial_castle_art = [
    "#" * GRID_WIDTH,
    "=" * GRID_WIDTH,
    "#" * (GRID_WIDTH // 2 - 5) + "*" * 10 + "#" * (GRID_WIDTH // 2 - 5),
]
castle_art = []

# 游戏状态变量
falling_objects = []
current_target = None
score = 0
current_level = 1
game_over = False
last_generate_time = None
show_red_line = False
red_line_target = None
red_line_timer = 0
RED_LINE_DURATION = 0.1
MEMORY_ITEM_CHANCE = 0.3
BONUS_CHANCE = 0.1
BONUS_SPEED_MULTIPLIER = 8.0
BONUS_SCORE_MULTIPLIER = 2
BONUS_DAMAGE_MULTIPLIER = 2
explosions = []

# 音频初始化（占位符，需替换为实际文件）
try:
    pygame.mixer.music.load("../res/background.mid")  # 替换为你的 MIDI 文件路径或 URL
    pygame.mixer.music.set_volume(0.5)
    pygame.mixer.music.play(-1)  # 循环播放
except pygame.error:
    print("Warning: Could not load background music. Please provide a valid MIDI file.")

try:
    hit_sound = pygame.mixer.Sound("../res/hit.wav")  # 替换为你的 WAV 或 MIDI 文件
    hit_sound.set_volume(0.7)
except pygame.error:
    print("Warning: Could not load hit sound. Please provide a valid WAV file.")
    hit_sound = None

# 生成掉落物体
def generate_falling_object():
    global falling_objects, last_generate_time
    now = time.time()
    if last_generate_time is None:
        last_generate_time = now
    level_settings = get_level_settings(current_level)
    generate_interval = level_settings['generate_interval']
    if level_settings['items'] and now - last_generate_time > generate_interval:
        if level_settings['memory_items'] and random.random() < MEMORY_ITEM_CHANCE:
            item = random.choice(level_settings['memory_items'])
        else:
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
        for j, char in enumerate(line):
            color = PURPLE if char == '*' else BLUE
            char_surface = font.render(char, True, color)
            surface.blit(char_surface, (j * CHAR_WIDTH, castle_top_pixel_y + i * CHAR_HEIGHT))

# 破坏城堡
def damage_castle(text_length, obj_x, row_index):
    global castle_art, game_over, explosions
    if not castle_art or row_index >= len(castle_art):
        game_over = True
        return
    grid_x = int(obj_x / CHAR_WIDTH)
    damage_start = max(0, grid_x)
    damage_end = min(GRID_WIDTH, grid_x + text_length)
    target_row = list(castle_art[row_index])
    for i in range(damage_start, damage_end):
        if i < len(target_row):
            target_row[i] = ' '
    castle_art[row_index] = ''.join(target_row)
    # 添加爆炸效果
    center_x, center_y = grid_x * CHAR_WIDTH + (text_length * CHAR_WIDTH) / 2, (GRID_HEIGHT - len(castle_art) + row_index) * CHAR_HEIGHT
    explosions.append(Explosion(center_x, center_y))
    # 播放击中音效
    if hit_sound:
        hit_sound.play()
    # 移除上方的空行
    while castle_art and all(c == ' ' for c in castle_art[0]):
        castle_art.pop(0)
    # 检查游戏结束条件
    if len(castle_art) == 1:
        core_start = GRID_WIDTH // 2 - 5
        core_end = core_start + 10
        core_chars = castle_art[0][core_start:core_end]
        if all(c == ' ' for c in core_chars):
            game_over = True
        elif sum(1 for c in castle_art[0] if c == ' ') >= GRID_WIDTH // 2:
            game_over = True

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
    global falling_objects, current_target, score, current_level, game_over, castle_art, last_generate_time, show_red_line, red_line_target, red_line_timer, explosions
    clock = pygame.time.Clock()
    castle_art = list(initial_castle_art)
    last_generate_time = time.time()

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
                        if current_target and current_target.active:
                            is_completed = current_target.handle_input(typed_char)
                            if is_completed:
                                show_red_line = True
                                red_line_target = current_target
                                red_line_timer = time.time()
                                points = len(current_target.text) * 10 * (BONUS_SCORE_MULTIPLIER if current_target.is_bonus else 1)
                                score += points
                                current_target = None
                            elif current_target.progress == 0:
                                current_target = None
                        else:
                            for obj in falling_objects:
                                if obj.active and obj.text.startswith(typed_char_upper):
                                    current_target = obj
                                    if len(obj.text) == 1:
                                        show_red_line = True
                                        red_line_target = obj
                                        red_line_timer = time.time()
                                        points = len(obj.text) * 10 * (BONUS_SCORE_MULTIPLIER if obj.is_bonus else 1)
                                        score += points
                                        obj.active = False
                                        current_target = None
                                    else:
                                        obj.progress = 1
                                    break

        if not game_over:
            check_for_level_up()
            generate_falling_object()
            active_objects_next_frame = []
            current_castle_height_grid = len(castle_art)
            if current_castle_height_grid == 0:
                game_over = True
            else:
                for obj in falling_objects:
                    if obj.active:
                        obj.move()
                        grid_x = int(obj.pixel_x / CHAR_WIDTH)
                        damage_start = max(0, grid_x)
                        damage_end = min(GRID_WIDTH, grid_x + len(obj.text))
                        hit_row = None
                        hit_pixel_y = WINDOW_PIXEL_HEIGHT
                        for col in range(damage_start, damage_end):
                            for row_idx, row in enumerate(castle_art):
                                if col < len(row) and row[col] != ' ':
                                    if hit_row is None or row_idx < hit_row:
                                        hit_row = row_idx
                                    break
                        if hit_row is not None:
                            hit_pixel_y = (GRID_HEIGHT - current_castle_height_grid + hit_row) * CHAR_HEIGHT
                        if obj.get_bottom_pixel_y() >= hit_pixel_y:
                            obj.active = False
                            damage_amount = len(obj.text) * (BONUS_DAMAGE_MULTIPLIER if obj.is_bonus else 1)
                            if hit_row is not None:
                                damage_castle(damage_amount, obj.pixel_x, hit_row)
                            if obj == current_target:
                                current_target = None
                        if obj.active:
                            active_objects_next_frame.append(obj)
                falling_objects = active_objects_next_frame

            # 更新爆炸效果
            explosions[:] = [exp for exp in explosions if exp.update(1.0 / 60)]

        if show_red_line and time.time() - red_line_timer > RED_LINE_DURATION:
            show_red_line = False
            red_line_target = None

        screen.fill(BLACK)
        if game_over:
            draw_game_over(screen, font)
        else:
            for obj in falling_objects:
                obj.draw(screen, font)
            draw_castle(screen, font, castle_art)
            for exp in explosions:
                exp.draw(screen)
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

async def main():
    await run_game()

if platform.system() == "Emscripten":
    asyncio.ensure_future(main())
else:
    if __name__ == "__main__":
        asyncio.run(main())