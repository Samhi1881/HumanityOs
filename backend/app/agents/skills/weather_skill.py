from typing import Any, Dict

class WeatherSkill:
    """Encapsulates storm danger indexing and climate hazard safety limit checks."""

    def calculate_storm_hazard_index(self, forecast: Dict[str, Any]) -> float:
        """Computes a hazard intensity index [0.0 - 10.0] from wind speed and rain probabilities."""
        forecast_days = forecast.get("forecast", [])
        if not forecast_days:
            return 0.0
            
        # Analyze first day forecast
        day_one = forecast_days[0]
        precip = day_one.get("precipitation_chance", 0.0)
        wind = day_one.get("wind_speed_mph", 0.0)
        
        # Simple weighted score
        score = (precip * 5.0) + (min(wind, 50.0) / 10.0)
        return round(min(score, 10.0), 2)

    def check_wind_safety_limits(self, wind_speed_mph: float, max_threshold: float = 35.0) -> bool:
        """Verifies if wind speeds allow safe aerial drone searches or ground truck transits."""
        return wind_speed_mph <= max_threshold
