import pygame
import math

pygame.init()

# Адаптивный экран
screen = pygame.display.set_mode((0, 0), pygame.RESIZABLE)
WIDTH, HEIGHT = screen.get_size()
clock = pygame.time.Clock()

# Шрифты
font_large = pygame.font.SysFont("sans-serif", int(HEIGHT * 0.035), bold=True)
font_med = pygame.font.SysFont("sans-serif", int(HEIGHT * 0.022), bold=True)
font_small = pygame.font.SysFont("sans-serif", int(HEIGHT * 0.016))
font_tree_title = pygame.font.SysFont("sans-serif", int(HEIGHT * 0.018), bold=True)
font_tree_desc = pygame.font.SysFont("sans-serif", int(HEIGHT * 0.014))

# Цвета
BG_COLOR = (15, 15, 22)
WHITE = (240, 240, 240)
GRAY = (70, 70, 85)
GOLD = (241, 196, 15)
PURPLE = (155, 89, 182)
CYAN = (52, 152, 219)
GREEN = (46, 204, 113)
RED = (231, 76, 60)
INF_BAR_BG = (30, 30, 45)
INF_BAR_FILL = (142, 68, 173)

# Игровые переменные
points = 0.0
infinity_points = 0
base_infinity_target = 1e12
prestige_multiplier = 1.0
time_multipliers = [1, 5, 10, 60]
time_speed_idx = 0

def format_num(val):
    val = float(val)
    if val < 1000: return f"{int(val)}"
    # Заменил список: добавил Sx, Sp, Oc, No, Dc
    units = ["", "k", "M", "B", "T", "Qa", "Qi", "Sx", "Sp", "Oc", "No", "Dc"]
    unit_idx = 0
    while val >= 1000 and unit_idx < len(units) - 1:
        val /= 1000.0
        unit_idx += 1
    return f"{val:.2f}{units[unit_idx]}"

inf_upgrades = {
    1: {"name": "Сила ОБ", "desc": "+50% дохода за ОБ", "cost": 1, "req": [], "bought": False, "pos": (0.50, 0.82)},
    2: {"name": "Разгон", "desc": "+25% скорости орбит", "cost": 2, "req": [1], "bought": False, "pos": (0.26, 0.72)},
    3: {"name": "Скидки", "desc": "-20% стоимости", "cost": 3, "req": [1], "bought": False, "pos": (0.74, 0.72)},
    4: {"name": "Запредел", "desc": "Шкала x10, сбор ОБ", "cost": 5, "req": [2], "bought": False, "pos": (0.26, 0.62)},
    9: {"name": "х10 ОБ", "desc": "Множитель ОБ x10", "cost": 5, "req": [3], "bought": False, "pos": (0.74, 0.62)},
    5: {"name": "Супер-Вознесение", "desc": "+100% за Вознесение", "cost": 10, "req": [4], "bought": False, "pos": (0.26, 0.52)},
    6: {"name": "Гипер-Скорость", "desc": "+30% скорости орбит", "cost": 15, "req": [9], "bought": False, "pos": (0.74, 0.52)},
    7: {"name": "Быстрый Престиж", "desc": "х2 рост престижа", "cost": 25, "req": [5, 6], "bought": False, "pos": (0.50, 0.42)},
    8: {"name": "Синергия", "desc": "+20% за орбиту", "cost": 50, "req": [7], "bought": False, "pos": (0.26, 0.32)},
    10: {"name": "Сжатие", "desc": "База 1T -> 500B", "cost": 100, "req": [7, 8], "bought": False, "pos": (0.50, 0.22)},
}

tree_connections = [
    (1, 2), (1, 3),
    (2, 4), (3, 9),
    (4, 5), (9, 6),
    (5, 7), (6, 7),
    (7, 8), (7, 10), (8, 10)
]

