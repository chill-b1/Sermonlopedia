import os
import time
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Configuration
API_KEY = 'AIzaSyD-6vxCBMLgFXBqqzfg7l296d88Lvhjr94'  # Replace with your YouTube API key

# Get the directory where this script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CHURCHES_FILE = os.path.join(SCRIPT_DIR, 'churches.txt')
VIDEO_KEYS_FOLDER = os.path.join(SCRIPT_DIR, 'videoKeys')
SLEEP_TIME = 2  # Seconds to wait between API calls to avoid rate limiting

def get_youtube_service():
    """Initialize and return YouTube API service."""
    return build('youtube', 'v3', developerKey=API_KEY)

def extract_channel_identifier(url_or_id):
    """
    Extract channel identifier from a YouTube URL or return the ID as-is.
    
    Handles formats like:
    - https://www.youtube.com/@channelname
    - https://www.youtube.com/channel/UC...
    - https://www.youtube.com/c/channelname
    - @channelname
    - UC... (channel ID)
    - channelname (username)
    """
    url_or_id = url_or_id.strip()
    
    # If it's a URL, extract the identifier
    if 'youtube.com' in url_or_id or 'youtu.be' in url_or_id:
        # Handle @username format in URL
        if '/@' in url_or_id:
            return url_or_id.split('/@')[-1].split('/')[0].split('?')[0]
        # Handle /channel/ format
        elif '/channel/' in url_or_id:
            return url_or_id.split('/channel/')[-1].split('/')[0].split('?')[0]
        # Handle /c/ format
        elif '/c/' in url_or_id:
            return url_or_id.split('/c/')[-1].split('/')[0].split('?')[0]
        # Handle /user/ format
        elif '/user/' in url_or_id:
            return url_or_id.split('/user/')[-1].split('/')[0].split('?')[0]
    
    # Remove @ if present
    if url_or_id.startswith('@'):
        return url_or_id[1:]
    
    return url_or_id

def get_channel_videos(youtube, channel_input, max_results=50):
    """
    Fetch videos from a channel, sorted by date (newest first).
    
    Args:
        youtube: YouTube API service object
        channel_input: YouTube channel URL, @handle, channel ID, or username
        max_results: Maximum number of videos to fetch
    
    Returns:
        List of video IDs, sorted from newest to oldest
    """
    try:
        channel_identifier = extract_channel_identifier(channel_input)
        
        # Try different methods to find the channel
        channel_response = None
        
        # Method 1: Try as handle (for @username format)
        try:
            channel_response = youtube.channels().list(
                part='contentDetails',
                forHandle=channel_identifier
            ).execute()
        except:
            pass
        
        # Method 2: Try as username
        if not channel_response or not channel_response.get('items'):
            try:
                channel_response = youtube.channels().list(
                    part='contentDetails',
                    forUsername=channel_identifier
                ).execute()
            except:
                pass
        
        # Method 3: Try as channel ID (starts with UC usually)
        if not channel_response or not channel_response.get('items'):
            try:
                channel_response = youtube.channels().list(
                    part='contentDetails',
                    id=channel_identifier
                ).execute()
            except:
                pass
        
        if not channel_response or not channel_response.get('items'):
            print(f"Channel not found: {channel_input}")
            return []
        
        uploads_playlist_id = channel_response['items'][0]['contentDetails']['relatedPlaylists']['uploads']
        
        # Get videos from the uploads playlist
        video_ids = []
        next_page_token = None
        
        while len(video_ids) < max_results:
            playlist_response = youtube.playlistItems().list(
                part='contentDetails',
                playlistId=uploads_playlist_id,
                maxResults=min(50, max_results - len(video_ids)),
                pageToken=next_page_token
            ).execute()
            
            for item in playlist_response['items']:
                video_ids.append(item['contentDetails']['videoId'])
            
            next_page_token = playlist_response.get('nextPageToken')
            if not next_page_token:
                break
        
        return video_ids
    
    except HttpError as e:
        print(f"Error fetching videos for channel {channel_input}: {e}")
        return []

def read_existing_video_ids(filepath):
    """Read existing video IDs from a file."""
    if not os.path.exists(filepath):
        return []
    
    with open(filepath, 'r') as f:
        return [line.strip() for line in f if line.strip()]

def write_video_id(filepath, video_id):
    """Append a video ID to a file."""
    with open(filepath, 'a') as f:
        f.write(video_id + '\n')

def read_channel_ids():
    """Read channel IDs from churches.txt."""
    if not os.path.exists(CHURCHES_FILE):
        print(f"Error: {CHURCHES_FILE} not found!")
        return []
    
    with open(CHURCHES_FILE, 'r') as f:
        content = f.read()
        # Split by both newlines and spaces, filter out empty strings
        channels = [ch.strip() for ch in content.replace('\n', ' ').split() if ch.strip()]
        return channels

def process_channel(youtube, channel_input):
    """
    Process a single channel: fetch latest video not yet in the file.
    
    Returns:
        True if a new video was added, False otherwise
    """
    # Create videoKeys folder if it doesn't exist
    if not os.path.exists(VIDEO_KEYS_FOLDER):
        os.makedirs(VIDEO_KEYS_FOLDER)
    
    # Extract clean channel identifier for filename
    channel_identifier = extract_channel_identifier(channel_input)
    
    # Path to this channel's video keys file
    video_file_path = os.path.join(VIDEO_KEYS_FOLDER, f'{channel_identifier}.txt')
    
    # Get existing video IDs
    existing_video_ids = read_existing_video_ids(video_file_path)
    
    # Fetch channel's videos
    print(f"Fetching videos for channel: {channel_input}")
    all_video_ids = get_channel_videos(youtube, channel_input)
    
    if not all_video_ids:
        print(f"  No videos found for {channel_identifier}")
        return False
    
    # Find the newest video that's not already in the file
    for video_id in all_video_ids:
        if video_id not in existing_video_ids:
            print(f"  Adding new video: {video_id}")
            write_video_id(video_file_path, video_id)
            return True
    
    print(f"  No new videos for {channel_identifier}")
    return False

def main():
    """Main loop: continuously cycle through channels and fetch latest videos."""
    youtube = get_youtube_service()
    channel_ids = read_channel_ids()
    
    if not channel_ids:
        print("No channels found in churches.txt")
        return
    
    print(f"Found {len(channel_ids)} channels to monitor")
    print("Starting continuous monitoring loop...\n")
    
    iteration = 0
    while True:
        iteration += 1
        print(f"\n{'='*60}")
        print(f"Iteration {iteration}")
        print(f"{'='*60}\n")
        
        any_new_videos = False
        
        for channel_input in channel_ids:
            try:
                new_video_added = process_channel(youtube, channel_input)
                if new_video_added:
                    any_new_videos = True
                
                # Sleep to avoid hitting rate limits
                time.sleep(SLEEP_TIME)
            
            except Exception as e:
                print(f"Error processing channel {channel_input}: {e}")
        
        if not any_new_videos:
            print("\nNo new videos found in this iteration")
        
        print(f"\nCompleted iteration {iteration}. Restarting cycle...")
        time.sleep(5)  # Wait a bit before starting next cycle

if __name__ == '__main__':
    main()
