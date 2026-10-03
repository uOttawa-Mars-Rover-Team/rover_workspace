import argparse
import os

import folium
import pandas as pd


def smooth_and_simplify(df, smoothing_window, simplify_step):
    """
    Applies a rolling average to smooth noisy GPS data,
    and drops rows to simplify the number of points drawn.
    """
    if smoothing_window > 1:
        # Rolling average to smooth out GPS "jumps"
        df["latitude"] = (
            df["latitude"]
            .rolling(window=smoothing_window, center=True, min_periods=1)
            .mean()
        )
        df["longitude"] = (
            df["longitude"]
            .rolling(window=smoothing_window, center=True, min_periods=1)
            .mean()
        )

    if simplify_step > 1:
        # Take every Nth point to reduce browser lag on huge datasets
        df = df.iloc[::simplify_step]

    return df


def main():
    parser = argparse.ArgumentParser(description="Map Actual vs Planned Rover Routes")
    parser.add_argument(
        "--actual",
        type=str,
        default="rover_gps_log.csv",
        help="Path to recorded GPS CSV",
    )
    parser.add_argument(
        "--planned",
        type=str,
        default=None,
        help="Path to planned route CSV (lat,lng columns)",
    )
    parser.add_argument(
        "--smoothing",
        type=int,
        default=5,
        help="Rolling average window size for smoothing (1 = no smoothing)",
    )
    parser.add_argument(
        "--simplify",
        type=int,
        default=2,
        help="Keep every Nth point (1 = keep all points)",
    )
    parser.add_argument(
        "--output", type=str, default="route_map.html", help="Output HTML file name"
    )

    args = parser.parse_args()

    if not os.path.exists(args.actual):
        print(f"Error: {args.actual} not found.")
        return

    # 1. Load and process the actual recorded route
    df_actual = pd.read_csv(args.actual)
    df_actual = smooth_and_simplify(df_actual, args.smoothing, args.simplify)
    actual_coords = list(zip(df_actual["latitude"], df_actual["longitude"]))

    # 2. Determine map center (Start of the actual route)
    start_lat, start_lon = actual_coords[0]

    # 3. Initialize the Folium Map (Leaflet.js under the hood)
    m = folium.Map(location=[start_lat, start_lon], zoom_start=18)

    # 4. Add the Google Satellite Tile Layer (Matching your React code)
    folium.TileLayer(
        tiles="https://mt0.google.com/vt/lyrs=s&x={x}&y={y}&z={z}",
        attr="Google",
        name="Google Satellite",
        max_zoom=21,
    ).add_to(m)

    # Add standard OpenStreetMap as an optional toggle
    folium.TileLayer("OpenStreetMap").add_to(m)

    # 5. Plot the Actual Route (Blue, solid line)
    folium.PolyLine(
        locations=actual_coords,
        color="cyan",
        weight=4,
        opacity=0.8,
        tooltip="Actual Recorded Route",
    ).add_to(m)

    # Add Start/End markers for the actual route
    folium.Marker(
        actual_coords[0],
        tooltip="Start (Actual)",
        icon=folium.Icon(color="green", icon="play"),
    ).add_to(m)
    folium.Marker(
        actual_coords[-1],
        tooltip="End (Actual)",
        icon=folium.Icon(color="red", icon="stop"),
    ).add_to(m)

    # 6. Plot the Planned Route (Optional)
    if args.planned and os.path.exists(args.planned):
        df_planned = pd.read_csv(args.planned)

        # Fallback to column indices if 'latitude'/'longitude' headers aren't present
        if "latitude" in df_planned.columns and "longitude" in df_planned.columns:
            planned_coords = list(zip(df_planned["latitude"], df_planned["longitude"]))
        else:
            planned_coords = list(zip(df_planned.iloc[:, 0], df_planned.iloc[:, 1]))

        # Plot Planned Route (Orange, dashed line)
        folium.PolyLine(
            locations=planned_coords,
            color="orange",
            weight=4,
            dash_array="10, 10",  # Makes it dashed to easily distinguish
            tooltip="Planned Route",
        ).add_to(m)

    # 7. Add Layer Control (Allows toggling satellite vs standard map, and turning routes on/off)
    folium.LayerControl().add_to(m)

    # 8. Save to HTML
    m.save(args.output)
    print(f"Map successfully generated! Open '{args.output}' in any web browser.")


if __name__ == "__main__":
    main()