class Orbit:
    def __init__(self, index, base_radius, color):
        self.index = index
        self.radius = base_radius
        self.color = color
        self.angle = 0.0
        self.unlocked = (index == 0)
        self.base_unlock_cost = 10.0
        self.upgrades_bought = 0
        self.speed_level = 0
        self.ascensions = 0
        self.base_points = 1.0 * (2.0 ** index)
        self.base_cost = 2.0

    @property
    def unlock_cost(self):
        cost = self.base_unlock_cost
        if inf_upgrades[3]["bought"]: cost *= 0.8
        return cost

    @property
    def upgrade_cost(self):
        cost = self.base_cost * (1.2 ** self.upgrades_bought)
        if inf_upgrades[3]["bought"]: cost *= 0.8
        return cost

    @property
    def income_mult(self):
        asc_bonus = 2.0 if inf_upgrades[5]["bought"] else 1.5
        ob_mult = 1.0 + (infinity_points * 0.5) if inf_upgrades[1]["bought"] else 1.0
        orbit_count_bonus = 1.0 + (sum(1 for o in orbits if o.unlocked) * 0.2) if inf_upgrades[8]["bought"] else 1.0
        return (asc_bonus ** self.ascensions) * prestige_multiplier * ob_mult * orbit_count_bonus

    def update(self, dt):
        global points
        if not self.unlocked: return
        speed_boost = 1.25 if inf_upgrades[2]["bought"] else 1.0
        hyper_boost = 1.3 if inf_upgrades[6]["bought"] else 1.0
        self.angle += (0.5 + self.index * 0.25) * (1.0 + self.speed_level * 0.15) * speed_boost * hyper_boost * dt
        if self.angle >= math.tau:
            self.angle -= math.tau
            points += self.base_points * self.income_mult

    def buy_unlock(self):
        global points
        if not self.unlocked and points >= self.unlock_cost:
            points -= self.unlock_cost
            self.unlocked = True
            return True
        return False

    def buy_upgrade(self):
        global points
        if not self.unlocked: return False
        cost = self.upgrade_cost
        if points >= cost:
            points -= cost
            self.upgrades_bought += 1
            self.speed_level += 1
            if self.speed_level >= 20:
                self.speed_level = 0
                self.ascensions += 1
            return True
        return False

    def reset(self):
        self.unlocked = (self.index == 0)
        self.angle = 0.0
        self.upgrades_bought = 0
        self.speed_level = 0
        self.ascensions = 0

orbits = [Orbit(i, int(min(WIDTH, HEIGHT) * 0.045 * (i + 1.5)), [(231,76,60), (230,126,34), (241,196,15), (46,204,113), (52,152,219), (155,89,182)][i]) for i in range(6)]

current_tab = "GAME"
shop_page = "ORBITS"

def buy_all():
    bought_something = True
    while bought_something:
        bought_something = False
        for i, o in enumerate(orbits):
            if not o.unlocked:
                if i == 0 or orbits[i-1].unlocked:
                    if o.buy_unlock(): bought_something = True
            else:
                if o.buy_upgrade(): bought_something = True

