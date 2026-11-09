from kivy.app import App
from kivy.core.window import Window
from kivy.uix.floatlayout import FloatLayout
from kivy.graphics import Color, Rectangle
from kivy.metrics import dp
from kivy.clock import Clock

from menu import MenuScreen
from interface import GameScreen
from settings import load_settings


class ChessApp(App):
    def build(self):
        self.title = "Chess 2.0"
        Window.clearcolor = (0.025, 0.03, 0.09, 1)
        self.root_layout = FloatLayout()
        self.current_screen = None
        self.settings = load_settings()
        self.show_menu()
        return self.root_layout

    def _replace(self, screen):
        if self.current_screen is not None:
            self.root_layout.remove_widget(self.current_screen)
        self.current_screen = screen
        self.root_layout.add_widget(screen)

    def show_menu(self, *args):
        self._replace(MenuScreen(on_start=self.start_game,
                                 settings=self.settings))

    def start_game(self, mode, difficulty, minutes, human_color, resume_data=None):
        self._replace(GameScreen(
            mode=mode, difficulty=difficulty, minutes=minutes,
            human_color=human_color, settings=self.settings,
            on_back=self.show_menu, resume_data=resume_data
        ))


if __name__ == "__main__":
    ChessApp().run()
