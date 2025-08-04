import tkinter
from tkinter import font, Canvas, Tk, LEFT, BOTH, TRUE
import time
from copy import deepcopy, copy
from enum import Enum
import random
import json
from datetime import datetime, timedelta

# Settings
DEFAULT_AUTOPLAY = True
DISABLE_DISPLAY = False
GRID_SIZE = 30
MAXROW = 20
MAXCOL = 10
CANVAS_HEIGHT = GRID_SIZE * (4 + MAXROW)
TOP_OFFSET = GRID_SIZE * 6  # Game area moved lower

class Direction(Enum):
    LEFT = -1
    RIGHT = 1

# Model Classes
class BlockBitmap:
    def __init__(self, rows, colour):
        self.rows = rows
        self.colour = colour
        self.size = len(rows)
        self.calculate_bounding_box()

    def str(self):
        txt = ""
        for row in self.rows:
            for tile in row:
                txt += "#" if tile == 1 else "."
            txt += "\n"
        return txt

    def clone(self):
        rows = [list(row) for row in self.rows]
        return BlockBitmap(rows, self.colour)

    def get_copy_of_tiles(self):
        return [tuple(row) for row in self.rows]

    def calculate_bounding_box(self):
        x_min = y_min = self.size
        x_max = y_max = 0
        for _y in range(self.size):
            for _x in range(self.size):
                if self.rows[_y][_x] == 1:
                    x_min = min(x_min, _x)
                    y_min = min(y_min, _y)
                    x_max = max(x_max, _x)
                    y_max = max(y_max, _y)
        self.bounding_box = (x_min, y_min, x_max, y_max)

    def rotate(self, direction):
        newrows = [[0] * self.size for _ in range(self.size)]
        if direction == Direction.RIGHT:
            for _y in range(self.size):
                for _x in range(self.size):
                    newrows[_x][self.size - 1 - _y] = self.rows[_y][_x]
        else:
            for _y in range(self.size):
                for _x in range(self.size):
                    newrows[self.size - 1 - _x][_y] = self.rows[_y][_x]
        self.rows = newrows
        self.calculate_bounding_box()

class IBlock(BlockBitmap):
    def __init__(self):
        BlockBitmap.__init__(self, ((0, 0, 0, 0), (1, 1, 1, 1), (0, 0, 0, 0), (0, 0, 0, 0)), "cyan")

class JBlock(BlockBitmap):
    def __init__(self):
        BlockBitmap.__init__(self, ((1, 0, 0), (1, 1, 1), (0, 0, 0)), "blue")

class LBlock(BlockBitmap):
    def __init__(self):
        BlockBitmap.__init__(self, ((0, 0, 1), (1, 1, 1), (0, 0, 0)), "orange")

class OBlock(BlockBitmap):
    def __init__(self):
        BlockBitmap.__init__(self, ((0, 0, 0, 0), (0, 1, 1, 0), (0, 1, 1, 0), (0, 0, 0, 0)), "yellow")

class SBlock(BlockBitmap):
    def __init__(self):
        BlockBitmap.__init__(self, ((0, 1, 1), (1, 1, 0), (0, 0, 0)), "green")

class TBlock(BlockBitmap):
    def __init__(self):
        BlockBitmap.__init__(self, ((0, 1, 0), (1, 1, 1), (0, 0, 0)), "purple")

class ZBlock(BlockBitmap):
    def __init__(self):
        BlockBitmap.__init__(self, ((1, 1, 0), (0, 1, 1), (0, 0, 0)), "red")

