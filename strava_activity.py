import json


class Strava_activity:

    def __init__(self, name, start_date_local, location_country, sport_type, elapsed_time, total_elevation_gain=None, distance=None, moving_time=None, suffer_score=None, elev_low=None, elev_high=None, max_speed=None):
        self.activity_name = name
        self.date = start_date_local
        self.elevation_gain = total_elevation_gain
        self.distance = distance
        self.elapsed_time = elapsed_time
        self.moving_time = moving_time
        self.suffer_score = suffer_score
        self.elevation_low = elev_low
        self.elevation_high = elev_high
        self.country = location_country
        self.sport_type = sport_type
        self.max_speed = max_speed

    def __iter__(self):
        yield from {
            "activity_name": self.activity_name,
            "date": self.date,
            "høydemeter": self.elevation_gain
        }.items()

    def __str__(self):
        return json.dumps(dict(self), ensure_ascii=False)

    def __repr__(self) -> str:
        return self.__str__()

    def to_json(self):
        return self.__str__()

    def default(obj):
        if hasattr(obj, 'to_json'):
            return obj.to_json()
        raise TypeError(
            f'Object of type {obj.__class__.__name__} is not JSON serializable')
