import pygame
from random import choice, choices, randint


# CONSTANTS
# Screen constants:
GRID_SIZE = 20
SCREEN_WIDTH, SCREEN_HEIGHT = 640, 480
GRID_WIDTH, GRID_HEIGHT = SCREEN_WIDTH // GRID_SIZE, SCREEN_HEIGHT // GRID_SIZE
GRID_CENTER_X, GRID_CENTER_Y = GRID_WIDTH // 2, GRID_HEIGHT // 2
# Move constants:
UP, DOWN, LEFT, RIGHT = (0, -1), (0, 1), (-1, 0), (1, 0)
# Keys for use in handle_keys()
# and for randomize the choice of direction upon restart:
KEY_TO_DIR = {
    pygame.K_UP: UP,
    pygame.K_DOWN: DOWN,
    pygame.K_LEFT: LEFT,
    pygame.K_RIGHT: RIGHT,
}
# Dictionary for not walking backwards:
REVERSED_KEY = {
    UP: DOWN,
    DOWN: UP,
    LEFT: RIGHT,
    RIGHT: LEFT,
}
# Colors constants:
BOARD_BACKGROUND_COLOR = (0, 0, 0)
LINE_BACKGROUND_COLOR = (15, 30, 50)
SCORE_COLOR = (0, 0, 30)
BORDER_COLOR = (93, 216, 228)
APPLE_COLOR = (255, 0, 0)
BAD_APPLE_COLOR = (155, 40, 60)
SNAKE_COLOR = (0, 255, 0)
# Initial speed:
SPEED = 5

# Pygame setup:
pygame.init()
pygame.display.set_caption('Змейка')
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), 0, 32)
clock = pygame.time.Clock()

# Classes 
class Utils:
    """Various additional tools."""

    @staticmethod
    def fit(value, omin, omax, nmin, nmax):
        """Fit value by min/max"""
        if omax == omin:
            raise ValueError('omin and omax should not be equal.')
        normalize = (value - omin) / (omax - omin)
        return nmin + normalize * (nmax - nmin)
    
    @staticmethod
    def clamp(value, min_value=0, max_value=255):
        """Clamp value."""
        return max(min_value, min(max_value, int(value)))

    @staticmethod
    def color_correct(color, step):
        """Correct color"""
        return tuple(Utils.clamp(c + step) for c in color)
    
class Board:
    """
    Creating a board, segment, account keeping, rendering light.
    
    """
    def __init__(self, surface=screen):
        self.surface = surface
        self.score = 0
        self.score_color = SCORE_COLOR
        self.rest_speed = SPEED
        self.speed = SPEED
        self.score_info = dict()

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
        col, row = position
        x = col * GRID_SIZE
        y = row * GRID_SIZE
        rect = pygame.Rect(x + 1, y + 1, GRID_SIZE - 2, GRID_SIZE - 2)
        pygame.draw.rect(self.surface, bg_color, rect)
        if line:
            pygame.draw.rect(self.surface, line_color, rect, 1)
    
    def update_score(self, eatable=1):
        """Counting the score and drawing it."""
        x = self.score % GRID_WIDTH
        y = self.score // GRID_WIDTH
        self.score += eatable
        if eatable == -1:
            self.draw_segment((x, y), bg_color=BOARD_BACKGROUND_COLOR)
        else:
            self.draw_segment((x, y), bg_color=self.score_color)

            score_step = self.score % 10
            speed_step = self.score // 10
            
            self.speed = self.speed + speed_step

            fit_score_step = Utils.fit(score_step, 0, 5, 0, 1)
            fit_speed_step = Utils.fit(speed_step + 1, 0, 10, 0, .5) + .25
            color_step = Utils.fit(fit_score_step * fit_speed_step, 0, 1, 0, 255)
            color = SCORE_COLOR

            self.score_color = Utils.color_correct(color, color_step) 
            self.score_info[(x, y)] = self.score_color

    def get_score_info(self):
        """Dict from score_position and score color."""
        return self.score_info

    def reset_score(self):
        """Reset score if snake collision with itself."""
        self.score = 0
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

    def __init__(self, board=screen, position=None, body_color=APPLE_COLOR):
        super().__init__(board, position, body_color)
        self.apple_type = 'good'

    def randomize_position(self, collision_positions=None):
        """Randomize apple position."""
        while True:
            self.position = (
                randint(0, GRID_WIDTH - 1),
                randint(0, GRID_HEIGHT - 1)
            )
            if self.position not in collision_positions:
                self.position = self.position
                return
    
    def randomize_apple_type(self):
        """Randomize apple"""
        apple_types = ['good', 'bad']
        weights = [.8, .2]
        self.apple_type = choices(apple_types, weights)[0]
        self.body_color = (
            BAD_APPLE_COLOR
            if self.apple_type == 'bad'
            else APPLE_COLOR
        )

    def draw(self):
        """Drawing the apple."""
        self.board.draw_segment(
            self.position,
            bg_color=self.body_color,
            line=True,
            line_color=BORDER_COLOR
        )

    def get_apple_type(self):
        """Return 1 if apple_type = 'good' and -1 if apple_type = 'bad'"""
        return 1 if self.apple_type == 'good' else -1
    

