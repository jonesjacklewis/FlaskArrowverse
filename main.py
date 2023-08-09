"""
The flask application.
"""

import sqlite3

from dataclasses import dataclass

from flask import Flask, render_template

@dataclass
class ArrowverseShow:
    """
    The ArrowverseShow class represents a show in the Arrowverse.
    """
    showname: str
    show_image: str
    background_color: str = "#000000"
    foreground_color: str = "#ffffff"

@dataclass
class ArrowverseShowEpisode:
    """
    The ArrowverseShowEpisode class represents an episode in the Arrowverse.
    """
    showname: str
    season: int
    episode: int
    name: str
    airdate: str
    image: str
    background_color: str = "#000000"
    foreground_color: str = "#ffffff"

app = Flask(__name__)

def get_shows() -> list[ArrowverseShow]:
    """
    Create a list of ArrowverseShow objects from the database.

    Parameters:
        None
    Returns:
        list[ArrowverseShow]: A list of ArrowverseShow objects
    """

    # Create a connection to the database
    conn: sqlite3.Connection = sqlite3.connect('arrowverse.db')

    # Create a cursor
    c: sqlite3.Cursor = conn.cursor()

    # Create a list of ArrowverseShow objects
    arrowverse_shows: list[ArrowverseShow] = []

    # Get all the episodes from the database
    c.execute("""
        SELECT Shows.Name, Shows.Image, Shows.BackgroundColor, Shows.ForegroundColor
        FROM Shows
    """)

    # Loop through the results
    for row in c.fetchall():
        # Create an ArrowverseShow object
        arrowverse_show: ArrowverseShow = ArrowverseShow(
            showname=row[0],
            show_image=row[1],
            background_color=row[2],
            foreground_color=row[3]
        )

        # Add the ArrowverseShow object to the list
        arrowverse_shows.append(arrowverse_show)

    # Close the connection
    conn.close()

    # Return the list of ArrowverseShow objects
    return arrowverse_shows
 
def get_list_of_episodes() -> list[ArrowverseShowEpisode]:
    """
    Create a list of ArrowverseShowEpisode objects from the database.

    Parameters:
        None
    Returns:
        list[ArrowverseShowEpisode]: A list of ArrowverseShowEpisode objects
    """

    # Create a connection to the database
    conn: sqlite3.Connection = sqlite3.connect('arrowverse.db')

    # Create a cursor
    c: sqlite3.Cursor = conn.cursor()

    # Create a list of ArrowverseShow objects
    arrowverse_shows: list[ArrowverseShowEpisode] = []

    # Get all the episodes from the database
    c.execute("""
        SELECT Shows.Name, Seasons.SeasonNumber, Episodes.EpisodeNumber, Episodes.Name, Episodes.AirDate, Episodes.Image, Shows.BackgroundColor, Shows.ForegroundColor
        FROM Shows
        JOIN Seasons ON Shows.ShowId = Seasons.ShowId
        JOIN Episodes ON Seasons.SeasonId = Episodes.SeasonId
        ORDER BY Episodes.AirDate ASC
    """)

    # Loop through the results
    for row in c.fetchall():
        # Create an ArrowverseShow object
        arrowverse_show: ArrowverseShowEpisode = ArrowverseShowEpisode(
            showname=row[0],
            season=row[1],
            episode=row[2],
            name=row[3],
            airdate=row[4],
            image=row[5],
            background_color=row[6],
            foreground_color=row[7]
        )

        # Add the ArrowverseShow object to the list
        arrowverse_shows.append(arrowverse_show)

    # Close the connection
    conn.close()

    # Return the list of ArrowverseShow objects
    return arrowverse_shows

@app.route('/')
def index() -> str:
    """
    The index route.

    Parameters:
        None
    Returns:
        str: The HTML for the index page
    """

    shows: list[ArrowverseShow] = get_shows()
    episodes: list[ArrowverseShowEpisode] = get_list_of_episodes()
    return render_template('index.html', shows = shows, episodes = episodes)

if __name__ == '__main__':
    app.run(debug=True)
