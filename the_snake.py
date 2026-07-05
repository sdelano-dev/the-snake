import pygame
from random import choice, randint


# CONSTANTS
# Screen constants:
GRID_SIZE = 20
SCREEN_WIDTH, SCREEN_HEIGHT = 640, 480
SCREEN_CENTER_X, SCREEN_CENTER_Y = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2
GRID_WIDTH, GRID_HEIGHT = SCREEN_WIDTH // GRID_SIZE, SCREEN_HEIGHT // GRID_SIZE

# Move constants:
UP, DOWN, LEFT, RIGHT = (0, -1), (0, 1), (-1, 0), (1, 0)

# Keys for use in handle_keys()
# And for randomize the choice of direction upon restart.
KEY_TO_DIR = {
    pygame.K_UP: UP,
    pygame.K_DOWN: DOWN,
    pygame.K_LEFT: LEFT,
    pygame.K_RIGHT: RIGHT,
}
# Dictionary for not walking backwards.
REVERSED_KEY = {
    UP: DOWN,
    DOWN: UP,
    LEFT: RIGHT,
    RIGHT: LEFT,
}

# Colors constants:
BOARD_BACKGROUND_COLOR = (0, 0, 0)
LINE_BACKGROUND_COLOR = (15, 30, 50)
BORDER_COLOR = (93, 216, 228)
APPLE_COLOR = (255, 0, 0)
SNAKE_COLOR = (0, 255, 0)

# Speed:
SPEED = 10

pygame.display.set_caption('Змейка')
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), 0, 32)
clock = pygame.time.Clock()


class Board:
    """Creating a board, segment, lighting and other game details."""

    def __init__(self, surface=screen):
        self.surface = surface

    def draw(self):
        """Drawing the board."""
        self.surface.fill(BOARD_BACKGROUND_COLOR)
        for y in range(0, SCREEN_HEIGHT, GRID_SIZE):
            pygame.draw.line(
                self.surface,
                LINE_BACKGROUND_COLOR,
                (0, y),
                (SCREEN_WIDTH, y),
                1
            )
        for x in range(0, SCREEN_WIDTH, GRID_SIZE):
            pygame.draw.line(
                self.surface,
                LINE_BACKGROUND_COLOR,
                (x, 0),
                (x, SCREEN_HEIGHT),
                1
            )

    def draw_segment(
            self,
            position, *,
            bg_color=BOARD_BACKGROUND_COLOR,
            line=False,
            line_color=LINE_BACKGROUND_COLOR
    ):
        """Drawing the one segment."""
        x, y = position
        rect = pygame.Rect(x + 1, y + 1, GRID_SIZE - 2, GRID_SIZE - 2)
        pygame.draw.rect(self.surface, bg_color, rect)
        if line:
            pygame.draw.rect(self.surface, line_color, rect, 1)


class GameObject:
    """Main object class."""

    def __init__(self, board=screen, position=None, body_color=(0, 0, 255)):
        self.board = board
        self.position = position or [SCREEN_CENTER_X, SCREEN_CENTER_Y]
        self.body_color = body_color

    def draw(self):
        """Basic Drawing Method."""
        pass


class Apple(GameObject):
    """Good and bad apple."""

    def __init__(self, board=screen, position=None, body_color=APPLE_COLOR):
        super().__init__(board, position, body_color)

    def randomize_position(self):
        """Randomize apple position."""
        self.position = [
            randint(0, GRID_WIDTH - 1) * GRID_SIZE,
            randint(0, GRID_HEIGHT - 1) * GRID_SIZE
        ]

    def draw(self):
        """Drawing the apple."""
        self.board.draw_segment(
            self.position,
            bg_color=self.body_color,
            line=True,
            line_color=BORDER_COLOR
        )


class Snake(GameObject):
    """Mr. Snake"""

    def __init__(self, board=screen, position=None, body_color=SNAKE_COLOR):
        super().__init__(board, position, body_color)
        self.positions = [self.position]
        self._length = 1
        self.direction = RIGHT
        self._next_direction = None
        self._last = None

    def get_head_position(self):
        """Head position."""
        return self.positions[0]

    def update_direction(self, next_direction):
        """Update snake direction based on keyboard input."""
        if next_direction is None:
            return
        if next_direction != REVERSED_KEY[self.direction]:
            self.direction = next_direction

    def move(self):
        """Move snake with keyboard."""
        x, y = self.positions[0]
        dx, dy = self.direction
        self.positions.insert(
            0,
            [
                (x + dx * GRID_SIZE) % SCREEN_WIDTH,
                (y + dy * GRID_SIZE) % SCREEN_HEIGHT
            ]
        )
        if len(self.positions) > self._length:
            self._last = self.positions[-1]
            self.positions.pop()

    def eat_apple(self, eatable=True):
        """Eat a good or bad apple. Lives increase or decrease."""
        health = 1 if eatable else -1
        self._length += health

    def choise_direction(self):
        """Choise random directory."""
        self.direction = choice(list(KEY_TO_DIR.values()))

    def draw(self):
        """Draw snake head and body."""
        # Body
        for position in self.positions[:-1]:
            self.board.draw_segment(
                position,
                bg_color=self.body_color,
                line=True,
                line_color=BORDER_COLOR
            )

        # Head
        self.board.draw_segment(
            self.positions[0],
            bg_color=self.body_color,
            line=True,
            line_color=BORDER_COLOR
        )

        # Remove last segment
        if self._last:
            self.board.draw_segment(self._last)

    def reset(self):
        """Reset on collision with itself."""
        self._length = 1
        self.positions = [self.position]


def handle_keys():
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
                next_direction = KEY_TO_DIR.get(event.key)
    return quit_request, next_direction


def main():
    """Start the programm"""
    pygame.init()

    board = Board()
    apple = Apple(board)
    apple.randomize_position()
    snake = Snake(board, [SCREEN_CENTER_X, SCREEN_CENTER_Y])

    board.draw()

    running = True
    while running:
        quit_request, next_direction = handle_keys()
        if quit_request:
            running = False
            continue

        snake.update_direction(next_direction)
        snake.move()

        # The snake eats itself.
        if snake.get_head_position() in snake.positions[1:]:
            snake.reset()
            board.draw()
            continue

        # The snake eats apple.
        if snake.get_head_position() == apple.position:
            apple.randomize_position()
            snake.eat_apple()

        apple.draw()
        snake.draw()

        pygame.display.update()
        clock.tick(SPEED)

    pygame.quit()


if __name__ == '__main__':
    main()
