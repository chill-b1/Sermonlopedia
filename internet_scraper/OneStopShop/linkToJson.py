import sys
import json
import requests
from openai import OpenAI

#EXAMPLE USAGE: python .\internet_scraper\OneStopShop\linkToJson.py 9oK2reI7NiM tscript.json

with open("secret.txt", "r") as f:
    API_KEY = f.read().strip()
    
def main():
    if len(sys.argv) != 3:
        print("Usage: python linkToJson.py <video_key> <json_filename>")
        sys.exit(1)
    
    video_key = sys.argv[1]
    json_filename = sys.argv[2]
    
    print(f"Fetching transcript for video key: {video_key}")

    response = requests.post(
        "https://www.youtube-transcript.io/api/transcripts",
        headers={
        "Authorization": "Basic 68dc36a035e03e535a210920",
        "Content-Type": "application/json"},
        json={"ids": [video_key]}
    )

    print("Transcript API response received.")

    # parse response, save to file, and enter an interactive Q&A loop using the transcript as context

    if not response.ok:
        print(f"Transcript API request failed: {response.status_code} {response.text}")
        sys.exit(1)

    data = response.json()

    # save raw json to file
    with open(json_filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"Transcript data saved to {json_filename}")
    
    # create OpenAI client
    client = OpenAI(api_key=API_KEY)

    print("Sending data to OpenAI for processing...")

    prompt_intro = (
        "The following is the transcript of a worship service in JSON format:\n"
    )
    prompt_body = (
        "\nReturn a JSON object with exactly the following keys (no extra keys):\n"
        " - start_time: string — the sermon start time (use the timestamp or hh:mm:ss if available)\n"
        " - end_time: string — the sermon end time\n"
        " - theme: string — one-word theme summarizing the sermon (one word only)\n"
        " - main_verse: string — the main Bible verse used (e.g. \"John 3:16\")\n"
        " - pastor: string — the name of the pastor, leave blank if unknown\n"
        "Then, append the data from the transcript that you were given, but only the entries after the start_time and before the end_time.  keep the timestamps in json format like they were given\n"
        "\nIMPORTANT: Reply with only valid JSON, make sure to wrap in curly braces, nothing else. Example:\n"
        "{\"start_time\": \"00:22:10\", \"end_time\": \"01:05:30\", \"theme\": \"Grace\", \"main_verse\": \"Ephesians 2:8-9\", \"pastor\": \"Pastor John\"}\n"
        "\nIf a value cannot be determined, set it to null.\n"
    )

    prompt = prompt_intro + json.dumps(data) + prompt_body

    response_obj = client.responses.create(model="gpt-5.2", input=prompt)

    print("OpenAI response received.")

    print("Saving processed data to JSON file...")
    # Extract just the text output from the response object
    text_output = response_obj.output[0].content[0].text

    lines = text_output.splitlines()
    if len(lines) <= 2:
        text_output = ""
    else:
        text_output = "\n".join(lines[1:-1])

    try:
        parsed = json.loads(text_output)
    except json.JSONDecodeError:
        with open(json_filename, "w", encoding="utf-8") as f:
            f.write(text_output)
    else:
        with open(json_filename, "w", encoding="utf-8") as f:
            json.dump(parsed, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
