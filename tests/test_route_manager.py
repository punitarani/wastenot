"""
Test RoutePlanner
"""

from wastenot import RoutePlanner, Store
from wastenot.models import Address

store = Store()

if __name__ == "__main__":
    landmarks = {
        "Metropolitan Museum of Art": Address("1000 5th Ave", None, "New York", "NY", "10028"),
        "Madison Square Garden": Address("4 Pennsylvania Plaza", None, "New York", "NY", "10001"),
        "Empire State Building": Address("350 5th Ave", None, "New York", "NY", "10118"),
        "Grand Central Terminal": Address("Grand Central Terminal", None, "New York", "NY", "10017"),
        "Battery Park": Address("Battery Park", None, "New York", "NY", "10004"),
        "Central Park Zoo": Address("Central Park Zoo", None, "New York", "NY", "10024"),
    }

    # Build the stops dictionary
    stops = {}
    for name, address in list(landmarks.items())[1:-1]:
        stops[name] = address

    # Create a route planner
    route_planner = RoutePlanner(
        landmarks[list(landmarks.keys())[0]],
        landmarks[list(landmarks.keys())[-1]],
        stops,
        store,
    )

    # Calculate the route
    route = route_planner.get_route()
    print(route)
    print(route_planner.get_google_maps_link(stops=route))

    # Calculate the route matrix
    stops, total_weight = route_planner.get_stops(30)
    print(stops)
    print(route_planner.get_google_maps_link(stops=stops))
