"""Небольшой шахматный движок: negamax, alpha-beta, сортировка ходов."""
import random
import chess

VALUES = {
    chess.PAWN: 100, chess.KNIGHT: 320, chess.BISHOP: 335,
    chess.ROOK: 500, chess.QUEEN: 900, chess.KING: 20000
}
MATE = 100000

def evaluate(board, perspective):
    score = 0
    for sq, piece in board.piece_map().items():
        value = VALUES[piece.piece_type]
        file_no = chess.square_file(sq)
        rank_no = chess.square_rank(sq)
        # Небольшие позиционные бонусы: центр и продвижение пешек.
        center = 3.5 - (abs(3.5-file_no) + abs(3.5-rank_no)) / 2
        if piece.piece_type in (chess.KNIGHT, chess.BISHOP):
            value += int(center * 8)
        elif piece.piece_type == chess.PAWN:
            advance = rank_no if piece.color == chess.WHITE else 7-rank_no
            value += advance * 5 + int(center * 3)
        score += value if piece.color == perspective else -value
    return score

def move_order_score(board, move):
    score = 0
    if board.is_capture(move):
        victim = board.piece_at(move.to_square)
        attacker = board.piece_at(move.from_square)
        victim_value = VALUES[victim.piece_type] if victim else VALUES[chess.PAWN]
        attacker_value = VALUES[attacker.piece_type] if attacker else 0
        score += 10 * victim_value - attacker_value
    if move.promotion:
        score += VALUES.get(move.promotion, 0) + 800
    if board.gives_check(move):
        score += 50
    return score

def negamax(board, depth, alpha, beta, ply=0):
    if board.is_checkmate():
        return -MATE + ply, None
    if (board.is_stalemate() or board.is_insufficient_material()
            or board.is_seventyfive_moves() or board.is_fivefold_repetition()):
        return 0, None
    if depth <= 0:
        return evaluate(board, board.turn), None

    moves = list(board.legal_moves)
    if not moves:
        return 0, None
    moves.sort(key=lambda m: move_order_score(board, m), reverse=True)
    best_move = moves[0]
    best_score = -MATE * 2

    for move in moves:
        board.push(move)
        score, _ = negamax(board, depth - 1, -beta, -alpha, ply + 1)
        score = -score
        board.pop()
        if score > best_score:
            best_score, best_move = score, move
        alpha = max(alpha, score)
        if alpha >= beta:
            break
    return best_score, best_move

def choose_move(board, difficulty):
    legal = list(board.legal_moves)
    if not legal:
        return None
    if difficulty == "easy":
        # Случайность с небольшим предпочтением взятий.
        if random.random() < 0.35:
            captures = [m for m in legal if board.is_capture(m)]
            if captures:
                return random.choice(captures)
        return random.choice(legal)
    depth = 2 if difficulty == "medium" else 3
    if difficulty == "hard":
        # На мобильных устройствах глубина 3 — разумный баланс скорости.
        depth = 3
    _, move = negamax(board, depth, -MATE * 2, MATE * 2)
    return move or random.choice(legal)
