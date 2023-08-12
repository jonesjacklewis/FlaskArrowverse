"""
The flask application.
"""

import sqlite3

from dataclasses import dataclass
from typing import Any, Union

from flask import Flask, redirect, render_template, request, url_for

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
    episode_id: int
    showname: str
    season: int
    episode: int
    name: str
    airdate: str
    image: str
    background_color: str = "#000000"
    foreground_color: str = "#ffffff"
    watched: int = 0

@dataclass
class EpisodeWatchState:
    """
    The EpisodeWatchState class represents the watched status of an episode.
    """
    episode_id: int
    watched: int = 0

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

def get_list_of_episodes(watchlist_uuid: Union[str, None] = None) -> list[ArrowverseShowEpisode]:
    """
    Create a list of ArrowverseShowEpisode objects from the database.

    Parameters:
        watchlist_uuid (Union[str, None], optional): The watchlist uuid. Defaults to None.
    Returns:
        list[ArrowverseShowEpisode]: A list of ArrowverseShowEpisode objects
    """

    # Create a connection to the database
    conn: sqlite3.Connection = sqlite3.connect('arrowverse.db')

    # Create a cursor
    c: sqlite3.Cursor = conn.cursor()

    # Create a list of ArrowverseShow objects
    arrowverse_shows: list[ArrowverseShowEpisode] = []

    query: str = """
        SELECT Episodes.EpisodeId, Shows.Name, Seasons.SeasonNumber, Episodes.EpisodeNumber, Episodes.Name, Episodes.AirDate, Episodes.Image, Shows.BackgroundColor, Shows.ForegroundColor
        FROM Shows
        JOIN Seasons ON Shows.ShowId = Seasons.ShowId
        JOIN Episodes ON Seasons.SeasonId = Episodes.SeasonId
        ORDER BY Episodes.AirDate ASC
    """

    if type(watchlist_uuid) == str:
        # get the episode details like normal, but also get the watched status from the watchlist if it exists
        query = f"""
        SELECT 
        Episodes.EpisodeId,
        Shows.Name AS ShowName,
        Seasons.SeasonNumber,
        Episodes.EpisodeNumber,
        Episodes.Name AS EpisodeName,
        Episodes.AirDate,
        Episodes.Image,
        Shows.BackgroundColor,
        Shows.ForegroundColor,
        CASE
            WHEN WatchlistItems.Watched IS NOT NULL 
            THEN WatchlistItems.Watched 
            ELSE 0 
            END 
        AS Watched
        FROM Episodes
        JOIN Seasons
        ON Episodes.SeasonId = Seasons.SeasonId
        JOIN Shows
        ON Seasons.ShowId = Shows.ShowId
        LEFT JOIN
        (
            SELECT DISTINCT EpisodeId, Watched
            FROM WatchlistItems
            JOIN Watchlists
            ON WatchlistItems.WatchlistId = Watchlists.WatchlistId
            WHERE Watchlists.WatchlistUUID = '{watchlist_uuid}'
        ) AS WatchlistItems
        ON Episodes.EpisodeId = WatchlistItems.EpisodeId
        ORDER BY Episodes.AirDate ASC;
        """

    # Get all the episodes from the database
    c.execute(query)

    # Loop through the results
    for row in c.fetchall():
        # Create an ArrowverseShow object
        if len(row) == 9: # if the watchlist_uuid is not provided, then the row will only have 9 columns
            row = list(row)
            row.append(0) # add the watched status to the end of the row
            row = tuple(row)

        arrowverse_show: ArrowverseShowEpisode = ArrowverseShowEpisode(
            episode_id=row[0],
            showname=row[1],
            season=row[2],
            episode=row[3],
            name=row[4],
            airdate=row[5],
            image=row[6],
            background_color=row[7],
            foreground_color=row[8],
            watched=row[9]
        )

        # Add the ArrowverseShow object to the list
        arrowverse_shows.append(arrowverse_show)

    # Close the connection
    conn.close()

    # Return the list of ArrowverseShow objects
    return arrowverse_shows

