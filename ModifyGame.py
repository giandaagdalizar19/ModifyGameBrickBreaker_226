import pygame
import random
import math
import struct
import sys

pygame.init()
pygame.mixer.init(frequency=44100, size=-16, channels=1)

# Dimensions
WIDTH, HEIGHT = 600, 500

# Pastel Pink & Lavender Colors
BLACK = (255, 240, 245)   # dipakai sebagai warna latar
WHITE = (255, 255, 255)
DARK = (60, 40, 60)       # untuk mata dan hidung beruang

SOFT_PINK = (255, 182, 209)
LAVENDER = (220, 198, 255)
BABY_PINK = (255, 200, 221)
BABY_BLUE = (189, 224, 254)
PEACH = (255, 214, 165)
MINT = (202, 255, 191)
LIGHT_LAVENDER = (230, 210, 255)

# Screen
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Block Breaker - Pastel Edition")

clock = pygame.time.Clock()
FPS = 30

font = pygame.font.Font("freesansbold.ttf", 15)
big_font = pygame.font.Font("freesansbold.ttf", 30)


# SOUND EFFECTS
def create_sound(frequency, duration=0.12, volume=0.3):
    sample_rate = 44100
    samples = []

    for i in range(int(sample_rate * duration)):
        t = i / sample_rate
        fade = 1 - (i / (sample_rate * duration))

        value = int(
            32767 * volume * fade *
            math.sin(2 * math.pi * frequency * t)
        )

        samples.append(struct.pack("<h", value))

    return pygame.mixer.Sound(buffer=b"".join(samples))


paddle_sound = create_sound(600, 0.10)
brick_sound = create_sound(900, 0.12)
wall_sound = create_sound(400, 0.08)
life_sound = create_sound(200, 0.35)


# STRIKER CLASS
class Striker:
    def __init__(self, posx, posy, width, height, speed, color):
        self.posx, self.posy = posx, posy
        self.width, self.height = width, height
        self.speed = speed
        self.color = color

        self.strikerRect = pygame.Rect(
            posx, posy, width, height
        )

    def display(self):
        pygame.draw.rect(
            screen, self.color, self.strikerRect,
            border_radius=8
        )

    def update(self, xFac):
        self.posx += self.speed * xFac

        if self.posx <= 0:
            self.posx = 0

        elif self.posx + self.width >= WIDTH:
            self.posx = WIDTH - self.width

        self.strikerRect = pygame.Rect(
            self.posx, self.posy,
            self.width, self.height
        )

    def getRect(self):
        return self.strikerRect