class Block:
    def __init__(self, block_type, x, y, falling):
        self.__x = x
        self.__y = y
        self.__angle = 0
        self.__type = block_type
        self.__falling = falling
        self.__bitmap = {
            "I": IBlock, "J": JBlock, "L": LBlock, "O": OBlock,
            "S": SBlock, "T": TBlock, "Z": ZBlock
        }[block_type]()

    @property
    def position(self):
        return (self.__x, self.__y)

    @property
    def angle(self):
        return self.__angle

    @property
    def bitmap(self):
        return self.__bitmap

    @property
    def colour(self):
        return self.__bitmap.colour

    @property
    def type(self):
        return self.__type

    @property
    def bounding_box(self):
        return self.__bitmap.bounding_box

    def is_falling(self):
        return self.__falling

    def fall(self):
        self.__falling = True

    def move(self, blockfield, direction):
        _x = self.__x + direction.value
        (xmin, _, xmax, _) = self.bounding_box
        if _x + xmin < 0 or _x + xmax >= MAXCOL:
            return False
        if blockfield.collision(self, direction.value, 0):
            return False
        self.__x = _x
        return True

    def rotate(self, blockfield, direction):
        oldbitmap = self.__bitmap
        newbitmap = self.__bitmap.clone()
        orig_angle = self.__angle
        orig_x = self.__x
        orig_y = self.__y
        self.__angle = (self.__angle + direction.value) % 4
        newbitmap.rotate(direction)
        self.__bitmap = newbitmap
        (xmin, _, xmax, _) = self.bounding_box
        while self.__x + xmin < 0:
            self.__x += 1
        while self.__x + xmax >= MAXCOL:
            self.__x -= 1
        if blockfield.collision(self, 0, 0):
            self.__bitmap = oldbitmap
            self.__x = orig_x
            self.__y = orig_y
            self.__angle = orig_angle

    def drop(self, blockfield):
        (_, block_y) = self.position
        (_, _, _, ymax) = self.bounding_box
        if (block_y + ymax == MAXROW - 1) or blockfield.collision(self, 0, 1):
            score, cleared_rows = blockfield.land(self)
            return (True, score, cleared_rows)
        self.__y += 1
        return (False, 0, [])

    def get_copy_of_tiles(self):
        return self.__bitmap.get_copy_of_tiles()

class BlockField:
    def __init__(self):
        self.__tiles = [[0] * MAXCOL for _ in range(MAXROW)]

    @property
    def bitmap(self):
        return self.__tiles

    def get_copy_of_tiles(self):
        return [tuple(row) for row in self.__tiles]

    def collision(self, block, xoffset, yoffset):
        (block_x, block_y) = block.position
        (xmin, ymin, xmax, ymax) = block.bounding_box
        if ymax + block_y + yoffset >= MAXROW or xmax + block_x + xoffset >= MAXCOL:
            return True
        bitmap = block.bitmap.rows
        for _y in range(ymin, ymax + 1):
            for _x in range(xmin, xmax + 1):
                if bitmap[_y][_x] != 0 and self.__tiles[block_y + _y + yoffset][block_x + _x + xoffset] != 0:
                    return True
        return False

    def land(self, block):
        (block_x, block_y) = block.position
        bitmap = block.bitmap.rows
        (xmin, ymin, xmax, ymax) = block.bounding_box
        for _y in range(ymin, ymax + 1):
            for _x in range(xmin, xmax + 1):
                if bitmap[_y][_x] != 0:
                    self.__tiles[block_y + _y][block_x + _x] = block.colour
        return self.check_full_rows()

    def drop_row(self, row_to_drop):
        for _y in range(row_to_drop, 0, -1):
            self.__tiles[_y] = self.__tiles[_y - 1]
        self.__tiles[0] = [0] * MAXCOL

    def check_full_rows(self):
        scores = [0, 100, 400, 800, 1600]
        rows_dropped = 0
        cleared_rows = []
        for _y in range(MAXROW):
            if all(self.__tiles[_y][_x] != 0 for _x in range(MAXCOL)):
                cleared_rows.append(_y)
                rows_dropped += 1
        for row in cleared_rows:
            self.drop_row(row)
        return scores[rows_dropped], cleared_rows