def get_watchlist_display_name(uuid: Union[str, None]) -> Union[str, None]:
    """
    Get the display name of a watchlist from the database.

    Parameters:
        uuid (Union[str, None]): The uuid of the watchlist.
    Returns:
        Union[str, None]: The display name of the watchlist or None if the watchlist does not exist.
    """

    if type(uuid) != str:
        return None

    # Create a connection to the database
    conn: sqlite3.Connection = sqlite3.connect('arrowverse.db')

    # Create a cursor
    c: sqlite3.Cursor = conn.cursor()

    query: str = f"""
        SELECT
        DisplayName
        FROM
        Watchlists
        WHERE
        WatchlistUUID = '{uuid}'
        """

    c.execute(query)

    # check if the watchlist exists
    if len(c.fetchall()) == 0:
        return None

    c.execute(query)

    # get the display name
    display_name: str = c.fetchone()[0]

    # Close the connection
    conn.close()

    return display_name

def ensure_watchlist_exists(watchlist_uuid: str, watchlist_display_name: str) -> None:
    """
    Ensure that a watchlist exists in the database. If it does not exist, create it.

    Parameters:
        watchlist_uuid (str): The uuid of the watchlist.
        watchlist_display_name (str): The display name of the watchlist.
    Returns:
        None
    """
    conn: sqlite3.Connection = sqlite3.connect('arrowverse.db')

    # Create a cursor
    c: sqlite3.Cursor = conn.cursor()

    query: str = f"""
        SELECT
        WatchlistId
        FROM
        Watchlists
        WHERE
        WatchlistUUID = '{watchlist_uuid}'
        """

    c.execute(query)

    # check if the watchlist exists
    if len(c.fetchall()) == 0:
        # create the watchlist
        query: str = f"""
            INSERT
            INTO Watchlists
            (WatchlistUUID, DisplayName)
            VALUES
            ('{watchlist_uuid}', '{watchlist_display_name}')
            """

        c.execute(query)

        conn.commit()

def get_watchlist_id(watchlist_uuid: str) -> int:
    """
    Get the id of a watchlist from the database.

    Parameters:
        watchlist_uuid (str): The uuid of the watchlist.
    Returns:
        int: The id of the watchlist or -1 if the watchlist does not exist.
    """
    conn: sqlite3.Connection = sqlite3.connect('arrowverse.db')

    # Create a cursor
    c: sqlite3.Cursor = conn.cursor()

    query: str = f"""
        SELECT
        WatchlistId
        FROM
        Watchlists
        WHERE
        WatchlistUUID = '{watchlist_uuid}'
        """

    c.execute(query)

    # check if the watchlist exists
    if len(c.fetchall()) == 0:
        return -1

    c.execute(query)

    # get the watchlist id
    watchlist_id: int = c.fetchone()[0]

    conn.close()

    return watchlist_id

def add_episodes(watchlist_uuid: str, watchlist_display_name: str, episode_watch_states: list[EpisodeWatchState]) -> None:
    """
    Add episodes to a watchlist.

    Parameters:
        watchlist_uuid (str): The uuid of the watchlist.
        watchlist_display_name (str): The display name of the watchlist.
        episode_watch_states (list[EpisodeWatchState]): A list of EpisodeWatchState objects.
    Returns:
        None
    """
    # check if the watchlist exists
    ensure_watchlist_exists(watchlist_uuid, watchlist_display_name)

    # get the watchlist id
    id: int = get_watchlist_id(watchlist_uuid)

    if id == -1:
        return

    conn: sqlite3.Connection = sqlite3.connect('arrowverse.db')

    # Create a cursor
    c: sqlite3.Cursor = conn.cursor()

    for episode_watch_state in episode_watch_states:
        episode_id: int = episode_watch_state.episode_id
        watched: int = episode_watch_state.watched

        query: str = f"""
            SELECT
            WatchlistItemId
            FROM
            WatchlistItems
            WHERE
            WatchlistId = {id} AND EpisodeId = {episode_id}
            """

        c.execute(query)

        # check if the episode is already in the watchlist
        if len(c.fetchall()) == 0:
            query: str = f"""
                INSERT
                INTO WatchlistItems
                (WatchlistId, EpisodeId, Watched)
                VALUES
                ({id}, {episode_id}, {watched})
                """

        else:
            # if the episode is already in the watchlist, and it is not watched, set it to watched else set it to not watched
            query: str = f"""
                UPDATE
                WatchlistItems
                SET
                Watched = {watched}
                WHERE
                WatchlistId = {id}
                AND EpisodeId = {episode_id}
                """
        c.execute(query)

    conn.commit()

