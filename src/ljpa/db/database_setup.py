import datetime
from os import path, getcwd

from peewee import CharField, DateField, Model, SqliteDatabase, TextField, BooleanField

from utilities.config import RESOURCES_PATH

# Define the path for the SQLite database file.
DATABASE_FILE_PATH = path.join(getcwd(), RESOURCES_PATH, "ai_database.db")
database = SqliteDatabase(DATABASE_FILE_PATH)


class TextEntry(Model):
    """
    Model representing a text entry for long-form AI discussions.
    """

    content = TextField()
    created_date = DateField(default=datetime.date.today)
    screenshot_path = CharField()
    cv_match = CharField(max_length=40, null=True)
    vacancy_title = CharField(max_length=40, null=True)
    credentials = CharField(max_length=40, null=True)
    visa_sponsorship = CharField(max_length=40, null=True)
    sent = CharField(max_length=40, null=True)
    deleted = BooleanField(null=True)
    spare1 = CharField(max_length=40, null=True)
    spare2 = CharField(max_length=40, null=True)
    spare3 = CharField(max_length=40, null=True)

    class Meta:
        database = database


def setup_database():
    """
    Initializes the SQLite database and creates required tables.
    If the TextEntry table is empty, a default entry is added.
    """
    database.connect()
    database.create_tables([TextEntry], safe=True)

    if not TextEntry.select().exists():
        TextEntry.create(
            content="Initial AI discussion",
            created_date=datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S"),
            screenshot_path="/screenshots/ai_intro.png",
            cv_match="test",
            vacancy_title="test",
            credentials="test",
            visa_sponsorship="test",
            sent="True",
            deleted=False,
            spare1="AI Introduction",
            spare2="Technical Overview",
            spare3="Future Trends",
        )


if __name__ == "__main__":
    setup_database()
    print("AI database created with initial long-form entry!")