class Model:
    def __init__(self, controller):
        self.__controller = controller
        self.blocktypes = ["I", "J", "L", "O", "S", "T", "Z"]
        self.__falling_block = None
        self.__is_dummy = False
        self.__blockfield = None
        self.__next_block = None
        self.__score = 0
        self.__last_drop = 0
        self.__moves = 0
        self.__rotates = 0
        self.__autoplay = False
        self.__move_time = 0.5
        self.__score_added = False

    def start(self):
        self.restart()

    def clone(self, is_dummy):
        newmodel = copy(self)
        newmodel.copy_in_state(
            is_dummy,
            deepcopy(self.__blockfield),
            deepcopy(self.__falling_block),
            deepcopy(self.__next_block),
        )
        return newmodel

    def copy_in_state(self, is_dummy, blockfield, falling_block, next_block):
        self.__is_dummy = is_dummy
        self.__blockfield = blockfield
        self.__falling_block = falling_block
        self.__next_block = next_block

    @property
    def blockfield(self):
        return self.__blockfield

    @property
    def falling_block_position(self):
        return self.__falling_block.position if self.__falling_block else (0, 0)

    @property
    def falling_block_angle(self):
        return self.__falling_block.angle if self.__falling_block else 0

    @property
    def falling_block_type(self):
        return self.__falling_block.type if self.__falling_block else ""

    @property
    def next_block_type(self):
        return self.__next_block.type if self.__next_block else ""

    def get_falling_block_tiles(self):
        return self.__falling_block.get_copy_of_tiles() if self.__falling_block else []

    def get_next_block_tiles(self):
        return self.__next_block.get_copy_of_tiles() if self.__next_block else []

    def get_copy_of_tiles(self):
        return self.__blockfield.get_copy_of_tiles() if self.__blockfield else []

    def init_score(self):
        self.__score = 0
        self.__score_added = False
        if not self.__is_dummy:
            self.__controller.update_score(0)

    @property
    def score(self):
        return self.__score

    @property
    def is_dummy(self):
        return self.__is_dummy

    def __create_new_block(self, falling):
        block_x = MAXCOL // 2 - 2
        block_y = 0
        blocknum = self.__controller.get_random_blocknum()
        blocktype = self.blocktypes[blocknum]
        return Block(blocktype, block_x, block_y, falling)

    def __check_falling_block(self, now):
        if not self.__falling_block:
            return False, False
        if (now - self.__last_drop > self.__move_time) or self.__is_dummy:
            self.__score += 1
            (landed, scorechange, cleared_rows) = self.__falling_block.drop(self.__blockfield)
            self.__last_drop = now
            if landed:
                (_, block_y) = self.__falling_block.position
                if block_y == 0:
                    self.__game_over()
                else:
                    self.__score += scorechange
                    if cleared_rows:
                        self.__controller.update_blockfield(self.__blockfield)
                    if not self.__is_dummy:
                        self.__controller.update_score(self.__score)
                    self.__start_next_block()
            return True, landed
        return False, False

    def __start_next_block(self):
        if not self.__is_dummy and self.__falling_block:
            self.__controller.unregister_block(self.__falling_block)
        self.__falling_block = self.__next_block
        if self.__falling_block:
            self.__falling_block.fall()
        self.__next_block = self.__create_new_block(False)
        if not self.__is_dummy:
            self.__controller.register_block(self.__next_block)
            self.__controller.update_blockfield(self.__blockfield)
            self.__controller.update_score(self.__score)

    def move(self, direction):
        if not self.__falling_block:
            return False
        self.__moves += 1
        if self.__moves > 1 and self.__autoplay:
            print("Illegal move - can't move twice per update")
            return False
        return self.__falling_block.move(self.__blockfield, direction)

    def rotate(self, direction):
        if not self.__falling_block:
            return False
        self.__rotates += 1
        if self.__rotates > 1 and self.__autoplay:
            print("Illegal rotate - can't rotate twice per update")
            return False
        return self.__falling_block.rotate(self.__blockfield, direction)

    def reset_counts(self):
        self.__moves = 0
        self.__rotates = 0

    def drop_block(self):
        if not self.__falling_block:
            return
        landed = False
        while not landed:
            (landed, scorechange, cleared_rows) = self.__falling_block.drop(self.__blockfield)
        (_, block_y) = self.__falling_block.position
        if block_y == 0:
            self.__game_over()
        else:
            self.__score += scorechange
            if cleared_rows:
                self.__controller.update_blockfield(self.__blockfield)
            if not self.__is_dummy:
                self.__controller.update_score(self.__score)
            self.__start_next_block()

    def __game_over(self):
        if not self.__is_dummy:
            self.__controller.game_over()

    def restart(self):
        self.init_score()
        if self.__falling_block:
            self.__controller.unregister_block(self.__falling_block)
        if self.__next_block:
            self.__controller.unregister_block(self.__next_block)
        self.__next_block = self.__create_new_block(False)
        self.__falling_block = self.__create_new_block(True)
        self.__controller.register_block(self.__falling_block)
        self.__controller.register_block(self.__next_block)
        self.__last_drop = 0.0
        self.__blockfield = BlockField()
        self.__controller.update_blockfield(self.__blockfield)
        self.__autoplay = False
        self.__move_time = 0.5
        self.reset_counts()

    def enable_autoplay(self, state):
        self.__autoplay = state
        self.__move_time = 0.01 if state else 0.5

    def update(self):
        now = time.time()
        self.reset_counts()
        if not self.__is_dummy:
            self.__controller.update_score(self.__score)
        return self.__check_falling_block(now)

