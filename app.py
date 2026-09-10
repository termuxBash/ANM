import sqlite3

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, Footer, Header, Input, Label


DB_PATH = "data.db"

# Database table names
SHOW_TABLE = "Anime"
BOOK_TABLE = "Manga"


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

    .page {
        height: auto;
    }

    #title {
        text-align: center;
        text-style: bold;
        margin-bottom: 1;
    }

    Input {
        margin: 1 0;
    }

    #navigation {
        height: auto;
        margin-bottom: 1;
    }

    #navigation Button {
        width: 1fr;
        margin: 0 1;
    }

    #buttons {
        height: auto;
        margin-top: 1;
    }

    #show_buttons,
    #book_buttons {
        height: auto;
        margin-top: 1;
    }

    #show_buttons Button,
    #book_buttons Button {
        width: 1fr;
        margin: 0 2;
    }


    #submit {
        margin-right: 1;
        background: $success;
    }

    #quit {
        margin-left: 1;
        background: $error;
    }

    .status {
        height: auto;
        margin-top: 1;
        text-align: center;
    }
    """

    def compose(self) -> ComposeResult:
        yield Header()

        with Container(id="form"):

            # Page navigation
            with Horizontal(id="navigation"):
                yield Button("Add Show", id="show_page")
                yield Button("Labeled Books", id="book_page")

            # -------------------------------------------------
            # SHOW PAGE
            # -------------------------------------------------

            with Vertical(id="show_form", classes="page"):

                yield Label("Add Show", id="show_title")

                yield Input(
                    placeholder="Code *",
                    id="show_code",
                )

                yield Input(
                    placeholder="Name *",
                    id="show_name",
                )

                yield Input(
                    placeholder="Rating (0-20)",
                    id="show_rating",
                    type="number",
                )

                yield Input(
                    placeholder="Manga Code",
                    id="show_mg_code",
                )

                with Horizontal(id="show_buttons"):
                    yield Button(
                        "Quit",
                        id="quit_show",
                        variant="error",
                    )
                    yield Button(
                        "Submit",
                        id="submit_show",
                        variant="success",
                    )

                    

                yield Label(
                    "",
                    id="show_status",
                    classes="status",
                )

            # -------------------------------------------------
            # BOOK PAGE
            # -------------------------------------------------

            with Vertical(id="book_form", classes="page"):

                yield Label("Labeled Books", id="book_title")

                yield Input(
                    placeholder="Code *",
                    id="book_code",
                )

                yield Input(
                    placeholder="Name *",
                    id="book_name",
                )

                yield Input(
                    placeholder="Reads",
                    id="book_reads",
                    type="number",
                )

                yield Input(
                    placeholder="Volumes",
                    id="book_volumes",
                    type="number",
                )

                yield Input(
                    placeholder="Rating (0-20)",
                    id="book_rating",
                    type="number",
                )

                with Horizontal(id="book_buttons"):
                    yield Button(
                        "Quit",
                        id="quit_book",
                        variant="error",
                    )

                    yield Button(
                        "Submit",
                        id="submit_book",
                        variant="success",
                    )

                yield Label(
                    "",
                    id="book_status",
                    classes="status",
                )

        yield Footer()

    def on_mount(self) -> None:
        # Start on the Show page
        self.show_show_page()

    # =========================================================
    # NAVIGATION
    # =========================================================

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id

        if button_id == "show_page":
            self.show_show_page()

        elif button_id == "book_page":
            self.show_book_page()

        elif button_id == "submit_show":
            self.insert_show()

        elif button_id == "submit_book":
            self.insert_book()

        elif button_id in ("quit_show", "quit_book"):
            self.exit()

    def show_show_page(self) -> None:
        self.query_one("#show_form").display = True
        self.query_one("#book_form").display = False

    def show_book_page(self) -> None:
        self.query_one("#show_form").display = False
        self.query_one("#book_form").display = True

    # =========================================================
    # SHOW
    # =========================================================

    def insert_show(self) -> None:
        code = self.query_one("#show_code", Input).value.strip()
        name = self.query_one("#show_name", Input).value.strip()
        rating = self.query_one("#show_rating", Input).value.strip()
        mg_code = self.query_one("#show_mg_code", Input).value.strip()

        status = self.query_one("#show_status", Label)

        # Required fields
        if not code:
            status.update("❌ Show code is required.")
            return

        if not name:
            status.update("❌ Show name is required.")
            return

        # Rating
        if rating:
            try:
                rating_value = float(rating)
            except ValueError:
                status.update("❌ Show rating must be a number.")
                return

            if not 0 <= rating_value <= 20:
                status.update(
                    "❌ Show rating must be between 0 and 20."
                )
                return
        else:
            rating_value = None

        # Empty Manga Code -> NULL
        mg_code_value = mg_code if mg_code else None

        try:
            with sqlite3.connect(DB_PATH) as conn:
                conn.execute(
                    f"""
                    INSERT INTO {SHOW_TABLE}
                    (code, Name, Rating, mg_code)
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

            status.update("✅ Show inserted successfully.")

            self.query_one("#show_code", Input).value = ""
            self.query_one("#show_name", Input).value = ""
            self.query_one("#show_rating", Input).value = ""
            self.query_one("#show_mg_code", Input).value = ""

        except sqlite3.IntegrityError as e:
            self.handle_integrity_error(
                e,
                status,
                "Show",
            )

        except sqlite3.Error as e:
            status.update(f"❌ SQLite error: {e}")

    # =========================================================
    # BOOK
    # =========================================================

    def insert_book(self) -> None:
        code = self.query_one("#book_code", Input).value.strip()
        name = self.query_one("#book_name", Input).value.strip()
        reads = self.query_one("#book_reads", Input).value.strip()
        volumes = self.query_one("#book_volumes", Input).value.strip()
        rating = self.query_one("#book_rating", Input).value.strip()

        status = self.query_one("#book_status", Label)

        # Required fields
        if not code:
            status.update("❌ Book code is required.")
            return

        if not name:
            status.update("❌ Book name is required.")
            return

        # Reads
        if reads:
            try:
                reads_value = int(reads)
            except ValueError:
                status.update("❌ Reads must be a whole number.")
                return

            if reads_value < 0:
                status.update("❌ Reads cannot be negative.")
                return
        else:
            reads_value = None

        # Volumes
        if volumes:
            try:
                volumes_value = int(volumes)
            except ValueError:
                status.update("❌ Volumes must be a whole number.")
                return

            if volumes_value < 0:
                status.update("❌ Volumes cannot be negative.")
                return
        else:
            volumes_value = None

        # Rating
        if rating:
            try:
                rating_value = float(rating)
            except ValueError:
                status.update("❌ Book rating must be a number.")
                return

            if not 0 <= rating_value <= 20:
                status.update(
                    "❌ Book rating must be between 0 and 20."
                )
                return
        else:
            rating_value = None

        try:
            with sqlite3.connect(DB_PATH) as conn:
                conn.execute(
                    f"""
                    INSERT INTO {BOOK_TABLE}
                    (code, Name, Reads, Volumes, Rating)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        code,
                        name,
                        reads_value,
                        volumes_value,
                        rating_value,
                    ),
                )

                conn.commit()

            status.update("✅ Book inserted successfully.")

            self.query_one("#book_code", Input).value = ""
            self.query_one("#book_name", Input).value = ""
            self.query_one("#book_reads", Input).value = ""
            self.query_one("#book_volumes", Input).value = ""
            self.query_one("#book_rating", Input).value = ""

        except sqlite3.IntegrityError as e:
            self.handle_integrity_error(
                e,
                status,
                "Book",
            )

        except sqlite3.Error as e:
            status.update(f"❌ SQLite error: {e}")

    # =========================================================
    # DATABASE ERRORS
    # =========================================================

    def handle_integrity_error(
        self,
        error: sqlite3.IntegrityError,
        status: Label,
        record_type: str,
    ) -> None:
        error_text = str(error).lower()

        if "unique constraint failed" in error_text:
            # Get the column after the final "."
            column = error_text.split(".")[-1].strip()

            if column == "code":
                status.update(
                    f"❌ {record_type} code already exists."
                )

            elif column == "name":
                status.update(
                    f"❌ {record_type} name already exists."
                )

            elif column == "mg_code":
                status.update(
                    "❌ Manga code already exists."
                )

            else:
                status.update(
                    f"❌ Duplicate value in {column}."
                )

        elif "not null constraint failed" in error_text:
            status.update(
                f"❌ A required database field is missing."
            )

        else:
            status.update(
                f"❌ Database constraint error: {error}"
            )


if __name__ == "__main__":
    AppTUI().run()
