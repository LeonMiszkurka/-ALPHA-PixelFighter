import tkinter as tk
from tkinter import ttk
import pygame
import sys
import random
import time
from network import Network  # make sure network.py exists

# ---------------- GAME ----------------
def run_game(mode):
    pygame.init()

    WIDTH, HEIGHT = 900, 500
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("GD Pixel Fighter")
    clock = pygame.time.Clock()
    FPS = 60
    jumpHeight = 10

    # ---------- COLORS ----------
    BG = (10, 10, 15)
    RED = (255, 60, 60)
    BLUE = (60, 160, 255)
    GREEN = (80, 255, 120)
    WHITE = (255, 255, 255)

    # ---------- STATE ----------
    paused = False
    game_over = False
    winner_text = ""
    gravity = 1

    # ---------- FIGHTER ----------
    class Fighter:
        def __init__(self, x, color, controls=None):
            self.rect = pygame.Rect(x, 320, 40, 40)
            self.color = color
            self.controls = controls
            self.health = 100
            self.speed = 5
            self.cooldown = 0
            self.attacking = False
            self.vel_y = 0
            self.on_ground = True
            self.direction = "R"

        def move(self, keys):
            if self.controls:
                if keys[self.controls["left"]]:
                    self.direction = "L"
                    self.rect.x -= self.speed
                if keys[self.controls["right"]]:
                    self.direction = "R"
                    self.rect.x += self.speed
                if keys[self.controls["jump"]] and self.on_ground:
                    self.vel_y = -15
                    self.on_ground = False

        def attack(self):
            if self.cooldown == 0:
                self.attacking = True
                self.cooldown = 20

        def update(self):
            if self.cooldown > 0:
                self.cooldown -= 1
            else:
                self.attacking = False

            # gravity
            self.vel_y += gravity
            self.rect.y += self.vel_y
            if self.rect.y >= 320:
                self.rect.y = 320
                self.vel_y = 0
                self.on_ground = True

        def draw(self):
            pygame.draw.rect(screen, self.color, self.rect)
            # What to draw if we are attacking
            if self.attacking:
                if self.direction == "L":
                    atk = pygame.Rect(self.rect.left - 20, self.rect.y + 10, 20, 20)
                    # TODO: different colors for more powerful swords
                    pygame.draw.rect(screen, WHITE, atk)
                else:
                    atk = pygame.Rect(self.rect.right, self.rect.y + 10, 20, 20)
                    pygame.draw.rect(screen, WHITE, atk)
                # TODO: Can we delete the return value?
                return atk
            return None

    # ---------- AI ----------
    def ai_control(ai, target):
        # Horizontal distance to player
        distance = target.rect.centerx - ai.rect.centerx

        # Decide if AI should move or stay
        if abs(distance) > 80:
            # Move toward player if far
            ai.rect.x += ai.speed if distance > 0 else -ai.speed
        else:
            # If close, maybe step back to avoid attacks
            if random.random() < 0.2:  # 20% chance to dodge
                ai.rect.x -= ai.speed if distance > 0 else -ai.speed

        # Jump if player is above or to dodge
        if target.rect.y < ai.rect.y and ai.on_ground:
            ai.vel_y = -15
            ai.on_ground = False
        elif abs(distance) < 50 and ai.on_ground and random.random() < 0.05:
            # small chance to jump to avoid hits
            ai.vel_y = -12
            ai.on_ground = False

        # Attack only if facing the player and cooldown is ready
        if abs(distance) <= 50 and ((distance > 0 and ai.rect.x < target.rect.x) or (
                distance < 0 and ai.rect.x > target.rect.x)) and ai.cooldown == 0:
            ai.attack()

    # ---------- PLAYERS ----------
    p1 = Fighter(200, RED, {
        "left": pygame.K_a,
        "right": pygame.K_d,
        "jump": pygame.K_SPACE
    })

    if mode == "online":
        ip = input("Enter host IP: ")
        host_choice = input("Host? y/n: ").lower() == "y"
        net = Network(host=host_choice, ip=ip)
        p2 = Fighter(600, BLUE)
    else:
        p2 = Fighter(600, BLUE, {
            "left": pygame.K_LEFT,
            "right": pygame.K_RIGHT,
            "jump": pygame.K_UP
        } if mode=="local" else None)

    font_big = pygame.font.SysFont("Arial", 36, bold=True)
    font_small = pygame.font.SysFont("Arial", 18)

    def draw_health(p, x, y):
        pygame.draw.rect(screen, (40,40,40), (x,y,200,12))
        pygame.draw.rect(screen, GREEN, (x,y,max(0,p.health)*2,12))

    def draw_pause():
        overlay = pygame.Surface((WIDTH, HEIGHT))
        overlay.set_alpha(180)
        overlay.fill((0,0,0))
        screen.blit(overlay,(0,0))
        screen.blit(font_big.render("PAUSED", True, WHITE), (360,200))
        screen.blit(font_small.render("ESC = Resume | Q = Quit", True, WHITE), (330,250))

    def draw_end():
        overlay = pygame.Surface((WIDTH, HEIGHT))
        overlay.set_alpha(200)
        overlay.fill((0,0,0))
        screen.blit(overlay,(0,0))
        screen.blit(font_big.render(winner_text, True, WHITE), (280,190))
        screen.blit(font_small.render("R = Restart | Q = Quit", True, WHITE), (300,240))

    # ---------- LOOP ----------
    running = True
    while running:
        clock.tick(FPS)
        screen.fill(BG)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    paused = not paused
                if paused and event.key == pygame.K_q:
                    running = False
                if game_over:
                    if event.key == pygame.K_q:
                        running = False
                    if event.key == pygame.K_r:
                        run_game(mode)
                        return

            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1 and not paused and not game_over:
                    p1.attack()

        keys = pygame.key.get_pressed()
        if not paused and not game_over:
            p1.move(keys)

            if mode == "single":
                ai_control(p2, p1)
            elif mode == "local":
                p2.move(keys)
            elif mode == "online":
                send_data = {
                    "x": p1.rect.x,
                    "y": p1.rect.y,
                    "attack": p1.attacking,
                    "health": p1.health
                }
                recv_data = net.send(send_data)
                p2.rect.x = recv_data["x"]
                p2.rect.y = recv_data["y"]
                p2.attacking = recv_data["attack"]
                p2.health = recv_data["health"]

            p1.update()
            p2.update()

            atk1 = p1.draw()
            atk2 = p2.draw()

            if atk1 and atk1.colliderect(p2.rect):
                p2.health -= 1
                if p2.health <=0:
                    game_over = True
                    winner_text = "You Win!" if mode=="single" else "Player 1 Wins"

            if atk2 and atk2.colliderect(p1.rect):
                p1.health -=1
                if p1.health <=0:
                    game_over = True
                    winner_text = "You Lose!" if mode=="single" else "Player 2 Wins"
        else:
            p1.draw()
            p2.draw()

        draw_health(p1,50,30)
        draw_health(p2,WIDTH-250,30)

        if paused:
            draw_pause()
        if game_over:
            draw_end()

        pygame.display.flip()

    pygame.quit()
    sys.exit()


