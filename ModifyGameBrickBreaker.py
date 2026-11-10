import math
import random
import tkinter as tk

# Susunan bata per level. Setiap angka = jumlah pukulan untuk menghancurkan
# bata (0 = kosong). 8 kolom per baris. Setelah level terakhir, susunan
# diulang dari awal tetapi bola makin cepat.
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


class PowerUp(GameObject):
    WIDTH = 36
    HEIGHT = 16
    FALL_SPEED = 5

    def __init__(self, canvas, x, y, kind):
        self.kind = kind
        info = POWERUP_TYPES[kind]
        item = canvas.create_rectangle(x - self.WIDTH / 2,
                                       y - self.HEIGHT / 2,
                                       x + self.WIDTH / 2,
                                       y + self.HEIGHT / 2,
                                       fill=info['color'], outline='black')
        self.label = canvas.create_text(x, y, text=info['label'],
                                        font=('Arial', 9, 'bold'))
        super().__init__(canvas, item)

    def update(self):
        self.move(0, self.FALL_SPEED)

    def move(self, x, y):
        super().move(x, y)
        self.canvas.move(self.label, x, y)

    def delete(self):
        super().delete()
        self.canvas.delete(self.label)


class Game(tk.Frame):
    PADDLE_Y = 326
    START_LIVES = 3
    BASE_SPEED = 12
    SPEED_STEP = 1.5
    MAX_SPEED = 18
    MAX_LIVES = 5
    DROP_CHANCE = 0.25            # peluang bata hancur menjatuhkan power-up
    EFFECT_FRAMES = 200           # 200 frame x 50 ms = 10 detik
    WIDE_PADDLE_WIDTH = 120
    SLOW_FACTOR = 0.7

    def __init__(self, master):
        super().__init__(master)
        self.width = 610
        self.height = 400
        self.canvas = tk.Canvas(self, bg='lightskyblue',
                                width=self.width,
                                height=self.height,
                                highlightthickness=0)
        self.canvas.pack()
        self.pack()

        self.items = {}
        self.ball = None
        self.messages = []
        self.after_id = None
        self.state = 'ready'   # ready | playing | between | over
        self.lives = self.START_LIVES
        self.score = 0
        self.level = 1
        self.hud = None
        self.score_hud = None
        self.level_hud = None
        self.effects_hud = None
        self.powerups = []
        self.effects = {}      # jenis efek -> sisa frame

        self.paddle = Paddle(self.canvas, self.width / 2, self.PADDLE_Y)
        self.items[self.paddle.item] = self.paddle

        self.draw_text(self.width / 2, 385,
                       'Arrows: move  |  Space: start  |  R: restart', 10)
        self.effects_hud = self.draw_text(self.width / 2, 365, '', 10)

        self.canvas.focus_set()
        self.canvas.bind('<Left>', lambda _: self.move_paddle(-10))
        self.canvas.bind('<Right>', lambda _: self.move_paddle(10))
        self.canvas.bind('<r>', lambda _: self.new_game())
        self.canvas.bind('<R>', lambda _: self.new_game())

        self.new_game()

    # ---------- pengaturan game ----------

    def new_game(self):
        """Mulai ulang dari awal: skor, nyawa, level, dan bata."""
        self.cancel_pending()
        self.canvas.unbind('<space>')
        self.clear_messages()
        self.clear_bricks()
        self.lives = self.START_LIVES
        self.score = 0
        self.level = 1
        self.build_bricks()
        self.paddle.reset(self.width / 2, self.PADDLE_Y)
        self.update_score_text()
        self.update_level_text()
        self.setup_game()

    def next_level(self):
        self.level += 1
        self.clear_messages()
        self.clear_bricks()
        self.build_bricks()
        self.paddle.reset(self.width / 2, self.PADDLE_Y)
        self.update_level_text()
        self.setup_game()

    def setup_game(self):
        self.state = 'ready'
        self.clear_powerups()
        self.reset_effects()
        self.add_ball()
        self.update_lives_text()
        self.show_message('Press Space to start')
        self.canvas.bind('<space>', lambda _: self.start_game())

    def start_game(self):
        self.canvas.unbind('<space>')
        self.clear_messages()
        self.paddle.ball = None
        self.state = 'playing'
        self.game_loop()

    def current_speed(self):
        speed = self.BASE_SPEED + (self.level - 1) * self.SPEED_STEP
        return min(speed, self.MAX_SPEED)

    def cancel_pending(self):
        if self.after_id is not None:
            self.after_cancel(self.after_id)
            self.after_id = None

    def move_paddle(self, offset):
        if self.state != 'over':
            self.paddle.move(offset)

    # ---------- objek ----------

    def add_ball(self):
        if self.ball is not None:
            self.ball.delete()
        paddle_coords = self.paddle.get_position()
        x = (paddle_coords[0] + paddle_coords[2]) * 0.5
        self.ball = Ball(self.canvas, x, 310, self.current_speed())
        self.paddle.set_ball(self.ball)

    def add_brick(self, x, y, hits):
        brick = Brick(self.canvas, x, y, hits)
        self.items[brick.item] = brick

    def build_bricks(self):
        layout = LEVELS[(self.level - 1) % len(LEVELS)]
        for row_index, row in enumerate(layout):
            y = 50 + row_index * 20
            for col, ch in enumerate(row):
                hits = int(ch)
                if hits:
                    self.add_brick(5 + col * 75 + 37.5, y, hits)

    def clear_bricks(self):
        for item_id in list(self.items):
            if isinstance(self.items[item_id], Brick):
                self.canvas.delete(item_id)
                del self.items[item_id]

    # ---------- teks ----------

    def draw_text(self, x, y, text, size=40):
        # 'Forte' hanya ada di Windows; 'Arial' lebih aman lintas platform
        font = ('Arial', size, 'bold')
        return self.canvas.create_text(x, y, text=text, font=font)

    def show_message(self, text, dy=0, size=40):
        item = self.draw_text(300, 200 + dy, text, size)
        self.messages.append(item)

    def clear_messages(self):
        for item in self.messages:
            self.canvas.delete(item)
        self.messages = []

    def update_lives_text(self):
        text = 'Lives: %s' % self.lives
        if self.hud is None:
            self.hud = self.draw_text(50, 20, text, 15)
        else:
            self.canvas.itemconfig(self.hud, text=text)

    def update_score_text(self):
        text = 'Score: %s' % self.score
        if self.score_hud is None:
            self.score_hud = self.draw_text(self.width - 70, 20, text, 15)
        else:
            self.canvas.itemconfig(self.score_hud, text=text)

    def update_level_text(self):
        text = 'Level %s' % self.level
        if self.level_hud is None:
            self.level_hud = self.draw_text(self.width / 2, 20, text, 15)
        else:
            self.canvas.itemconfig(self.level_hud, text=text)

    # ---------- power-up ----------

    def score_multiplier(self):
        return 2 if 'double' in self.effects else 1

    def maybe_drop_powerup(self, x, y):
        if random.random() < self.DROP_CHANCE:
            kinds = list(POWERUP_TYPES)
            weights = [POWERUP_TYPES[k]['weight'] for k in kinds]
            kind = random.choices(kinds, weights=weights)[0]
            self.powerups.append(PowerUp(self.canvas, x, y, kind))

    def update_powerups(self):
        for p in self.powerups:
            p.update()
        caught = set(self.canvas.find_overlapping(
            *self.paddle.get_position()))
        for p in list(self.powerups):
            if p.item in caught:
                self.apply_powerup(p.kind)
                p.delete()
                self.powerups.remove(p)
            elif p.get_position()[1] > self.height:
                p.delete()
                self.powerups.remove(p)

    def apply_powerup(self, kind):
        if kind == 'life':
            self.lives = min(self.lives + 1, self.MAX_LIVES)
            self.update_lives_text()
            return
        self.effects[kind] = self.EFFECT_FRAMES   # ambil lagi = perpanjang
        if kind == 'wide':
            self.paddle.set_width(self.WIDE_PADDLE_WIDTH)
        elif kind == 'slow':
            self.ball.speed = self.current_speed() * self.SLOW_FACTOR
        self.update_effects_text()

    def end_effect(self, kind):
        if kind == 'wide':
            self.paddle.set_width(Paddle.DEFAULT_WIDTH)
        elif kind == 'slow':
            self.ball.speed = self.current_speed()

    def update_effects(self):
        for kind in list(self.effects):
            self.effects[kind] -= 1
            if self.effects[kind] <= 0:
                del self.effects[kind]
                self.end_effect(kind)
        self.update_effects_text()

    def reset_effects(self):
        self.effects = {}
        self.paddle.set_width(Paddle.DEFAULT_WIDTH)
        self.update_effects_text()

    def clear_powerups(self):
        for p in self.powerups:
            p.delete()
        self.powerups = []

    def update_effects_text(self):
        parts = ['%s %ds' % (POWERUP_TYPES[k]['name'], math.ceil(f * 0.05))
                 for k, f in self.effects.items()]
        self.canvas.itemconfig(self.effects_hud, text='   '.join(parts))

    # ---------- loop utama ----------

    def game_loop(self):
        self.check_collisions()
        num_bricks = len(self.canvas.find_withtag('brick'))
        if num_bricks == 0:
            self.ball.speed = 0
            self.clear_powerups()
            self.state = 'between'
            self.show_message('Level %s cleared!' % self.level)
            self.show_message('Score: %s' % self.score, 50, 20)
            self.after_id = self.after(1500, self.next_level)
        elif self.ball.get_position()[3] >= self.height:
            self.ball.speed = 0
            self.clear_powerups()
            self.lives -= 1
            self.update_lives_text()
            if self.lives <= 0:
                self.state = 'over'
                self.show_message('Game Over!')
                self.show_message('Final Score: %s' % self.score, 50, 20)
                self.show_message('Press R to restart', 85, 15)
            else:
                self.state = 'between'
                self.after_id = self.after(1000, self.setup_game)
        else:
            self.update_powerups()
            self.update_effects()
            self.ball.update()
            self.after_id = self.after(50, self.game_loop)

    def check_collisions(self):
        ball_coords = self.ball.get_position()
        items = self.canvas.find_overlapping(*ball_coords)
        objects = [self.items[x] for x in items if x in self.items]
        points, destroyed = self.ball.collide(objects)
        for x, y in destroyed:
            self.maybe_drop_powerup(x, y)
        if points:
            self.score += points * self.score_multiplier()
            self.update_score_text()


if __name__ == '__main__':
    root = tk.Tk()
    root.title('Hello, Jarvis!')
    game = Game(root)
    game.mainloop()