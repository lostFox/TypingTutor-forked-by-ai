import asyncio
import platform
import pygame
import sys
import random
import time
import math

# ==============================================================================
# Pygame 初始化和全局设置
# ==============================================================================
pygame.init()
pygame.mixer.init()

# 估算的字符尺寸 (用于初始化)
CHAR_WIDTH_ESTIMATE = 12
CHAR_HEIGHT_ESTIMATE = 22

# 网格尺寸
GRID_WIDTH = 80
GRID_HEIGHT = 35

# 窗口像素尺寸 (初始)
WINDOW_PIXEL_WIDTH = GRID_WIDTH * CHAR_WIDTH_ESTIMATE
WINDOW_PIXEL_HEIGHT = GRID_HEIGHT * CHAR_HEIGHT_ESTIMATE

# 创建屏幕
screen = pygame.display.set_mode((WINDOW_PIXEL_WIDTH, WINDOW_PIXEL_HEIGHT))
pygame.display.set_caption("Typing Defender")

# ==============================================================================
# 颜色定义 (使用更具活力的色板)
# ==============================================================================
BLACK = (0, 0, 0)
WHITE = (220, 220, 220)
GREEN = (0, 255, 120)
GREEN_DARK = (0, 100, 40)
RED = (255, 80, 80)
YELLOW = (255, 255, 100)
BLUE = (100, 180, 255)
GRAY = (100, 100, 100)
PURPLE = (220, 100, 255)
CYAN_HIGHLIGHT = (0, 255, 255)

# ==============================================================================
# 字体设置 (加载更具风格的字体)
# ==============================================================================
font = None
try:
    # 尝试加载一个更具科技感的字体
    font = pygame.font.SysFont("Consolas", CHAR_HEIGHT_ESTIMATE, bold=True)
except pygame.error:
    font = pygame.font.Font(None, CHAR_HEIGHT_ESTIMATE)

# 获取精确的字符尺寸并重新设置窗口大小
char_size = font.size(" ")
CHAR_WIDTH = char_size[0] if char_size[0] > 0 else CHAR_WIDTH_ESTIMATE
CHAR_HEIGHT = char_size[1] if char_size[1] > 0 else CHAR_HEIGHT_ESTIMATE
WINDOW_PIXEL_WIDTH = GRID_WIDTH * CHAR_WIDTH
WINDOW_PIXEL_HEIGHT = GRID_HEIGHT * CHAR_HEIGHT
screen = pygame.display.set_mode((WINDOW_PIXEL_WIDTH, WINDOW_PIXEL_HEIGHT))


# ==============================================================================
# 增强的视觉效果类
# ==============================================================================

class ScreenShake:
    """管理屏幕震动效果"""

    def __init__(self):
        self.magnitude = 0
        self.duration = 0
        self.start_time = 0

    def start(self, magnitude=5, duration=0.2):
        self.magnitude = magnitude
        self.duration = duration
        self.start_time = time.time()

    def get_offset(self):
        elapsed = time.time() - self.start_time
        if elapsed < self.duration:
            # 随着时间推移减弱震动
            current_magnitude = self.magnitude * (1 - (elapsed / self.duration))
            return [random.uniform(-current_magnitude, current_magnitude) for _ in range(2)]
        return [0, 0]


class DigitalRain:
    """创建“黑客帝国”风格的数字雨背景"""

    def __init__(self, width, height, char_width, char_height, font_to_use):
        self.width = width
        self.height = height
        self.char_width = char_width
        self.char_height = char_height
        self.font = font_to_use
        self.columns = int(width / char_width)
        self.drops = [-1 for _ in range(self.columns)]
        self.chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890"

    def draw(self, surface):
        for i in range(self.columns):
            if self.drops[i] * self.char_height > self.height and random.random() > 0.975:
                self.drops[i] = 0

            if self.drops[i] != -1:
                y = self.drops[i] * self.char_height
                char = random.choice(self.chars)
                # 头部使用亮绿色
                text_surface = self.font.render(char, True, GREEN)
                surface.blit(text_surface, (i * self.char_width, y))

                # 尾部使用深绿色
                if y > self.char_height * 2:
                    prev_char = random.choice(self.chars)
                    text_surface_dark = self.font.render(prev_char, True, GREEN_DARK)
                    surface.blit(text_surface_dark, (i * self.char_width, y - self.char_height))

                self.drops[i] += 1