@app.route('/')
def index():
    """
    The index route.

    Parameters:
        None
    Returns:
        str: The rendered template
    """

    # Get the query parameters
    shownames: Union[str, None] = request.args.get('shownames')
    watchlist_uuid: Union[str, None] = request.args.get('watchlist')
    watchlist_display_name: Union[str, None] = get_watchlist_display_name(
        watchlist_uuid)

    # Create a list of ArrowverseShow objects
    arrowverse_shows: list[ArrowverseShow] = get_shows()

    # Create a list of ArrowverseShowEpisode objects
    arrowverse_episodes: list[ArrowverseShowEpisode] = get_list_of_episodes(
        watchlist_uuid=watchlist_uuid)
    
    
    print(set(show.showname.lower() for show in arrowverse_shows))

    showname_map: dict[str, str] = {
        'dclot': 'DC Legends of Tomorrow',
        'tf': 'The Flash',
        'a': 'Arrow',
        'sg': 'Supergirl',
        'bw': 'Batwoman',
        'bl': 'Black Lightning',
    }

    if type(shownames) == str:
        shownames_list: list[str] = shownames.split(',')

        shownames_list = [showname_map[showname.lower()]
                          for showname in shownames_list]

        arrowverse_shows = [
            show for show in arrowverse_shows if show.showname in shownames_list]
        arrowverse_episodes = [
            episode for episode in arrowverse_episodes if episode.showname in shownames_list]

    # Render the template
    return render_template(
        'index.html',
        watchlist_uuid=watchlist_uuid,
        watchlist_display_name=watchlist_display_name,
        shows=arrowverse_shows,
        episodes=arrowverse_episodes
    )

# post endpoint /save_watchlist takes a JSON payload
@app.route('/save_watchlist', methods=['POST'])
def save_watchlist():
    """
    POST endpoint to save a watchlist.

    Parameters:
        None
    Returns:
        str: A redirect to the index route.
    """

    json_data: Any = request.get_json()

    if json_data is None:
        return redirect(url_for('index'))

    # if the watchlist_uuid is not in the JSON payload
    if 'watchlist_uuid' not in json_data:
        return redirect(url_for('index'))

    # if the watchlist_uuid is not a string
    if type(json_data['watchlist_uuid']) != str:
        return redirect(url_for('index'))

    # if the watchlist_uuid is empty
    if len(json_data['watchlist_uuid']) == 0:
        return redirect(url_for('index'))

    watchlist_uuid: str = json_data['watchlist_uuid']

    valid_display_name: bool = True

    # if the watchlist_display_name is not in the JSON payload
    if 'watchlist_display_name' not in json_data:
        valid_display_name = False

    # if the watchlist_display_name is not a string
    if type(json_data['watchlist_display_name']) != str:
        valid_display_name = False

    # if the watchlist_display_name is empty
    if len(json_data['watchlist_display_name']) == 0:
        valid_display_name = False
    
    watchlist_display_name: str = "My Watchlist"

    if valid_display_name:
        watchlist_display_name: str = json_data['watchlist_display_name']

    episode_watch_states: list[EpisodeWatchState] = []

    # loop through episode_watch_states attribute in the JSON payload
    for episode_watch_state in json_data['episode_watch_states']:
        state = EpisodeWatchState(
            episode_id=episode_watch_state['episode_id'],
            watched=episode_watch_state['watched']
            )
        episode_watch_states.append(state)
    


    add_episodes(watchlist_uuid, watchlist_display_name, episode_watch_states)

    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
