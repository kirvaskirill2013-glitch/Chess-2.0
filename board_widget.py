import chess
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle, Ellipse, Line
from kivy.metrics import dp

GLYPHS = {
    (chess.WHITE, chess.KING): "♔", (chess.WHITE, chess.QUEEN): "♕",
    (chess.WHITE, chess.ROOK): "♖", (chess.WHITE, chess.BISHOP): "♗",
    (chess.WHITE, chess.KNIGHT): "♘", (chess.WHITE, chess.PAWN): "♙",
    (chess.BLACK, chess.KING): "♚", (chess.BLACK, chess.QUEEN): "♛",
    (chess.BLACK, chess.ROOK): "♜", (chess.BLACK, chess.BISHOP): "♝",
    (chess.BLACK, chess.KNIGHT): "♞", (chess.BLACK, chess.PAWN): "♟"
}

class BoardWidget(Widget):
    def __init__(self, game, on_square, settings=None, **kwargs):
        super().__init__(**kwargs)
        self.game = game
        self.on_square = on_square
        self.settings = settings or {}
        self.selected = None
        self.targets = []
        self.last_move = None
        self.flipped = False
        self.bind(pos=self.redraw, size=self.redraw)

    def redraw(self, *args):
        self.canvas.clear()
        side = min(self.width, self.height)
        if side <= 0:
            return
        self.cell = side / 8
        self.left = self.x + (self.width-side)/2
        self.bottom = self.y + (self.height-side)/2
        with self.canvas:
            for row in range(8):
                for col in range(8):
                    light = (row+col) % 2 == 0
                    Color(*( (.91,.84,.72,1) if light else (.43,.30,.23,1) ))
                    Rectangle(pos=(self.left+col*self.cell,
                                   self.bottom+row*self.cell),
                              size=(self.cell,self.cell))
            if self.last_move:
                for sq in self.last_move:
                    file_no, rank_no = chess.square_file(sq), chess.square_rank(sq)
                    if self.flipped:
                        file_no, rank_no = 7-file_no, 7-rank_no
                    Color(.95,.78,.20,.35)
                    Rectangle(pos=(self.left+file_no*self.cell,
                                   self.bottom+rank_no*self.cell),
                              size=(self.cell,self.cell))
            if self.selected is not None:
                f, r = chess.square_file(self.selected), chess.square_rank(self.selected)
                if self.flipped: f, r = 7-f, 7-r
                Color(.95,.78,.12,.55)
                Rectangle(pos=(self.left+f*self.cell,self.bottom+r*self.cell),
                          size=(self.cell,self.cell))
            for sq in self.targets:
                f, r = chess.square_file(sq), chess.square_rank(sq)
                if self.flipped: f, r = 7-f, 7-r
                x, y = self.left+f*self.cell, self.bottom+r*self.cell
                if self.game.board.piece_at(sq):
                    Color(.88,.20,.18,.8)
                    Line(rectangle=(x+dp(3),y+dp(3),self.cell-dp(6),
                                    self.cell-dp(6)),width=dp(3))
                else:
                    Color(.12,.65,.25,.8)
                    rad=self.cell*.13
                    Ellipse(pos=(x+self.cell/2-rad,y+self.cell/2-rad),
                            size=(rad*2,rad*2))
            for sq, piece in self.game.board.piece_map().items():
                f, r = chess.square_file(sq), chess.square_rank(sq)
                if self.flipped: f, r = 7-f, 7-r
                x, y = self.left+f*self.cell, self.bottom+r*self.cell
                glyph = GLYPHS[(piece.color,piece.piece_type)]
                # Подложка улучшает контраст символов на разных Android-шрифтах.
                Color(0,0,0,.10)
                Ellipse(pos=(x+self.cell*.13,y+self.cell*.08),
                        size=(self.cell*.74,self.cell*.18))
                from kivy.graphics import InstructionGroup
                from kivy.uix.label import Label
                # Фигуры рисуются отдельными Label-виджетами в GameScreen.

    def square_at(self, pos):
        if not hasattr(self, "cell") or self.cell <= 0:
            return None
        x, y = pos
        col = int((x-self.left)/self.cell)
        row = int((y-self.bottom)/self.cell)
        if not (0 <= col < 8 and 0 <= row < 8):
            return None
        if self.flipped:
            col, row = 7-col, 7-row
        return chess.square(col,row)

    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            return False
        square = self.square_at(touch.pos)
        if square is not None:
            self.on_square(square)
            return True
        return False
