"""Игра "Изгиб питона" на pygame.

Помимо основной логики, реализовал:
- Яблоко не появляется на змейке.
- Есть ускорение при зажатии клавиши.
- Скорость увеличивается после каждых 10 съеденных яблок.
- Реализована отрисовка счёта.
- Есть хорошие и плохие яблоки.
- Плохие яблоки укорачивают хвост.
- Яблоки исчезают по таймеру с разным временем жизни.
- Выход по ESC.
"""

from random import choice, choices, randint

import pygame

GRID_SIZE = 20
SCREEN_WIDTH, SCREEN_HEIGHT = 640, 480
GRID_WIDTH, GRID_HEIGHT = SCREEN_WIDTH // GRID_SIZE, SCREEN_HEIGHT // GRID_SIZE
GRID_CENTER_X, GRID_CENTER_Y = GRID_WIDTH // 2, GRID_HEIGHT // 2

UP, DOWN, LEFT, RIGHT = (0, -1), (0, 1), (-1, 0), (1, 0)

KEYS = {
    (pygame.K_UP, LEFT): UP,
    (pygame.K_UP, RIGHT): UP,

    (pygame.K_DOWN, LEFT): DOWN,
    (pygame.K_DOWN, RIGHT): DOWN,

    (pygame.K_LEFT, UP): LEFT,
    (pygame.K_LEFT, DOWN): LEFT,

    (pygame.K_RIGHT, UP): RIGHT,
    (pygame.K_RIGHT, DOWN): RIGHT,
}

BOARD_BACKGROUND_COLOR = (0, 0, 0)
LINE_BACKGROUND_COLOR = (15, 30, 50)
SCORE_COLOR = (0, 0, 30)
BORDER_COLOR = (100, 100, 100)
APPLE_COLOR = (240, 180, 0)
BAD_APPLE_COLOR = (120, 40, 200)
SNAKE_COLOR = (255, 255, 255)

SPEED = 5

pygame.init()
pygame.display.set_caption('Изгиб питона')
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), 0, 32)
clock = pygame.time.Clock()


class Board:
    """Creating a board, segment, account keeping, rendering light."""

    def __init__(self, surface=screen):
        self.surface = surface
        self.rest_speed = SPEED
        self.reset_score()

    def draw(self):
        """Drawing the board."""
        self.surface.fill(BOARD_BACKGROUND_COLOR)
        for y in range(0, SCREEN_HEIGHT, GRID_SIZE):
            pygame.draw.line(
                self.surface,
                LINE_BACKGROUND_COLOR,
                (0, y),
                (SCREEN_WIDTH, y),
                1,
            )
        for x in range(0, SCREEN_WIDTH, GRID_SIZE):
            pygame.draw.line(
                self.surface,
                LINE_BACKGROUND_COLOR,
                (x, 0),
                (x, SCREEN_HEIGHT),
                1,
            )

    def draw_segment(
            self,
            position, *,
            bg_color=BOARD_BACKGROUND_COLOR,
            line=False,
            line_color=LINE_BACKGROUND_COLOR,
    ):
        """Drawing the one segment."""
        col, row = position
        x = col * GRID_SIZE
        y = row * GRID_SIZE
        rect = pygame.Rect(x + 1, y + 1, GRID_SIZE - 2, GRID_SIZE - 2)
        pygame.draw.rect(self.surface, bg_color, rect)
        if line:
            pygame.draw.rect(self.surface, line_color, rect, 1)

    def update_score(self, eatable=1):
        """Counting the score and drawing it."""
        old_score = self.score
        self.score = max(0, self.score + eatable)
        if eatable > 0:
            x = old_score % GRID_WIDTH
            y = old_score // GRID_WIDTH
            self.draw_segment((x, y), bg_color=self.score_color)

            score_step = self.score % 10
            self.speed_step = self.score // 10
            self.speed = self.rest_speed + self.speed_step

            fit_score_step = fit(score_step, 0, 5, 0, 1)
            fit_speed_step = fit(self.speed_step + 1, 0, 9, 0, .5) + .25
            color_step = fit(
                fit_score_step * fit_speed_step,
                0, 1, 0, 255,
            )

            self.score_color = color_correct(SCORE_COLOR, color_step)
            self.score_info[(x, y)] = self.score_color

        elif eatable < 0 and old_score > 0:
            x = (old_score - 1) % GRID_WIDTH
            y = (old_score - 1) // GRID_WIDTH
            self.draw_segment((x, y), bg_color=BOARD_BACKGROUND_COLOR)

            self.score_info.pop((x, y), None)
            self.speed_step = self.score // 10
            self.speed = self.rest_speed + self.speed_step

            score_step = self.score % 10
            fit_score_step = fit(score_step, 0, 5, 0, 1)
            fit_speed_step = fit(self.speed_step + 1, 0, 9, 0, .5) + .25
            color_step = fit(
                fit_score_step * fit_speed_step,
                0, 1, 0, 255,
            )

            self.score_color = color_correct(SCORE_COLOR, color_step)

    def acceleration(self, key_pressed):
        """Acceleration while pressing the key."""
        base_speed = self.rest_speed + self.speed_step
        self.speed = base_speed + 5 if key_pressed else base_speed

    def get_speed(self):
        """Return game speeed."""
        return self.speed

    def get_score_info(self):
        """Dict from score_position and score color."""
        return self.score_info

    def reset_score(self):
        """Reset score if snake collision with itself."""
        self.score = 0
        self.speed_step = 0
        self.speed = self.rest_speed
        self.score_color = SCORE_COLOR
        self.score_info = dict()


