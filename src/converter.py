"""Convert solver outputs to markdown files."""

import argparse
from pathlib import Path

from trip_solver.models.internal import Events
from trip_solver.util.cost_matrix import load_cost_matrix_from_json

from consts import CURRENT_SEASON, SOURCE
from format import (
    create_league_index_page,
    create_solution_markdown,
    create_team_index_page,
)


def main() -> None:
    """
    Convert solver outputs to Jekyll-ready Markdown files.

    The input directory are required to provide the following files:
    - distance_matrix.json
    - duration_matrix.json
    - events.json
    in the format specified by the trip solver models.

    The input directory is also required to contain an solutions subdirectory,
    containing the results of invoking the solver on the data files in the input directory.

    It is assumed that each directory in the solutions directory corresponds to a team, and
    each file in the team directory uses the solver output format.
    """
    parser = argparse.ArgumentParser(description="Ultimate Fan Trip Solver CLI")
    parser.add_argument("input_dir", type=str, help="Path to the input directory")
    args = parser.parse_args()

    input_dir = Path(args.input_dir)

    if not input_dir.is_dir():
        raise ValueError(
            f"Input directory '{input_dir}' does not exist or is not a directory.",
        )
    if not (input_dir / "solutions").is_dir():
        raise ValueError(
            f"Input directory '{input_dir}' does not contain a 'solutions' subdirectory.",
        )

    for required_file in [
        "distance_matrix.json",
        "duration_matrix.json",
        "events.json",
    ]:
        if not (input_dir / required_file).is_file():
            raise ValueError(f"Required file '{required_file}' not found in input directory.")

    events = Events.model_validate_json((input_dir / "events.json").read_text())
    distance_matrix = load_cost_matrix_from_json(input_dir / "distance_matrix.json")
    duration_matrix = load_cost_matrix_from_json(input_dir / "duration_matrix.json")

    create_league_index_page(
        input_dir / "solutions",
        SOURCE / CURRENT_SEASON / input_dir.name,
        (input_dir.name).upper(),
    )

    for team_dir in (input_dir / "solutions").iterdir():
        create_team_index_page(
            team_dir,
            SOURCE / CURRENT_SEASON / input_dir.name / team_dir.name,
        )
        for solution_file in team_dir.iterdir():
            if solution_file.is_file():
                create_solution_markdown(
                    solution_file,
                    SOURCE
                    / CURRENT_SEASON
                    / input_dir.name
                    / team_dir.name
                    / f"{(solution_file.name).replace('.txt', '.md')}",
                    events,
                    distance_matrix,
                    duration_matrix,
                )


if __name__ == "__main__":
    main()
