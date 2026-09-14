import pygame
import sys
import random
import time
import os

##==========================================
##1. KHỞI TẠO VÀ CẤU HÌNH CƠ BẢN
###==========================================
pygame.init()
#Thêm âm thanh nền
pygame.mixer.init()

# Load âm thanh
sound_eat = pygame.mixer.Sound("eat.wav.mp3")
sound_click = pygame.mixer.Sound("click.wav.mp3")

# Nhạc nền
pygame.mixer.music.load("nhacnen.mp3.mp3")
pygame.mixer.music.set_volume(0.5)
pygame.mixer.music.play(-1)  # lặp vô hạn

WIDTH, HEIGHT = 1000, 700
win = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Hungry Snake")

clock = pygame.time.Clock()

FONT_MAIN = pygame.font.SysFont("Verdana", 40, bold=True)
FONT_GAME = pygame.font.SysFont("Verdana", 20, bold=True)
FONT_TITLE = pygame.font.SysFont("Verdana", 56, bold=True)

BLACK, WHITE, GREEN = (0, 0, 0), (255, 255, 255), (0, 255, 0)
UI_TEXT_COLOR = (255, 215, 0)
WARN_COLOR, WARN_OUTLINE = (255, 200, 0), (255, 160, 0)
IMPACT_COLOR, SPIKE_COLOR = (255, 80, 40), (255, 70, 90)

BLOCK = 25 ## kích thước
FPS = 10 ## nhịp độ
UI_HEIGHT = 50 

VICTORY_ASIAN = 10
VICTORY_MEDIUM = 40

MAX_HEALTH = 4
DAMAGE_PER_HIT = 1
APPROACH_RADIUS = 5

METEOR_MIN, METEOR_MAX = 30, 60
METEOR_WARNING_MS, METEOR_IMPACT_MS = 1000, 250
HAZARD_RADIUS = 15

SPIKE_MIN, SPIKE_MAX = 3, 6
SPIKE_WARNING_MS, SPIKE_ACTIVE_MS, SPIKE_TICK_MS = 2000, 1500, 300

## tải hình ảnh
def load_image(name, scale=None):
    base_path = os.path.dirname(__file__)
    path = os.path.join(base_path, name) 
    try:
        if not os.path.exists(path):
            return None
        image = pygame.image.load(path).convert_alpha()
        if scale: image = pygame.transform.scale(image, scale)
        return image
    except:
        return None

HEAD_SCALE = (BLOCK + 15, BLOCK + 15)
SNAKE_HEADS = [
    load_image('head_1.png', HEAD_SCALE),
    load_image('head_2.png', HEAD_SCALE),
    load_image('head_3.png', HEAD_SCALE),
    load_image('head_4.png', HEAD_SCALE),
]

FRUIT_ASSETS = {
    "apple": {"img": load_image('apple_3d.png', (BLOCK, BLOCK)), "score": 1, "fallback": (255, 0, 0)},
    "watermelon": {"img": load_image('watermelon_3d.png', (BLOCK, BLOCK)), "score": 2, "fallback": (0, 200, 0)},
    "sugarcane": {"img": load_image('sugarcane_3d.png', (BLOCK, BLOCK)), "score": 5, "fallback": (150, 255, 150)},
    "durian": {"img": load_image('durian_3d.png', (BLOCK, BLOCK)), "score": 3, "fallback": (200, 150, 0)}
}

# KHAI BÁO BIẾN THÂN RẮN Ở ĐÂY ĐỂ TRÁNH LỖI
img_snake_body = load_image('body.png', (BLOCK, BLOCK))

## hàm tiện ích
def draw_text(text, font, color, x, y, align="left"):
    label = font.render(text, True, color)
    if align == "center": x -= label.get_width() // 2
    win.blit(label, (x, y))

def draw_grid():
    c_dark, c_light = (25, 60, 25), (35, 75, 35)
    for x in range(0, WIDTH, BLOCK):
        for y in range(UI_HEIGHT, HEIGHT, BLOCK):
            rect = (x, y, BLOCK, BLOCK)
            pygame.draw.rect(win, c_dark if (x // BLOCK + y // BLOCK) % 2 == 0 else c_light, rect)

def chebyshev(a, b):
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]))

