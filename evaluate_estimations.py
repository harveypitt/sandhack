import csv
import argparse
import os
from math import radians, sin, cos, sqrt, atan2
from typing import List, Tuple, Any
from tabulate import tabulate

def load_csv(filepath: str) -> List[dict[str, Any]]:
    with open(filepath, newline='') as csvfile:
        return list(csv.DictReader(csvfile))

def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371e3  # meters
    phi1, phi2 = radians(lat1), radians(lat2)
    d_phi = radians(lat2 - lat1)
    d_lambda = radians(lon2 - lon1)

    a = sin(d_phi / 2)**2 + cos(phi1) * cos(phi2) * sin(d_lambda / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c

def compare_guesses_to_truth(guesses_path: str, truth_path: str) -> Tuple[List[List[str]], float, int, int]:
    guesses = load_csv(guesses_path)
    truths = load_csv(truth_path)

    guess_dict = {row['image_id']: row for row in guesses}
    truth_dict = {row['image_id']: row for row in truths}

    results: List[List[str]] = []
    total_error = 0.0
    match_count = 0
    not_supplied_count = 0

    for image_id in truth_dict:
        if image_id in guess_dict:
            try:
                lat1 = float(truth_dict[image_id]['latitude'])
                lon1 = float(truth_dict[image_id]['longitude'])
                lat2 = float(guess_dict[image_id]['latitude'])
                lon2 = float(guess_dict[image_id]['longitude'])
                error = haversine(lat1, lon1, lat2, lon2)

                results.append([
                    image_id,
                    f"{lat1:.6f}, {lon1:.6f}",
                    f"{lat2:.6f}, {lon2:.6f}",
                    f"{error:.2f} m"
                ])
                total_error += error
                match_count += 1
            except ValueError:
                print(f"[WARN] Invalid lat/lon for image_id {image_id}")
        else:
            print(f"[WARN] No guess provided for image_id {image_id}")
            results.append([
                image_id,
                f"{truth_dict[image_id]['latitude']}, {truth_dict[image_id]['longitude']}",
                "N/A",
                "N/A"
            ])
            not_supplied_count += 1

    return results, total_error, match_count, not_supplied_count

def main() -> None:
    parser = argparse.ArgumentParser(description='Compare estimations.csv and truth.csv in a given directory.')
    parser.add_argument('directory', help='Path to directory containing estimations.csv and truth.csv')
    args = parser.parse_args()

    guesses_path = os.path.join(args.directory, "estimations.csv")
    truth_path = os.path.join(args.directory, "truth.csv")

    if not os.path.isfile(guesses_path):
        print(f"❌ File not found: {guesses_path}")
        return
    if not os.path.isfile(truth_path):
        print(f"❌ File not found: {truth_path}")
        return

    results, total_error, match_count, not_supplied_count = compare_guesses_to_truth(guesses_path, truth_path)

    headers = ['Image ID', 'Truth (lat, lon)', 'Guess (lat, lon)', 'Error']
    print("\n")
    print(tabulate(results, headers=headers, tablefmt='pretty'))
    print(f"\nTotal error: {total_error:.2f} m over {match_count} matches\n")
    if not_supplied_count > 0:
        print(f"{not_supplied_count} estimation(s) were not provided\n")


if __name__ == '__main__':
    main()