class Explosion:
    """增强的爆炸效果，包含粒子和冲击波"""

    def __init__(self, x, y, color=YELLOW):
        self.x = x
        self.y = y
        self.start_time = time.time()
        self.duration = 0.5
        self.particles = []
        self.shockwave_radius = 0
        self.shockwave_max_radius = 60
        self.shockwave_color = color

        for _ in range(random.randint(20, 30)):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(80, 150)
            self.particles.append({
                'pos': [self.x, self.y],
                'vel': [speed * math.cos(angle), speed * math.sin(angle)],
                'radius': random.uniform(2, 5),
                'color': random.choice([color, RED, WHITE])
            })

    def update(self, dt):
        for p in self.particles:
            p['pos'][0] += p['vel'][0] * dt
            p['pos'][1] += p['vel'][1] * dt
            p['radius'] -= 2 * dt  # 粒子快速消失
        self.particles = [p for p in self.particles if p['radius'] > 0]

        # 更新冲击波
        self.shockwave_radius += 200 * dt
        return time.time() - self.start_time < self.duration

    def draw(self, surface):
        # 绘制冲击波
        if self.shockwave_radius < self.shockwave_max_radius:
            alpha = max(0, 255 * (1 - self.shockwave_radius / self.shockwave_max_radius))
            pygame.draw.circle(surface, self.shockwave_color + (alpha,), (self.x, self.y), int(self.shockwave_radius),
                               2)

        # 绘制粒子
        for p in self.particles:
            pygame.draw.circle(surface, p['color'], [int(c) for c in p['pos']], int(p['radius']))


class Laser:
    """从城堡发射的激光效果"""

    def __init__(self, start_pos, end_pos):
        self.start_pos = start_pos
        self.end_pos = end_pos
        self.start_time = time.time()
        self.duration = 0.2

    def is_active(self):
        return time.time() - self.start_time < self.duration

    def draw(self, surface):
        elapsed = time.time() - self.start_time
        alpha = max(0, 255 * (1 - elapsed / self.duration))
        color = (*CYAN_HIGHLIGHT, alpha)

        # 绘制多层线条来模拟辉光
        pygame.draw.line(surface, color, self.start_pos, self.end_pos, 5)
        pygame.draw.line(surface, (*WHITE, alpha), self.start_pos, self.end_pos, 2)


# ==============================================================================
# 辅助函数
# ==============================================================================
def draw_text_glow(surface, text, pos, font_to_use, color=WHITE, glow_color=GREEN):
    """绘制带有辉光效果的文本"""
    # 辉光
    text_surf_glow = font_to_use.render(text, True, glow_color)
    text_surf_glow.set_alpha(100)
    surface.blit(text_surf_glow, (pos[0] - 1, pos[1] - 1))
    surface.blit(text_surf_glow, (pos[0] + 1, pos[1] - 1))
    surface.blit(text_surf_glow, (pos[0] - 1, pos[1] + 1))
    surface.blit(text_surf_glow, (pos[0] + 1, pos[1] + 1))
    # 主文本
    text_surf = font_to_use.render(text, True, color)
    surface.blit(text_surf, pos)


# ==============================================================================
# 游戏核心类
# ==============================================================================
class FallingObject:
    def __init__(self, text, speed_grid_per_sec=0.5, is_bonus=False):
        self.text = text.upper()
        self.is_bonus = is_bonus
        self.speed_pixel_per_sec = speed_grid_per_sec * CHAR_HEIGHT
        self.pixel_y_float = 0.0
        self.pixel_x = random.randint(0, max(0, GRID_WIDTH - len(text))) * CHAR_WIDTH
        self.active = True
        self.progress = 0

    def draw(self, surface, font_to_use):
        if not self.active: return

        glow = YELLOW if self.is_bonus else GREEN
        draw_text_glow(surface, self.text, (self.pixel_x, self.pixel_y_float), font_to_use, WHITE, glow)

        # 绘制已输入部分
        if self.progress > 0:
            inputted_text = self.text[:self.progress]
            input_surface = font_to_use.render(inputted_text, True, CYAN_HIGHLIGHT)
            surface.blit(input_surface, (self.pixel_x, int(self.pixel_y_float)))

    def move(self, dt):
        if self.active:
            self.pixel_y_float += self.speed_pixel_per_sec * dt

    def handle_input(self, typed_char):
        if not self.active or self.progress >= len(self.text):
            return False
        if typed_char.upper() == self.text[self.progress]:
            self.progress += 1
            if self.progress == len(self.text):
                self.active = False
                return True
        else:
            self.progress = 0
        return False

    def get_bottom_pixel_y(self):
        return self.pixel_y_float + CHAR_HEIGHT

    def get_center_position(self):
        center_x = self.pixel_x + (len(self.text) * CHAR_WIDTH) / 2
        center_y = self.pixel_y_float + CHAR_HEIGHT / 2
        return center_x, center_y


