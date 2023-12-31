"""
Sets up the database and saves the shows to the database.
"""

# standard library full imports
import json
import os
import requests
import sqlite3

# standard library partial imports
from dataclasses import dataclass
from typing import Any, Union

@dataclass
class MockResponse:
    """
    MockResponse class
    """
    status_code: int = 0

@dataclass
class TVMazeShow:
    """
    TVMazeShow class
    """
    showname: str
    showcode: str
    background_color: str = "#000000"
    foreground_color: str = "#ffffff"

@dataclass
class Show:
    """
    Show class
    """
    name: str
    image: str
    background_color: str = "#000000"
    foreground_color: str = "#ffffff"

@dataclass
class Season:
    """
    Season class
    """
    season_number: int

@dataclass
class Episode:
    """
    Episode class
    """
    episode_number: int
    name: str
    air_date: str
    image: str

# constants
JSON_DIRECTORY: str = "json"
DB_FILENAME: str = "arrowverse.db"

def create_sqlite_database() -> None:
    """
    Creates the SQLite database and tables if they do not exist.

    Parameters:
        None
    Returns:
        None
    """

    with sqlite3.connect(DB_FILENAME) as conn:
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Shows (
                ShowId INTEGER PRIMARY KEY AUTOINCREMENT,
                Name TEXT NOT NULL,
                BackgroundColor TEXT NOT NULL,
                ForegroundColor TEXT NOT NULL,
                Image TEXT
            );
        """
                       )

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Seasons (
                SeasonId INTEGER PRIMARY KEY AUTOINCREMENT,
                ShowId INTEGER NOT NULL,
                SeasonNumber INTEGER NOT NULL,
                FOREIGN KEY(ShowId) REFERENCES Shows(ShowId)
            );
        """
                       )

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Episodes (
                EpisodeId INTEGER PRIMARY KEY AUTOINCREMENT,
                SeasonId INTEGER NOT NULL,
                EpisodeNumber INTEGER NOT NULL,
                Name TEXT NOT NULL,
                AirDate TEXT NOT NULL,
                Image TEXT,
                FOREIGN KEY(SeasonId) REFERENCES Seasons(SeasonId)
            );
        """
                       )

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Watchlists (
                WatchlistId INTEGER PRIMARY KEY AUTOINCREMENT,
                WatchlistUUID TEXT NOT NULL UNIQUE,
                DisplayName TEXT NOT NULL
            );
        """
                       )

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS WatchlistItems (
                WatchlistItemId INTEGER PRIMARY KEY AUTOINCREMENT,
                WatchlistId INTEGER NOT NULL,
                EpisodeId INTEGER NOT NULL,
                Watched INTEGER DEFAULT 0,
                FOREIGN KEY(WatchlistId) REFERENCES Watchlists(WatchlistId),
                FOREIGN KEY(EpisodeId) REFERENCES Episodes(EpisodeId)
            );
        """
                       )

        conn.commit()

def save_show(show_name: str, show_code: str, background_color: str, foreground_color: str) -> None:
    """
    Saves the show to the database, using the TVMaze API.

    Parameters:
        show_name (str): The name of the show
        show_code (str): The TVMaze show code
        background_color (str): The background color of the show
        foreground_color (str): The foreground color of the show
    Returns:
        None
    """

    json_path: str = f'{JSON_DIRECTORY}/{show_name}.json'

    show: Any = None

    if os.path.exists(json_path):
        # load json file

        with open(json_path, 'r') as f:
            show = json.load(f)

    response: Union[MockResponse, requests.Response] = MockResponse()

    if show is None:
        print("Making request to API")
        url: str = f"https://api.tvmaze.com/shows/{show_code}?embed[]=episodes&embed[]=seasons"
        response = requests.get(url)

    if response.status_code in [0, 200]:

        if not os.path.exists(JSON_DIRECTORY):
            os.makedirs(JSON_DIRECTORY)

        if response.status_code == 200 and type(response) is requests.Response:
            show: Any = response.json()

            # if json/{show_name}.json does not exist, create it
            if not os.path.exists(json_path):
                with open(json_path, 'w') as f:
                    print("Writing JSON")
                    f.write(response.text)

        show_name_json: str = show['name']
        show_image: Any = show['image']['original']

        # get seasons and episodes

        with sqlite3.connect(DB_FILENAME) as conn:
            cursor: sqlite3.Cursor = conn.cursor()

            # create show object
            show_obj: Show = Show(show_name_json, show_image)

            cursor.execute("""
                INSERT
                INTO Shows (
                    Name,
                    Image,
                    BackgroundColor,
                    ForegroundColor
                )
                VALUES (
                        ?,
                        ?,
                        ?,
                        ?
                )
            """, (show_obj.name, show_obj.image, background_color, foreground_color))

            print(show_obj.name)
            cursor.execute("""
                SELECT
                ShowId
                From Shows
                WHERE
                Name = ?
            """, (show_obj.name,))

            show_id: int = cursor.fetchone()[0]

            seasons: Any = show['_embedded']['seasons']

            for season in seasons:
                season_number: Any = season['number']

                if not str(season_number).isdigit():
                    raise TypeError("Season Number isn't an integer!")

                season_number = int(season_number)

                # create season object
                season_obj = Season(season_number)

                cursor.execute("""
                    INSERT INTO
                    Seasons (
                        ShowId,
                        SeasonNumber
                    )
                    VALUES (
                        ?,
                        ?
                    )
                """, (show_id, season_obj.season_number))

            # episodes
            episodes: Any = show['_embedded']['episodes']

            for episode in episodes:
                season_number: Any = episode['season']

                if not str(season_number).isdigit():
                    raise TypeError("Season Number is not an integer!")

                season_number = int(season_number)

                cursor.execute("""
                    SELECT
                    SeasonId
                    FROM
                    Seasons
                    WHERE
                    ShowId = ?
                    AND SeasonNumber = ?
                """, (show_id, season_number))

                season_id: int = cursor.fetchone()[0]

                episode_number: Any = episode['number']

                if not str(episode_number).isdigit():
                    raise TypeError("Episode Number isn't an integer!")

                episode_number = int(episode_number)

                episode_name: str = str(episode['name'])
                episode_air_date: str = str(episode['airdate'])
                episode_image: str = str(episode['image']['original'])

                # create episode object
                episode_obj = Episode(
                    episode_number,
                    episode_name,
                    episode_air_date,
                    episode_image
                )

                cursor.execute(
                    """
                    INSERT INTO
                    Episodes (
                        SeasonId,
                        EpisodeNumber,
                        Name,
                        AirDate,
                        Image
                    )
                    VALUES (
                        ?,
                        ?,
                        ?,
                        ?,
                        ?
                    )
                    """, (
                        season_id,
                        episode_obj.episode_number,
                        episode_obj.name,
                        episode_obj.air_date,
                        episode_obj.image
                    )
                )

            conn.commit()

def main() -> None:
    """
    Main function

    Parameters:
        None
    Returns:
        None
    """

    create_sqlite_database()

    shows: list[TVMazeShow] = [
        TVMazeShow("Arrow", "4", "#013300", "#ffffff"),
        TVMazeShow("The Flash", "13", '#AB0020', '#ffffff'),
        TVMazeShow("Supergirl", "1850", '#0200FF', '#ffffff'),
        TVMazeShow("Legends of Tomorrow", "1851", '#BBBBBB', '#000000'),
        TVMazeShow("Batwoman", "37776", "#B40800", "#ffffff"),
        TVMazeShow("Black Lightning", "20683", '#F3CC06', '#000000'),
    ]

    for show in shows:
        save_show(show.showname, show.showcode,
                  show.background_color, show.foreground_color)

if __name__ == "__main__":
    main()
