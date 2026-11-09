from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle
from kivy.metrics import dp
from statistics import load_stats
from save_manager import has_saved_game, load_game

BG = (0.035, 0.045, 0.12, 1)
GOLD = (0.96, 0.78, 0.36, 1)

def styled_button(text, color=(0.15, 0.19, 0.34, 1), height=48):
    b = Button(text=text, size_hint_y=None, height=dp(height),
               background_normal="", background_down="",
               background_color=color, color=(1,1,1,1),
               bold=True, font_size="15sp")
    return b

class MenuScreen(FloatLayout):
    def __init__(self, on_start, settings, **kwargs):
        super().__init__(**kwargs)
        self.on_start = on_start
        self.settings = settings
        with self.canvas.before:
            Color(*BG)
            self.bg = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._resize_bg, size=self._resize_bg)

        panel = BoxLayout(orientation="vertical", size_hint=(0.88, 0.94),
                          pos_hint={"center_x": .5, "center_y": .5},
                          padding=dp(18), spacing=dp(9))
        panel.add_widget(Label(text="♛  CHESS 2.0  ♛", font_size="32sp",
                               bold=True, color=GOLD, size_hint_y=None,
                               height=dp(65)))
        panel.add_widget(Label(text="Классические шахматы с искусственным интеллектом",
                               font_size="12sp", color=(.72,.76,.9,1),
                               size_hint_y=None, height=dp(30)))

        self.mode = "bot"
        self.difficulty = "medium"
        self.mode_spinner = Spinner(text="Игра с ботом",
            values=("Игра с ботом", "Два игрока"),
            size_hint_y=None, height=dp(46))
        self.diff_spinner = Spinner(text="Средний уровень",
            values=("Лёгкий уровень", "Средний уровень", "Сложный уровень"),
            size_hint_y=None, height=dp(46))
        self.time_spinner = Spinner(text=f'{settings.get("minutes",10)} минут',
            values=("3 минуты", "5 минут", "10 минут", "15 минут", "30 минут"),
            size_hint_y=None, height=dp(46))
        self.color_spinner = Spinner(text="Играть белыми",
            values=("Играть белыми", "Играть чёрными"),
            size_hint_y=None, height=dp(46))

        for caption, control in [
            ("РЕЖИМ ИГРЫ", self.mode_spinner),
            ("СЛОЖНОСТЬ", self.diff_spinner),
            ("КОНТРОЛЬ ВРЕМЕНИ", self.time_spinner),
            ("ЦВЕТ ФИГУР", self.color_spinner)
        ]:
            panel.add_widget(Label(text=caption, color=GOLD, bold=True,
                                   size_hint_y=None, height=dp(23)))
            panel.add_widget(control)

        self.mode_spinner.bind(text=self._mode_changed)
        play = styled_button("НАЧАТЬ ИГРУ", (0.12, .48, .31, 1), 54)
        play.bind(on_release=self._start)
        panel.add_widget(Widget(size_hint_y=None, height=dp(4)))
        panel.add_widget(play)

        stats = load_stats()
        self.stats_label = Label(
            text=f'Партии: {stats["games"]}   Победы: {stats["wins"]}   '
                 f'Поражения: {stats["losses"]}   Ничьи: {stats["draws"]}',
            color=(.82,.84,.92,1), font_size="11sp", size_hint_y=None,
            height=dp(35))
        panel.add_widget(self.stats_label)

        if has_saved_game():
            resume = styled_button("Продолжить сохранённую партию", height=42)
            resume.bind(on_release=self._resume)
            panel.add_widget(resume)
        self.add_widget(panel)

    def _resize_bg(self, *args):
        self.bg.pos, self.bg.size = self.pos, self.size

    def _mode_changed(self, spinner, value):
        self.diff_spinner.disabled = value == "Два игрока"
        self.color_spinner.disabled = value == "Два игрока"
        self.diff_spinner.opacity = .35 if self.diff_spinner.disabled else 1

    def _start(self, *args):
        mode = "2p" if self.mode_spinner.text == "Два игрока" else "bot"
        diff = {"Лёгкий уровень":"easy", "Средний уровень":"medium",
                "Сложный уровень":"hard"}.get(self.diff_spinner.text, "medium")
        minutes = int(self.time_spinner.text.split()[0])
        color = "b" if self.color_spinner.text == "Играть чёрными" else "w"
        self.on_start(mode, diff, minutes, color)

    def _resume(self, *args):
        data = load_game()
        if data:
            self.on_start(data["mode"], data["difficulty"],
                          int(data["clocks"].get("initial", 10)),
                          data["human_color"], data)
