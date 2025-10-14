"""Formatters to build Jekyll-ready markdown files."""

from inspect import cleandoc
from itertools import pairwise
from pathlib import Path
from zoneinfo import ZoneInfo

from trip_solver.models.internal import CostMatrix, Event, Events
from trip_solver.util.google_maps_util import format_route_url

from consts import CURRENT_SEASON, SOURCE


def format_jekyll_link(name: str, path: Path) -> str:
    """Format a Jekyll-style markdown link to a path."""
    relative_path = path.relative_to(SOURCE)
    return f"[{name}]" + "({% link " + relative_path.as_posix() + " %})"


def beautify_file_system_name(name: str) -> str:
    """Convert a name used in the file system, usually snake case, to title case."""
    return name.replace("_", " ").title()


def create_league_index_page(
    input_dir: Path,
    output_dir: Path,
    title: str,
    season: str = CURRENT_SEASON,
) -> None:
    """
    Input directory should be the root of all solutions for a league.

    Output directory must be under the publishing source.
    """
    if SOURCE not in output_dir.parents:
        raise ValueError(f"Path '{output_dir}' is not under publishing source '{SOURCE}'.")

    output_dir.mkdir(parents=True, exist_ok=True)

    front_matter = cleandoc(
        f"""
        ---
        title: {title}, {season} season
        ---
        """,
    )
    team_list_heading = "# Teams"
    teams = sorted([child.name for child in input_dir.iterdir() if child.is_dir()])
    team_list = "\n".join([
        f"- {
            format_jekyll_link(beautify_file_system_name(team), output_dir / team / 'index.md')
        }"
        for team in teams
    ])
    back_link = format_jekyll_link("Home", SOURCE / "index.md")

    (output_dir / "index.md").write_text(
        f"{front_matter}\n\n{team_list_heading}\n{team_list}\n\n{back_link}\n",
    )


def create_team_index_page(
    input_dir: Path,
    output_dir: Path,
    season: str = CURRENT_SEASON,
) -> None:
    """
    Input directory should be the directory containing solutions for a team.

    Output directory must be under the publishing source.
    """
    if SOURCE not in output_dir.parents:
        raise ValueError(f"Path '{output_dir}' is not under publishing source '{SOURCE}'.")

    output_dir.mkdir(parents=True, exist_ok=True)

    front_matter = cleandoc(
        f"""
        ---
        title: {beautify_file_system_name(input_dir.name)}, {season} season
        ---
        """,
    )
    solution_list_heading = "# Optimization Criteria"
    solutions = sorted([child for child in input_dir.iterdir() if child.is_file()])
    solutions_list = "\n".join([
        f"- {
            format_jekyll_link(
                beautify_file_system_name(solution.stem),
                output_dir / f'{solution.name.replace(".txt", ".md")}',
            )
        }"
        for solution in solutions
    ])
    back_link = format_jekyll_link(
        f"Back to {output_dir.parent.name.upper()}, {season} season",
        output_dir.parent / "index.md",
    )

    (output_dir / "index.md").write_text(
        f"{front_matter}\n\n{solution_list_heading}\n{solutions_list}\n\n{back_link}\n",
    )


def readable_time(seconds: int) -> str:
    """Convert seconds to a human-readable string."""
    if seconds < 60:  # noqa: PLR2004
        return f"{seconds} seconds"

    minutes_all, seconds_part = divmod(seconds, 60)
    if minutes_all < 60:  # noqa: PLR2004
        return f"{minutes_all} minutes, {seconds_part} seconds"

    hours_all, minutes_part = divmod(minutes_all, 60)
    if hours_all < 24:  # noqa: PLR2004
        return f"{hours_all} hours, {minutes_part} minutes"

    days_all, hours_part = divmod(hours_all, 24)
    return f"{days_all} days, {hours_part} hours, {minutes_part} minutes"


def readable_distance(meters: int) -> str:
    """Convert meters to a string of kilometers and miles."""
    kilometers = meters / 1000
    miles = meters / 1609.34
    return f"{kilometers:.1f} km / {miles:.1f} miles"


