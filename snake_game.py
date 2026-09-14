import pygame
import sys
import random
import time
import os

pygame.init()

# --- CẤU HÌNH CỬA SỔ ---
WIDTH, HEIGHT = 1000, 700
win = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Snake Vietnam - NHHQ Edition")

clock = pygame.time.Clock()

# --- FONT CHỮ ---
FONT_MAIN = pygame.font.SysFont("Verdana", 40, bold=True)
FONT_SUB = pygame.font.SysFont("Verdana", 25, bold=True)
FONT_GAME = pygame.font.SysFont("Verdana", 20, bold=True)
FONT_TITLE = pygame.font.SysFont("Verdana", 56, bold=True)

# --- MÀU SẮC ---
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
UI_TEXT_COLOR = (255, 215, 0)
IMPACT_COLOR = (255, 80, 40)
SPIKE_COLOR = (255, 70, 90)

BLOCK = 25
FPS = 10

# --- 4 LỰA CHỌN MÀU NEON CHO THÂN RẮN ---
SNAKE_COLORS = [
    {"name": "Xanh Lá Neon", "body": (50, 255, 50), "tail": (0, 100, 0)},
    {"name": "Hồng Lửa", "body": (255, 20, 147), "tail": (100, 0, 50)},
    {"name": "Tím Biển", "body": (191, 0, 255), "tail": (60, 0, 80)},
    {"name": "Vàng Neon", "body": (255, 255, 0), "tail": (150, 150, 0)}
]