# ==============================================================================
# 难度和城堡设置
# ==============================================================================
difficulty_levels = [
    {'level': 1, 'items': ['F', 'G', 'H', 'J'], 'speed_grid_per_sec': 0.3, 'generate_interval': 2.0,
     'score_threshold': 50},
    {'level': 2, 'items': ['R', 'T', 'Y', 'U', 'B', 'N', 'M'], 'speed_grid_per_sec': 0.35, 'generate_interval': 1.8,
     'score_threshold': 150},
    {'level': 3, 'items': ['D', 'K', 'I', 'E', 'C', ','], 'speed_grid_per_sec': 0.4, 'generate_interval': 1.6,
     'score_threshold': 300},
    {'level': 4, 'items': ['S', 'L', 'W', 'O', '.'], 'speed_grid_per_sec': 0.45, 'generate_interval': 1.4,
     'score_threshold': 500},
    {'level': 5, 'items': ['A', 'Z', 'X', ';', 'P'], 'speed_grid_per_sec': 0.5, 'generate_interval': 1.5,
     'score_threshold': 800},
    {'level': 6, 'items': ['THE', 'AND', 'FOR', 'ARE', 'BUT'], 'speed_grid_per_sec': 0.55, 'generate_interval': 2.2,
     'score_threshold': 1200},
    {'level': 7, 'items': ['THIS', 'THAT', 'WITH', 'FROM', 'HAVE'], 'speed_grid_per_sec': 0.6, 'generate_interval': 2.0,
     'score_threshold': 1800},
    {'level': 8, 'items': ['PYTHON', 'PYGAME', 'CODING', 'TYPING', 'CASTLE'], 'speed_grid_per_sec': 0.65,
     'generate_interval': 2.5, 'score_threshold': 2500},
    {'level': 9, 'items': ['PROGRAM', 'DEVELOP', 'KEYBOARD', 'ACCURACY', 'CHALLENGE'], 'speed_grid_per_sec': 0.7,
     'generate_interval': 2.3, 'score_threshold': 3200},
    {'level': 10, 'items': ['INTELLIGENCE', 'COMMUNICATION', 'ENVIRONMENT', 'FRAMEWORK'], 'speed_grid_per_sec': 0.75,
     'generate_interval': 3.0, 'score_threshold': 4000}
]

# 重新设计的城堡
CORE_CHAR = '$'
initial_castle_art = [
    "  /MM\\MM/MM\\MM/MM\\MM/MM\\MM/MM\\MM/MM\\MM/MM\\MM/MM\\MM/MM\\MM/MM\\MM/MM\\MM/MM\\  ",
    "//===========================\\\\_" + CORE_CHAR + "_//===========================\\\\",
    "##======================================================================##",
    "##########################################################################"
]
castle_art = []
core_position_grid = None  # (行, 列) in castle_art


def find_core_position():
    """在城堡艺术中找到核心的初始位置"""
    global core_position_grid
    for r, row_str in enumerate(initial_castle_art):
        if CORE_CHAR in row_str:
            c = row_str.find(CORE_CHAR)
            core_position_grid = (r, c)
            return


find_core_position()