class GameObject:
    """Main object class."""

    def __init__(self, board=screen, position=None, body_color=(0, 0, 255)):
        self.board = board
        self.position = position or (GRID_CENTER_X, GRID_CENTER_Y)
        self.body_color = body_color

    def draw(self):
        """Basic Drawing Method."""
        pass


class Apple(GameObject):
    """Good and bad apple."""

    def __init__(
            self,
            board=screen,
            position=None,
            collision_positions=None,
            body_color=APPLE_COLOR,
    ):
        super().__init__(board, position, body_color)
        self.apple_type = 'good'
        self.time = 0
        self._last_position = None
        self.randomize_position(collision_positions)

    def randomize_position(self, collision_positions=None):
        """Randomize apple position."""
        collision_positions = set(collision_positions or [])
        self._last_position = self.position
        while True:
            position = (
                randint(0, GRID_WIDTH - 1),
                randint(0, GRID_HEIGHT - 1),
            )
            if position not in collision_positions:
                self.position = position
                return

    def randomize_apple_type(self):
        """Randomize apple."""
        apple_types = ['good', 'bad']
        weight = .7
        weights = [weight, 1 - weight]
        self.apple_type = choices(apple_types, weights)[0]
        self.body_color = (
            BAD_APPLE_COLOR
            if self.apple_type == 'bad'
            else APPLE_COLOR
        )
        self.time = 0

    def timer(self, max_time=10):
        """Timer. How long to show the apple."""
        self.time += 1
        if self.time > max_time:
            self.time = 0
            return True
        return False

    def draw(self):
        """Drawing the apple."""
        self.board.draw_segment(
            self.position,
            bg_color=self.body_color,
            line=True,
            line_color=BORDER_COLOR,
        )

    def get_apple_type(self):
        """Return 1 if apple_type = 'good' and -1 if apple_type = 'bad'"""
        return self.apple_type

    def get_position(self):
        """Apple position."""
        return self.position

    def clear_old(self):
        """Clear previos apple position."""
        if self._last_position is not None:
            bg_color = self.board.get_score_info().get(
                self._last_position, BOARD_BACKGROUND_COLOR
            )
            self.board.draw_segment(self._last_position, bg_color=bg_color)
            self._last_position = None


