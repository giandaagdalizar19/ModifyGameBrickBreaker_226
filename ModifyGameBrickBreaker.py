import math
import random
import tkinter as tk

# Susunan bata per level. Setiap angka = jumlah pukulan untuk menghancurkan

LEVELS = [
    ["22222222",
     "11111111",
     "11111111"],
    ["33333333",
     "22222222",
     "11111111",
     "11111111"],
    ["32323232",
     "23232323",
     "11111111",
     "10101010"],
    ["33333333",
     "30000003",
     "32222223",
     "11111111"],
]

class GameObject:
    def __init__(self, canvas, item):
        self.canvas = canvas
        self.item = item

    def get_position(self):
        return self.canvas.coords(self.item)

    def move(self, x, y):
        self.canvas.move(self.item, x, y)

    def delete(self):
        self.canvas.delete(self.item)


class Ball(GameObject):
    POINTS_PER_HIT = 10          # poin setiap kali bata terkena
    POINTS_BONUS_DESTROY = 10    # bonus saat bata hancur
    MAX_OFFSET = 0.85            # batas sudut pantulan dari paddle
    MIN_OFFSET = 0.10            # supaya bola tidak naik lurus terus

    def __init__(self, canvas, x, y, speed):
        self.radius = 10
        self.direction = [1.0, -1.0]
        self.speed = speed
        item = canvas.create_oval(x - self.radius, y - self.radius,
                                  x + self.radius, y + self.radius,
                                  fill='white')
        super().__init__(canvas, item)

    def update(self):
        coords = self.get_position()
        width = self.canvas.winfo_width()
        if coords[0] <= 0:
            self.direction[0] = abs(self.direction[0])
        elif coords[2] >= width:
            self.direction[0] = -abs(self.direction[0])
        if coords[1] <= 0:
            self.direction[1] = abs(self.direction[1])
        x = self.direction[0] * self.speed
        y = self.direction[1] * self.speed
        self.move(x, y)

    def bounce_off_paddle(self, paddle, ball_x):
        # Arah pantulan bergantung pada bagian paddle yang terkena:
        # tengah = lurus ke atas, tepi = miring ke kiri/kanan.
        p = paddle.get_position()
        center = (p[0] + p[2]) / 2
        half = (p[2] - p[0]) / 2
        offset = (ball_x - center) / half
        offset = max(-self.MAX_OFFSET, min(self.MAX_OFFSET, offset))
        if abs(offset) < self.MIN_OFFSET:
            offset = self.MIN_OFFSET if offset >= 0 else -self.MIN_OFFSET
        self.direction[0] = offset
        self.direction[1] = -math.sqrt(1 - offset * offset)

    def collide(self, game_objects):
        coords = self.get_position()
        x = (coords[0] + coords[2]) * 0.5

        paddle = next((o for o in game_objects if isinstance(o, Paddle)),
                      None)
        if paddle is not None:
            # Hanya memantul jika bola sedang turun (cegah pantulan ganda)
            if self.direction[1] > 0:
                self.bounce_off_paddle(paddle, x)
        elif len(game_objects) > 1:
            self.direction[1] *= -1
        elif len(game_objects) == 1:
            coords = game_objects[0].get_position()
            if x > coords[2]:
                self.direction[0] = abs(self.direction[0])
            elif x < coords[0]:
                self.direction[0] = -abs(self.direction[0])
            else:
                self.direction[1] *= -1

        points = 0
        destroyed = []   # posisi tengah bata yang hancur (untuk power-up)
        for game_object in game_objects:
            if isinstance(game_object, Brick):
                b = game_object.get_position()
                center = ((b[0] + b[2]) / 2, (b[1] + b[3]) / 2)
                points += Ball.POINTS_PER_HIT
                if game_object.hit():
                    points += Ball.POINTS_BONUS_DESTROY
                    destroyed.append(center)
        return points, destroyed


class Paddle(GameObject):
    DEFAULT_WIDTH = 80

    def __init__(self, canvas, x, y):
        self.width = self.DEFAULT_WIDTH
        self.height = 10
        self.ball = None
        item = canvas.create_rectangle(x - self.width / 2,
                                       y - self.height / 2,
                                       x + self.width / 2,
                                       y + self.height / 2,
                                       fill='yellow')
        super().__init__(canvas, item)

    def set_ball(self, ball):
        self.ball = ball

    def reset(self, x, y):
        self.canvas.coords(self.item,
                           x - self.width / 2, y - self.height / 2,
                           x + self.width / 2, y + self.height / 2)

    def set_width(self, width):
        # Ubah lebar paddle dengan titik tengah tetap
        coords = self.get_position()
        center = (coords[0] + coords[2]) / 2
        canvas_width = float(self.canvas.cget('width'))
        self.width = width
        left = max(0, min(canvas_width - width, center - width / 2))
        self.canvas.coords(self.item, left, coords[1],
                           left + width, coords[3])

    def move(self, offset):
        coords = self.get_position()
        width = self.canvas.winfo_width()
        if coords[0] + offset >= 0 and coords[2] + offset <= width:
            super().move(offset, 0)
            if self.ball is not None:
                self.ball.move(offset, 0)


class Brick(GameObject):
    COLORS = {1: 'red', 2: 'dodgerblue', 3: 'black'}

    def __init__(self, canvas, x, y, hits):
        self.width = 75
        self.height = 20
        self.hits = hits
        color = Brick.COLORS[hits]
        item = canvas.create_rectangle(x - self.width / 2,
                                       y - self.height / 2,
                                       x + self.width / 2,
                                       y + self.height / 2,
                                       fill=color, tags='brick')
        super().__init__(canvas, item)

    def hit(self):
        """Kurangi sisa pukulan. Mengembalikan True jika bata hancur."""
        self.hits -= 1
        if self.hits == 0:
            self.delete()
            return True
        self.canvas.itemconfig(self.item, fill=Brick.COLORS[self.hits])
        return False


POWERUP_TYPES = {
    'wide':   {'color': 'limegreen', 'label': 'W',  'name': 'Wide',  'weight': 3},
    'slow':   {'color': 'orange',    'label': 'S',  'name': 'Slow',  'weight': 3},
    'double': {'color': 'gold',      'label': 'x2', 'name': 'x2',    'weight': 3},
    'life':   {'color': 'hotpink',   'label': '+1', 'name': 'Life',  'weight': 1},
}