class Snake(GameObject):
    """Mr. Snake"""

    def __init__(self, board=screen, position=None, body_color=SNAKE_COLOR):
        super().__init__(board, position, body_color)
        self.positions = [self.position]
        self._length = 1
        self.direction = RIGHT
        self._next_direction = None
        self._last = None
        self._apple_count = 0

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
            (
                (x + dx) % GRID_WIDTH,
                (y + dy) % GRID_HEIGHT
            )
        )
        if len(self.positions) > self._length:
            self._last = self.positions[-1]
            self.positions.pop()

    def eat_apple(self, eatable=1):
        """Eat a good or bad apple. Lives increase or decrease."""
        self._length += eatable
        self._apple_count += 1

    def choise_direction(self):
        """Choise random directory."""
        self.direction = choice(list(KEY_TO_DIR.values()))

    def draw(self, background_color):
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
            self.board.draw_segment(self._last, bg_color=background_color)

    def get_head_position(self):
        """Head position."""
        return self.positions[0]
    
    def get_last_position(self):
        """Last position."""
        return self._last
    
    def get_positions(self):
        """All snake positions."""
        return self.positions
    
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
    
    keys = pygame.key.get_pressed()
    key_pressed = None
    for key in KEY_TO_DIR:
        if keys[key]:
            key_pressed = True
    return quit_request, next_direction, key_pressed


def main():
    """Start the programm"""

    board = Board()
    # board_color = BOARD_BACKGROUND_COLOR
    snake = Snake(board, (GRID_CENTER_X, GRID_CENTER_Y))
    apple = Apple(board)
    apple.randomize_position([snake.get_head_position()])

    board.draw()

    running = True
    while running:
        quit_request, next_direction, key_pressed = handle_keys()
        if quit_request:
            running = False
            continue

        snake.update_direction(next_direction)

        

        snake.move()

        # The snake eats itself.
        if snake.get_head_position() in snake.positions[1:]:
            snake.reset()
            board.reset_score()
            board.draw()
            continue
        

            
        # The snake eats apple.
        if snake.get_head_position() == apple.position:
            snake.eat_apple(eatable=apple.get_apple_type())
            apple.randomize_position(snake.get_positions())
            apple.randomize_apple_type()
            board.update_score(eatable=apple.get_apple_type())
        
        board_color = board.get_score_info().get(
            snake.get_last_position(),
            BOARD_BACKGROUND_COLOR
        )

        apple.draw()
        snake.draw(board_color)

        speed = board.speed + 5 if key_pressed else board.speed

        pygame.display.update()
        clock.tick(speed)

    pygame.quit()

if __name__ == '__main__':
    main()