# View Classes
class TileView:
    def __init__(self, canvas, x, y, colour, left_offset):
        tile_y = TOP_OFFSET + GRID_SIZE * y
        tile_x = left_offset + GRID_SIZE * x
        # Add a slight border to tiles for better visibility
        self.__rect = canvas.create_rectangle(
            tile_x + 1, tile_y + 1, 
            tile_x + GRID_SIZE - 1, tile_y + GRID_SIZE - 1, 
            fill=colour, outline="#222", width=1
        )
        self.__y = y

    def erase(self, canvas):
        canvas.delete(self.__rect)

class BlockView:
    def __init__(self, block):
        self.__block = block
        self.__tiles = []

    @property
    def block(self):
        return self.__block

    def draw(self, canvas, left_offset):
        if self.__block.is_falling():
            (block_x, block_y) = self.__block.position
        else:
            block_x, block_y = -5, 5
        bitmap = self.__block.bitmap
        self.__tiles = []
        _y = block_y
        for row in bitmap.rows:
            _x = block_x
            for tile in row:
                if tile == 1:
                    tileview = TileView(canvas, _x, _y, self.__block.colour, left_offset)
                    self.__tiles.append(tileview)
                _x += 1
            _y += 1

    def redraw(self, canvas, left_offset):
        self.erase(canvas)
        self.draw(canvas, left_offset)

    def erase(self, canvas):
        for tile in self.__tiles:
            tile.erase(canvas)
        self.__tiles.clear()

class BlockfieldView:
    def __init__(self):
        self.__tiles = []

    def redraw(self, canvas, blockfield, left_offset):
        for tileview in self.__tiles:
            tileview.erase(canvas)
        self.__tiles.clear()
        bitmap = blockfield.bitmap
        for _y, row in enumerate(bitmap):
            for _x, tile in enumerate(row):
                if tile != 0:
                    tileview = TileView(canvas, _x, _y, tile, left_offset)
                    self.__tiles.append(tileview)