class Snake(GameObject):
    """Mr. Snake"""

    def __init__(self, board=screen, position=None, body_color=SNAKE_COLOR):
        super().__init__(board, position, body_color)
        self.direction = RIGHT
        self.reset(choise_dir=False)

    def update_direction(self, next_direction):
        """Update snake direction based on keyboard input."""
        if next_direction:
            self.direction = next_direction

    def move(self):
        """Move snake with keyboard."""
        self._removed = []

        x, y = self.positions[0]
        dx, dy = self.direction
        self.positions.insert(
            0,
            (
                (x + dx) % GRID_WIDTH,
                (y + dy) % GRID_HEIGHT,
            )
        )
        if len(self.positions) > self._length:
            removed = self.positions.pop()
            self._last = removed
            self._removed.append(removed)

    def eat_apple(self, eatable=1):
        """Eat a good or bad apple. Lives increase or decrease."""
        self._length = max(1, self._length + eatable)

        while len(self.positions) > self._length:
            removed = self.positions.pop()
            self._last = removed
            self._removed.append(removed)

    def choise_direction(self):
        """Choise random directory."""
        self.direction = choice(tuple(set(KEYS.values())))

    def draw(self, background_color):
        """Draw snake head and body."""
        self.board.draw_segment(
            self.positions[0],
            bg_color=self.body_color,
            line=True,
            line_color=BORDER_COLOR,
        )
        for pos in self._removed:
            self.board.draw_segment(pos, bg_color=background_color)
        self._removed = []

    def get_head_position(self):
        """Head position."""
        return self.positions[0]

    def get_last_position(self):
        """Last position."""
        return self._last

    def get_positions(self):
        """All snake positions."""
        return self.positions

    def get_direction(self):
        """Current direction"""
        return self.direction

    def reset(self, choise_dir=True):
        """Reset on collision with itself."""
        self.positions = [self.position]
        self._length = 1
        self._last = None
        self._removed = []
        if choise_dir:
            self.choise_direction()


def fit(value, omin, omax, nmin, nmax):
    """Fit value by min/max"""
    if omax == omin:
        raise ValueError('omin and omax should not be equal.')
    normalize = (value - omin) / (omax - omin)
    return nmin + normalize * (nmax - nmin)


def clamp(value, min_value=0, max_value=255):
    """Clamp value."""
    return max(min_value, min(max_value, int(value)))


def color_correct(color, step):
    """Correct color"""
    return tuple(clamp(c + step) for c in color)


def handle_keys(direction):
    """Keyboard input."""
    quit_request = False
    next_direction = None
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            quit_request = True
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                quit_request = True
            else:
                next_direction = KEYS.get((event.key, direction))
    keys = pygame.key.get_pressed()
    key_pressed = any(keys[key[0]] for key in KEYS)
    return quit_request, next_direction, key_pressed


def main():
    """Start the programm"""
    board = Board()
    snake = Snake(board, (GRID_CENTER_X, GRID_CENTER_Y))
    apple = Apple(board, collision_positions=snake.get_positions())

    board.draw()

    running = True
    while running:
        quit_request, next_direction, key_pressed = handle_keys(
            snake.get_direction()
        )
        if quit_request:
            running = False
            continue

        snake.update_direction(next_direction)
        snake.move()

        if apple.get_apple_type() == 'good':
            if apple.timer(50):
                apple.randomize_position(snake.get_positions())
                apple.clear_old()
                apple.randomize_apple_type()
        else:
            if apple.timer(15):
                apple.randomize_position(snake.get_positions())
                apple.clear_old()
                apple.randomize_apple_type()

        if snake.get_head_position() in snake.positions[1:]:
            snake.reset()
            board.reset_score()
            board.draw()
        elif snake.get_head_position() == apple.position:
            apple_effect = 1 if apple.get_apple_type() == 'good' else -1
            snake.eat_apple(eatable=apple_effect)
            board.update_score(eatable=apple_effect)
            apple.randomize_position(snake.get_positions())
            apple.clear_old()
            apple.randomize_apple_type()

        board_color = board.get_score_info().get(
            snake.get_last_position(),
            BOARD_BACKGROUND_COLOR,
        )

        apple.draw()
        snake.draw(board_color)
        board.acceleration(key_pressed)

        pygame.display.update()
        clock.tick(board.get_speed())

    pygame.quit()


if __name__ == '__main__':
    main()