class SnakeGame:
    def __init__(self, mode="Easy", color_scheme=None):
        self.mode = mode
        self.color_body = color_scheme["body"] if color_scheme else (0, 255, 0)
        self.color_tail = color_scheme["tail"] if color_scheme else (0, 100, 0)
        
        # --- ĐẦU RẮN SIÊU TO (60x60) ---
        try:
            temp_head = pygame.image.load("head.png").convert_alpha()
            temp_head.set_colorkey((255, 255, 255)) # Tách nền trắng
            self.head_img = pygame.transform.scale(temp_head, (60, 60))
        except:
            self.head_img = None
            
        self.reset()

    def reset(self):
        self.snake = [[WIDTH // 2, HEIGHT // 2], [WIDTH // 2 - BLOCK, HEIGHT // 2]]
        self.direction = self.pending_dir = "RIGHT"
        self.score = 0
        self.start_time = time.time()
        self.fruits = []
        self.speed = FPS
        self.game_over = False
        self.health = 4 if self.mode == "Asian" else 1
        self.hazards = []
        self.hazard_timer = 0
        
        num = 12 if self.mode in ["Medium", "Hard"] else 1
        for _ in range(num): self.spawn_fruit()

    def spawn_fruit(self):
        while True:
            pos = [random.randint(0, (WIDTH//BLOCK)-1)*BLOCK, random.randint(2, (HEIGHT//BLOCK)-1)*BLOCK]
            if pos not in self.snake:
                self.fruits.append({"pos": pos})
                break

    def update_asian_hazards(self):
        if self.mode != "Asian": return
        now = pygame.time.get_ticks()
        if now - self.hazard_timer > 2500:
            self.hazard_timer = now
            head = self.snake[-1]
            for _ in range(2):
                cell = [head[0] + random.randint(-4, 4)*BLOCK, head[1] + random.randint(-4, 4)*BLOCK]
                self.hazards.append({"pos": cell, "end": now + 2000, "type": random.choice(["meteor", "spike"])})

    def move(self):
        self.direction = self.pending_dir
        head = self.snake[-1][:]
        if self.direction == "UP": head[1] -= BLOCK
        elif self.direction == "DOWN": head[1] += BLOCK
        elif self.direction == "LEFT": head[0] -= BLOCK
        elif self.direction == "RIGHT": head[0] += BLOCK

        if self.mode in ["Easy", "Asian"]:
            head[0] %= WIDTH
            if head[1] < 50: head[1] = HEIGHT - BLOCK
            elif head[1] >= HEIGHT: head[1] = 50
        
        self.snake.append(head)
        self.snake.pop(0)

    def draw(self):
        # Vẽ nền Grid Sân Cỏ tối
        win.fill((15, 30, 15))
        for x in range(0, WIDTH, BLOCK):
            for y in range(50, HEIGHT, BLOCK):
                if (x//BLOCK + y//BLOCK) % 2 == 0:
                    pygame.draw.rect(win, (20, 45, 20), (x, y, BLOCK, BLOCK))

        for f in self.fruits:
            pygame.draw.circle(win, (255, 0, 0), (f["pos"][0]+BLOCK//2, f["pos"][1]+BLOCK//2), BLOCK//2)
        
        for h in self.hazards:
            c = IMPACT_COLOR if h["type"] == "meteor" else SPIKE_COLOR
            pygame.draw.rect(win, c, (*h["pos"], BLOCK, BLOCK), border_radius=10)

        # --- VẼ RẮN HIỆU ỨNG NEON ---
        length = len(self.snake)
        for i, (x, y) in enumerate(self.snake):
            if i == length - 1: # ĐẦU RẮN SIÊU TO
                if self.head_img:
                    rot = pygame.transform.rotate(self.head_img, {"UP":0,"DOWN":180,"LEFT":90,"RIGHT":270}[self.direction])
                    offset = (rot.get_width() - BLOCK) // 2
                    win.blit(rot, (x - offset, y - offset))
                else: 
                    pygame.draw.rect(win, WHITE, (x, y, BLOCK, BLOCK))
            else: # THÂN RẮN
                fade = i / length
                c = [int(self.color_tail[j] + (self.color_body[j]-self.color_tail[j])*fade) for j in range(3)]
                # Đốt thân bo góc
                pygame.draw.rect(win, c, (x, y, BLOCK, BLOCK), border_radius=8)
                # Viền Neon trắng mỏng
                pygame.draw.rect(win, WHITE, (x, y, BLOCK, BLOCK), 1, border_radius=8)

        # UI Bar
        pygame.draw.rect(win, (10, 10, 10), (0, 0, WIDTH, 50))
        draw_text(f"SCORE: {self.score} | MODE: {self.mode}", FONT_GAME, UI_TEXT_COLOR, 20, 12)
        if self.mode == "Asian": draw_text(f"HP: {'♥'*self.health}", FONT_GAME, (255, 50, 50), WIDTH//2, 12, "center")

        if self.game_over:
            draw_text("GAME OVER!", FONT_TITLE, WHITE, WIDTH//2, HEIGHT//2, "center")
            draw_text("Press SPACE to Menu", FONT_SUB, WHITE, WIDTH//2, HEIGHT//2 + 70, "center")
        pygame.display.update()

    def run(self):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT: pygame.quit(); sys.exit()
                if event.type == pygame.KEYDOWN:
                    if self.game_over and event.key == pygame.K_SPACE: return
                    if event.key in [pygame.K_UP, pygame.K_w] and self.direction != "DOWN": self.pending_dir = "UP"
                    if event.key in [pygame.K_DOWN, pygame.K_s] and self.direction != "UP": self.pending_dir = "DOWN"
                    if event.key in [pygame.K_LEFT, pygame.K_a] and self.direction != "RIGHT": self.pending_dir = "LEFT"
                    if event.key in [pygame.K_RIGHT, pygame.K_d] and self.direction != "LEFT": self.pending_dir = "RIGHT"

            if not self.game_over:
                self.move()
                head = self.snake[-1]
                if head in self.snake[:-1]: self.game_over = True
                if self.mode in ["Medium", "Hard"] and (head[0]<0 or head[0]>=WIDTH or head[1]<50 or head[1]>=HEIGHT):
                    self.game_over = True
                
                for f in self.fruits[:]:
                    if head == f["pos"]:
                        self.score += 1
                        self.snake.insert(0, self.snake[0][:])
                        self.fruits.remove(f)
                        self.spawn_fruit()
                        if self.mode == "Medium": self.snake.reverse()
                self.update_asian_hazards()
            self.draw()
            clock.tick(self.speed + (self.score//5))

def draw_text(text, font, color, x, y, align="left"):
    label = font.render(text, True, color)
    if align == "center": x -= label.get_width() // 2
    win.blit(label, (x, y))

# --- HỆ THỐNG MENU ---
def main_menu():
    while True:
        win.fill((20, 20, 20))
        draw_text("NHHQ - HUNGRY SNAKE", FONT_TITLE, GREEN, WIDTH//2, 150, "center")
        btn = pygame.Rect(WIDTH//2 - 100, 350, 200, 60)
        pygame.draw.rect(win, (0, 128, 0), btn, border_radius=10)
        draw_text("START", FONT_MAIN, WHITE, WIDTH//2, 360, "center")
        pygame.display.update()
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if btn.collidepoint(event.pos):
                    c = choose_color()
                    if c: choose_mode(c)

def choose_color():
    while True:
        win.fill((10,10,10)); draw_text("CHỌN MÀU RẮN", FONT_MAIN, UI_TEXT_COLOR, WIDTH//2, 80, "center")
        btns = []
        for i, c in enumerate(SNAKE_COLORS):
            r = pygame.Rect(WIDTH//2-150, 200+i*80, 300, 60)
            pygame.draw.rect(win, c["body"], r, border_radius=10)
            draw_text(c["name"], FONT_SUB, WHITE if i!=3 else BLACK, WIDTH//2, 215+i*80, "center")
            btns.append((r, c))
        pygame.display.update()
        for event in pygame.event.get():
            if event.type == pygame.MOUSEBUTTONDOWN:
                for r, c in btns:
                    if r.collidepoint(event.pos): return c
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()

def choose_mode(color):
    modes = [("1. Easy", (0,200,0), "Easy"), ("2. Medium", (200,200,0), "Medium"), 
             ("3. Hard", (200,100,0), "Hard"), ("4. Asian (Pro)", (200,0,0), "Asian")]
    while True:
        win.fill((10,20,40)); draw_text("CHỌN ĐỘ KHÓ", FONT_MAIN, WHITE, WIDTH//2, 80, "center")
        btns = []
        for i, (txt, col, m) in enumerate(modes):
            r = pygame.Rect(WIDTH//2-150, 200+i*90, 300, 70)
            pygame.draw.rect(win, col, r, border_radius=10)
            draw_text(txt, FONT_SUB, WHITE if i!=1 else BLACK, WIDTH//2, 220+i*90, "center")
            btns.append((r, m))
        pygame.display.update()
        for event in pygame.event.get():
            if event.type == pygame.MOUSEBUTTONDOWN:
                for r, m in btns:
                    if r.collidepoint(event.pos): SnakeGame(m, color).run(); return
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()

if __name__ == "__main__":
    main_menu()