# BLOCK CLASS (berbentuk kepala beruang)
class Block:
    def __init__(self, posx, posy, width, height, color):
        self.posx, self.posy = posx, posy
        self.width, self.height = width, height
        self.color = color
        self.damage = 100

        self.health = 200 if color == LIGHT_LAVENDER else 100

        self.blockRect = pygame.Rect(
            posx, posy, width, height
        )

    def display(self):
        if self.health > 0:
            x, y = self.blockRect.x, self.blockRect.y
            w, h = self.blockRect.width, self.blockRect.height

            # telinga bulat kiri dan kanan
            pygame.draw.circle(screen, self.color, (x+8, y+7), 6)
            pygame.draw.circle(screen, self.color, (x+w-8, y+7), 6)

            # kepala
            pygame.draw.ellipse(screen, self.color, (x+2, y+5, w-4, h-5))

            # mata
            pygame.draw.circle(screen, DARK, (x+w//3, y+h//2), 2)
            pygame.draw.circle(screen, DARK, (x+w*2//3, y+h//2), 2)

            # moncong dan hidung
            pygame.draw.ellipse(
                screen, WHITE, (x+w//2-6, y+h*2//3-2, 12, 9))
            pygame.draw.circle(screen, DARK, (x+w//2, y+h*2//3+1), 2)

    def hit(self):
        self.health -= self.damage

    def getRect(self):
        return self.blockRect

    def getHealth(self):
        return self.health


# BALL CLASS
class Ball:
    def __init__(self, posx, posy, radius, speed, color):
        self.posx, self.posy = posx, posy
        self.radius = radius
        self.speed = speed
        self.color = color
        self.xFac, self.yFac = 1, -1

        self.ball = pygame.Rect(
            posx - radius, posy - radius,
            radius * 2, radius * 2
        )

    def display(self):
        pygame.draw.circle(
            screen, self.color,
            (int(self.posx), int(self.posy)),
            self.radius
        )

    def update(self):
        self.posx += self.xFac * self.speed
        self.posy += self.yFac * self.speed

        if self.posx <= self.radius:
            self.posx = self.radius
            self.xFac = 1
            wall_sound.play()

        elif self.posx >= WIDTH - self.radius:
            self.posx = WIDTH - self.radius
            self.xFac = -1
            wall_sound.play()

        if self.posy <= self.radius:
            self.posy = self.radius
            self.yFac = 1
            wall_sound.play()

        self.ball = pygame.Rect(
            int(self.posx - self.radius),
            int(self.posy - self.radius),
            self.radius * 2,
            self.radius * 2
        )

        if self.posy >= HEIGHT:
            return True

        return False

    def reset(self):
        self.posx = WIDTH // 2
        self.posy = HEIGHT - 150
        self.xFac = 1
        self.yFac = -1

    def hit(self):
        self.yFac *= -1

    def getRect(self):
        return self.ball


# COLLISION CHECKER
def collisionChecker(rect, ball):
    return rect.colliderect(ball)


# POPULATE BLOCKS
def populateBlocks(blockWidth, blockHeight,
                   horizontalGap, verticalGap):

    listOfBlocks = []

    pastel_colors = [
        SOFT_PINK,
        LAVENDER,
        BABY_BLUE,
        PEACH,
        MINT,
        BABY_PINK,
        LIGHT_LAVENDER
    ]

    for i in range(0, WIDTH, blockWidth + horizontalGap):
        for j in range(0, HEIGHT // 2,
                       blockHeight + verticalGap):

            color = random.choice(pastel_colors)

            listOfBlocks.append(
                Block(
                    i, j,
                    blockWidth,
                    blockHeight,
                    color
                )
            )

    return listOfBlocks


# GAME OVER
def gameOver():
    while True:
        screen.fill(BLACK)

        title = big_font.render(
            "GAME OVER!", True, SOFT_PINK
        )

        restart = font.render(
            "Press SPACE to Restart", True, LAVENDER
        )

        quit_text = font.render(
            "Press ESC to Quit", True, SOFT_PINK
        )

        screen.blit(
            title,
            title.get_rect(center=(WIDTH // 2, 200))
        )

        screen.blit(
            restart,
            restart.get_rect(center=(WIDTH // 2, 260))
        )

        screen.blit(
            quit_text,
            quit_text.get_rect(center=(WIDTH // 2, 290))
        )

        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    return True

                if event.key == pygame.K_ESCAPE:
                    return False

        clock.tick(FPS)


# YOU WIN
def youWin(score):
    while True:
        screen.fill(BLACK)

        title = big_font.render(
            "YOU WIN!", True, (180, 130, 180)
        )

        skor = font.render(
            "Score : " + str(score), True, SOFT_PINK
        )

        restart = font.render(
            "Press SPACE to Play Again", True, LAVENDER
        )

        quit_text = font.render(
            "Press ESC to Quit", True, SOFT_PINK
        )

        screen.blit(
            title,
            title.get_rect(center=(WIDTH // 2, 190))
        )

        screen.blit(
            skor,
            skor.get_rect(center=(WIDTH // 2, 240))
        )

        screen.blit(
            restart,
            restart.get_rect(center=(WIDTH // 2, 280))
        )

        screen.blit(
            quit_text,
            quit_text.get_rect(center=(WIDTH // 2, 310))
        )

        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    return True

                if event.key == pygame.K_ESCAPE:
                    return False

        clock.tick(FPS)


# MENU
def show_menu():
    menu = True

    title_font = pygame.font.SysFont("arial", 45, bold=True)
    button_font = pygame.font.SysFont("arial", 28, bold=True)

    play_button = pygame.Rect(200, 250, 200, 60)
    quit_button = pygame.Rect(200, 330, 200, 60)

    while menu:
        screen.fill((255, 240, 245))

        title = title_font.render(
            "PASTEL BRICK BREAKER", True, (180, 130, 180)
        )
        screen.blit(title, title.get_rect(center=(WIDTH // 2, 150)))

        pygame.draw.rect(screen, (255, 182, 209), play_button, border_radius=20)
        pygame.draw.rect(screen, (220, 198, 255), quit_button, border_radius=20)

        play_text = button_font.render("PLAY", True, WHITE)
        quit_text = button_font.render("QUIT", True, WHITE)

        screen.blit(play_text, play_text.get_rect(center=play_button.center))
        screen.blit(quit_text, quit_text.get_rect(center=quit_button.center))

        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN:
                if play_button.collidepoint(event.pos):
                    menu = False
                elif quit_button.collidepoint(event.pos):
                    pygame.quit()
                    sys.exit()


# MAIN GAME
def main():
    running = True
    lives = 3
    score = 0

    striker = Striker(
        250, HEIGHT - 50, 100, 20, 10, SOFT_PINK
    )

    strikerXFac = 0

    ball = Ball(
        WIDTH // 2, HEIGHT - 150,
        13, 5, BABY_PINK
    )

    blockWidth, blockHeight = 40, 30
    horizontalGap, verticalGap = 20, 15

    listOfBlocks = populateBlocks(
        blockWidth, blockHeight,
        horizontalGap, verticalGap
    )

    while running:
        screen.fill(BLACK)

        # SCORE AND LIVES
        scoreText = font.render(
            "Score : " + str(score),
            True, SOFT_PINK
        )

        livesText = font.render(
            "Lives : " + str(lives),
            True, LAVENDER
        )

        screen.blit(scoreText, (20, HEIGHT - 25))
        screen.blit(livesText, (130, HEIGHT - 25))

        # YOU WIN (semua block habis)
        if not listOfBlocks:
            running = youWin(score)

            if not running:
                break

            lives = 3
            score = 0
            ball.reset()

            striker.posx = 250
            strikerXFac = 0

            listOfBlocks = populateBlocks(
                blockWidth, blockHeight,
                horizontalGap, verticalGap
            )

        # GAME OVER
        if lives <= 0:
            running = gameOver()

            if not running:
                break

            lives = 3
            score = 0
            ball.reset()

            striker.posx = 250
            strikerXFac = 0

            listOfBlocks = populateBlocks(
                blockWidth, blockHeight,
                horizontalGap, verticalGap
            )

        # EVENT HANDLING
        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:

                if event.key == pygame.K_LEFT:
                    strikerXFac = -1

                if event.key == pygame.K_RIGHT:
                    strikerXFac = 1

            if event.type == pygame.KEYUP:

                if event.key in (
                    pygame.K_LEFT,
                    pygame.K_RIGHT
                ):
                    strikerXFac = 0

        # PADDLE COLLISION
        if collisionChecker(
            striker.getRect(), ball.getRect()
        ) and ball.yFac > 0:

            ball.hit()
            paddle_sound.play()

        # BLOCK COLLISION
        for block in listOfBlocks[:]:

            if collisionChecker(
                block.getRect(), ball.getRect()
            ):

                ball.hit()
                block.hit()

                if block.getHealth() <= 0:
                    brick_sound.play()
                    listOfBlocks.remove(block)
                    score += 5

                break

        # UPDATE
        striker.update(strikerXFac)

        lifeLost = ball.update()

        if lifeLost:
            lives -= 1
            life_sound.play()
            ball.reset()

        # DISPLAY
        striker.display()
        ball.display()

        for block in listOfBlocks:
            block.display()

        pygame.display.update()
        clock.tick(FPS)


# RUN GAME
show_menu()
main()
pygame.quit()