running = True
while running:
    dt = clock.tick(60) / 1000.0
    effective_dt = dt * time_multipliers[time_speed_idx]

    btn_prestige = pygame.Rect(WIDTH - int(WIDTH * 0.38), int(HEIGHT * 0.02), int(WIDTH * 0.35), int(HEIGHT * 0.065))
    btn_tab_orbits = pygame.Rect(int(WIDTH * 0.04), int(HEIGHT * 0.125), int(WIDTH * 0.44), int(HEIGHT * 0.045))
    btn_tab_tree = pygame.Rect(int(WIDTH * 0.52), int(HEIGHT * 0.125), int(WIDTH * 0.44), int(HEIGHT * 0.045))

    btn_h = int(HEIGHT * 0.07)
    btn_y = HEIGHT - btn_h - 15
    btn_shop = pygame.Rect(int(WIDTH * 0.04), btn_y, int(WIDTH * 0.28), btn_h)
    btn_middle = pygame.Rect(int(WIDTH * 0.36), btn_y, int(WIDTH * 0.28), btn_h)
    btn_time = pygame.Rect(int(WIDTH * 0.68), btn_y, int(WIDTH * 0.28), btn_h)

    base_target = 5e11 if inf_upgrades[10]["bought"] else base_infinity_target
    cur_target = base_target
    if inf_upgrades[4]["bought"]:
        while points >= cur_target: cur_target *= 10.0

    pending_ob = int(points // base_target) * (10 if inf_upgrades[9]["bought"] else 1)
    btn_claim_ob = pygame.Rect(int(WIDTH * 0.3), int(HEIGHT * 0.115), int(WIDTH * 0.4), int(HEIGHT * 0.035))

    for event in pygame.event.get():
        if event.type == pygame.QUIT: running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            pos = event.pos
            if inf_upgrades[4]["bought"] and pending_ob >= 1 and btn_claim_ob.collidepoint(pos):
                infinity_points += pending_ob
                points = 0; prestige_multiplier = 1.0
                for o in orbits: o.reset()
            elif points >= 15000 and btn_prestige.collidepoint(pos):
                gain = int(points // 1000) * (2 if inf_upgrades[7]["bought"] else 1)
                prestige_multiplier += gain
                points = 0
                for o in orbits: o.reset()
            elif btn_shop.collidepoint(pos):
                current_tab = "SHOP" if current_tab == "GAME" else "GAME"
            elif btn_middle.collidepoint(pos) and current_tab == "SHOP": 
                buy_all()
            elif btn_time.collidepoint(pos): 
                time_speed_idx = (time_speed_idx + 1) % len(time_multipliers)
            elif current_tab == "SHOP":
                if btn_tab_orbits.collidepoint(pos): shop_page = "ORBITS"
                elif btn_tab_tree.collidepoint(pos): shop_page = "TREE"
                elif shop_page == "ORBITS":
                    for i, o in enumerate(orbits):
                        btn_buy = pygame.Rect(WIDTH - int(WIDTH * 0.35), int(HEIGHT * 0.185) + i * int(HEIGHT * 0.08) + 5, int(WIDTH * 0.28), int(HEIGHT * 0.05))
                        if btn_buy.collidepoint(pos):
                            if not o.unlocked:
                                if i == 0 or orbits[i-1].unlocked: o.buy_unlock()
                            else: o.buy_upgrade()
                elif shop_page == "TREE":
                    for uid, upg in inf_upgrades.items():
                        ux, uy = int(WIDTH * upg["pos"][0]), int(HEIGHT * upg["pos"][1])
                        if pygame.Rect(ux - int(WIDTH * 0.21), uy - int(HEIGHT * 0.04), int(WIDTH * 0.42), int(HEIGHT * 0.08)).collidepoint(pos):
                            if not upg["bought"] and infinity_points >= upg["cost"] and all(inf_upgrades[r]["bought"] for r in upg["req"]):
                                infinity_points -= upg["cost"]
                                upg["bought"] = True

    for o in orbits: o.update(effective_dt)
    
    if not inf_upgrades[4]["bought"] and points >= cur_target:
        infinity_points += int(points // cur_target) * (10 if inf_upgrades[9]["bought"] else 1)
        points = 0; prestige_multiplier = 1.0; 
        for o in orbits: o.reset()

    screen.fill(BG_COLOR)
    
    screen.blit(font_large.render(f"Очки: {format_num(points)}", True, GOLD), (int(WIDTH * 0.04), int(HEIGHT * 0.012)))
    screen.blit(font_small.render(f"ОБ: {infinity_points}", True, INF_BAR_FILL), (int(WIDTH * 0.04), int(HEIGHT * 0.048)))
    if prestige_multiplier > 1.0: screen.blit(font_small.render(f"Множитель: {format_num(prestige_multiplier)}x", True, PURPLE), (int(WIDTH * 0.04), int(HEIGHT * 0.068)))

    bar_w, bar_h = int(WIDTH * 0.92), int(HEIGHT * 0.02)
    bar_x, bar_y = int(WIDTH * 0.04), int(HEIGHT * 0.09)
    progress = min(1.0, points / cur_target)
    pygame.draw.rect(screen, INF_BAR_BG, (bar_x, bar_y, bar_w, bar_h), border_radius=4)
    if progress > 0: pygame.draw.rect(screen, INF_BAR_FILL, (bar_x, bar_y, int(bar_w * progress), bar_h), border_radius=4)
    prog_txt = font_small.render(f"До {format_num(cur_target)}: {progress * 100:.1f}%", True, WHITE)
    screen.blit(prog_txt, prog_txt.get_rect(center=(bar_x + bar_w // 2, bar_y + bar_h // 2)))

    if inf_upgrades[4]["bought"]:
        can_claim = pending_ob >= 1
        pygame.draw.rect(screen, GOLD if can_claim else GRAY, btn_claim_ob, border_radius=6)
        claim_txt = font_small.render(f"ЗАБРАТЬ {pending_ob} ОБ" if can_claim else "НАКОПИТЕ 1T ДЛЯ ОБ", True, (0,0,0) if can_claim else WHITE)
        screen.blit(claim_txt, claim_txt.get_rect(center=btn_claim_ob.center))

    can_prestige = points >= 15000
    prestige_gain = int(points // 1000) * (2 if inf_upgrades[7]["bought"] else 1) if can_prestige else 0
    pygame.draw.rect(screen, PURPLE if can_prestige else (40, 40, 50), btn_prestige, border_radius=10)
    lbl_title = font_small.render("ПРЕСТИЖ", True, WHITE if can_prestige else GRAY)
    lbl_gain = font_tree_desc.render(f"+{format_num(prestige_gain)}x" if can_prestige else "от 15k", True, GOLD if can_prestige else GRAY)
    screen.blit(lbl_title, (btn_prestige.centerx - lbl_title.get_width() // 2, btn_prestige.y + 6))
    screen.blit(lbl_gain, (btn_prestige.centerx - lbl_gain.get_width() // 2, btn_prestige.y + 26))

    if current_tab == "GAME":
        center = (WIDTH // 2, HEIGHT // 2 + int(HEIGHT * 0.02))
        for o in orbits:
            if o.unlocked:
                pygame.draw.circle(screen, GRAY, center, o.radius, 1)
                px = center[0] + int(math.cos(o.angle) * o.radius)
                py = center[1] + int(math.sin(o.angle) * o.radius)
                pygame.draw.circle(screen, o.color, (px, py), 8)
                if o.ascensions > 0: pygame.draw.circle(screen, PURPLE, (px, py), 12, 2)
    elif current_tab == "SHOP":
        pygame.draw.rect(screen, GOLD if shop_page == "ORBITS" else GRAY, btn_tab_orbits, border_radius=6)
        pygame.draw.rect(screen, INF_BAR_FILL if shop_page == "TREE" else GRAY, btn_tab_tree, border_radius=6)
        screen.blit(font_small.render("ОРБИТЫ", True, WHITE), (btn_tab_orbits.centerx - 25, btn_tab_orbits.centery - 8))
        screen.blit(font_small.render("ДЕРЕВО ОБ", True, WHITE), (btn_tab_tree.centerx - 35, btn_tab_tree.centery - 8))
        if shop_page == "ORBITS":
            for i, o in enumerate(orbits):
                y = int(HEIGHT * 0.185) + i * int(HEIGHT * 0.08)
                pygame.draw.rect(screen, (25, 25, 35), (int(WIDTH * 0.04), y, WIDTH - int(WIDTH * 0.08), int(HEIGHT * 0.07)), border_radius=8)
                screen.blit(font_med.render(f"Орбита {i+1}", True, WHITE if o.unlocked else GRAY), (int(WIDTH * 0.1), y + 10))
                btn_buy = pygame.Rect(WIDTH - int(WIDTH * 0.35), y + 5, int(WIDTH * 0.28), int(HEIGHT * 0.05))
                cost = o.upgrade_cost if o.unlocked else o.unlock_cost
                can_afford = points >= cost
                pygame.draw.rect(screen, CYAN if can_afford else GRAY, btn_buy, border_radius=6)
                cost_txt = font_small.render(format_num(cost), True, (0, 0, 0) if can_afford else WHITE)
                screen.blit(cost_txt, cost_txt.get_rect(center=btn_buy.center))
        elif shop_page == "TREE":
            for s_id, e_id in tree_connections:
                x1, y1 = int(WIDTH * inf_upgrades[s_id]["pos"][0]), int(HEIGHT * inf_upgrades[s_id]["pos"][1])
                x2, y2 = int(WIDTH * inf_upgrades[e_id]["pos"][0]), int(HEIGHT * inf_upgrades[e_id]["pos"][1])
                pygame.draw.line(screen, INF_BAR_FILL if inf_upgrades[s_id]["bought"] else GRAY, (x1, y1), (x2, y2), 3)
            for uid, upg in inf_upgrades.items():
                ux, uy = int(WIDTH * upg["pos"][0]), int(HEIGHT * upg["pos"][1])
                rect = pygame.Rect(ux - int(WIDTH * 0.21), uy - int(HEIGHT * 0.04), int(WIDTH * 0.42), int(HEIGHT * 0.08))
                can_buy = (not upg["bought"]) and (infinity_points >= upg["cost"]) and all(inf_upgrades[r]["bought"] for r in upg["req"])
                bg = (25, 75, 45) if upg["bought"] else (55, 30, 80) if can_buy else (22, 22, 30)
                pygame.draw.rect(screen, bg, rect, border_radius=10)
                pygame.draw.rect(screen, GREEN if upg["bought"] else INF_BAR_FILL, rect, 2, border_radius=10)
                screen.blit(font_tree_title.render(upg["name"], True, WHITE), (rect.x + 8, rect.y + 4))
                screen.blit(font_tree_desc.render(upg["desc"], True, WHITE), (rect.x + 8, rect.y + 24))
                screen.blit(font_tree_desc.render(f"Цена: {format_num(upg['cost'])} ОБ", True, GOLD), (rect.x + 8, rect.y + 42))

    pygame.draw.rect(screen, GOLD if current_tab == "SHOP" else GRAY, btn_shop, border_radius=10)
    screen.blit(font_small.render("МАГАЗИН" if current_tab == "GAME" else "ИГРА", True, WHITE), (btn_shop.centerx - 30, btn_shop.centery - 8))
    
    if current_tab == "SHOP":
        pygame.draw.rect(screen, GREEN, btn_middle, border_radius=10)
        btn_txt = font_small.render("ВСЁ", True, WHITE)
        screen.blit(btn_txt, btn_txt.get_rect(center=btn_middle.center))
    else:
        pygame.draw.rect(screen, GRAY, btn_middle, border_radius=10)
        
    pygame.draw.rect(screen, CYAN, btn_time, border_radius=10)
    time_txt = font_small.render(f"{time_multipliers[time_speed_idx]}x", True, WHITE)
    screen.blit(time_txt, time_txt.get_rect(center=btn_time.center))

    pygame.display.flip()

pygame.quit()
