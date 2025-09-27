#!/usr/bin/env python3
import json
import random
import argparse
from datetime import datetime, timedelta


def load_workers():
    """Load workers from Worker.json file."""
    with open("src/data/WorkerObjects.json", "r", encoding="utf-8") as f:
        return json.load(f)


def generate_random_object_id():
    """Generate a random object ID."""
    return f"obj_{random.randint(100000, 999999)}"


def get_random_contacts(workers, count=4):
    """Get random contact SystemIds from workers."""
    selected_workers = random.sample(workers, count)
    return [worker["SystemId"] for worker in selected_workers]


def generate_random_date(days_back=30):
    """Generate a random date within the last N days."""
    base_date = datetime.now()
    random_days = random.randint(0, days_back)
    random_date = base_date - timedelta(days=random_days)
    return random_date.strftime("%Y-%m-%dT%H:%M:%SZ")


def generate_incoming_object(workers):
    """Generate a single campaign object with random data."""
    contacts = get_random_contacts(workers, 4)
    object_id = generate_random_object_id()

    # Create the base object with required fields
    obj = {"object_id": object_id, "last_verified_date": generate_random_date(60)}

    # Add optional contact IDs (randomly decide how many to include)
    num_contacts = random.randint(1, 4)
    for i in range(num_contacts):
        obj[f"contact_id_{i+1}"] = contacts[i]

    # Add optional fields with some probability
    if random.random() > 0.0:  # 100% chance to have edit_url
        obj["edit_url"] = f"https://app.example.com/objects/{object_id}/edit"

    if random.random() > 0.4:  # 60% chance to have last_updated_date
        # Make sure last_updated_date is after last_verified_date
        verified_date = datetime.strptime(
            obj["last_verified_date"], "%Y-%m-%dT%H:%M:%SZ"
        )
        updated_date = verified_date + timedelta(days=random.randint(1, 30))
        obj["last_updated_date"] = updated_date.strftime("%Y-%m-%dT%H:%M:%SZ")

    return obj


def main(num_objects=6):
    """Generate random campaign objects."""
    workers = load_workers()

    # Generate random objects
    objects = []
    for _ in range(num_objects):
        obj = generate_incoming_object(workers)
        objects.append(obj)

    # Save to JSON file
    output_file = "sample_campaign_objects.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(objects, f, indent=2)

    print(f"Generated {num_objects} random campaign objects saved to {output_file}")

    # Also print them to console for verification
    print("\nGenerated objects:")
    print(json.dumps(objects, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate random campaign objects using contacts from Worker.json"
    )
    parser.add_argument(
        "-n",
        "--num-objects",
        type=int,
        default=6,
        help="Number of objects to generate (default: 6)",
    )

    args = parser.parse_args()
    main(args.num_objects)
