from googleapiclient.discovery import build
import sys
import os
import re
import json

API_KEY = "AIzaSyD-6vxCBMLgFXBqqzfg7l296d88Lvhjr94"

def get_channel_info(handle, dir_path):
    youtube = build("youtube", "v3", developerKey=API_KEY)
    
    channel_response = youtube.channels().list(
        part = "id, snippet, statistics, contentOwnerDetails",
        forHandle = handle
    ).execute()
    
    file_path = os.path.join(dir_path, "channel_info.json")
    
    with open(file_path, "w", encoding="utf-8") as f:
        # Add "done": "false" to the start of the object
        output = {"done": "false"}
        output.update(channel_response)
        json.dump(output, f, indent=4, ensure_ascii=False)
		

def main():
	# Locate churchChannels.txt in the same directory as this script
	base = os.path.dirname(__file__)
	path = os.path.join(base, 'churchChannels.txt')
	try:
		with open(path, 'r', encoding='utf-8') as f:
			first = f.readline().rstrip('\n')
	except FileNotFoundError:
		print(f'File not found: {path}')
		return
	except Exception as e:
		print(f'Error reading file: {e}')
		return

	# Create a directory named after the first line (sanitized) if it doesn't exist
	safe_name = re.sub(r'[^A-Za-z0-9._-]', '_', first).strip('_')
	if not safe_name:
		print('First line is empty or contains no valid characters for a folder name')
		return

	dir_path = os.path.join(base, safe_name)
	try:
		if os.path.exists(dir_path):
			if os.path.isdir(dir_path):
				print(f'Directory already exists: {dir_path}')
			else:
				print(f'Path exists and is not a directory: {dir_path}')
		else:
			os.makedirs(dir_path)
			print(f'Created directory: {dir_path}')
	except OSError as e:
		print(f'Failed to create directory {dir_path}: {e}')
	
	get_channel_info(first, dir_path)


if __name__ == '__main__':
	main()
