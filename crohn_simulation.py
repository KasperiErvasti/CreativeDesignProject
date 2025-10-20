from datetime import datetime, timedelta
from enum import Enum
import random, time
import winsound


class SeverityValues:
    def __init__(self, min_daily_rate, max_daily_rate, cluster_prob):
        self.min_daily_rate = min_daily_rate
        self.max_daily_rate = max_daily_rate
        self.cluster_prob = cluster_prob


class Severity(Enum):
    MILD = SeverityValues(min_daily_rate=3, max_daily_rate=5, cluster_prob=0.0)
    MODERATE = SeverityValues(min_daily_rate=6, max_daily_rate=10, cluster_prob=0.10)
    SEVERE = SeverityValues(min_daily_rate=11, max_daily_rate=20, cluster_prob=0.15)

    def __init__(self, values: SeverityValues):
        self.values = values

    def random_daily_rate(self) -> int:
        return random.randint(self.values.min_daily_rate, self.values.max_daily_rate)

    def should_cluster(
        self,
        hours_since_last_cluster: float | None,
        clusters_today: int,
        max_clusters_per_day=3,
    ):
        if clusters_today >= max_clusters_per_day:
            return False

        prob = self.values.cluster_prob
        if hours_since_last_cluster is not None:
            prob = min(prob * (hours_since_last_cluster / 4), prob)
        return random.random() < prob


def time_weighted_multiplier(hour: int):
    if 0 <= hour < 6:
        return 0.1
    elif 6 <= hour < 9:
        return 1.6
    elif 15 <= hour < 21:
        return 1.6
    else:
        return 1.0


def next_interval_minutes(
    current_hour: int,
    mean_minutes: float,
    remaining_time: float,
    remaining_events: int,
):
    adjusted_mean = mean_minutes / time_weighted_multiplier(current_hour)

    stddev = adjusted_mean * 0.3
    interval = random.gauss(adjusted_mean, stddev)

    interval = min(interval, adjusted_mean * 2) # Avoid very high values
    max_interval = remaining_time / remaining_events
    interval = min(interval, max_interval)

    return interval


def generate_cluster_events(max_events_remaining: int):
    weights = [0.6, 0.35, 0.05]
    choices = [2, 3, 4]
    num_events = min(random.choices(choices, weights=weights)[0], max_events_remaining)
    intervals = [random.uniform(5, 30) for _ in range(num_events - 1)]
    return intervals

def audio_alert(frequency = 250, duration = 1500):
    winsound.Beep(frequency, duration)
    time.sleep(0.1)
    winsound.Beep(frequency, duration)


def simulate(severity: Severity, duration_hours: int, start_hour=8, realtime=False):
    if not realtime:
        simulated_time = datetime.now().replace(hour=start_hour, minute=0, second=0)
    else:
        simulated_time = datetime.now()
    end_time = simulated_time + timedelta(hours=duration_hours)

    # Scale target events for different durations (1h, 4h, ... 24h)
    target_events = max(1, int(severity.random_daily_rate() * (duration_hours / 24)))
    remaining_events = target_events
    mean_minutes = duration_hours * 60 / target_events

    clusters_today = 0
    last_cluster_time = None
    total_triggered = 0

    mode = "REAL TIME" if realtime else "TEST IN FAST TIME"
    print(f"\nStarting Crohn's symptom simulation ({severity.name}, {mode})")
    print(f"Duration: {duration_hours}h, target {target_events} events\n")
    
    first = True
    while remaining_events > 0:
        remaining_time = (end_time - simulated_time).total_seconds() / 60
        if remaining_time <= 0:
            break

        interval = next_interval_minutes(
            simulated_time.hour, mean_minutes, remaining_time, remaining_events
        )

        if first:
            first = False
            print(f"[{simulated_time.strftime('%H:%M')}] Start...")

        if realtime:
            print(f'(interval: {interval:.1f} min)')
            audio_alert()
            time.sleep(interval * 60)
            simulated_time = datetime.now()
        else:
            simulated_time += timedelta(minutes=interval)

        # Night skip
        if 1 <= simulated_time.hour < 8:
            if realtime:
                target_time = simulated_time.replace(hour=8, minute=0)
                sleep_seconds = (target_time - datetime.now()).total_seconds()
                if sleep_seconds > 0:
                    time.sleep(sleep_seconds)
                simulated_time = target_time
            else:
                simulated_time = simulated_time.replace(hour=8, minute=0)
            print(f"[{simulated_time.strftime('%H:%M')}] Night skipped")
            continue

        total_triggered += 1
        remaining_events -= 1
        print(
            f"[{simulated_time.strftime('%H:%M')}] Bathroom event (interval: {interval:.1f} min)"
        )

        hours_since_last = (
            (simulated_time - last_cluster_time).total_seconds() / 3600
            if last_cluster_time
            else None
        )

        if severity.should_cluster(
            hours_since_last, clusters_today, max_clusters_per_day=3
        ):
            cluster_intervals = generate_cluster_events(remaining_events)
            last_cluster_time = simulated_time
            clusters_today += 1
            for cluster_interval in cluster_intervals:
                if realtime:
                    audio_alert()
                    time.sleep(cluster_interval * 60)
                    simulated_time = datetime.now()
                else:
                    simulated_time += timedelta(minutes=cluster_interval)
                total_triggered += 1
                remaining_events -= 1
                print(
                    f"   [Cluster {simulated_time.strftime('%H:%M')}] Another Bathroom event! (interval: {cluster_interval:.1f} min)"
                )

    print("------------------------------------------------------------")
    print(f"Simulation complete")
    print(f"Total bathroom events: {total_triggered}")
    print("------------------------------------------------------------")


def choose_severity():
    print("Choose severity level:")
    for i, sevverity in enumerate(Severity, 1):
        print(f"{i}. {sevverity.name.title()}")
    while True:
        try:
            choice = int(input("Enter number (1-3): "))
            if 1 <= choice <= 3:
                return list(Severity)[choice - 1]
        except ValueError:
            pass
        print("Invalid input. Try again.")


def choose_duration():
    options = {
        1: 1,
        2: 4,
        3: 8,
        4: 16,
        5: 24,
    }
    print("\nChoose duration:")
    print("1. 1 hour \n2. 4 hours\n3. 8 hours\n4. 16 hours\n5. 1 day (24h)")
    while True:
        try:
            choice = int(input("Enter number (1-5): "))
            if choice in options:
                return options[choice]
        except ValueError:
            pass
        print("Invalid input. Try again.")


if __name__ == "__main__":
    TESTING = False
    TESTING_SEVERITY = Severity.SEVERE
    TESTING_DURATION = 24

    if not TESTING:
        severity = choose_severity()
        duration = choose_duration()
    else:
        severity = TESTING_SEVERITY
        duration = TESTING_DURATION

    simulate(severity, duration_hours=duration, realtime=(not TESTING), start_hour=8)
