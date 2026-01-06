import pygame
import sys
import random
import math

pygame.init()


WIDTH, HEIGHT = 1000, 700
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Street Racer by Zach")

clock = pygame.time.Clock()
FPS = 60

game_state = "menu"
selected_car_index = 0
menu_animation = 0



def draw_car(color, width=60, height=100):
    surf = pygame.Surface((width, height), pygame.SRCALPHA)
    pygame.draw.rect(surf, color, (10, 20, width-20, height-40), border_radius=8)

    cabin_color = tuple(max(0, c - 40) for c in color)
    pygame.draw.rect(surf, cabin_color, (15, 30, width-30, 35), border_radius=6)
    pygame.draw.rect(surf, (180,220,255), (18,35,width-36,12))
    pygame.draw.rect(surf, (180,220,255), (18,50,width-36,10))

    wheel_color = (30,30,30)
    pygame.draw.ellipse(surf, wheel_color, (5,15,15,20))
    pygame.draw.ellipse(surf, wheel_color, (width-20,15,15,20))
    pygame.draw.ellipse(surf, wheel_color, (5,height-35,15,20))
    pygame.draw.ellipse(surf, wheel_color, (width-20,height-35,15,20))

    return surf

def draw_powerup(color):
    surf = pygame.Surface((30,30), pygame.SRCALPHA)
    pygame.draw.circle(surf, color, (15,15), 14)
    return surf

def draw_traffic_car(color, width=50, height=80):
    surf = pygame.Surface((width, height), pygame.SRCALPHA)
    pygame.draw.rect(surf, color, (8,15,width-16,height-30), border_radius=6)

    cabin_color = tuple(max(0,c-40) for c in color)
    pygame.draw.rect(surf, cabin_color, (12,20,width-24,25), border_radius=5)
    pygame.draw.rect(surf, (180,220,255), (15,25,width-30,15))

    wheel_color = (30,30,30)
    pygame.draw.ellipse(surf, wheel_color, (3,12,12,16))
    pygame.draw.ellipse(surf, wheel_color, (width-15,12,12,16))
    pygame.draw.ellipse(surf, wheel_color, (3,height-28,12,16))
    pygame.draw.ellipse(surf, wheel_color, (width-15,height-28,12,16))

    return surf


def draw_text(text, size, color, x, y, center=True):
    font = pygame.font.SysFont("Arial", size, bold=True)
    img = font.render(text, True, color)
    rect = img.get_rect()
    if center: rect.center = (x, y)
    else: rect.topleft = (x, y)
    WIN.blit(img, rect)


CAR_COLORS = [
    (50,255,50),
    (255,50,50),
    (50,150,255),
    (255,220,50),
    (180,50,255),   # unlockable
    (255,100,0)     # unlockable
]

CAR_COSTS = [0,0,0,0, 40, 75]

CAR_IMAGES = [draw_car(c) for c in CAR_COLORS]

TRAFFIC_COLORS = [
    (150,150,150),
    (100,100,200),
    (200,100,50)
]
TRAFFIC_IMAGES = [draw_traffic_car(c) for c in TRAFFIC_COLORS]

POWERUP_TYPES = {
    "boost": (255, 100, 0),
    "magnet": (0, 255, 255),
    "invincible": (255, 255, 255)
}


