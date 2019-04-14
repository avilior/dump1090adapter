from geographiclib.geodesic import Geodesic


home_lat = 45.25056
home_lon = -75.89996

north_lat = 50.25056
north_lon = -75.89996

south_lat = 40.25056
south_lon = -75.89996

east_lat = 45.25056
east_lon = -70.89996

west_lat = 45.25056
west_lon = -80.89996



home = Geodesic.WGS84.Inverse(home_lat, home_lon, north_lat, north_lon)
home_distance = home['s12'] / 1e3
home_heading  = home['azi1']

print(f"NORTH home distance {home_distance}  home heading {home_heading}")


home = Geodesic.WGS84.Inverse(home_lat, home_lon, east_lat, east_lon)
home_distance = home['s12'] / 1e3
home_heading  = home['azi1']

print(f"EAST home distance {home_distance}  home heading {home_heading}")


home = Geodesic.WGS84.Inverse(home_lat, home_lon, south_lat, south_lon)
home_distance = home['s12'] / 1e3
home_heading  = home['azi1']

print(f"SOUTH home distance {home_distance}  home heading {home_heading}")

home = Geodesic.WGS84.Inverse(home_lat, home_lon, west_lat, west_lon)
home_distance = home['s12'] / 1e3
home_heading  = home['azi1']

print(f"WEST home distance {home_distance}  home heading {home_heading}")