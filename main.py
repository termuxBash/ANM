import textual
import os
from textual.app import App, ComposeResult
from textual.widgets import Button, Header, Footer, Static, Input, Label
from textual.containers import Vertical, Horizontal
import sqlite3

class DataApp(App):
    pass

if __name__ == "__main__":
    app = DataApp()
    app.run()