class PlayerCar:
    def __init__(self, image):
        self.original_img = image
        self.img = image
        self.x = WIDTH//2
        self.y = HEIGHT-150

        # Upgradable values
        self.base_max_speed = 15
        self.base_acceleration = 0.4
        self.magnet_base_time = 300  # 5 sec

        self.speed = 0
        self.max_speed = self.base_max_speed
        self.acceleration = self.base_acceleration
        self.deceleration = 0.25

        # timers
        self.boost_timer = 0
        self.magnet_timer = 0
        self.invincible_timer = 0

    def update_upgrades(self):
        self.max_speed = self.base_max_speed + upgrade_speed_level * 2
        self.acceleration = self.base_acceleration + upgrade_accel_level * 0.1
        self.magnet_base_time = 300 + upgrade_magnet_level * 120

    def update(self, keys):
        accelerate = keys[pygame.K_UP] or keys[pygame.K_w]
        brake = keys[pygame.K_DOWN] or keys[pygame.K_s]
        left = keys[pygame.K_LEFT] or keys[pygame.K_a]
        right = keys[pygame.K_RIGHT] or keys[pygame.K_d]

        if accelerate:
            self.speed = min(self.max_speed, self.speed + self.acceleration)
        elif brake:
            self.speed = max(0, self.speed - self.deceleration * 2)
        else:
            self.speed *= 0.97

        if left: self.x -= 6
        if right: self.x += 6

        if self.boost_timer > 0:
            self.speed = min(self.max_speed+10, self.speed+0.8)
            self.boost_timer -= 1

        self.x = max(200, min(WIDTH-200, self.x))
        self.img = self.original_img

    def draw(self):
        rect = self.img.get_rect(center=(self.x, self.y))
        WIN.blit(self.img, rect)
        return rect



LANES = [WIDTH*0.3, WIDTH*0.5, WIDTH*0.7]