class View:
    def __init__(self, root, controller):
        self.__controller = controller
        self.__frame = root
        self.screen_width = root.winfo_screenwidth()
        self.screen_height = root.winfo_screenheight()
        
        # Calculate center offsets
        self.left_offset = (self.screen_width - (MAXCOL * GRID_SIZE)) // 2
        self.top_offset = (self.screen_height - (MAXROW * GRID_SIZE)) // 2 - GRID_SIZE * 2
        
        # Create canvas with full screen dimensions
        self.__canvas = Canvas(
            self.__frame, 
            width=self.screen_width, 
            height=self.screen_height, 
            bg="#111",  # Dark background
            highlightthickness=0  # Remove border
        )
        self.__canvas.pack(fill=BOTH, expand=TRUE)
        
        self.__init_fonts()
        self.__init_arena()
        self.__init_score()
        self.__init_high_scores()
        self.__block_views = []
        self.__blockfield_view = BlockfieldView()
        self.__messages = []
        self.__high_scores_texts = []

    def __init_fonts(self):
        self.bigfont = font.Font(family="Helvetica", size=36, weight="bold")
        self.scorefont = font.Font(family="Helvetica", size=24, weight="bold")
        self.smallfont = font.Font(family="Helvetica", size=14)

    def __init_score(self):
        self.score_text = self.__canvas.create_text(
            self.screen_width // 2, self.top_offset // 2,
            anchor="center", 
            text="Skor: 0", 
            font=self.scorefont, 
            fill="#ddd"  # Light gray
        )

    def __init_arena(self):
        # Game area background
        self.__canvas.create_rectangle(
            self.left_offset - 10, self.top_offset - 10,
            self.left_offset + MAXCOL * GRID_SIZE + 10, 
            self.top_offset + MAXROW * GRID_SIZE + 10,
            fill="#222",  # Dark gray background
            outline="#444",  # Slightly lighter border
            width=2
        )
        
        # "Next:" text
        nextblocktext = self.__canvas.create_text(
            self.left_offset - GRID_SIZE * 5, self.top_offset + GRID_SIZE * 3, 
            anchor="nw",
            text="Sonraki:", 
            font=self.smallfont, 
            fill="#aaa"
        )

    def __init_high_scores(self):


        
        # Titles with better styling
        self.daily_title = self.__canvas.create_text(
            self.screen_width // 6, 30, 
            anchor="n", text="Günlük En Yüksek Skorlar:", 
            font=self.smallfont, fill="#aaa"
        )
        
        self.all_time_title = self.__canvas.create_text(
            self.screen_width - self.screen_width // 6, 30, 
            anchor="n", text="Tüm Zamanların En Yüksek Skorları:", 
            font=self.smallfont, fill="#aaa"
        )

    def display_high_scores(self, high_scores):
        for txt in self.__high_scores_texts:
            self.__canvas.delete(txt)
        self.__high_scores_texts = []

        y_offset = 60
        for i, s in enumerate(high_scores.get('daily', [])[:10]):
            score_text = f"{i+1}. {s['score']}"
            date_text = f"{s['date']}"
            
            txt_score = self.__canvas.create_text(
                self.screen_width // 6 - 100, y_offset + i * 25, 
                anchor="nw", text=score_text, 
                font=self.smallfont, fill="#ccc"
            )
            
            txt_date = self.__canvas.create_text(
                self.screen_width // 6 + 100, y_offset + i * 25, 
                anchor="nw", text=date_text, 
                font=self.smallfont, fill="#999"
            )
            
            self.__high_scores_texts.extend([txt_score, txt_date])

        y_offset = 60
        for i, s in enumerate(high_scores.get('all_time', [])[:10]):
            score_text = f"{i+1}. {s['score']}"
            date_text = f"{s['date']}"
            
            txt_score = self.__canvas.create_text(
                self.screen_width - self.screen_width // 3 + 20, y_offset + i * 25, 
                anchor="nw", text=score_text, 
                font=self.smallfont, fill="#ccc"
            )
            
            txt_date = self.__canvas.create_text(
                self.screen_width - self.screen_width // 3 + 200, y_offset + i * 25, 
                anchor="nw", text=date_text, 
                font=self.smallfont, fill="#999"
            )
            
            self.__high_scores_texts.extend([txt_score, txt_date])

    def register_block(self, block):
        self.__block_views.append(BlockView(block))

    def unregister_block(self, block):
        for block_view in self.__block_views[:]:
            if block_view.block is block:
                block_view.erase(self.__canvas)
                self.__block_views.remove(block_view)

    def update_blockfield(self, blockfield):
        self.__blockfield_view.redraw(self.__canvas, blockfield, self.left_offset)

    def display_score(self, score):
        self.__canvas.itemconfig(self.score_text, text=f"Skor: {score}")

    def game_over(self):
        self.__controller.restart_game()

    def clear_messages(self):
        for txt in self.__messages:
            self.__canvas.delete(txt)
        self.__messages.clear()

    def update(self, score, high_scores):
        for block_view in self.__block_views:
            block_view.redraw(self.__canvas, self.left_offset)
        self.display_score(score)
        self.display_high_scores(high_scores)

