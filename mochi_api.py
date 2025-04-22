import argparse
import datetime
import sys

import httpx


class MochiAPI:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://app.mochi.cards/api"

    def get_all_cards(self) -> list[dict]:
        """Fetch all cards using pagination."""
        all_cards = []
        bookmark = None

        while True:
            url = f"{self.base_url}/cards/?limit=100"
            if bookmark:
                url += f"&bookmark={bookmark}"

            response = httpx.get(url, auth=(self.api_key, ""))

            if response.status_code != 200:
                print(f"Error fetching cards: {response.status_code}")
                print(response.text)
                sys.exit(1)

            data = response.json()
            all_cards.extend(data["docs"])

            # Check if we have more pages
            new_bookmark = data.get("bookmark")
            if new_bookmark == bookmark:
                break
            bookmark = new_bookmark

        return all_cards

    def get_cards_by_deck(self, deck_id: str) -> list[dict]:
        """Fetch all cards for a specific deck using pagination."""
        all_cards = []
        bookmark = None

        while True:
            url = f"{self.base_url}/cards/?deck-id={deck_id}"
            if bookmark:
                url += f"&bookmark={bookmark}"

            response = httpx.get(url, auth=(self.api_key, ""))

            if response.status_code != 200:
                print(f"Error fetching cards: {response.status_code}")
                print(response.text)
                sys.exit(1)

            data = response.json()
            all_cards.extend(data["docs"])

            # Check if we have more pages
            bookmark = data.get("bookmark")
            if not bookmark:
                break

        return all_cards

    def get_all_decks(self) -> list[dict]:
        """Fetch all decks using pagination."""
        all_decks = []
        bookmark = None

        while True:
            url = f"{self.base_url}/decks/"
            if bookmark:
                url += f"?bookmark={bookmark}"

            response = httpx.get(url, auth=(self.api_key, ""))

            if response.status_code != 200:
                print(f"Error fetching decks: {response.status_code}")
                print(response.text)
                sys.exit(1)

            data = response.json()
            all_decks.extend(data["docs"])

            # Check if we have more pages
            bookmark = data.get("bookmark")
            if not bookmark:
                break

        return all_decks


def count_cards(cards: list[dict]) -> dict[str, int]:
    """Count total cards and categorize by review status."""
    today = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    results = {
        "total": len(cards),
        "due_today": 0,
        "due_tomorrow": 0,
        "due_this_week": 0,
        "new": 0,
        "learning": 0,
        "reviewed_today": 0,
    }

    for card in cards:
        # Check review status
        reviews = card.get("reviews", [])

        # If no reviews or card is explicitly marked as new, it's a new card
        if not reviews or card.get("new?", False):
            results["new"] += 1
            continue

        # Get the most recent review
        latest_review = reviews[-1]

        # Check if reviewed today by looking at the most recent review
        if latest_review.get("date") and "date" in latest_review["date"]:
            review_date_str = latest_review["date"]["date"]
            review_date = datetime.datetime.fromisoformat(
                review_date_str.replace("Z", "+00:00")
            )
            if review_date.date() == today.date():
                results["reviewed_today"] += 1

        # Check if due
        if latest_review.get("due") and "date" in latest_review["due"]:
            due_date_str = latest_review["due"]["date"]
            due_date = datetime.datetime.fromisoformat(
                due_date_str.replace("Z", "+00:00")
            )

            # Check if due today
            if due_date.date() == today.date():
                results["due_today"] += 1
            # Due tomorrow
            elif due_date.date() == (today + datetime.timedelta(days=1)).date():
                results["due_tomorrow"] += 1
            # Due this week (but not today or tomorrow)
            elif (
                due_date.date() > (today + datetime.timedelta(days=1)).date()
                and due_date.date() <= (today + datetime.timedelta(days=7)).date()
            ):
                results["due_this_week"] += 1

        # Check if in learning phase (interval < 21 days)
        if "interval" in latest_review and latest_review["interval"] < 21:
            results["learning"] += 1

    return results


def post_to_beeminder(api_key: str, username: str, goal: str, value: int):
    """Post data to Beeminder API."""
    url = f"https://www.beeminder.com/api/v1/users/{username}/goals/{goal}/datapoints.json"

    data = {
        "auth_token": api_key,
        "value": value,
        "comment": f"Mochi cards reviewed on {datetime.datetime.now().strftime('%Y-%m-%d')}",
    }

    response = httpx.post(url, data=data)

    if response.status_code == 200:
        print(f"Successfully posted {value} to Beeminder goal {goal}")
    else:
        print(f"Error posting to Beeminder: {response.status_code}")
        print(response.text)


def is_successful_review_day(counts: dict[str, int], minimum_cards: int = 10) -> bool:
    """Determine if today counts as a successful review day."""
    return counts["due_today"] == 0 or counts["reviewed_today"] >= minimum_cards


def assert_not_none(value, name: str = "value"):
    if value is None:
        raise ValueError(f"{name}={value} should not be None!")
    return value


def main():
    parser = argparse.ArgumentParser(
        description="Count Mochi cards and optionally post to Beeminder"
    )
    parser.add_argument("--mochi-key", required=True, help="Mochi API key")
    parser.add_argument("--deck-id", help="Specific deck ID to count (optional)")
    parser.add_argument("--beeminder", action="store_true", help="Post to Beeminder")
    parser.add_argument("--beeminder-key", help="Beeminder API key")
    parser.add_argument("--beeminder-user", help="Beeminder username")
    parser.add_argument("--beeminder-goal", help="Beeminder goal name")
    parser.add_argument(
        "--minimum-cards",
        type=int,
        default=10,
        help="Minimum cards for a successful review day",
    )

    args = parser.parse_args()

    mochi = MochiAPI(args.mochi_key)

    if args.deck_id:
        cards = mochi.get_cards_by_deck(args.deck_id)
    else:
        cards = mochi.get_all_cards()

    counts = count_cards(cards)
    success_value = is_successful_review_day(
        counts, minimum_cards=args.minimum_cards
    )

    if args.beeminder:
        assert_not_none(args.beeminder_key, "Beeminder API key")
        assert_not_none(args.beeminder_user, "Beeminder username")
        assert_not_none(args.beeminder_goal, "Beeminder goal")
        post_to_beeminder(
            args.beeminder_key,
            args.beeminder_user,
            args.beeminder_goal,
            int(success_value),
        )


if __name__ == "__main__":
    main()
