import kivy

from kivy.app import App
from kivy.uix.label import Label
from kivy import Config

Config.set('graphics', 'multisamples', '0')

class SimpleApp(App):
    def build(self):
        return Label(text='Hello World')

if __name__ == '__main__':
    SimpleApp().run()