# GameState
class GameState:
    def __init__(self, model):
        self.__model = model
        self.__is_a_clone = False

    def get_falling_block_position(self):
        return self.__model.falling_block_position

    def get_falling_block_angle(self):
        return self.__model.falling_block_angle

    def get_falling_block_tiles(self):
        return self.__model.get_falling_block_tiles()

    def get_next_block_tiles(self):
        return self.__model.get_next_block_tiles()

    def get_falling_block_type(self):
        return self.__model.falling_block_type

    def get_next_block_type(self):
        return self.__model.next_block_type

    def get_tiles(self):
        return self.__model.get_copy_of_tiles()

    def get_score(self):
        return self.__model.score

    def clone(self, is_dummy):
        game = GameState(self.__model.clone(is_dummy))
        game._set_model(self.__model.clone(is_dummy), True)
        return game

    def _set_model(self, model, is_a_clone):
        self.__model = model
        self.__is_a_clone = is_a_clone

    def move(self, direction):
        self.__model.move(direction)

    def rotate(self, direction):
        self.__model.rotate(direction)

    def update(self):
        if self.__model.is_dummy:
            return self.__model.update()[1]
        return False

# AutoPlayer
class AutoPlayer:
    def __init__(self, controller):
        self.controller = controller
        self.rand = random.Random()
        self.holesWeight = -8.5
        self.totalHeightWeight = -3
        self.smoothnessWeight = -2.5
        self.completedLinesWeight = 100
        self.rangeWeight = -5.5
        self.maxYWeight = 0
        self.minYWeight = 0
        self.holesNumWeight = -7
        self.rowMovementWeight = -5.5
        self.columnMovementWeight = -6.5
        self.blockHeightWeight = 0
        self.bestPosition = 0
        self.bestAngle = 0
        self.prevY = -1

    def next_move(self, gamestate):
        x, y = gamestate.get_falling_block_position()
        if y < self.prevY:
            self.bestPosition, self.bestAngle = self.best_move(gamestate)
        self.prevY = y
        self.make_move(gamestate, self.bestPosition, self.bestAngle)

    def calculate_total_height(self, clone):
        tiles = clone.get_tiles()
        columnHeights = []
        for column in range(MAXCOL):
            for row in range(MAXROW):
                if tiles[row][column] != 0:
                    columnHeights.append(MAXROW - row)
                    break
                elif row == MAXROW - 1:
                    columnHeights.append(0)
        return columnHeights

    def calculate_smoothness(self, heights):
        smoothness = 0
        for x in range(len(heights) - 1):
            smoothness += abs(heights[x] - heights[x + 1])
        return smoothness

    def holes(self, clone):
        tiles = clone.get_tiles()
        numHoles = 0
        for column in range(MAXCOL):
            counter = 0
            gap = False
            for row in range(MAXROW):
                if gap:
                    counter += 1
                if row < MAXROW - 1 and tiles[row][column] != 0 and tiles[row + 1][column] == 0:
                    gap = True
                if row < MAXROW - 1 and tiles[row][column] == 0 and tiles[row + 1][column] != 0:
                    gap = False
            numHoles += counter
        return numHoles

    def calculate_RowAndColumn_Movement(self, clone):
        tiles = clone.get_tiles()
        rowMovement = columnMovement = 0
        for column in range(MAXCOL):
            for row in range(MAXROW - 1):
                if (tiles[row][column] != tiles[row + 1][column]) and (tiles[row][column] == 0 or tiles[row + 1][column] == 0):
                    columnMovement += 1
        for row in range(MAXROW):
            for column in range(MAXCOL - 1):
                if (tiles[row][column] != tiles[row][column + 1]) and (tiles[row][column] == 0 or tiles[row][column + 1] == 0):
                    rowMovement += 1
        return (rowMovement, columnMovement)

    def calculate_holes(self, clone):
        tiles = clone.get_tiles()
        holes = 0
        for row in range(MAXROW - 1):
            for column in range(MAXCOL):
                if tiles[row][column] != 0 and tiles[row + 1][column] == 0:
                    holes += 1
        return holes

    def calculate_completed_lines(self, oldscore, clone):
        newScore = clone.get_score()
        diff = newScore - oldscore
        if 100 < diff < 130:
            return 1
        elif 400 < diff < 450:
            return 2
        elif 800 < diff < 850:
            return 3
        elif 1600 < diff < 1650:
            return 4
        return 0

    def find_block_coordinate(self, clone, oldTiles, completedLines):
        newTiles = clone.get_tiles()
        blockCoor = []
        for y in range(MAXROW):
            for x in range(MAXCOL):
                if oldTiles[y][x] != newTiles[y][x]:
                    blockCoor.append((x, y))
        return blockCoor

    def make_move(self, gamestate, targetPosition, targetAngle):
        x, y = gamestate.get_falling_block_position()
        angle = gamestate.get_falling_block_angle()
        if targetPosition > x:
            gamestate.move(Direction.RIGHT)
        if targetPosition < x:
            gamestate.move(Direction.LEFT)
        if targetAngle == 3 and angle == 0:
            gamestate.rotate(Direction.LEFT)
        elif targetAngle > angle:
            gamestate.rotate(Direction.RIGHT)

    def best_move(self, gamestate):
        bestPosition = bestAngle = 0
        bestScore = -float('inf')
        for angle in range(4):
            for position in range(-3, 13):
                clone = gamestate.clone(True)
                oldScore = clone.get_score()
                oldTiles = clone.get_tiles()
                while not clone.update():
                    x, y = clone.get_falling_block_position()
                    blockAngle = clone.get_falling_block_angle()
                    if position > x:
                        clone.move(Direction.RIGHT)
                    if position < x:
                        clone.move(Direction.LEFT)
                    if angle == 3 and blockAngle == 0:
                        clone.rotate(Direction.LEFT)
                    elif angle > blockAngle:
                        clone.rotate(Direction.RIGHT)
                heights = self.calculate_total_height(clone)
                totalHeight = sum(heights)
                smoothness = self.calculate_smoothness(heights)
                holes = self.calculate_holes(clone)
                completedLines = self.calculate_completed_lines(oldScore, clone)
                maxYCanvas = max(heights) if heights else 0
                minYCanvas = min(heights) if heights else 0
                rangeCanvas = maxYCanvas - minYCanvas
                holeNum = self.holes(clone)
                rowMovement, columnMovement = self.calculate_RowAndColumn_Movement(clone)
                blockCoor = self.find_block_coordinate(clone, oldTiles, completedLines)
                blockHeight = (max(c[1] for c in blockCoor) + min(c[1] for c in blockCoor)) / 2 if blockCoor else 0
                score = (
                    smoothness * self.smoothnessWeight +
                    totalHeight * self.totalHeightWeight +
                    completedLines * self.completedLinesWeight +
                    rangeCanvas * self.rangeWeight +
                    maxYCanvas * self.maxYWeight +
                    minYCanvas * self.minYWeight +
                    holeNum * self.holesNumWeight +
                    rowMovement * self.rowMovementWeight +
                    columnMovement * self.columnMovementWeight +
                    blockHeight * self.blockHeightWeight
                )
                if score > bestScore:
                    bestScore = score
                    bestPosition = position
                    bestAngle = angle
        return (bestPosition, bestAngle)

