import time

from tqdm import tqdm

from wtrl_ttt_scraper.calculate import calculate_percentile, latest_race
from config import Config
from wtrl_ttt_scraper.render import render_results, generate_index_html
from wtrl_ttt_scraper.scrape import (
    scrape_result,
    is_authenticated,
    scrape_event,
    get_authentication_credentials,
)


if __name__ == "__main__":
    try:
        config = Config.load()
        team_names = [team.team_name for team in config.teams]
        print(f"Generating results for: {team_names}\n")
    except FileNotFoundError:
        raise f"Error: Configuration file not found."
    except KeyError as e:
        raise f"Error: Missing key in configuration file: {e}"

    if not is_authenticated():
        # we need to update the credentials
        credentials = get_authentication_credentials()
        Config.save_credentials(credentials)
        assert is_authenticated()

    latest = latest_race()
    summary_stats = {}
    result_updates = []
    event_updates = []
    for config_team in config.teams:
        summary_stats[config_team.team_name] = []

    for race in tqdm(range(latest, 0, -1), desc="Processing Races"):
        event, cached_event = scrape_event(race, refresh_cache=False)
        result, cached_result = scrape_result(
            race, refresh_cache=not event.is_finalised
        )
        if not cached_event:
            event_updates.append(race)
        if not cached_result:
            result_updates.append(race)

        if result:
            for config_team in config.teams:
                team = result.get_team(config_team.team_name)
                if not team and config_team.aliases:
                    for alias in config_team.aliases:
                        team = result.get_team(alias)
                        if team:
                            break

                if team:
                    summary_stats[config_team.team_name].append(
                        {
                            "Race": race,
                            "Date": event.race_date,
                            "Course": event.course_name,
                            "Laps": event.laps,
                            "Rank": team.rank,
                            "Entries": result.entries,
                            "Percentile": calculate_percentile(
                                team.rank, result.entries
                            ),
                            "Riders": team.rider_count,
                            "Team": team.rider_initials_list("·"),
                            "Distance (km)": round(event.distance_km, 1),
                            "Time": team.finish_time,
                            "Speed (km/h)": team.average_speed,
                            "P1-4 (W/kg)": team.average_power,
                            "Coffee️ Class": team.coffee_class,
                            "Coffee Rank": result.coffee_rank(team),
                            "Coffee️ Entries": result.coffee_class_entries(
                                team.coffee_class
                            ),
                            "Coffee️ Percentile": calculate_percentile(
                                result.coffee_rank(team),
                                result.coffee_class_entries(team.coffee_class),
                            ),
                            "Status": event.status,
                        }
                    )
        if not (cached_result or cached_event):
            time.sleep(0.5)

    print(f'\nEvents updated: {", ".join([str(event) for event in event_updates])}')
    print(f'Results updated: {", ".join([str(result) for result in result_updates])}')

    # render all the outputs
    print("\nPages generated:")
    for key, val in summary_stats.items():
        if val:
            render_results(val, key)
        else:
            # TODO: handle no results
            pass

    generate_index_html(list(summary_stats.keys()))
