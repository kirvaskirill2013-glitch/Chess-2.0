"""Тонкая обёртка над python-chess: правила и состояние партии."""
import chess

PIECE_NAMES = {
    chess.PAWN: "пешка", chess.KNIGHT: "конь", chess.BISHOP: "слон",
    chess.ROOK: "ладья", chess.QUEEN: "ферзь", chess.KING: "король"
}

class ChessGame:
    def __init__(self, fen=None, uci_moves=None):
        # При восстановлении воспроизводим ходы от начальной позиции:
        # так сохраняются история повторений и возможность отмены.
        self.board = chess.Board()
        self.san_history = []
        if uci_moves:
            for uci in uci_moves:
                move = chess.Move.from_uci(uci)
                if move not in self.board.legal_moves:
                    raise ValueError("Сохранённая партия содержит нелегальный ход")
                self.san_history.append(self.board.san(move))
                self.board.push(move)
        elif fen:
            self.board.set_fen(fen)

    def legal_moves_from(self, square):
        return [m for m in self.board.legal_moves if m.from_square == square]

    def push(self, move):
        if move not in self.board.legal_moves:
            return None
        san = self.board.san(move)
        self.board.push(move)
        self.san_history.append(san)
        return san

    def undo(self):
        if not self.board.move_stack:
            return False
        self.board.pop()
        if self.san_history:
            self.san_history.pop()
        return True

    def status(self):
        b = self.board
        if b.is_checkmate():
            return "Мат", "Победа чёрных" if b.turn else "Победа белых", "checkmate"
        if b.is_stalemate():
            return "Пат", "Ничья", "draw"
        if b.is_insufficient_material():
            return "Ничья", "Недостаточно материала", "draw"
        if b.can_claim_fifty_moves():
            return "Ничья возможна", "Правило 50 ходов", "claim"
        if b.can_claim_threefold_repetition():
            return "Ничья возможна", "Троекратное повторение", "claim"
        if b.is_check():
            return ("Шах белым" if b.turn else "Шах чёрным"), "Нужно защитить короля", "check"
        return ("Ход белых" if b.turn else "Ход чёрных"), "", "playing"

    def result(self):
        if self.board.is_checkmate():
            return "0-1" if self.board.turn else "1-0"
        if (self.board.is_stalemate() or self.board.is_insufficient_material()
                or self.board.is_seventyfive_moves() or self.board.is_fivefold_repetition()):
            return "1/2-1/2"
        return "*"