# Controller
class Controller:
    def __init__(self):
        self.__root = Tk()
        self.__root.attributes('-fullscreen', True)
        self.__root.configure(bg='black')
        self.__root.bind('<Any-KeyPress>', self.exit_screensaver)
        self.__root.bind('<Motion>', self.exit_screensaver)
        self.__root.bind_all("<Key>", self.key)
        self.__running = True
        self.__destroyed = False
        self.__score = 0
        self.__autoplay = True
        self.__high_scores = self.load_high_scores()
        self.__gen_random()
        self.__model = Model(self)
        self.__gamestate_api = GameState(self.__model)
        self.__view = View(self.__root, self)
        self.__blockfield = self.__model.blockfield
        self.__lost = False
        self.__model.start()
        self.__model.enable_autoplay(True)
        self.__autoplayer = AutoPlayer(self)

    def load_high_scores(self):
        try:
            with open('high_scores.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {"daily": [], "all_time": []}

    def save_high_scores(self):
        with open('high_scores.json', 'w') as f:
            json.dump(self.__high_scores, f)

    def add_score(self, score):
        if score <= 0 or self.__model._Model__score_added:
            return
        now = datetime.now()
        date_str = now.strftime("%Y-%m-%d %H:%M:%S")
        self.__high_scores["all_time"].append({"score": score, "date": date_str})
        self.__high_scores["all_time"] = sorted(self.__high_scores["all_time"], key=lambda x: x["score"], reverse=True)[:25]
        daily = [s for s in self.__high_scores.get("daily", []) if datetime.strptime(s["date"], "%Y-%m-%d %H:%M:%S").date() == now.date()]
        daily.append({"score": score, "date": date_str})
        daily = sorted(daily, key=lambda x: x["score"], reverse=True)[:25]
        self.__high_scores["daily"] = daily
        self.__model._Model__score_added = True
        self.save_high_scores()

    def __gen_random(self):
        self.__rand = random.Random()
        self.__rand.seed(42)
        self.rand_ix = 0
        self.maxrand = 100000
        maxblocktype = 6
        self.randlist = [self.__rand.randint(0, maxblocktype) for _ in range(self.maxrand)]

    def get_random_blocknum(self):
        self.rand_ix = (self.rand_ix + 1) % self.maxrand
        return self.randlist[self.rand_ix]

    def register_block(self, block):
        if not self.__destroyed:
            self.__view.register_block(block)

    def unregister_block(self, block):
        if not self.__destroyed:
            self.__view.unregister_block(block)

    def update_blockfield(self, blockfield):
        self.__blockfield = blockfield
        if not self.__destroyed:
            self.__view.update_blockfield(blockfield)

    def update_score(self, score):
        self.__score = score
        if not self.__destroyed:
            self.__view.display_score(score)

    @property
    def score(self):
        return self.__score

    def game_over(self):
        self.__lost = True
        if not self.__destroyed:
            self.add_score(self.__score)
            self.restart_game()

    def restart_game(self):
        self.__view.clear_messages()
        self.__lost = False
        self.__model.restart()
        self.__model.enable_autoplay(self.__autoplay)

    def exit_screensaver(self, event):
        self.__running = False
        if not self.__destroyed:
            self.__destroyed = True
            try:
                self.__root.destroy()
            except tkinter.TclError:
                pass

    def key(self, event):
        if self.__destroyed:
            return
        if event.char == " ":
            self.__model.drop_block()
        elif event.char == "q":
            self.__running = False
        elif event.char == "a":
            self.__model.move(Direction.LEFT)
        elif event.char == "s":
            self.__model.move(Direction.RIGHT)
        elif event.char == "k":
            self.__model.rotate(Direction.LEFT)
        elif event.char == "l":
            self.__model.rotate(Direction.RIGHT)
        elif event.char == "y":
            self.__autoplay = not self.__autoplay
            self.__model.enable_autoplay(self.__autoplay)
        elif event.char == "r":
            self.restart_game()

    def run(self):
        dropped = False
        while self.__running and not self.__destroyed:
            try:
                if not self.__lost:
                    if dropped and self.__autoplay:
                        self.__model.reset_counts()
                        self.__autoplayer.next_move(self.__gamestate_api)
                    (dropped, _landed) = self.__model.update()
                self.__view.update(self.__score, self.__high_scores)
                self.__root.update()
            except tkinter.TclError:
                self.__running = False
                break
        if not self.__destroyed:
            self.__destroyed = True
            try:
                self.__root.destroy()
            except tkinter.TclError:
                pass

# Main
if __name__ == "__main__":
    controller = Controller()
    controller.run()
