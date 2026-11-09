import threading
import time
import chess

from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle
from kivy.metrics import dp
from kivy.clock import Clock

from chess_engine import ChessGame
from chess_ai import choose_move
from board_widget import BoardWidget, GLYPHS
from save_manager import save_game
from statistics import record_result

BG = (0.035,0.045,0.12,1)
GOLD = (0.96,0.78,0.36,1)

def button(text, color=(.15,.19,.34,1), height=42):
    b=Button(text=text,size_hint_y=None,height=dp(height),
             background_normal="",background_down="",
             background_color=color,color=(1,1,1,1),bold=True,
             font_size="13sp")
    return b

class GameScreen(FloatLayout):
    def __init__(self, mode="bot", difficulty="medium", minutes=10,
                 human_color="w", settings=None, on_back=None,
                 resume_data=None, **kwargs):
        super().__init__(**kwargs)
        self.mode, self.difficulty = mode, difficulty
        self.human_color = chess.WHITE if human_color == "w" else chess.BLACK
        self.bot_color = not self.human_color
        self.minutes = minutes
        self.settings = settings or {}
        self.on_back = on_back
        self.game = ChessGame(
            uci_moves=resume_data.get("uci_moves", []) if resume_data else None,
            fen=resume_data.get("fen") if resume_data else None
        )
        self.move_history = list(resume_data.get("moves", [])) if resume_data else []
        self.initial_seconds = minutes*60
        self.clocks = {"w": self.initial_seconds, "b": self.initial_seconds}
        if resume_data:
            saved = resume_data.get("clocks", {})
            self.clocks["w"] = float(saved.get("w", self.initial_seconds))
            self.clocks["b"] = float(saved.get("b", self.initial_seconds))
        self.last_tick = time.monotonic()
        self.selected = None
        self.bot_thinking = False
        self.finished = False
        self.result_recorded = False

        with self.canvas.before:
            Color(*BG)
            self.bg = Rectangle(pos=self.pos,size=self.size)
        self.bind(pos=self._bg_resize,size=self._bg_resize)

        root=BoxLayout(orientation="vertical",padding=dp(7),spacing=dp(5))
        top=BoxLayout(size_hint_y=None,height=dp(43),spacing=dp(5))
        back=button("← Меню",height=40); back.bind(on_release=self._back)
        new=button("Новая",height=40); new.bind(on_release=self.new_game)
        flip=button("Перевернуть",height=40); flip.bind(on_release=self.flip_board)
        top.add_widget(back); top.add_widget(new); top.add_widget(flip)
        root.add_widget(top)

        self.status=Label(text="Ход белых",size_hint_y=None,height=dp(30),
                          color=GOLD,font_size="17sp",bold=True)
        root.add_widget(self.status)

        self.clock_row=BoxLayout(size_hint_y=None,height=dp(35))
        self.white_clock=Label(text="Белые 10:00",color=(1,1,1,1),font_size="14sp")
        self.black_clock=Label(text="Чёрные 10:00",color=(1,1,1,1),font_size="14sp")
        self.clock_row.add_widget(self.black_clock)
        self.clock_row.add_widget(self.white_clock)
        root.add_widget(self.clock_row)

        self.board_area=FloatLayout(size_hint=(1,.68))
        self.board=BoardWidget(self.game,self.on_square,self.settings,
                               size_hint=(1,1))
        self.board_area.add_widget(self.board)
        self.piece_labels=[]
        self._build_piece_labels()
        root.add_widget(self.board_area)

        bottom=BoxLayout(size_hint_y=None,height=dp(112),spacing=dp(6))
        self.history=Label(text="ХОДЫ\n—",color=(.83,.85,.93,1),
                           font_size="11sp",halign="left",valign="top",
                           size_hint=(.65,1),text_size=(None,None))
        bottom.add_widget(self.history)
        actions=BoxLayout(orientation="vertical",spacing=dp(4),
                          size_hint=(.35,1))
        undo=button("↶ Отменить",height=32); undo.bind(on_release=self.undo)
        save=button("Сохранить",height=32); save.bind(on_release=self.save)
        draw=button("Предложить ничью",height=32); draw.bind(on_release=self.offer_draw)
        actions.add_widget(undo); actions.add_widget(save); actions.add_widget(draw)
        bottom.add_widget(actions)
        root.add_widget(bottom)
        self.add_widget(root)

        Clock.schedule_interval(self._tick,1)
        Clock.schedule_once(lambda dt:self._refresh(),.1)
        Clock.schedule_once(lambda dt:self._maybe_bot(),.35)

    def _bg_resize(self,*args):
        self.bg.pos,self.bg.size=self.pos,self.size

    def _build_piece_labels(self):
        for label in self.piece_labels:
            self.board_area.remove_widget(label)
        self.piece_labels=[]
        for sq in chess.SQUARES:
            label=Label(text="",font_size="34sp",bold=True,
                        color=(.98,.96,.88,1),outline_color=(.08,.05,.03,1),
                        outline_width=1)
            self.piece_labels.append(label)
            self.board_area.add_widget(label)
        self.board.bind(pos=lambda *a:self._position_labels(),
                        size=lambda *a:self._position_labels())
        Clock.schedule_once(lambda dt:self._position_labels(),.1)

    def _position_labels(self):
        if not hasattr(self.board,"cell") or self.board.cell<=0:
            return
        cell=self.board.cell
        for sq,label in enumerate(self.piece_labels):
            piece=self.game.board.piece_at(sq)
            if piece:
                f,r=chess.square_file(sq),chess.square_rank(sq)
                if self.board.flipped: f,r=7-f,7-r
                label.text=GLYPHS[(piece.color,piece.piece_type)]
                label.color=(.98,.97,.91,1) if piece.color else (.10,.08,.07,1)
                label.font_size=cell*.78
                label.size=(cell,cell)
                label.pos=(self.board.left+f*cell,self.board.bottom+r*cell)
                label.opacity=1
            else:
                label.text=""
                label.opacity=0

    def _refresh(self):
        self.board.game=self.game
        self.board.last_move=(self.game.board.peek().from_square,
                              self.game.board.peek().to_square) if self.game.board.move_stack else None
        self.board.selected=self.selected
        self.board.targets=[m.to_square for m in self.game.legal_moves_from(self.selected)] if self.selected is not None else []
        title,detail,state=self.game.status()
        self.status.text=title + (f" · {detail}" if detail else "")
        self._update_clocks()
        self._position_labels()
        self.board.redraw()
        self._update_history()
        if state in ("checkmate","draw"):
            self._finish(state)

    def _update_history(self):
        if not self.move_history:
            self.history.text="ХОДЫ\n—"
        else:
            lines=[]
            for i in range(0,len(self.move_history),2):
                white=self.move_history[i]
                black=self.move_history[i+1] if i+1<len(self.move_history) else ""
                lines.append(f"{i//2+1}. {white}   {black}")
            self.history.text="ХОДЫ\n"+"\n".join(lines[-5:])

    def on_square(self,square):
        if self.finished or self.bot_thinking:
            return
        if self.mode=="bot" and self.game.board.turn != self.human_color:
            return
        piece=self.game.board.piece_at(square)
        if self.selected is not None:
            candidate=chess.Move(self.selected,square)
            if candidate in self.game.board.legal_moves:
                if self.game.board.piece_at(self.selected).piece_type==chess.PAWN and chess.square_rank(square) in (0,7):
                    self._promotion_popup(self.selected,square)
                else:
                    self._play(candidate)
                return
        if piece and piece.color==self.game.board.turn:
            self.selected=square
        else:
            self.selected=None
        self._refresh()

    def _promotion_popup(self,fr,to):
        content=BoxLayout(spacing=dp(5),padding=dp(8))
        popup=Popup(title="Превращение пешки",content=content,
                    size_hint=(.9,.25),auto_dismiss=False)
        for p,name in [(chess.QUEEN,"Ферзь"),(chess.ROOK,"Ладья"),
                       (chess.BISHOP,"Слон"),(chess.KNIGHT,"Конь")]:
            b=Button(text=name)
            b.bind(on_release=lambda inst,piece=p:self._promote(popup,fr,to,piece))
            content.add_widget(b)
        popup.open()

    def _promote(self,popup,fr,to,piece):
        popup.dismiss()
        self._play(chess.Move(fr,to,promotion=piece))

    def _play(self,move):
        san=self.game.push(move)
        if san is None:
            return
        self.move_history.append(san)
        self.selected=None
        self.last_tick=time.monotonic()
        self._refresh()
        self._maybe_bot()

    def _maybe_bot(self):
        if (self.mode!="bot" or self.finished or self.bot_thinking
                or self.game.board.turn==self.human_color
                or self.game.board.is_game_over()):
            return
        self.bot_thinking=True
        self.status.text="Бот анализирует позицию…"
        board_copy=self.game.board.copy(stack=True)
        difficulty=self.difficulty
        def worker():
            move=choose_move(board_copy,difficulty)
            Clock.schedule_once(lambda dt:self._apply_bot(move),0)
        threading.Thread(target=worker,daemon=True).start()

    def _apply_bot(self,move):
        self.bot_thinking=False
        if self.finished or move is None:
            self._refresh()
            return
        self._play(move)

    def undo(self,*args):
        if self.finished or self.bot_thinking:
            return
        count=2 if self.mode=="bot" and len(self.game.board.move_stack)>=2 else 1
        for _ in range(count):
            if self.game.undo() and self.move_history:
                self.move_history.pop()
        self.selected=None
        self._refresh()

    def new_game(self,*args):
        self.game=ChessGame()
        self.move_history=[]
        self.selected=None
        self.finished=False
        self.result_recorded=False
        self.clocks={"w":self.initial_seconds,"b":self.initial_seconds}
        self.last_tick=time.monotonic()
        self.board.game=self.game
        self._refresh()
        self._maybe_bot()

    def flip_board(self,*args):
        self.board.flipped=not self.board.flipped
        self._refresh()

    def save(self,*args):
        ok=save_game(self.game.board,self.move_history,self.mode,
                     self.difficulty,"w" if self.human_color else "b",
                     {"w":self.clocks["w"],"b":self.clocks["b"],
                      "initial":self.minutes})
        self.status.text="Партия сохранена" if ok else "Не удалось сохранить партию"

    def offer_draw(self,*args):
        if self.mode=="2p":
            self._finish("draw")
        else:
            self.status.text="Бот не принял предложение ничьей"

    def _tick(self,dt):
        if self.finished or self.bot_thinking:
            self.last_tick=time.monotonic()
            return
        now=time.monotonic()
        elapsed=max(0,now-self.last_tick)
        self.last_tick=now
        key="w" if self.game.board.turn else "b"
        self.clocks[key]=max(0,self.clocks[key]-elapsed)
        if self.clocks[key]<=0:
            self.finished=True
            winner="Чёрные" if key=="w" else "Белые"
            self.status.text=f"Время! Победа: {winner}"
            self._record("loss" if (key=="w" and self.human_color) or
                         (key=="b" and not self.human_color) else "win")
        self._update_clocks()

    def _update_clocks(self):
        def fmt(value):
            value=max(0,int(value))
            return f"{value//60:02d}:{value%60:02d}"
        self.white_clock.text="Белые  "+fmt(self.clocks["w"])
        self.black_clock.text="Чёрные  "+fmt(self.clocks["b"])

    def _finish(self,state):
        if self.finished:
            return
        self.finished=True
        if state=="checkmate":
            winner="Чёрные" if self.game.board.turn else "Белые"
            self.status.text=f"МАТ! Победа: {winner}"
            if self.mode=="2p":
                result="win" if winner=="Белые" else "loss"
            else:
                result="win" if (winner=="Белые")==self.human_color else "loss"
        else:
            self.status.text="Ничья"
            result="draw"
        self._record(result)

    def _record(self,result):
        if not self.result_recorded:
            record_result(result,len(self.game.board.move_stack))
            self.result_recorded=True

    def _back(self,*args):
        self.save()
        if self.on_back:
            self.on_back()
