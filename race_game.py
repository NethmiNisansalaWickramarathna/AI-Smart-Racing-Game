import pygame
import random
import os

# Game එක පටන් ගැනීම
pygame.init()
pygame.mixer.init()

SCREEN_WIDTH = 400
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("AI Smart Racing - Settings & Menu")
clock = pygame.time.Clock()

high_score = 0
difficulty = "MEDIUM" # Default අගය

# --- Sounds ---
try:
    pygame.mixer.music.load('background.mp3')
    pygame.mixer.music.set_volume(0.3)
    crash_sound = pygame.mixer.Sound('crash.wav')
    score_sound = pygame.mixer.Sound('score.wav')
except:
    crash_sound = score_sound = None

def load_and_precise_crop(name, width, left, right, top, bottom):
    try:
        img = pygame.image.load(name).convert_alpha()
        w, h = img.get_size()
        inner_rect = pygame.Rect(int(w * left), int(h * top), int(w * (1 - left - right)), int(h * (1 - top - bottom)))
        cleaned_img = img.subsurface(inner_rect)
        cw, ch = cleaned_img.get_size()
        aspect_ratio = ch / cw
        return pygame.transform.scale(cleaned_img, (width, int(width * aspect_ratio)))
    except:
        surf = pygame.Surface((width, width + 20)); surf.fill((255, 0, 0))
        return surf

# Assets load කිරීම
try:
    player_img = load_and_precise_crop('player_car.png', 45, 0.18, 0.18, 0.16, 0.15)
    enemy_img = load_and_precise_crop('enemy_car.png', 45, 0.28, 0.28, 0.31, 0.31)
    road_img = pygame.image.load('road_background.png').convert_alpha()
    road_img = pygame.transform.scale(road_img, (SCREEN_WIDTH, SCREEN_HEIGHT))
except:
    pygame.quit(); exit()