def format_trip_details(
    trip: list[Event],
    distance_matrix: CostMatrix,
) -> str:
    """Produce a description of a trip from a list of events in the order visited."""
    trip_details = ""

    for index, (event_1, event_2) in enumerate(pairwise(trip), start=1):
        game_time = event_1.time.astimezone(ZoneInfo("America/New_York")).strftime(
            "%b %d %Y, %I:%M%p %Z",
        )
        game_desc = f"Attend the game against the **{event_1.home_team.name}** in {event_1.venue.name} on **{game_time}**."  # noqa: E501

        driving_distance = readable_distance(
            distance_matrix[event_1.venue.id][event_2.venue.id],
        )
        route_link = format_route_url([event_1.venue, event_2.venue])
        travel_desc = f"Then [drive]({route_link}) {driving_distance} to {event_2.venue.name}."

        trip_details += f"{index}. {game_desc} {travel_desc}\n"

    final_game_time = (
        trip[-1]
        .time.astimezone(ZoneInfo("America/New_York"))
        .strftime(
            "%b %d %Y, %I:%M%p %Z",
        )
    )
    trip_details += f"{len(trip)}. Attend the game against **{trip[-1].home_team.name}** in {trip[-1].venue.name} at **{final_game_time}**."  # noqa: E501

    return trip_details


def create_solution_markdown(
    input_file: Path,
    output_file: Path,
    events: Events,
    distance_matrix: CostMatrix,
    duration_matrix: CostMatrix,
    season: str = CURRENT_SEASON,
) -> None:
    """Format the input solution file into an informational markdown file."""
    if SOURCE not in output_file.parents:
        raise ValueError(f"Path '{output_file}' is not under publishing source '{SOURCE}'.")

    output_file.parent.mkdir(parents=True, exist_ok=True)

    event_index = {event.id: event for event in events.events}

    team_name = beautify_file_system_name(input_file.parent.name)
    front_matter = cleandoc(
        f"""
        ---
        title: {team_name}, {season} season, {beautify_file_system_name(input_file.stem)}
        ---
        """,
    )

    # first line is the total cost (will be recomputed here)
    # second line is the max daily driving hours
    # the remaining lines are the event IDs in the order visited
    solution = input_file.read_text(encoding="utf-8").strip().splitlines()
    max_daily_driving_hours = solution[1]
    trip = [event_index[event_id] for event_id in solution[2:]]

    total_driving_duration = 0
    total_driving_distance = 0
    total_trip_duration = (
        trip[-1].time.astimezone(ZoneInfo("America/New_York"))
        - trip[0].time.astimezone(ZoneInfo("America/New_York"))
    ).days + 1

    for event_1, event_2 in pairwise(trip):
        total_driving_duration += duration_matrix[event_1.venue.id][event_2.venue.id]
        total_driving_distance += distance_matrix[event_1.venue.id][event_2.venue.id]

    trip_summary_heading = "# Trip Summary"
    trip_summary = cleandoc(
        f"""
        - **Season:** {season}
        - **Team:** {team_name}
        - **Stops on the Trip:** {len(trip)}
        - **Most Required Driving in a Day:** {max_daily_driving_hours} hours
        - **Total Trip Duration:** {total_trip_duration} days
        - **Total Driving Distance:** {readable_distance(total_driving_distance)}
        - **Total Driving Duration:** {readable_time(total_driving_duration)}

        [View the route on Google Maps]({format_route_url([event.venue for event in trip])})
        """,
    )

    trip_details_heading = "# Trip Details"
    trip_details = format_trip_details(trip, distance_matrix)

    back_link = format_jekyll_link(
        f"Back to {team_name}, {season} season",
        output_file.parent / "index.md",
    )

    output_file.write_text(
        f"{front_matter}\n\n{trip_summary_heading}\n{trip_summary}\n\n{trip_details_heading}\n{trip_details}\n\n{back_link}\n",
        encoding="utf-8",
    )
