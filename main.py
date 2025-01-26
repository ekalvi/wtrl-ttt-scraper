import time

from wtrl_ttt_scraper.calculate import calculate_percentile, latest_race, race_to_date
from config import Config
from wtrl_ttt_scraper.render import render_results, generate_index_html
from wtrl_ttt_scraper.scrape import (
    scrape_race,
    is_authenticated,
    get_authentication_credentials,
)
from wtrl_ttt_scraper.format import iso_8601_format


if __name__ == "__main__":
    try:
        config = Config.load()
        print(f"Config loaded for teams: {config.teams}")
    except FileNotFoundError:
        raise f"Error: Configuration file not found."
    except KeyError as e:
        raise f"Error: Missing key in configuration file: {e}"

    if not is_authenticated():
        # we need to update the credentials
        # credentials = get_authentication_credentials()
        # Config.save_credentials(credentials)
        # assert is_authenticated()
        pass

    latest = latest_race()
    summary_stats = {}
    for config_team in config.teams:
        summary_stats[config_team.team_name] = []

    for race in range(latest, 0, -1):
        wtrl_result, cached = scrape_race(race, refresh_cache=False)
        if wtrl_result:
            for config_team in config.teams:
                team = wtrl_result.get_team(config_team.team_name)
                if not team and config_team.aliases:
                    for alias in config_team.aliases:
                        team = wtrl_result.get_team(alias)
                        if team:
                            break

                if team:
                    summary_stats[config_team.team_name].append(
                        {
                            "Race": race,
                            "Date": iso_8601_format(race_to_date(race)),
                            "Rank": team.rank,
                            "Entries": wtrl_result.entries,
                            "Percentile": calculate_percentile(
                                team.rank, wtrl_result.entries
                            ),
                            "Riders": team.rider_count,
                            "Team": team.rider_initials_list("·"),
                            "Time": team.finish_time,
                            "Speed (km/h)": team.average_speed,
                            "P1-4 (W/kg)": team.average_power,
                            "Coffee️ Class": team.coffee_class,
                            "Coffee Rank": wtrl_result.coffee_rank(team),
                            "Coffee️ Entries": wtrl_result.coffee_class_entries(
                                team.coffee_class
                            ),
                            "Coffee️ Percentile": calculate_percentile(
                                wtrl_result.coffee_rank(team),
                                wtrl_result.coffee_class_entries(team.coffee_class),
                            ),
                        }
                    )
        if not cached:
            time.sleep(0.5)

    # render all the outputs
    for key, val in summary_stats.items():
        if val:
            render_results(val, key)
        else:
            # TODO: handle no results
            pass

    generate_index_html(list(summary_stats.keys()))