# ---------------- TKINTER LOADING & MENU ----------------
class App:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Pixel Fighter")
        self.root.geometry("800x400")
        self.root.configure(bg="#0a0a12")
        self.root.resizable(False,False)

        self.frame = tk.Frame(self.root, bg="#0a0a12")
        self.frame.pack(expand=True)

        self.show_intro()

        self.root.mainloop()

    def show_intro(self):
        self.intro_label = tk.Label(self.frame, text="ARM GAMES", font=("Arial", 36, "bold"), fg="#4fc3ff", bg="#0a0a12")
        self.intro_label.pack(pady=150)

        self.progress = ttk.Progressbar(self.frame, orient="horizontal", length=400, mode="determinate")
        self.progress.pack(pady=20)

        self.root.after(100, self.loading_step, 0)

    def loading_step(self, value):
        if value > 100:
            self.intro_label.pack_forget()
            self.progress.pack_forget()
            self.show_menu()
            return
        self.progress["value"] = value
        self.root.after(50, self.loading_step, value+2)

    def show_menu(self):
        try:
            logo_img = tk.PhotoImage(file="pf_teico.png")
            tk.Label(self.frame,image=logo_img,bg="#0a0a12").pack(pady=20)
            self.logo_img = logo_img  # keep reference
        except:
            tk.Label(self.frame,text="PF_TEICO",fg="#4fc3ff",bg="#0a0a12", font=("Arial",36,"bold")).pack(pady=30)

        ttk.Button(self.frame,text="▶ Singleplayer",command=lambda:self.start_game("single")).pack(pady=8)
        ttk.Button(self.frame,text="👥 Local 2 Player",command=lambda:self.start_game("local")).pack(pady=8)
        ttk.Button(self.frame,text="🌐 Online (LAN)",command=lambda:self.start_game("online")).pack(pady=8)
        ttk.Button(self.frame,text="✖ Quit",command=self.root.destroy).pack(pady=10)

    def start_game(self, mode):
        self.root.destroy()
        run_game(mode)


if __name__ == "__main__":
    App()