# --- Drawing Functions ---
def draw_heart(surface, x, y, size):
    color = (255, 0, 0)
    pygame.draw.circle(surface, color, (x - size//4, y), size//4)
    pygame.draw.circle(surface, color, (x + size//4, y), size//4)
    points = [(x - size//2, y + size//8), (x + size//2, y + size//8), (x, y + size)]
    pygame.draw.polygon(surface, color, points)

def draw_nitro(surface, x, y, size):
    pygame.draw.rect(surface, (0, 191, 255), (x-size//2, y-size//2, size, size), border_radius=5)
    pygame.draw.polygon(surface, (255, 255, 255), [(x, y-size//3), (x-size//4, y+size//4), (x+size//4, y+size//4)])

def draw_button(text, x, y, w, h, base_color, hover_color, active=False):
    mouse = pygame.mouse.get_pos(); click = pygame.mouse.get_pressed()
    color = hover_color if (x + w > mouse[0] > x and y + h > mouse[1] > y) or active else base_color
    pygame.draw.rect(screen, color, (x, y, w, h), border_radius=15)
    font = pygame.font.Font(None, 35)
    txt = font.render(text, True, (255, 255, 255))
    screen.blit(txt, txt.get_rect(center=(x + w/2, y + h/2)))
    return x + w > mouse[0] > x and y + h > mouse[1] > y and click[0] == 1

# --- Screens ---
def show_settings():
    global difficulty
    while True:
        screen.blit(road_img, (0, 0))
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200)); screen.blit(overlay, (0, 0))
        
        font = pygame.font.Font(None, 50)
        screen.blit(font.render("SETTINGS", True, (255, 255, 0)), (110, 80))
        
        # Difficulty Buttons
        if draw_button("EASY", 100, 180, 200, 50, (0, 100, 0), (0, 200, 0), difficulty == "EASY"):
            difficulty = "EASY"; pygame.time.delay(150)
        if draw_button("MEDIUM", 100, 250, 200, 50, (100, 100, 0), (200, 200, 0), difficulty == "MEDIUM"):
            difficulty = "MEDIUM"; pygame.time.delay(150)
        if draw_button("HARD", 100, 320, 200, 50, (100, 0, 0), (200, 0, 0), difficulty == "HARD"):
            difficulty = "HARD"; pygame.time.delay(150)
        
        if draw_button("BACK", 100, 450, 200, 50, (50, 50, 50), (100, 100, 100)):
            return

        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); exit()
        pygame.display.flip(); clock.tick(15)

def show_start_screen():
    if not pygame.mixer.music.get_busy():
        try: pygame.mixer.music.play(-1)
        except: pass
    while True:
        screen.blit(road_img, (0, 0))
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160)); screen.blit(overlay, (0, 0))
        
        font = pygame.font.Font(None, 60); title = font.render("SMART AI RACER", True, (0, 255, 0))
        screen.blit(title, (SCREEN_WIDTH // 2 - 165, 120))
        
        if draw_button("START", 100, 250, 200, 60, (0, 120, 0), (0, 200, 0)): return "START"
        if draw_button("SETTINGS", 100, 330, 200, 60, (0, 0, 120), (0, 0, 200)): show_settings()
        if draw_button("EXIT", 100, 410, 200, 60, (120, 0, 0), (200, 0, 0)): return "QUIT"
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT: return "QUIT"
        pygame.display.flip(); clock.tick(15)

def main_game():
    global difficulty
    p_w, p_h = player_img.get_size()
    player_x, player_y = SCREEN_WIDTH // 2 - (p_w // 2), 500
    
    # --- Difficulty මත පදනම් වූ අගයන් ---
    if difficulty == "EASY":
        base_speed, lives, ai_track = 2.5, 5, 0.4
    elif difficulty == "HARD":
        base_speed, lives, ai_track = 4.5, 2, 0.8
    else: # MEDIUM
        base_speed, lives, ai_track = 3.5, 3, 0.6

    enemies = [{"x": random.randint(60, 300), "y": -200}]
    score, current_level, nitro_timer, inv_frames = 0, 1, 0, 0
    life_item_x, life_item_y, life_item_active = 0, -500, False

    while True:
        screen.blit(road_img, (0, 0))
        for event in pygame.event.get():
            if event.type == pygame.QUIT: return "QUIT"

        keys = pygame.key.get_pressed()
        p_speed = 12 if nitro_timer > 0 else 7
        if keys[pygame.K_LEFT] and player_x > 40: player_x -= p_speed
        if keys[pygame.K_RIGHT] and player_x < SCREEN_WIDTH - 85: player_x += p_speed

        e_speed = base_speed * 0.5 if nitro_timer > 0 else base_speed

        for enemy in enemies:
            enemy["y"] += e_speed
            if enemy["y"] < player_y:
                if enemy["x"] < player_x: enemy["x"] += ai_track
                elif enemy["x"] > player_x: enemy["x"] -= ai_track
            
            if enemy["y"] > SCREEN_HEIGHT:
                enemy["y"], enemy["x"], score = -150, random.randint(60, 300), score + 1
                if score_sound: score_sound.play()
                if score % 10 == 0 and current_level < 5:
                    current_level, base_speed, ai_track = current_level + 1, base_speed + 0.8, ai_track + 0.1
                    if current_level in [3, 5]: enemies.append({"x": random.randint(60, 300), "y": -200})

            # Collision
            p_rect = player_img.get_rect(topleft=(player_x, player_y))
            e_rect = enemy_img.get_rect(topleft=(enemy["x"], enemy["y"]))
            if inv_frames == 0 and nitro_timer == 0:
                if p_rect.inflate(-12, -12).colliderect(e_rect.inflate(-12, -12)):
                    lives -= 1
                    if lives > 0: inv_frames, enemy["y"] = 60, -200
                    else: return show_game_over(score)
            screen.blit(enemy_img, (enemy["x"], enemy["y"]))

        # Player Draw
        if inv_frames > 0:
            inv_frames -= 1
            if inv_frames % 10 < 5: screen.blit(player_img, (player_x, player_y))
        else: screen.blit(player_img, (player_x, player_y))

        # UI
        font = pygame.font.Font(None, 32)
        screen.blit(font.render(f"Score: {score}  Lives: {lives}  Lvl: {current_level}", True, (255, 255, 255)), (15, 20))
        if nitro_timer > 0: nitro_timer -= 1
        
        pygame.display.flip(); clock.tick(60)

# --- Game Over Logic කලින් විදිහටමයි ---
def show_game_over(score):
    global high_score
    if score > high_score: high_score = score
    pygame.mixer.music.stop()
    if crash_sound: crash_sound.play()
    while True:
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 190)); screen.blit(overlay, (0, 0))
        font = pygame.font.Font(None, 70); screen.blit(font.render("GAME OVER!", True, (255, 0, 0)), (50, 150))
        if draw_button("RESTART", 100, 350, 200, 55, (0, 150, 0), (0, 255, 0)): 
            pygame.mixer.music.play(-1); return "RESTART"
        if draw_button("QUIT", 100, 430, 200, 55, (150, 0, 0), (255, 0, 0)): return "QUIT"
        for event in pygame.event.get():
            if event.type == pygame.QUIT: return "QUIT"
        pygame.display.flip(); clock.tick(15)

res = show_start_screen()
if res != "QUIT":
    while True:
        if main_game() == "QUIT": break
pygame.quit()