# ==============================================================================
# 游戏主函数
# ==============================================================================
async def run_game():
    global castle_art

    # 游戏状态
    game_state = {
        'falling_objects': [], 'current_target': None, 'score': 0,
        'current_level': 1, 'game_over': False, 'last_generate_time': time.time(),
        'explosions': [], 'lasers': [], 'level_up_timer': 0
    }

    castle_art = list(initial_castle_art)

    # 特效对象
    screen_shake = ScreenShake()
    digital_rain = DigitalRain(WINDOW_PIXEL_WIDTH, WINDOW_PIXEL_HEIGHT, CHAR_WIDTH, CHAR_HEIGHT, font)

    clock = pygame.time.Clock()
    running = True

    # 游戏主循环
    while running:
        dt = min(0.1, clock.tick(60) / 1000.0)

        # 事件处理
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if game_state['game_over']:
                    running = False;
                    continue

                typed_char = event.unicode
                if typed_char and (typed_char.isalnum() or typed_char in ';.,'):
                    if game_state['current_target']:
                        if game_state['current_target'].handle_input(typed_char):
                            # 单词完成
                            points = len(game_state['current_target'].text) * 10
                            game_state['score'] += points * 2 if game_state['current_target'].is_bonus else points

                            # 创建激光
                            castle_top_grid_y = GRID_HEIGHT - len(castle_art)
                            core_screen_pos = ((core_position_grid[1] + 0.5) * CHAR_WIDTH,
                                               (castle_top_grid_y + core_position_grid[0] + 0.5) * CHAR_HEIGHT)
                            game_state['lasers'].append(
                                Laser(core_screen_pos, game_state['current_target'].get_center_position()))
                            game_state['current_target'] = None

                        elif game_state['current_target'].progress == 0:
                            game_state['current_target'] = None  # 输入错误，取消目标

                    if not game_state['current_target']:
                        # 寻找新目标
                        best_match = None
                        for obj in game_state['falling_objects']:
                            if obj.active and obj.text.startswith(typed_char.upper()):
                                if not best_match or obj.pixel_y_float > best_match.pixel_y_float:
                                    best_match = obj
                        if best_match:
                            game_state['current_target'] = best_match
                            if best_match.handle_input(typed_char):  # 单字母单词
                                points = len(best_match.text) * 10
                                game_state['score'] += points
                                castle_top_grid_y = GRID_HEIGHT - len(castle_art)
                                core_screen_pos = ((core_position_grid[1] + 0.5) * CHAR_WIDTH,
                                                   (castle_top_grid_y + core_position_grid[0] + 0.5) * CHAR_HEIGHT)
                                game_state['lasers'].append(Laser(core_screen_pos, best_match.get_center_position()))
                                game_state['current_target'] = None

        # 游戏逻辑更新
        if not game_state['game_over']:
            # 升级检查
            old_level = game_state['current_level']
            level_settings = difficulty_levels[min(len(difficulty_levels) - 1, game_state['current_level'] - 1)]
            if game_state['score'] >= level_settings['score_threshold']:
                game_state['current_level'] += 1
            if game_state['current_level'] > old_level:
                game_state['level_up_timer'] = time.time()  # 触发升级提示

            # 生成新对象
            if time.time() - game_state['last_generate_time'] > level_settings['generate_interval']:
                is_bonus = random.random() < 0.1
                item_text = random.choice(level_settings['items'])
                speed = level_settings['speed_grid_per_sec'] * (2.0 if is_bonus else 1.0)
                game_state['falling_objects'].append(FallingObject(item_text, speed, is_bonus))
                game_state['last_generate_time'] = time.time()

            # 移动和碰撞检测
            castle_top_y_px = (GRID_HEIGHT - len(castle_art)) * CHAR_HEIGHT if castle_art else WINDOW_PIXEL_HEIGHT
            for obj in list(game_state['falling_objects']):
                if obj.active:
                    obj.move(dt)
                    if obj.get_bottom_pixel_y() >= castle_top_y_px:
                        obj.active = False
                        if obj == game_state['current_target']:
                            game_state['current_target'] = None

                        # 城堡伤害
                        screen_shake.start(magnitude=8, duration=0.3)
                        pos = obj.get_center_position()
                        game_state['explosions'].append(Explosion(pos[0], castle_top_y_px, RED))

                        # 简化伤害逻辑：每次命中移除一层
                        if castle_art:
                            # 检查核心是否在被摧毁的层
                            if len(castle_art) - 1 == core_position_grid[0]:
                                game_state['game_over'] = True
                            castle_art.pop()
                        if not castle_art:
                            game_state['game_over'] = True

            # 清理非活动对象
            game_state['falling_objects'] = [o for o in game_state['falling_objects'] if o.active]
            game_state['explosions'] = [e for e in game_state['explosions'] if e.update(dt)]
            game_state['lasers'] = [l for l in game_state['lasers'] if l.is_active()]

        # 渲染
        screen.fill(BLACK)

        # 绘制背景和特效
        digital_rain.draw(screen)
        offset = screen_shake.get_offset()
        render_surface = screen.copy()

        # 绘制城堡
        if not game_state['game_over']:
            castle_top_grid_y = GRID_HEIGHT - len(castle_art)
            for i, line in enumerate(castle_art):
                y = (castle_top_grid_y + i) * CHAR_HEIGHT
                for j, char in enumerate(line):
                    if char != ' ':
                        color = GRAY
                        if char in '#=': color = BLUE
                        if char == CORE_CHAR:
                            # 让核心闪烁
                            pulse = (math.sin(time.time() * 5) + 1) / 2
                            color = (
                                int(PURPLE[0] * (0.5 + pulse * 0.5)),
                                int(PURPLE[1] * (0.5 + pulse * 0.5)),
                                int(PURPLE[2] * (0.5 + pulse * 0.5))
                            )
                        char_surf = font.render(char, True, color)
                        render_surface.blit(char_surf, (j * CHAR_WIDTH, y))

        # 绘制游戏对象
        for obj in game_state['falling_objects']:
            obj.draw(render_surface, font)
        for las in game_state['lasers']:
            las.draw(render_surface)
        for exp in game_state['explosions']:
            exp.draw(render_surface)

        # 绘制UI
        score_text = f"SCORE: {game_state['score']}  LEVEL: {game_state['current_level']}"
        draw_text_glow(render_surface, score_text, (10, 10), font, WHITE, BLUE)
        if game_state['current_target']:
            pygame.draw.rect(render_surface, CYAN_HIGHLIGHT, (game_state['current_target'].pixel_x - 2,
                                                              int(game_state['current_target'].pixel_y_float) - 2,
                                                              len(game_state['current_target'].text) * CHAR_WIDTH + 4,
                                                              CHAR_HEIGHT + 4), 1)

        # 绘制升级提示
        if game_state['level_up_timer'] and time.time() - game_state['level_up_timer'] < 1.5:
            alpha = max(0, 255 * (1 - (time.time() - game_state['level_up_timer']) / 1.5))
            level_up_font = pygame.font.SysFont("Consolas", int(CHAR_HEIGHT * 2.5), bold=True)
            text_surf = level_up_font.render("LEVEL UP", True, (*YELLOW, alpha))
            pos = (WINDOW_PIXEL_WIDTH / 2 - text_surf.get_width() / 2,
                   WINDOW_PIXEL_HEIGHT / 2 - text_surf.get_height() / 2)
            render_surface.blit(text_surf, pos)
        else:
            game_state['level_up_timer'] = 0

        # 应用屏幕震动
        screen.blit(render_surface, offset)

        # 游戏结束画面
        if game_state['game_over']:
            overlay = pygame.Surface((WINDOW_PIXEL_WIDTH, WINDOW_PIXEL_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            screen.blit(overlay, (0, 0))

            large_font = pygame.font.SysFont("Consolas", CHAR_HEIGHT * 3, bold=True)
            draw_text_glow(screen, "SYSTEM FAILURE", (WINDOW_PIXEL_WIDTH / 2 - large_font.size("SYSTEM FAILURE")[0] / 2,
                                                      WINDOW_PIXEL_HEIGHT * 0.3), large_font, RED, RED)
            draw_text_glow(screen, f"FINAL SCORE: {game_state['score']}",
                           (WINDOW_PIXEL_WIDTH / 2 - font.size(f"FINAL SCORE: {game_state['score']}")[0] / 2,
                            WINDOW_PIXEL_HEIGHT * 0.5), font, WHITE, BLUE)
            draw_text_glow(screen, "Press any key to disconnect...",
                           (WINDOW_PIXEL_WIDTH / 2 - font.size("Press any key to disconnect...")[0] / 2,
                            WINDOW_PIXEL_HEIGHT * 0.7), font, GRAY, BLACK)

        pygame.display.flip()
        await asyncio.sleep(0)

    # 退出Pygame
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    if platform.system() == "Emscripten":
        asyncio.run(run_game())
    else:
        # 在非Web环境中，直接运行
        asyncio.run(run_game())
