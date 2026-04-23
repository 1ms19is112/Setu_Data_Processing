import json
import requests
import time

API_URL = "http://127.0.0.1:8000/events"
FILE_PATH = "sample_events.json"   # adjust if needed

TIMEOUT = 5
RETRIES = 2


def send_event(event):
    """
    Sends a single event with basic retry logic
    """
    for attempt in range(RETRIES + 1):
        try:
            response = requests.post(API_URL, json=event, timeout=TIMEOUT)

            # success cases
            if response.status_code == 200:
                return "success", response.json()

            # validation or bad request
            elif response.status_code == 422:
                return "failed", response.text

            # retryable errors
            else:
                if attempt < RETRIES:
                    time.sleep(0.2)
                    continue
                return "failed", response.text

        except requests.exceptions.RequestException as e:
            if attempt < RETRIES:
                time.sleep(0.2)
                continue
            return "error", str(e)


def main():
    # Load events
    with open(FILE_PATH, "r") as f:
        events = json.load(f)

    success = 0
    duplicates = 0
    failed = 0

    start_time = time.time()

    for i, event in enumerate(events):

        # 🔧 Ensure merchant_name exists (important fix)
        if "merchant_name" not in event or not event["merchant_name"]:
            event["merchant_name"] = event.get("merchant_id", "Unknown")

        status, result = send_event(event)

        if status == "success":
            msg = result.get("message", "")
            if "duplicate" in msg:
                duplicates += 1
            else:
                success += 1

        else:
            failed += 1
            print(f"\n❌ Failed at index {i}")
            print(f"Event: {event}")
            print(f"Error: {result}")

        # progress log
        if i % 100 == 0:
            print(f"Processed {i}/{len(events)}")

    end_time = time.time()

    print("\n====================")
    print("Seeding Complete")
    print("====================")
    print(f"Total events: {len(events)}")
    print(f"Success: {success}")
    print(f"Duplicates: {duplicates}")
    print(f"Failed: {failed}")
    print(f"Time taken: {round(end_time - start_time, 2)} seconds")


if __name__ == "__main__":
    main()