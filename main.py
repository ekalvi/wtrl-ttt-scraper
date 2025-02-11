import os
import time
from tqdm import tqdm
from config import Config
from wtrl_ttt_scraper.calculate import calculate_percentile, latest_race
from wtrl_ttt_scraper.format import slugify
from wtrl_ttt_scraper.render import generate_index_html, render_results
from wtrl_ttt_scraper.scrape import (
    scrape_result,
    is_authenticated,
    scrape_event,
    get_authentication_credentials,
    AuthenticationError,
)
from wtrl_ttt_scraper.deploy import deploy_all_sites  # Import deploy logic


def load_config():
    """Load configuration from `config.secret.json` if available, otherwise fallback to `config.json`."""
    config_file = (
        "config.secret.json" if os.path.exists("config.secret.json") else "config.json"
    )
    print(f"\n📂 Loading configuration from: {config_file}")
    return Config.load(config_file)


def main_scraper_logic(config_: Config):
    """Main scraping logic for all clubs and teams."""
    try:
        print("\n📊 Generating results for the following teams:\n")
        for club in config_.clubs:
            print(f"🏢 {club.club_name}")
            for team in club.teams:
                print(f"   ├── 🚴 {team.team_name}")
        print("\n")
    except FileNotFoundError:
        raise FileNotFoundError("❌ Error: Configuration file not found.")
    except KeyError as e:
        raise KeyError(f"❌ Error: Missing key in configuration file: {e}")

    # Authenticate once for all clubs
    if not is_authenticated():
        print("\n🔐 Authenticating with WTRL...")
        credentials = get_authentication_credentials()
        config_ = config_.save_credentials(credentials)
        assert is_authenticated()
        print("✅ Authentication successful!\n")

    latest = latest_race()

    # ✅ Fix: Use club names and team names as dictionary keys
    summary_stats = {
        club.club_name: {team.team_name: [] for team in club.teams}
        for club in config_.clubs
    }

    result_updates, event_updates, errors = [], [], []

    for race in tqdm(range(latest, 0, -1), desc="⏳ Processing Races"):
        try:
            event, cached_event = scrape_event(race, refresh_cache=False)
            should_refresh = not event.is_finalised and event.is_recent
            if should_refresh and cached_event:
                event, cached_event = scrape_event(race, refresh_cache=True)
            result, cached_result = scrape_result(race, refresh_cache=should_refresh)

        except AuthenticationError:
            errors.append(race)
            continue

        if not cached_event:
            event_updates.append(race)
        if not cached_result:
            result_updates.append(race)

        if result:
            for club in config_.clubs:
                for team_config in club.teams:
                    team = result.get_team(team_config.team_name)

                    # Check aliases if no exact team match found
                    if not team and team_config.aliases:
                        for alias in team_config.aliases:
                            team = result.get_team(alias)
                            if team:
                                break

                    if team:
                        summary_stats[club.club_name][team_config.team_name].append(
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

    print("\n📊 Summary of Updates:\n")

    if event_updates:
        print(
            f"📅 Events updated ({len(event_updates)}): {', '.join(map(str, event_updates))}"
        )
    else:
        print("📅 No event updates.")

    if result_updates:
        print(
            f"📊 Results updated ({len(result_updates)}): {', '.join(map(str, result_updates))}"
        )
    else:
        print("📊 No result updates.")

    if errors:
        print(f"❌ Errors ({len(errors)}): {', '.join(map(str, errors))}")
    else:
        print("✅ No errors encountered.")

    print("\n📄 Pages generated:")
    for club_name, team_results in summary_stats.items():
        print(f"\n🏢 {club_name}")
        for team_name, results in team_results.items():
            if results:
                club = next(
                    club for club in config_.clubs if club.club_name == club_name
                )
                render_results(results, club, team_name)
                print(f"   ├── 📄 {slugify(team_name)}.html")
            else:
                print(f"   ├── ⚠ No results found for {team_name}")

    for club in config_.clubs:
        generate_index_html(club)
        print(f"📄 Index generated: {club.club_results_dir}/index.html")


if __name__ == "__main__":
    config = load_config()
    main_scraper_logic(config)
    # ✅ Deploy all sites after results are generated
    deploy_all_sites(config)