## lõi game
class SnakeGame:
    def __init__(self, mode="Easy", head_index=0):
        self.mode = mode
        self.head_index = head_index
        self.clock = pygame.time.Clock()
        self.reset()

    def reset(self):
        self.snake = [[WIDTH // 2, HEIGHT // 2]]
        self.direction = "RIGHT"
        self.pending_dir = "RIGHT"
        self.score = 0
        self.start_time = time.time()
        self.fruits = []
        self.speed = FPS
        self.health = MAX_HEALTH if self.mode == "Asian" else 1
        self.hazards = []
        self.hazard_for_this_food = False
        self.game_over = False
        self.game_win = False
        if self.mode in ["Easy", "Asian"]: self.spawn_fruit()
        else:
            for _ in range(15): self.spawn_fruit()

    def spawn_fruit(self):
        fruit_type = "apple"
        if self.mode == "Medium": fruit_type = random.choice(["apple", "watermelon", "durian"])
        elif self.mode == "Hard": fruit_type = random.choice(["apple", "watermelon", "durian", "sugarcane"])
        cols, rows = WIDTH // BLOCK, HEIGHT // BLOCK
        while True:
            pos = [random.randint(0, cols - 1) * BLOCK, random.randint(UI_HEIGHT // BLOCK, rows - 1) * BLOCK]
            if pos not in self.snake and not any(f["pos"] == pos for f in self.fruits):
                self.fruits.append({"type": fruit_type, "pos": pos})
                break
## tạo cái bẫy gai
    def make_spike_specs(self):
        cols, rows = WIDTH // BLOCK, HEIGHT // BLOCK
        specs = []
        for _ in range(random.randint(SPIKE_MIN, SPIKE_MAX)):
            edge = random.choice(["top", "bottom", "left", "right"])
            if edge in ("top", "bottom"):
                x = random.randint(0, cols - 1) * BLOCK
                length = rows // 2
                path = [[x, y * BLOCK] for y in range(UI_HEIGHT // BLOCK, length + UI_HEIGHT // BLOCK)] if edge == "top" else [[x, y * BLOCK] for y in range(rows - 1, rows - 1 - length, -1)]
            else:
                y = random.randint(UI_HEIGHT // BLOCK, rows - 1) * BLOCK 
                length = cols // 2
                path = [[x * BLOCK, y] for x in range(0, length)] if edge == "left" else [[x * BLOCK, y] for x in range(cols - 1, cols - 1 - length, -1)]
            specs.append({"cells": path, "edge": edge})
        return specs
## để kích hoạt bẫy trong màn asian
    def update_hazards(self, now):
        if self.mode != "Asian" or self.game_over or self.game_win: return
        head = self.snake[-1]
        food = self.fruits[0]["pos"] if self.fruits else [-100, -100]
        if not self.hazard_for_this_food and chebyshev((head[0]//BLOCK, head[1]//BLOCK), (food[0]//BLOCK, food[1]//BLOCK)) <= APPROACH_RADIUS:
            cand = [[head[0] + dx * BLOCK, head[1] + dy * BLOCK] for dx in range(-HAZARD_RADIUS, HAZARD_RADIUS + 1) for dy in range(-HAZARD_RADIUS, HAZARD_RADIUS + 1) if 0 <= head[0] + dx * BLOCK < WIDTH and UI_HEIGHT <= head[1] + dy * BLOCK < HEIGHT]
            random.shuffle(cand)
            for cell in cand[:min(random.randint(METEOR_MIN, METEOR_MAX), len(cand))]:
                t = now + METEOR_WARNING_MS
                self.hazards.append({"type": "meteor", "cells": [cell], "impact": t, "end": t + METEOR_IMPACT_MS, "state": "warn", "done_damage": False})
            for spec in self.make_spike_specs():
                t = now + SPIKE_WARNING_MS
                self.hazards.append({"type": "spike", "cells": spec["cells"], "edge": spec["edge"], "impact": t, "end": t + SPIKE_ACTIVE_MS, "state": "warn", "next_tick": None})
            self.hazard_for_this_food = True
        for hz in self.hazards:
            if hz["state"] == "warn" and now >= hz["impact"]:
                hz["state"] = "impact"
                if hz["type"] == "meteor" and not hz["done_damage"] and any(c in self.snake for c in hz["cells"]):
                    self.health -= DAMAGE_PER_HIT
                    hz["done_damage"] = True
                elif hz["type"] == "spike": hz["next_tick"] = now
            elif hz["state"] == "impact" and hz["type"] == "spike" and any(c in self.snake for c in hz["cells"]) and now >= hz["next_tick"]:
                self.health -= DAMAGE_PER_HIT
                hz["next_tick"] = now + SPIKE_TICK_MS
            if now >= hz["end"]: hz["state"] = "done"
        self.hazards = [h for h in self.hazards if h["state"] != "done"]
        if self.health <= 0: self.game_over = True

    def move(self):
        self.direction = self.pending_dir
        head = self.snake[-1][:]
        if self.direction == "UP": head[1] -= BLOCK
        elif self.direction == "DOWN": head[1] += BLOCK
        elif self.direction == "LEFT": head[0] -= BLOCK
        elif self.direction == "RIGHT": head[0] += BLOCK
        if self.mode in ["Easy", "Asian"]:
            head[0] %= WIDTH
            if head[1] < UI_HEIGHT: head[1] = HEIGHT - BLOCK
            elif head[1] >= HEIGHT: head[1] = UI_HEIGHT
        self.snake.append(head)
        self.snake.pop(0)

    def check_collision(self):
        head = self.snake[-1]
        if self.mode in ["Medium", "Hard"]:
            if head[0] < 0 or head[0] >= WIDTH or head[1] < UI_HEIGHT or head[1] >= HEIGHT:
                self.game_over = True
        if self.mode in ["Easy", "Hard"] and head in self.snake[:-1]:
            self.game_over = True

    def eat(self):
        head = self.snake[-1]
        for fruit in self.fruits[:]:
            if head == fruit["pos"]:
                sound_eat.play()  # Thêm âm thanh khi rắn ăn mồi
                self.score += FRUIT_ASSETS[fruit["type"]]["score"]
                self.snake.insert(0, self.snake[0][:]) 
                if self.mode in ["Medium", "Asian"]:
                    self.snake.reverse()
                    if len(self.snake) > 1:
                        new_head, neck = self.snake[-1], self.snake[-2]
                        if new_head[0] > neck[0]: self.pending_dir = "RIGHT"
                        elif new_head[0] < neck[0]: self.pending_dir = "LEFT"
                        elif new_head[1] > neck[1]: self.pending_dir = "DOWN"
                        elif new_head[1] < neck[1]: self.pending_dir = "UP"
                if self.mode == "Hard" and fruit["type"] == "sugarcane":
                    self.speed = min(FPS * 2, 20)
                if self.mode == "Asian":
                    self.speed = min(20, FPS + self.score // 3)
                    self.hazard_for_this_food = False
                    if self.score >= VICTORY_ASIAN: self.game_win = True
                if self.mode == "Medium":
                    if self.score >= VICTORY_MEDIUM: self.game_win = True
                self.fruits.remove(fruit)
                self.spawn_fruit()
                if self.mode == "Easy" and len(self.fruits) < 15: self.spawn_fruit() 

    def draw(self):
        draw_grid()
        for fruit in self.fruits:
            asset = FRUIT_ASSETS[fruit["type"]]
            win.blit(asset["img"], (*fruit["pos"], BLOCK, BLOCK)) if asset["img"] else pygame.draw.rect(win, asset["fallback"], (*fruit["pos"], BLOCK, BLOCK))
        now = pygame.time.get_ticks()
        self.draw_hazards(now)
        for x, y in self.snake[:-1]:
            win.blit(img_snake_body, (x, y)) if img_snake_body else pygame.draw.rect(win, (200, 200, 0), (x, y, BLOCK, BLOCK)) 
        
        head_x, head_y = self.snake[-1]
        current_head_img = SNAKE_HEADS[self.head_index] 
        if current_head_img:
            angle = -90 if self.direction in ["UP", "DOWN"] else 0
            rotated_head = pygame.transform.rotate(current_head_img, angle)
            rect = rotated_head.get_rect(center=(head_x + BLOCK // 2, head_y + BLOCK // 2))
            win.blit(rotated_head, rect.topleft)
        else:
            pygame.draw.rect(win, (255, 215, 0), (head_x, head_y, BLOCK, BLOCK))

        pygame.draw.rect(win, (15, 15, 15), (0, 0, WIDTH, UI_HEIGHT))
        pygame.draw.line(win, (100, 100, 100), (0, UI_HEIGHT), (WIDTH, UI_HEIGHT), 2)
        elapsed = int(time.time() - self.start_time)
        score_text = f"SCORE: {self.score}"
        if self.mode == "Asian": score_text += f"/{VICTORY_ASIAN}"
        elif self.mode == "Medium": score_text += f"/{VICTORY_MEDIUM}"
        draw_text(score_text, FONT_GAME, WHITE, 20, 12)
        draw_text(f"MODE: {self.mode.upper()}", FONT_GAME, UI_TEXT_COLOR, WIDTH // 2, 12, "center")
        draw_text(f"TIME: {elapsed // 3600:02}:{(elapsed % 3600) // 60:02}:{elapsed % 60:02}", FONT_GAME, WHITE, WIDTH - 200, 12)

        if self.mode == "Asian":
            for i in range(MAX_HEALTH):
                pygame.draw.rect(win, (220, 40, 60) if i < self.health else (90, 90, 100), pygame.Rect(200 + i * 20, 15, 15, 15), 0 if i < self.health else 2, border_radius=3)

        if self.game_over or self.game_win:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150)) 
            win.blit(overlay, (0, 0))
            title = "YOU WIN!" if self.game_win else "GAME OVER!"
            color = GREEN if self.game_win else (255, 50, 50)
            draw_text(title, FONT_TITLE, color, WIDTH // 2, HEIGHT // 2 - 50, "center")
            draw_text("SPACE: Restart   |   ESC: Menu", FONT_GAME, WHITE, WIDTH // 2, HEIGHT // 2 + 20, "center")
        pygame.display.update()

    def draw_hazards(self, now):
        for hz in self.hazards:
            for c in hz["cells"]:
                rect = pygame.Rect(c[0], c[1], BLOCK, BLOCK)
                if hz["state"] == "warn":
                    pygame.draw.rect(win, (60, 60, 10), rect)
                    pygame.draw.rect(win, WARN_OUTLINE, rect, 2)
                    col = WARN_COLOR if (now // 200) % 2 == 0 else WARN_OUTLINE
                    if hz["type"] == "meteor":
                        pygame.draw.line(win, col, rect.topleft, rect.bottomright, 2)
                        pygame.draw.line(win, col, rect.topright, rect.bottomleft, 2)
                    else:
                        pygame.draw.rect(win, col, pygame.Rect(rect.centerx-2, rect.top+4, 4, BLOCK-12))
                        pygame.draw.rect(win, col, pygame.Rect(rect.centerx-2, rect.bottom-8, 4, 4))
                else:
                    if hz["type"] == "meteor": pygame.draw.rect(win, IMPACT_COLOR, rect)
                    else:
                        edge = hz["edge"]
                        pts = [rect.topleft, rect.topright, rect.midbottom] if edge == "top" else [rect.bottomleft, rect.bottomright, rect.midtop] if edge == "bottom" else [rect.topleft, rect.bottomleft, rect.midright] if edge == "left" else [rect.topright, rect.bottomright, rect.midleft]
                        pygame.draw.polygon(win, SPIKE_COLOR, pts)

    def run(self):
        while True:
            now = pygame.time.get_ticks()
            for event in pygame.event.get():
                if event.type == pygame.QUIT: pygame.quit(); sys.exit()
                if event.type == pygame.KEYDOWN:
                    if self.game_over or self.game_win:
                        if event.key == pygame.K_SPACE: self.reset()
                        if event.key == pygame.K_ESCAPE: return # Thoát về Menu chính
                    else:
                        if event.key in (pygame.K_UP, pygame.K_w) and self.direction != "DOWN": self.pending_dir = "UP"
                        if event.key in (pygame.K_DOWN, pygame.K_s) and self.direction != "UP": self.pending_dir = "DOWN"
                        if event.key in (pygame.K_LEFT, pygame.K_a) and self.direction != "RIGHT": self.pending_dir = "LEFT"
                        if event.key in (pygame.K_RIGHT, pygame.K_d) and self.direction != "LEFT": self.pending_dir = "RIGHT"
            if not self.game_over and not self.game_win:
                self.move()
                self.check_collision()
                self.eat()
                self.update_hazards(now)
            self.draw()
            self.clock.tick(self.speed)

# --- CÁC HÀM MENU SỬA LẠI ĐỂ TRẢ VỀ GIÁ TRỊ (FIX LỖI THOÁT GAME) ---

def choose_skin():
    selected_index = 0
    while True:
        win.fill((20, 30, 50))
        draw_text("CHOOSE YOUR SNAKE HEAD", FONT_GAME, UI_TEXT_COLOR, WIDTH // 2, 150, "center")
        for i in range(4):
            rect = pygame.Rect(WIDTH//2 - 250 + i*130, 250, 100, 100)
            color = (0, 255, 0) if i == selected_index else (100, 100, 100)
            pygame.draw.rect(win, color, rect, 3, border_radius=10)
            if SNAKE_HEADS[i]:
                preview = pygame.transform.scale(SNAKE_HEADS[i], (80, 80))
                win.blit(preview, (rect.x + 10, rect.y + 10))
            else: draw_text(f"{i+1}", FONT_GAME, WHITE, rect.centerx, rect.centery, "center")
        
        btn_play = pygame.Rect(WIDTH//2 - 100, 450, 200, 60)
        pygame.draw.rect(win, (0, 200, 0), btn_play, border_radius=10)
        draw_text("START GAME", FONT_GAME, WHITE, WIDTH // 2, 465, "center")
        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                for i in range(4):
                    if pygame.Rect(WIDTH//2 - 250 + i*130, 250, 100, 100).collidepoint(event.pos):
                        selected_index = i
                        sound_click.play()  # Phát âm thanh click khi chọn skin
                if btn_play.collidepoint(event.pos):
                    sound_click.play()  # Phát âm thanh click khi bấm START GAME
                    return selected_index # Trả về index skin được chọn
                
        clock.tick(60)

def choose_mode():
    while True:
        win.fill((10, 20, 40))
        draw_text("SELECT MODE", FONT_MAIN, UI_TEXT_COLOR, WIDTH // 2, 80, "center")
        btns = [
            (pygame.Rect(WIDTH//2-100, 200, 200, 60), (0, 200, 0), "Easy", WHITE),
            (pygame.Rect(WIDTH//2-100, 300, 200, 60), (200, 200, 0), "Medium", BLACK),
            (pygame.Rect(WIDTH//2-100, 400, 200, 60), (200, 0, 0), "Hard", WHITE),
            (pygame.Rect(WIDTH//2-100, 500, 200, 60), (150, 0, 200), "Asian", WHITE)
        ]
        for rect, bg_col, text, txt_col in btns:
            pygame.draw.rect(win, bg_col, rect, border_radius=10)
            draw_text(text, FONT_MAIN, txt_col, WIDTH // 2, rect.y + 10, "center")
        pygame.display.update()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                for idx, (rect, _, _, _) in enumerate(btns):
                    if rect.collidepoint(event.pos):
                        sound_click.play()  # Phát âm thanh click khi chọn mode
                        return ["Easy", "Medium", "Hard", "Asian"][idx] # Trả về mode được chọn
        clock.tick(60)

def main_menu():
    while True:
        win.fill((20, 20, 20))
        draw_text("HUNGRY SNAKE", FONT_MAIN, GREEN, WIDTH // 2, 100, "center")
        btn_start = pygame.Rect(WIDTH // 2 - 100, 250, 200, 60)
        btn_exit = pygame.Rect(WIDTH // 2 - 100, 350, 200, 60)
        pygame.draw.rect(win, (0, 128, 0), btn_start, border_radius=10)
        draw_text("Start", FONT_MAIN, WHITE, WIDTH // 2, 260, "center")
        pygame.draw.rect(win, (255, 0, 0), btn_exit, border_radius=10)
        draw_text("Exit", FONT_MAIN, WHITE, WIDTH // 2, 360, "center")
        draw_text("NHHQ", FONT_GAME, UI_TEXT_COLOR, 10, HEIGHT - 30)
        pygame.display.update()
            
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if btn_start.collidepoint(event.pos): 
                    sound_click.play()  # Phát âm thanh click khi bấm Start
                    mode = choose_mode() # 1. Chọn Mode xong mới đi tiếp
                    if mode:
                        skin = choose_skin() # 2. Chọn Skin xong mới đi tiếp
                        game = SnakeGame(mode=mode, head_index=skin) # 3. Khởi tạo game
                        game.run() # 4. Chạy game
                elif btn_exit.collidepoint(event.pos): 
                    sound_click.play()  # Phát âm thanh click khi bấm Exit
                    pygame.quit(); sys.exit()
        clock.tick(60)

if __name__ == "__main__":
    main_menu()