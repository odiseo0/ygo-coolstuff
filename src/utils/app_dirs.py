from pathlib import Path

from platformdirs import user_data_dir


APP_NAME = "coolstuffscrape"
DB_FILENAME = "card_database.db"
DB_SUBDIR = "db"
TEMPLATE_FILENAME = "Template.xlsx"


def get_app_data_dir() -> Path:
    path = Path(user_data_dir(APP_NAME, APP_NAME))
    path.mkdir(parents=True, exist_ok=True)

    return path


def get_db_path() -> Path:
    base = get_app_data_dir()
    db_dir = base / DB_SUBDIR
    db_dir.mkdir(parents=True, exist_ok=True)

    return db_dir / DB_FILENAME


def get_template_path() -> Path:
    return get_app_data_dir() / TEMPLATE_FILENAME
