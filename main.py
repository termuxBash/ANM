import sqlite3

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal
from textual.widgets import Button, Footer, Header, Input, Label


DB_PATH = "data.db"


class AppTUI(App):
    CSS = """
    Screen {
        align: center middle;
    }

    #form {
        width: 60;
        height: auto;
        border: round $accent;
        padding: 1 2;
    }

    #title {
        text-align: center;
        text-style: bold;
        margin-bottom: 1;
    }

    Input {
        margin: 1 0;
    }

    #buttons {
        height: auto;
        margin-top: 1;
    }

    #buttons Button {
        width: 1fr;
        margin: 0 1;
    }

    #submit {
        background: $success;
    }

    #quit {
        background: $error;
    }

    #status {
        height: auto;
        margin-top: 1;
        text-align: center;
    }
    """

    def compose(self) -> ComposeResult:
        yield Header()

        with Container(id="form"):
            yield Label("Add Record", id="title")

            yield Input(
                placeholder="Code *",
                id="code",
            )

            yield Input(
                placeholder="Name *",
                id="name",
            )

            yield Input(
                placeholder="Rating (0-20)",
                id="rating",
                type="number",
            )

            yield Input(
                placeholder="Manga Code",
                id="mg_code",
            )

            with Horizontal(id="buttons"):
                yield Button(
                    "Submit",
                    id="submit",
                    variant="success",
                )

                yield Button(
                    "Quit",
                    id="quit",
                    variant="error",
                )

            yield Label("", id="status")

        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "submit":
            self.insert_record()

        elif event.button.id == "quit":
            self.exit()

    def insert_record(self) -> None:
        code = self.query_one("#code", Input).value.strip()
        name = self.query_one("#name", Input).value.strip()
        rating = self.query_one("#rating", Input).value.strip()
        mg_code = self.query_one("#mg_code", Input).value.strip()

        status = self.query_one("#status", Label)

        # Required fields
        if not code:
            status.update("❌ Code is required.")
            return

        if not name:
            status.update("❌ Name is required.")
            return

        # Validate rating
        if rating:
            try:
                rating_value = float(rating)
            except ValueError:
                status.update("❌ Rating must be a number.")
                return

            if not 0 <= rating_value <= 20:
                status.update("❌ Rating must be between 0 and 20.")
                return
        else:
            rating_value = None

        # Empty Manga Code becomes NULL
        mg_code_value = mg_code if mg_code else None

        try:
            with sqlite3.connect(DB_PATH) as conn:
                conn.execute(
                    """
                    INSERT INTO Anime (code, Name, Rating, mg_code)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        code,
                        name,
                        rating_value,
                        mg_code_value,
                    ),
                )

                conn.commit()

            status.update("✅ Inserted successfully.")

            # Clear inputs after successful insert
            self.query_one("#code", Input).value = ""
            self.query_one("#name", Input).value = ""
            self.query_one("#rating", Input).value = ""
            self.query_one("#mg_code", Input).value = ""

        except sqlite3.IntegrityError as e:
            error = str(e).lower()

            # Detect which UNIQUE field caused the error
            if "anime.code" in error or "code" in error:
                status.update("❌ Code already exists.")

            elif "anime.name" in error or "name" in error:
                status.update("❌ Name already exists.")

            elif "anime.mg_code" in error or "mg_code" in error:
                status.update("❌ MG Code already exists.")

            else:
                status.update("❌ Record already exists.")

        except sqlite3.Error as e:
            status.update(f"❌ SQLite error: {e}")


if __name__ == "__main__":
    AppTUI().run()