class TrafficCar:
    def __init__(self):
        self.img = random.choice(TRAFFIC_IMAGES)
        self.x = random.choice(LANES)
        self.y = -120
        self.speed = random.uniform(3,6)

    def update(self, player_speed):
        self.y += self.speed + player_speed*0.5

    def draw(self):
        WIN.blit(self.img, (self.x-self.img.get_width()//2, self.y))

    def is_off(self):
        return self.y > HEIGHT+120

    def rect(self):
        return pygame.Rect(self.x-self.img.get_width()//2, self.y,
                           self.img.get_width(), self.img.get_height())

class Coin:
    def __init__(self, lane):
        self.x = lane
        self.y = -40
        self.speed = 5
        self.radius = 15

    def update(self, spd):
        self.y += spd + 4

    def draw(self):
        pygame.draw.circle(WIN, (255,255,80), (int(self.x), int(self.y)), self.radius)

    def is_off(self):
        return self.y > HEIGHT+40

    def rect(self):
        return pygame.Rect(self.x-self.radius, self.y-self.radius,
                           self.radius*2, self.radius*2)

class PowerUp:
    def __init__(self, lane):
        self.type = random.choice(list(POWERUP_TYPES.keys()))
        self.color = POWERUP_TYPES[self.type]
        self.img = draw_powerup(self.color)

        self.x = lane
        self.y = -40

    def update(self, spd):
        self.y += spd+4

    def draw(self):
        WIN.blit(self.img, (self.x-15, self.y-15))

    def is_off(self):
        return self.y > HEIGHT+40

    def rect(self):
        return pygame.Rect(self.x-15, self.y-15, 30, 30)



track_scroll = 0
def draw_track(speed):
    global track_scroll
    track_scroll += speed
    if track_scroll >= 100: track_scroll = 0

    WIN.fill((34,139,34))
    road_color = (50,50,50)
    pygame.draw.rect(WIN, road_color, (200,0,WIDTH-400,HEIGHT))

    pygame.draw.rect(WIN, (255,255,255), (200,0,10,HEIGHT))
    pygame.draw.rect(WIN, (255,255,255), (WIDTH-210,0,10,HEIGHT))

    for i in range(-2, HEIGHT//50+2):
        y = i*100 + (track_scroll % 100)
        pygame.draw.rect(WIN, (255,255,60), (WIDTH*0.4-5, y, 10, 60))
        pygame.draw.rect(WIN, (255,255,60), (WIDTH*0.6-5, y, 10, 60))



traffic_list = []
coin_list = []
powerup_list = []

coins_collected = 0
score = 0
distance = 0

spawn_timer = 0
coin_timer = 0
powerup_timer = 0

spawn_rate = 100
coin_rate = 100
powerup_rate = 350

unlocked_cars = [True,True,True,True, False, False]

# Upgrade levels
upgrade_speed_level = 0
upgrade_accel_level = 0
upgrade_magnet_level = 0



def reset_game():
    global traffic_list, coin_list, powerup_list
    global spawn_timer, coin_timer, powerup_timer
    global score, distance, track_scroll, spawn_rate

    traffic_list = []
    coin_list = []
    powerup_list = []

    score = 0
    distance = 0
    track_scroll = 0

    spawn_timer = 0
    coin_timer = 0
    powerup_timer = 0

    spawn_rate = 100



def menu_screen():
    global menu_animation
    menu_animation += 1

    # Gradient background
    for y in range(HEIGHT):
        c = int(40 + (y / HEIGHT) * 80)
        pygame.draw.line(WIN, (c, c//3, c*2//3), (0, y), (WIDTH, y))

    # Animated waving flag
    bounce = math.sin(menu_animation * 0.05) * 20
    flag_y = 120 + bounce
    flag_x = WIDTH // 2
    square = 25

    for row in range(4):
        for col in range(6):
            color = (255,255,255) if (row+col)%2==0 else (30,30,30)
            pygame.draw.rect(WIN, color,
                             (flag_x - 75 + col*square,
                              flag_y + row*square,
                              square, square))

    # Flagpole
    pygame.draw.rect(WIN, (139,69,19), (flag_x - 80, flag_y, 8, 120))

    # Cars moving slightly
    car1_x = 160 + math.sin(menu_animation * 0.03) * 30
    car2_x = WIDTH - 160 + math.cos(menu_animation * 0.03) * 30

    carL = pygame.transform.scale(CAR_IMAGES[1], (110,160))
    carR = pygame.transform.scale(CAR_IMAGES[2], (110,160))
    WIN.blit(carL, (car1_x - 55, HEIGHT - 220))
    WIN.blit(carR, (car2_x - 55, HEIGHT - 220))

    # Title with shadow
    for offset in [5, 3]:
        draw_text("STREET RACER", 105, (255,60,60), WIDTH//2 + offset, 330 + offset)
    draw_text("STREET RACER", 105, (255,255,80), WIDTH//2, 330)

    draw_text("ENTER → Play", 50, (255,255,255), WIDTH//2, 475)
    draw_text("C → Select Car", 40, (255,255,255), WIDTH//2, 540)
    draw_text("U → Upgrades", 38, (255,255,200), WIDTH//2, 590)
    draw_text("ESC → Quit", 35, (200,100,100), WIDTH//2, 635)

    pygame.display.flip()


def car_select_screen():
    WIN.fill((30,30,50))
    draw_text("Select Your Car", 80, (255,200,50), WIDTH//2, 100)

    spacing = 220
    start_x = WIDTH//2 - ((len(CAR_IMAGES)-1) * spacing // 2)

    for i, img in enumerate(CAR_IMAGES):
        x = start_x + i*spacing
        y = HEIGHT//2

        locked = not unlocked_cars[i]

        # Glow highlight
        if i == selected_car_index:
            for glow in [180,130,80]:
                glow_surf = pygame.Surface((160,220), pygame.SRCALPHA)
                pygame.draw.rect(glow_surf, (255,255,0,glow),
                                 (0,0,160,220), border_radius=12)
                WIN.blit(glow_surf, (x-80, y-110))

        pygame.draw.rect(WIN, (255,255,0),
                         (x-75, y-105,150,210), 5, border_radius=10)

        scaled = pygame.transform.scale(img, (130,190))
        WIN.blit(scaled, (x - scaled.get_width()//2, y-95))

        if locked:
            draw_text(f"{CAR_COSTS[i]} coins", 30, (255,80,80), x, y+130)
        else:
            draw_text("Owned", 30, (150,255,150), x, y+130)

    draw_text("← → Move | ENTER Select | ESC Back",
              32, (220,220,220), WIDTH//2, HEIGHT - 60)

    pygame.display.flip()


def upgrade_screen():
    WIN.fill((20,25,40))

    draw_text("UPGRADE SHOP", 85, (255,220,90), WIDTH//2, 90)
    draw_text(f"Coins: {coins_collected}", 45, (255,255,180), WIDTH//2, 160)

    # Upgrade boxes
    box_w = 650
    box_h = 120
    start_y = 250

    upgrades = [
        ("Speed Upgrade", "+2 Max Speed", 30, upgrade_speed_level),
        ("Acceleration Upgrade", "+0.1 Accel", 20, upgrade_accel_level),
        ("Magnet Duration", "+2 sec Magnet", 35, upgrade_magnet_level)
    ]

    for i, (name, effect, cost, level) in enumerate(upgrades):
        y = start_y + i * (box_h + 30)
        pygame.draw.rect(WIN, (40,40,70), (WIDTH//2 - box_w//2, y, box_w, box_h), border_radius=12)
        pygame.draw.rect(WIN, (255,255,255), (WIDTH//2 - box_w//2, y, box_w, box_h), 3, border_radius=12)

        draw_text(name, 40, (255,255,255), WIDTH//2, y+35)
        draw_text(effect, 28, (180,200,255), WIDTH//2, y+70)
        draw_text(f"Level: {level}", 28, (255,255,150), WIDTH//2 + 230, y+40)
        draw_text(f"{cost} coins", 28, (255,150,150), WIDTH//2 + 230, y+78)

    draw_text("Press 1 / 2 / 3 to Buy | ESC to return",
              35, (200,200,200), WIDTH//2, HEIGHT - 60)

    pygame.display.flip()


def game_loop(player):
    global spawn_timer, coin_timer, powerup_timer
    global coins_collected, score, distance
    global spawn_rate

    running = True

    while running:
        clock.tick(FPS)
        keys = pygame.key.get_pressed()

        # ----------- Quit -----------
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return  # back to menu

        # ----------- Update Player -----------
        player.update(keys)
        distance += player.speed / 50
        score = int(distance)

        # ----------- Spawn Traffic -----------
        spawn_timer += 1
        if spawn_timer >= spawn_rate:
            spawn_timer = 0
            traffic_list.append(TrafficCar())

            # slowly increase difficulty
            if spawn_rate > 45:
                spawn_rate -= 0.3

        # ----------- Spawn Coins -----------
        coin_timer += 1
        if coin_timer >= coin_rate:
            coin_timer = 0
            lane = random.choice(LANES)

            # avoid spawning coin inside a traffic car
            safe = True
            for t in traffic_list:
                if abs(t.x - lane) < 60 and abs(t.y) < 150:
                    safe = False
                    break

            if safe:
                coin_list.append(Coin(lane))

        # ----------- Spawn Powerups -----------
        powerup_timer += 1
        if powerup_timer >= powerup_rate:
            powerup_timer = 0
            lane = random.choice(LANES)
            powerup_list.append(PowerUp(lane))

        # ----------- Update Traffic -----------
        for t in traffic_list:
            t.update(player.speed)
        traffic_list[:] = [t for t in traffic_list if not t.is_off()]

        # ----------- Update Coins -----------
        for c in coin_list:
            c.update(player.speed)
        coin_list[:] = [c for c in coin_list if not c.is_off()]

        # ----------- Update Powerups -----------
        for p in powerup_list:
            p.update(player.speed)
        powerup_list[:] = [p for p in powerup_list if not p.is_off()]



        player_rect = player.draw()

        # --- Collide with traffic ---
        for t in traffic_list:
            if player_rect.colliderect(t.rect()):
                if player.invincible_timer <= 0:
                    return  # game over (back to menu)

        # --- Collect coins ---
        for c in coin_list[:]:
            if player_rect.colliderect(c.rect()):
                coins_collected += 1
                coin_list.remove(c)

        # --- Magnet effect ---
        if player.magnet_timer > 0:
            for c in coin_list:
                dx = player.x - c.x
                dy = player.y - c.y
                dist = math.hypot(dx, dy)
                if dist < 200:
                    c.x += dx * 0.15
                    c.y += dy * 0.15
            player.magnet_timer -= 1

        # --- Check coin collisions again for magnet ---
        for c in coin_list[:]:
            if player_rect.colliderect(c.rect()):
                coins_collected += 1
                coin_list.remove(c)

        # --- Collect powerups ---
        for p in powerup_list[:]:
            if player_rect.colliderect(p.rect()):
                if p.type == "boost":
                    player.boost_timer = 180    # 3 sec
                elif p.type == "magnet":
                    player.magnet_timer = player.magnet_base_time
                elif p.type == "invincible":
                    player.invincible_timer = 600   # 10 sec (60 FPS)
                powerup_list.remove(p)

       
        if player.invincible_timer > 0:
            player.invincible_timer -= 1

      
        draw_track(player.speed)

        # Draw traffic
        for t in traffic_list:
            t.draw()

        # Draw coins
        for c in coin_list:
            c.draw()

        # Draw powerups
        for p in powerup_list:
            p.draw()

        # Draw player
        player.draw()

        # ----------- HUD -----------
        draw_text(f"Coins: {coins_collected}", 35, (255,255,120), 150, 40)
        draw_text(f"Score: {score}", 35, (255,255,255), 150, 80)

        # Powerup indicators
        if player.boost_timer > 0:
            draw_text("BOOST!", 40, (255,150,0), WIDTH-160, 40)

        if player.magnet_timer > 0:
            draw_text("MAGNET", 40, (0,255,255), WIDTH-160, 90)

        if player.invincible_timer > 0:
            sec = round(player.invincible_timer / 60, 1)
            draw_text(f"INVINCIBLE ({sec}s)", 40, (255,255,255), WIDTH-200, 140)

            # yellow aura
            pygame.draw.circle(WIN, (255,255,0,80),
                               (int(player.x), int(player.y)),
                               80)

        pygame.display.flip()


def handle_car_select_events():
    global selected_car_index, game_state, coins_collected

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit(); sys.exit()

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                game_state = "menu"

            if event.key == pygame.K_RIGHT:
                selected_car_index = (selected_car_index + 1) % len(CAR_IMAGES)

            if event.key == pygame.K_LEFT:
                selected_car_index = (selected_car_index - 1) % len(CAR_IMAGES)

            if event.key == pygame.K_RETURN:
                # purchase if needed
                if not unlocked_cars[selected_car_index]:
                    cost = CAR_COSTS[selected_car_index]
                    if coins_collected >= cost:
                        coins_collected -= cost
                        unlocked_cars[selected_car_index] = True
                else:
                    game_state = "menu"


def handle_upgrade_events():
    global upgrade_speed_level, upgrade_accel_level, upgrade_magnet_level
    global coins_collected, game_state

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit(); sys.exit()

        if event.type == pygame.KEYDOWN:

            if event.key == pygame.K_ESCAPE:
                game_state = "menu"

            # ------- Buy Upgrades -------
            if event.key == pygame.K_1:
                if coins_collected >= 30:
                    coins_collected -= 30
                    upgrade_speed_level += 1

            if event.key == pygame.K_2:
                if coins_collected >= 20:
                    coins_collected -= 20
                    upgrade_accel_level += 1

            if event.key == pygame.K_3:
                if coins_collected >= 35:
                    coins_collected -= 35
                    upgrade_magnet_level += 1


player = PlayerCar(CAR_IMAGES[selected_car_index])

while True:
    if game_state == "menu":
        menu_screen()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    reset_game()
                    player = PlayerCar(CAR_IMAGES[selected_car_index])
                    player.update_upgrades()
                    game_loop(player)

                if event.key == pygame.K_c:
                    game_state = "car_select"

                if event.key == pygame.K_u:
                    game_state = "upgrade"

                if event.key == pygame.K_ESCAPE:
                    pygame.quit(); sys.exit()

    elif game_state == "car_select":
        car_select_screen()
        handle_car_select_events()

    elif game_state == "upgrade":
        upgrade_screen()
        handle_upgrade_events()
