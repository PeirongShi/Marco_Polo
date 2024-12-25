import csv
import requests
import polyline
import math
import matplotlib.pyplot as plt
from shapely.geometry import Polygon

# Function to read a CSV file
def read_csv_file(csv_file: str) -> list:
    """
    Reads a CSV file and returns its content as a list of dictionaries.

    Parameters:
    - csv_file (str): The path to the CSV file.

    Returns:
    - list: A list of dictionaries, where each dictionary represents a row in the CSV.
    """
    with open(csv_file, mode='r') as file:
        reader = csv.DictReader(file)
        return [row for row in reader]

# Function to write results to a CSV file
def write_csv_file(output_csv: str, results: list, fieldnames: list) -> None:
    """
    Writes the results to a CSV file.

    Parameters:
    - output_csv (str): The path to the output CSV file.
    - results (list): A list of dictionaries containing the data to write.
    - fieldnames (list): A list of field names for the CSV file.

    Returns:
    - None
    """
    with open(output_csv, mode='w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

# Function to fetch route data
def get_route_data(origin: str, destination: str, api_key: str) -> tuple:
    """
    Fetches route data from the Google Maps Directions API and decodes it.

    Parameters:
    - origin (str): The starting point of the route (latitude,longitude).
    - destination (str): The endpoint of the route (latitude,longitude).
    - api_key (str): The API key for accessing the Google Maps Directions API.

    Returns:
    - tuple:
        - list: A list of (latitude, longitude) tuples representing the route.
        - float: Total route distance in kilometers.
        - float: Total route time in minutes.
    """
    url = f"https://maps.googleapis.com/maps/api/directions/json?origin={origin}&destination={destination}&key={api_key}"
    response = requests.get(url)
    directions_data = response.json()

    if directions_data['status'] == 'OK':
        route_polyline = directions_data['routes'][0]['overview_polyline']['points']
        coordinates = polyline.decode(route_polyline)
        total_distance = directions_data['routes'][0]['legs'][0]['distance']['value'] / 1000  # kilometers
        total_time = directions_data['routes'][0]['legs'][0]['duration']['value'] / 60  # minutes
        return coordinates, total_distance, total_time
    else:
        print("Error fetching directions:", directions_data['status'])
        return [], 0, 0


# Function to find common nodes
def find_common_nodes(coordinates_a: list, coordinates_b: list) -> tuple:
    """
    Finds the first and last common nodes between two routes.

    Parameters:
    - coordinates_a (list): A list of (latitude, longitude) tuples representing route A.
    - coordinates_b (list): A list of (latitude, longitude) tuples representing route B.

    Returns:
    - tuple:
        - tuple or None: The first common node (latitude, longitude) or None if not found.
        - tuple or None: The last common node (latitude, longitude) or None if not found.
    """
    first_common_node = next((coord for coord in coordinates_a if coord in coordinates_b), None)
    last_common_node = next((coord for coord in reversed(coordinates_a) if coord in coordinates_b), None)
    return first_common_node, last_common_node


# Function to split route segments
def split_segments(coordinates: list, first_common: tuple, last_common: tuple) -> tuple:
    """
    Splits a route into 'before', 'overlap', and 'after' segments.

    Parameters:
    - coordinates (list): A list of (latitude, longitude) tuples representing the route.
    - first_common (tuple): The first common node (latitude, longitude).
    - last_common (tuple): The last common node (latitude, longitude).

    Returns:
    - tuple:
        - list: The 'before' segment of the route.
        - list: The 'overlap' segment of the route.
        - list: The 'after' segment of the route.
    """
    index_first = coordinates.index(first_common)
    index_last = coordinates.index(last_common)
    return coordinates[:index_first + 1], coordinates[index_first:index_last + 1], coordinates[index_last:]


# Function to compute percentages
def compute_percentages(segment_value: float, total_value: float) -> float:
    """
    Computes the percentage of a segment relative to the total.

    Parameters:
    - segment_value (float): The value of the segment (e.g., distance or time).
    - total_value (float): The total value (e.g., total distance or time).

    Returns:
    - float: The percentage of the segment relative to the total, or 0 if total_value is 0.
    """
    return (segment_value / total_value) * 100 if total_value > 0 else 0

# Function to plot routes
def plot_routes(coordinates_a: list, coordinates_b: list, first_common: tuple, last_common: tuple) -> None:
    """
    Plots routes A and B with common nodes highlighted.

    Parameters:
    - coordinates_a (list): A list of (latitude, longitude) tuples for route A.
    - coordinates_b (list): A list of (latitude, longitude) tuples for route B.
    - first_common (tuple): The first common node (latitude, longitude).
    - last_common (tuple): The last common node (latitude, longitude).

    Returns:
    - None
    """
    fig, ax = plt.subplots(figsize=(10, 8))
    latitudes_a = [coord[0] for coord in coordinates_a]
    longitudes_a = [coord[1] for coord in coordinates_a]
    latitudes_b = [coord[0] for coord in coordinates_b]
    longitudes_b = [coord[1] for coord in coordinates_b]

    ax.plot(longitudes_a, latitudes_a, marker='o', color='blue', label='Route A')
    ax.plot(longitudes_b, latitudes_b, marker='o', color='red', label='Route B')

    if first_common:
        ax.scatter(*reversed(first_common), color='green', label='First Common Node', zorder=5)
    if last_common:
        ax.scatter(*reversed(last_common), color='orange', label='Last Common Node', zorder=5)

    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_title("Route Visualization with Common Nodes")
    ax.legend()
    plt.show()

def process_routes_with_csv(csv_file: str, api_key: str, output_csv: str = "output.csv") -> list:
    """
    Processes routes from a CSV file, computes time and distance travelled before, during, and after overlaps, and writes results to a CSV file.

    Parameters:
    - csv_file (str): The path to the input CSV file.
    - api_key (str): The API key for accessing the Google Maps Directions API.
    - output_csv (str): The path to the output CSV file.

    Returns:
    - list: A list of dictionaries containing the computed results.
    """
    data = read_csv_file(csv_file)
    results = []

    for row in data:
        origin_a, destination_a = row['Origin of A'], row['Destination of A']
        origin_b, destination_b = row['Origin of B'], row['Destination of B']

        # Get full route details for A and B
        coordinates_a, total_distance_a, total_time_a = get_route_data(origin_a, destination_a, api_key)
        coordinates_b, total_distance_b, total_time_b = get_route_data(origin_b, destination_b, api_key)

        # Find common nodes
        first_common_node, last_common_node = find_common_nodes(coordinates_a, coordinates_b)

        if not first_common_node or not last_common_node:
            print("No common nodes found for these routes.")
            continue

        # Split segments
        before_a, overlap_a, after_a = split_segments(coordinates_a, first_common_node, last_common_node)
        before_b, overlap_b, after_b = split_segments(coordinates_b, first_common_node, last_common_node)

        # Calculate distances and times for A
        _, before_a_distance, before_a_time = get_route_data(origin_a, f"{before_a[-1][0]},{before_a[-1][1]}", api_key)
        _, overlap_a_distance, overlap_a_time = get_route_data(f"{overlap_a[0][0]},{overlap_a[0][1]}", f"{overlap_a[-1][0]},{overlap_a[-1][1]}", api_key)
        _, after_a_distance, after_a_time = get_route_data(f"{after_a[0][0]},{after_a[0][1]}", destination_a, api_key)

        # Calculate distances and times for B
        _, before_b_distance, before_b_time = get_route_data(origin_b, f"{before_b[-1][0]},{before_b[-1][1]}", api_key)
        #_, overlap_b_distance, overlap_b_time = get_route_data(f"{overlap_b[0][0]},{overlap_b[0][1]}", f"{overlap_b[-1][0]},{overlap_b[-1][1]}", api_key)
        _, after_b_distance, after_b_time = get_route_data(f"{after_b[0][0]},{after_b[0][1]}", destination_b, api_key)

        # Compute percentages for A
        a_overlap_distance_percentage = compute_percentages(overlap_a_distance, total_distance_a)
        a_overlap_time_percentage = compute_percentages(overlap_a_time, total_time_a)
        a_before_distance_percentage = compute_percentages(before_a_distance, total_distance_a)
        a_before_time_percentage = compute_percentages(before_a_time, total_time_a)
        a_after_distance_percentage = compute_percentages(after_a_distance, total_distance_a)
        a_after_time_percentage = compute_percentages(after_a_time, total_time_a)

        # Compute percentages for B
        b_overlap_distance_percentage = compute_percentages(overlap_a_distance, total_distance_b)
        b_overlap_time_percentage = compute_percentages(overlap_a_time, total_time_b)
        b_before_distance_percentage = compute_percentages(before_b_distance, total_distance_b)
        b_before_time_percentage = compute_percentages(before_b_time, total_time_b)
        b_after_distance_percentage = compute_percentages(after_b_distance, total_distance_b)
        b_after_time_percentage = compute_percentages(after_b_time, total_time_b)

        # Append results
        results.append({
            "Overlap Distance": overlap_a_distance,
            "Overlap Time": overlap_a_time,
            "A Overlap Distance Percentage": a_overlap_distance_percentage,
            "A Overlap Time Percentage": a_overlap_time_percentage,
            "B Overlap Distance Percentage": b_overlap_distance_percentage,
            "B Overlap Time Percentage": b_overlap_time_percentage,
            "A Before Distance Percentage": a_before_distance_percentage,
            "A Before Time Percentage": a_before_time_percentage,
            "A After Distance Percentage": a_after_distance_percentage,
            "A After Time Percentage": a_after_time_percentage,
            "B Before Distance Percentage": b_before_distance_percentage,
            "B Before Time Percentage": b_before_time_percentage,
            "B After Distance Percentage": b_after_distance_percentage,
            "B After Time Percentage": b_after_time_percentage
        })

        # Plot routes
        plot_routes(coordinates_a, coordinates_b, first_common_node, last_common_node)

    # Write results to CSV
    fieldnames = [
        "Overlap Distance", "Overlap Time",
        "A Overlap Distance Percentage", "A Overlap Time Percentage",
        "B Overlap Distance Percentage", "B Overlap Time Percentage",
        "A Before Distance Percentage", "A Before Time Percentage",
        "A After Distance Percentage", "A After Time Percentage",
        "B Before Distance Percentage", "B Before Time Percentage",
        "B After Distance Percentage", "B After Time Percentage"
    ]
    write_csv_file(output_csv, results, fieldnames)

    return results

def process_routes_only_overlap_with_csv(csv_file: str, api_key: str, output_csv: str = "output.csv") -> list:
    """
    Processes routes from a CSV file, computes time and distance travelled during overlaps, and writes results to a CSV file.

    Parameters:
    - csv_file (str): The path to the input CSV file.
    - api_key (str): The API key for accessing the Google Maps Directions API.
    - output_csv (str): The path to the output CSV file.

    Returns:
    - list: A list of dictionaries containing the computed results.
    """
    data = read_csv_file(csv_file)
    results = []

    for row in data:
        origin_a, destination_a = row['Origin of A'], row['Destination of A']
        origin_b, destination_b = row['Origin of B'], row['Destination of B']

        # Get full route details for A and B
        coordinates_a, total_distance_a, total_time_a = get_route_data(origin_a, destination_a, api_key)
        coordinates_b, total_distance_b, total_time_b = get_route_data(origin_b, destination_b, api_key)

        # Find common nodes
        first_common_node, last_common_node = find_common_nodes(coordinates_a, coordinates_b)

        if not first_common_node or not last_common_node:
            print("No common nodes found for these routes.")
            continue

        # Split segments
        before_a, overlap_a, after_a = split_segments(coordinates_a, first_common_node, last_common_node)
        before_b, overlap_b, after_b = split_segments(coordinates_b, first_common_node, last_common_node)

        # Calculate overlap distance and time
        _, overlap_a_distance, overlap_a_time = get_route_data(f"{overlap_a[0][0]},{overlap_a[0][1]}", f"{overlap_a[-1][0]},{overlap_a[-1][1]}", api_key)

        # Compute percentages for A
        a_overlap_distance_percentage = compute_percentages(overlap_a_distance, total_distance_a)
        a_overlap_time_percentage = compute_percentages(overlap_a_time, total_time_a)

        # Compute percentages for B
        b_overlap_distance_percentage = compute_percentages(overlap_a_distance, total_distance_b)
        b_overlap_time_percentage = compute_percentages(overlap_a_time, total_time_b)

        # Append results
        results.append({
            "Overlap Distance": overlap_a_distance,
            "Overlap Time": overlap_a_time,
            "A Overlap Distance Percentage": a_overlap_distance_percentage,
            "A Overlap Time Percentage": a_overlap_time_percentage,
            "B Overlap Distance Percentage": b_overlap_distance_percentage,
            "B Overlap Time Percentage": b_overlap_time_percentage
        })

        # Plot routes
        plot_routes(coordinates_a, coordinates_b, first_common_node, last_common_node)

    # Write results to CSV
    fieldnames = [
        "Overlap Distance", "Overlap Time",
        "A Overlap Distance Percentage", "A Overlap Time Percentage",
        "B Overlap Distance Percentage", "B Overlap Time Percentage"
    ]
    write_csv_file(output_csv, results, fieldnames)

    return results

##Starting here, the following functions are used for finding approximations around the first and last common node. The approximation is probably more relevant when two routes crosses each other. 
def great_circle_distance(coord1, coord2):  # Function from Urban Economics and Real Estate course Homework 1.
    """
    Compute the great-circle distance between two points using the provided formula.

    Parameters:
    - coord1: tuple of (latitude, longitude)
    - coord2: tuple of (latitude, longitude)

    Returns:
    - float: Distance in meters
    """
    OLA, OLO = coord1
    DLA, DLO = coord2

    # Convert latitude and longitude from degrees to radians
    L1 = OLA * math.pi / 180
    L2 = DLA * math.pi / 180
    DLo = abs(OLO - DLO) * math.pi / 180

    # Apply the great circle formula
    cosd = (math.sin(L1) * math.sin(L2)) + (math.cos(L1) * math.cos(L2) * math.cos(DLo))
    cosd = min(1, max(-1, cosd))  # Ensure cosd is in the range [-1, 1]

    # Take the arc cosine
    dist_degrees = math.acos(cosd) * 180 / math.pi

    # Convert degrees to miles
    dist_miles = 69.16 * dist_degrees

    # Convert miles to kilometers
    dist_km = 1.609 * dist_miles

    return dist_km * 1000  # Convert to meters

def calculate_distances(segment: list, label_prefix: str) -> list:
    """
    Calculates distances and creates labeled segments for a given list of coordinates.

    Parameters:
    - segment (list): A list of (latitude, longitude) tuples.
    - label_prefix (str): The prefix for labeling segments (e.g., 't' or 'T').

    Returns:
    - list: A list of dictionaries, each containing:
        - 'label': The label of the segment (e.g., t1, t2, ...).
        - 'start': Start coordinates of the segment.
        - 'end': End coordinates of the segment.
        - 'distance': Distance (in meters) for the segment.
    """
    segment_details = []
    for i in range(len(segment) - 1):
        start = segment[i]
        end = segment[i + 1]
        distance = great_circle_distance(start, end)
        label = f"{label_prefix}{i + 1}"
        segment_details.append({
            "label": label,
            "start": start,
            "end": end,
            "distance": distance
        })
    return segment_details

def calculate_segment_distances(before: list, after: list) -> dict:
    """
    Calculates the distance between each consecutive pair of coordinates in the
    'before' and 'after' segments from the split_segments function.
    Labels the segments as t1, t2, ... for before, and T1, T2, ... for after.

    Parameters:
    - before (list): A list of (latitude, longitude) tuples representing the route before the overlap.
    - after (list): A list of (latitude, longitude) tuples representing the route after the overlap.

    Returns:
    - dict: A dictionary with two keys:
        - 'before_segments': A list of dictionaries containing details about each segment in the 'before' route.
        - 'after_segments': A list of dictionaries containing details about each segment in the 'after' route.
    """
    # Calculate labeled segments for 'before' and 'after'
    before_segments = calculate_distances(before, label_prefix="t")
    after_segments = calculate_distances(after, label_prefix="T")

    return {
        "before_segments": before_segments,
        "after_segments": after_segments
    }

def calculate_rectangle_coordinates(start, end, width: float) -> list:
    """
    Calculates the coordinates of the corners of a rectangle for a given segment.

    Parameters:
    - start (tuple): The starting coordinate of the segment (latitude, longitude).
    - end (tuple): The ending coordinate of the segment (latitude, longitude).
    - width (float): The width of the rectangle in meters.

    Returns:
    - list: A list of 5 tuples representing the corners of the rectangle,
            including the repeated first corner to close the polygon.
    """
    # Calculate unit direction vector of the segment
    dx = end[1] - start[1]
    dy = end[0] - start[0]
    magnitude = (dx**2 + dy**2)**0.5
    unit_dx = dx / magnitude
    unit_dy = dy / magnitude

    # Perpendicular vector for the rectangle width
    perp_dx = -unit_dy
    perp_dy = unit_dx

    # Convert width to degrees (approximately)
    half_width = width / 2 / 111_111  # 111,111 meters per degree of latitude

    # Rectangle corner offsets
    offset_x = perp_dx * half_width
    offset_y = perp_dy * half_width

    # Define rectangle corners
    bottom_left = (start[0] - offset_y, start[1] - offset_x)
    top_left = (start[0] + offset_y, start[1] + offset_x)
    bottom_right = (end[0] - offset_y, end[1] - offset_x)
    top_right = (end[0] + offset_y, end[1] + offset_x)

    return [bottom_left, top_left, top_right, bottom_right, bottom_left]

def create_segment_rectangles(segments: list, width: float = 100) -> list:
    """
    Creates rectangles for each segment, where the length of the rectangle is the segment's distance
    and the width is the given default width.

    Parameters:
    - segments (list): A list of dictionaries, each containing:
        - 'label': The label of the segment (e.g., t1, t2, T1, T2).
        - 'start': Start coordinates of the segment.
        - 'end': End coordinates of the segment.
        - 'distance': Length of the segment in meters.
    - width (float): The width of the rectangle in meters (default: 100).

    Returns:
    - list: A list of dictionaries, each containing:
        - 'label': The label of the segment.
        - 'rectangle': A Shapely Polygon representing the rectangle.
    """
    rectangles = []
    for segment in segments:
        start = segment["start"]
        end = segment["end"]
        rectangle_coords = calculate_rectangle_coordinates(start, end, width)
        rectangle_polygon = Polygon(rectangle_coords)
        rectangles.append({
            "label": segment["label"],
            "rectangle": rectangle_polygon
        })

    return rectangles

def find_segment_combinations(rectangles_a: list, rectangles_b: list) -> dict:
    """
    Finds all combinations of segments between two routes (A and B).
    Each combination consists of one segment from A and one segment from B.

    Parameters:
    - rectangles_a (list): A list of dictionaries, each representing a rectangle segment from Route A.
        - Each dictionary contains:
            - 'label': The label of the segment (e.g., t1, t2, T1, T2).
            - 'rectangle': A Shapely Polygon representing the rectangle.
    - rectangles_b (list): A list of dictionaries, each representing a rectangle segment from Route B.

    Returns:
    - dict: A dictionary with two keys:
        - 'before_combinations': A list of tuples, each containing:
            - 'segment_a': The label of a segment from Route A.
            - 'segment_b': The label of a segment from Route B.
        - 'after_combinations': A list of tuples, with the same structure as above.
    """
    before_combinations = []
    after_combinations = []

    # Separate rectangles into before and after overlap based on labels
    before_a = [rect for rect in rectangles_a if rect['label'].startswith('t')]
    after_a = [rect for rect in rectangles_a if rect['label'].startswith('T')]
    before_b = [rect for rect in rectangles_b if rect['label'].startswith('t')]
    after_b = [rect for rect in rectangles_b if rect['label'].startswith('T')]

    # Find all combinations for "before" segments
    for rect_a in before_a:
        for rect_b in before_b:
            before_combinations.append((rect_a['label'], rect_b['label']))

    # Find all combinations for "after" segments
    for rect_a in after_a:
        for rect_b in after_b:
            after_combinations.append((rect_a['label'], rect_b['label']))

    return {
        "before_combinations": before_combinations,
        "after_combinations": after_combinations
    }

def calculate_overlap_ratio(polygon_a, polygon_b) -> float:
    """
    Calculates the overlap area ratio between two polygons.

    Parameters:
    - polygon_a: A Shapely Polygon representing the first rectangle.
    - polygon_b: A Shapely Polygon representing the second rectangle.

    Returns:
    - float: The ratio of the overlapping area to the smaller polygon's area, as a percentage.
    """
    intersection = polygon_a.intersection(polygon_b)
    if intersection.is_empty:
        return 0.0

    overlap_area = intersection.area
    smaller_area = min(polygon_a.area, polygon_b.area)
    return (overlap_area / smaller_area) * 100 if smaller_area > 0 else 0.0

def filter_combinations_by_overlap(rectangles_a: list, rectangles_b: list, threshold: float = 50) -> dict:
    """
    Finds and filters segment combinations based on overlapping area ratios.
    Retains only those combinations where the overlapping area is greater than
    the specified threshold of the smaller rectangle's area.

    Parameters:
    - rectangles_a (list): A list of dictionaries representing segments from Route A.
        - Each dictionary contains:
            - 'label': The label of the segment (e.g., t1, t2, T1, T2).
            - 'rectangle': A Shapely Polygon representing the rectangle.
    - rectangles_b (list): A list of dictionaries representing segments from Route B.
    - threshold (float): The minimum percentage overlap required (default: 50).

    Returns:
    - dict: A dictionary with two keys:
        - 'before_combinations': A list of tuples with retained combinations for "before overlap".
        - 'after_combinations': A list of tuples with retained combinations for "after overlap".
    """
    filtered_before_combinations = []
    filtered_after_combinations = []

    # Separate rectangles into before and after overlap
    before_a = [rect for rect in rectangles_a if rect['label'].startswith('t')]
    after_a = [rect for rect in rectangles_a if rect['label'].startswith('T')]
    before_b = [rect for rect in rectangles_b if rect['label'].startswith('t')]
    after_b = [rect for rect in rectangles_b if rect['label'].startswith('T')]

    # Process "before overlap" combinations
    for rect_a in before_a:
        for rect_b in before_b:
            overlap_ratio = calculate_overlap_ratio(rect_a['rectangle'], rect_b['rectangle'])
            if overlap_ratio >= threshold:
                filtered_before_combinations.append((rect_a['label'], rect_b['label'], overlap_ratio))

    # Process "after overlap" combinations
    for rect_a in after_a:
        for rect_b in after_b:
            overlap_ratio = calculate_overlap_ratio(rect_a['rectangle'], rect_b['rectangle'])
            if overlap_ratio >= threshold:
                filtered_after_combinations.append((rect_a['label'], rect_b['label'], overlap_ratio))

    return {
        "before_combinations": filtered_before_combinations,
        "after_combinations": filtered_after_combinations
    }

def get_segment_by_label(rectangles: list, label: str) -> dict:
    """
    Finds a segment dictionary by its label.

    Parameters:
    - rectangles (list): A list of dictionaries, each representing a segment.
        - Each dictionary contains:
            - 'label': The label of the segment.
            - 'rectangle': A Shapely Polygon representing the rectangle.
    - label (str): The label of the segment to find.

    Returns:
    - dict: The dictionary representing the segment with the matching label.
    - None: If no matching segment is found.
    """
    for rect in rectangles:
        if rect["label"] == label:
            return rect
    return None

def find_overlap_boundary_nodes(filtered_combinations: dict, rectangles_a: list, rectangles_b: list) -> dict:
    """
    Finds the first node of overlapping segments before the overlap and the last node of overlapping
    segments after the overlap for both Route A and Route B.

    Parameters:
    - filtered_combinations (dict): The filtered combinations output from filter_combinations_by_overlap.
        Contains 'before_combinations' and 'after_combinations'.
    - rectangles_a (list): A list of dictionaries representing segments from Route A.
    - rectangles_b (list): A list of dictionaries representing segments from Route B.

    Returns:
    - dict: A dictionary containing:
        - 'first_node_before_overlap': The first overlapping node and its label for Route A and B.
        - 'last_node_after_overlap': The last overlapping node and its label for Route A and B.
    """
    # Get the first combination before the overlap
    first_before_combination = filtered_combinations["before_combinations"][0] if filtered_combinations["before_combinations"] else None
    # Get the last combination after the overlap
    last_after_combination = filtered_combinations["after_combinations"][-1] if filtered_combinations["after_combinations"] else None

    first_node_before = None
    last_node_after = None

    if first_before_combination:
        # Extract labels from the first before overlap combination
        label_a, label_b, _ = first_before_combination

        # Find the corresponding segments
        segment_a = get_segment_by_label(rectangles_a, label_a)
        segment_b = get_segment_by_label(rectangles_b, label_b)

        # Get the first node of the segment
        if segment_a and segment_b:
            first_node_before = {
                "label_a": segment_a["label"],
                "node_a": segment_a["rectangle"].exterior.coords[0],
                "label_b": segment_b["label"],
                "node_b": segment_b["rectangle"].exterior.coords[0]
            }

    if last_after_combination:
        # Extract labels from the last after overlap combination
        label_a, label_b, _ = last_after_combination

        # Find the corresponding segments
        segment_a = get_segment_by_label(rectangles_a, label_a)
        segment_b = get_segment_by_label(rectangles_b, label_b)

        # Get the last node of the segment
        if segment_a and segment_b:
            last_node_after = {
                "label_a": segment_a["label"],
                "node_a": segment_a["rectangle"].exterior.coords[-2],  # Second-to-last for the last node
                "label_b": segment_b["label"],
                "node_b": segment_b["rectangle"].exterior.coords[-2]  # Second-to-last for the last node
            }

    return {
        "first_node_before_overlap": first_node_before,
        "last_node_after_overlap": last_node_after
    }

def overlap_rec(csv_file: str, api_key: str, output_csv: str = "outputRec.csv", threshold=50, width=100) -> list:
    """
    Processes routes from a CSV file, computes time and distance travelled before, during,
    and after overlaps, and writes results to a CSV file.

    Parameters:
    - csv_file (str): The path to the input CSV file.
    - api_key (str): The API key for accessing the Google Maps Directions API.
    - output_csv (str): The path to the output CSV file.

    Returns:
    - list: A list of dictionaries containing the computed results.
    """
    # Read data from CSV
    data = read_csv_file(csv_file)
    results = []

    for row in data:
        # Extract origins and destinations for routes A and B
        origin_a, destination_a = row['Origin of A'], row['Destination of A']
        origin_b, destination_b = row['Origin of B'], row['Destination of B']

        # Fetch route data
        coordinates_a, total_distance_a, total_time_a = get_route_data(origin_a, destination_a, api_key)
        coordinates_b, total_distance_b, total_time_b = get_route_data(origin_b, destination_b, api_key)

        # Find common nodes
        first_common_node, last_common_node = find_common_nodes(coordinates_a, coordinates_b)

        if not first_common_node or not last_common_node:
            print("No common nodes found for these routes.")
            continue

        # Split the segments
        before_a, overlap_a, after_a = split_segments(coordinates_a, first_common_node, last_common_node)
        before_b, overlap_b, after_b = split_segments(coordinates_b, first_common_node, last_common_node)

        # Calculate distances for segments
        a_segment_distances = calculate_segment_distances(before_a, after_a)
        b_segment_distances = calculate_segment_distances(before_b, after_b)

        # Construct rectangles for segments
        rectangles_a = create_segment_rectangles(a_segment_distances["before_segments"] + a_segment_distances["after_segments"], width=100)
        rectangles_b = create_segment_rectangles(b_segment_distances["before_segments"] + b_segment_distances["after_segments"], width=100)

        # Filter combinations based on overlap
        filtered_combinations = filter_combinations_by_overlap(rectangles_a, rectangles_b, threshold=50)

        # Find first and last nodes of overlap
        boundary_nodes = find_overlap_boundary_nodes(filtered_combinations, rectangles_a, rectangles_b)

        # Fallback to first and last common nodes if boundary nodes are invalid
        if not boundary_nodes["first_node_before_overlap"] or not boundary_nodes["last_node_after_overlap"]:
            #print(f"Boundary nodes not found for routes: {origin_a} -> {destination_a} and {origin_b} -> {destination_b}")
            boundary_nodes = {
                "first_node_before_overlap": {
                    "node_a": first_common_node,
                    "node_b": first_common_node
                },
                "last_node_after_overlap": {
                    "node_a": last_common_node,
                    "node_b": last_common_node
                }
            }

        # Fetch distances and times for segments
        _, before_a_distance, before_a_time = get_route_data(
            origin_a,
            f"{boundary_nodes['first_node_before_overlap']['node_a'][0]},{boundary_nodes['first_node_before_overlap']['node_a'][1]}",
            api_key
        )

        _, overlap_a_distance, overlap_a_time = get_route_data(
            f"{boundary_nodes['first_node_before_overlap']['node_a'][0]},{boundary_nodes['first_node_before_overlap']['node_a'][1]}",
            f"{boundary_nodes['last_node_after_overlap']['node_a'][0]},{boundary_nodes['last_node_after_overlap']['node_a'][1]}",
            api_key
        )

        _, after_a_distance, after_a_time = get_route_data(
            f"{boundary_nodes['last_node_after_overlap']['node_a'][0]},{boundary_nodes['last_node_after_overlap']['node_a'][1]}",
            destination_a,
            api_key
        )

        _, before_b_distance, before_b_time = get_route_data(
            origin_b,
            f"{boundary_nodes['first_node_before_overlap']['node_b'][0]},{boundary_nodes['first_node_before_overlap']['node_b'][1]}",
            api_key
        )

        _, overlap_b_distance, overlap_b_time = get_route_data(
            f"{boundary_nodes['first_node_before_overlap']['node_b'][0]},{boundary_nodes['first_node_before_overlap']['node_b'][1]}",
            f"{boundary_nodes['last_node_after_overlap']['node_b'][0]},{boundary_nodes['last_node_after_overlap']['node_b'][1]}",
            api_key
        )

        _, after_b_distance, after_b_time = get_route_data(
            f"{boundary_nodes['last_node_after_overlap']['node_b'][0]},{boundary_nodes['last_node_after_overlap']['node_b'][1]}",
            destination_b,
            api_key
        )

        # Calculate percentages
        a_overlap_distance_percentage = compute_percentages(overlap_a_distance, total_distance_a)
        a_overlap_time_percentage = compute_percentages(overlap_a_time, total_time_a)
        b_overlap_distance_percentage = compute_percentages(overlap_b_distance, total_distance_b)
        b_overlap_time_percentage = compute_percentages(overlap_b_time, total_time_b)

        a_before_distance_percentage = compute_percentages(before_a_distance, total_distance_a)
        a_before_time_percentage = compute_percentages(before_a_time, total_time_a)
        a_after_distance_percentage = compute_percentages(after_a_distance, total_distance_a)
        a_after_time_percentage = compute_percentages(after_a_time, total_time_a)

        b_before_distance_percentage = compute_percentages(before_b_distance, total_distance_b)
        b_before_time_percentage = compute_percentages(before_b_time, total_time_b)
        b_after_distance_percentage = compute_percentages(after_b_distance, total_distance_b)
        b_after_time_percentage = compute_percentages(after_b_time, total_time_b)

        # Append results
        results.append({
            "Overlap Distance": overlap_a_distance,
            "Overlap Time": overlap_a_time,
            "A Overlap Distance Percentage": a_overlap_distance_percentage,
            "A Overlap Time Percentage": a_overlap_time_percentage,
            "B Overlap Distance Percentage": b_overlap_distance_percentage,
            "B Overlap Time Percentage": b_overlap_time_percentage,
            "A Before Distance Percentage": a_before_distance_percentage,
            "A Before Time Percentage": a_before_time_percentage,
            "A After Distance Percentage": a_after_distance_percentage,
            "A After Time Percentage": a_after_time_percentage,
            "B Before Distance Percentage": b_before_distance_percentage,
            "B Before Time Percentage": b_before_time_percentage,
            "B After Distance Percentage": b_after_distance_percentage,
            "B After Time Percentage": b_after_time_percentage
        })

        # Plot routes
        plot_routes(coordinates_a, coordinates_b, first_common_node, last_common_node)

    # Write results to CSV
    fieldnames = [
        "Overlap Distance", "Overlap Time",
        "A Overlap Distance Percentage", "A Overlap Time Percentage",
        "B Overlap Distance Percentage", "B Overlap Time Percentage",
        "A Before Distance Percentage", "A Before Time Percentage",
        "A After Distance Percentage", "A After Time Percentage",
        "B Before Distance Percentage", "B Before Time Percentage",
        "B After Distance Percentage", "B After Time Percentage"
    ]
    write_csv_file(output_csv, results, fieldnames)

    return results


def only_overlap_rec(csv_file: str, api_key: str, output_csv: str = "outputRec_only_overlap.csv", threshold=50, width=100) -> list:
    """
    Processes routes from a CSV file, computes time and distance travelled before, during,
    and after overlaps, and writes results to a CSV file.

    Parameters:
    - csv_file (str): The path to the input CSV file.
    - api_key (str): The API key for accessing the Google Maps Directions API.
    - output_csv (str): The path to the output CSV file.

    Returns:
    - list: A list of dictionaries containing the computed results.
    """
    # Read data from CSV
    data = read_csv_file(csv_file)
    results = []

    for row in data:
        # Extract origins and destinations for routes A and B
        origin_a, destination_a = row['Origin of A'], row['Destination of A']
        origin_b, destination_b = row['Origin of B'], row['Destination of B']

        # Fetch route data
        coordinates_a, total_distance_a, total_time_a = get_route_data(origin_a, destination_a, api_key)
        coordinates_b, total_distance_b, total_time_b = get_route_data(origin_b, destination_b, api_key)

        # Find common nodes
        first_common_node, last_common_node = find_common_nodes(coordinates_a, coordinates_b)

        if not first_common_node or not last_common_node:
            print("No common nodes found for these routes.")
            continue

        # Split the segments
        before_a, overlap_a, after_a = split_segments(coordinates_a, first_common_node, last_common_node)
        before_b, overlap_b, after_b = split_segments(coordinates_b, first_common_node, last_common_node)

        # Calculate distances for segments
        a_segment_distances = calculate_segment_distances(before_a, after_a)
        b_segment_distances = calculate_segment_distances(before_b, after_b)

        # Construct rectangles for segments
        rectangles_a = create_segment_rectangles(a_segment_distances["before_segments"] + a_segment_distances["after_segments"], width=100)
        rectangles_b = create_segment_rectangles(b_segment_distances["before_segments"] + b_segment_distances["after_segments"], width=100)

        # Filter combinations based on overlap
        filtered_combinations = filter_combinations_by_overlap(rectangles_a, rectangles_b, threshold=50)

        # Find first and last nodes of overlap
        boundary_nodes = find_overlap_boundary_nodes(filtered_combinations, rectangles_a, rectangles_b)

        # Fallback to first and last common nodes if boundary nodes are invalid
        if not boundary_nodes["first_node_before_overlap"] or not boundary_nodes["last_node_after_overlap"]:
            #print(f"Boundary nodes not found for routes: {origin_a} -> {destination_a} and {origin_b} -> {destination_b}")
            boundary_nodes = {
                "first_node_before_overlap": {
                    "node_a": first_common_node,
                    "node_b": first_common_node
                },
                "last_node_after_overlap": {
                    "node_a": last_common_node,
                    "node_b": last_common_node
                }
            }

        _, overlap_a_distance, overlap_a_time = get_route_data(
            f"{boundary_nodes['first_node_before_overlap']['node_a'][0]},{boundary_nodes['first_node_before_overlap']['node_a'][1]}",
            f"{boundary_nodes['last_node_after_overlap']['node_a'][0]},{boundary_nodes['last_node_after_overlap']['node_a'][1]}",
            api_key
        )

        _, overlap_b_distance, overlap_b_time = get_route_data(
            f"{boundary_nodes['first_node_before_overlap']['node_b'][0]},{boundary_nodes['first_node_before_overlap']['node_b'][1]}",
            f"{boundary_nodes['last_node_after_overlap']['node_b'][0]},{boundary_nodes['last_node_after_overlap']['node_b'][1]}",
            api_key
        )

        # Calculate percentages
        a_overlap_distance_percentage = compute_percentages(overlap_a_distance, total_distance_a)
        a_overlap_time_percentage = compute_percentages(overlap_a_time, total_time_a)
        b_overlap_distance_percentage = compute_percentages(overlap_b_distance, total_distance_b)
        b_overlap_time_percentage = compute_percentages(overlap_b_time, total_time_b)

        # Append results
        results.append({
            "Overlap Distance": overlap_a_distance,
            "Overlap Time": overlap_a_time,
            "A Overlap Distance Percentage": a_overlap_distance_percentage,
            "A Overlap Time Percentage": a_overlap_time_percentage,
            "B Overlap Distance Percentage": b_overlap_distance_percentage,
            "B Overlap Time Percentage": b_overlap_time_percentage
        })

        # Plot routes
        plot_routes(coordinates_a, coordinates_b, first_common_node, last_common_node)

    # Write results to CSV
    fieldnames = [
        "Overlap Distance", "Overlap Time",
        "A Overlap Distance Percentage", "A Overlap Time Percentage",
        "B Overlap Distance Percentage", "B Overlap Time Percentage"
    ]
    write_csv_file(output_csv, results, fieldnames)

    return results

##This is the main function with user interaction. 
def Overlap_Function(csv_file: str, api_key: str, threshold: int = 50, width: int = 100) -> None:
    """
    Analyze route overlaps and optionally gather commuting information.

    Args:
        csv_file (str): Path to the input CSV file containing route data.
            The CSV should include columns like:
                - Origin of A
                - Destination of A
                - Origin of B
                - Destination of B.
        api_key (str): Google API key for fetching route and distance data.
        threshold (int, optional): Percentage threshold for determining significant overlap.
            Defaults to 50%.
        width (int, optional): Width (in meters) for creating rectangles around route segments
            for overlap approximation. Defaults to 100 meters.

    Interactive Prompts:
        - Whether to approximate overlapping nodes.
        - Whether to gather commuting information before and after the overlap.
          Note: Selecting this option may result in additional API calls and costs.

    Workflow:
        - If the user opts for overlapping node approximation:
            - Calls `overlap_rec` to compute detailed overlap information.
            - Alternatively, calls `only_overlap_rec` for simplified overlap details.
        - If the user skips approximation:
            - Calls `process_routes_with_csv` for detailed commuting analysis.
            - Alternatively, calls `process_routes_only_overlap_with_csv` for simplified analysis.

    Returns:
        None: This function does not return a value. It performs computations and writes the results
            to CSV files.
    """
    option = input('Would you like to have approximation for the overlapping nodes? Please enter yes or no: ') 
    if option.lower() == 'yes':
        call = input('Would you like to have information regarding commuting before and after the overlap? Note that this can incur higher costs by calling Google API for multiple times. Please enter yes or no: ')
        if call.lower() == 'yes':
            overlap_rec(csv_file, api_key, output_csv="outputRec.csv", threshold=threshold, width=width)
        elif call.lower() == 'no':
            only_overlap_rec(csv_file, api_key, output_csv="outputRec_only_overlap.csv", threshold=threshold, width=width)
    elif option.lower() == 'no':
        call = input('Would you like to have information regarding commuting before and after the overlap? Note that this can incur higher costs by calling Google API for multiple times. Please enter yes or no: ')
        if call.lower() == 'yes':
            process_routes_with_csv(csv_file, api_key)
        elif call.lower() == 'no':
            process_routes_only_overlap_with_csv(csv_file, api_key)