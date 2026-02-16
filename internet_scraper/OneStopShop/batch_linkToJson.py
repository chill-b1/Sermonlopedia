"""
batch_linkToJson.py

Usage:
  python batch_linkToJson.py <channel> [--delay 1.0] [--overwrite] [--limit N]

What it does:
  - Reads video IDs from ../automation/videoKeys/<channel_identifier>.txt
  - Creates a folder named after the channel inside this folder (OneStopShop/<channel>)
  - For each video ID: fetches the YouTube title (oEmbed), sanitizes it, and runs
    linkToJson.py to produce a JSON file named with the video's title (video id
    appended for uniqueness).

Notes:
  - linkToJson.py is executed with cwd=OneStopShop so it can read secret.txt.
  - If oEmbed fails the script falls back to using the video id as filename.

Example:
  python batch_linkToJson.py https://www.youtube.com/@HighlandChurchMemphis

"""
from __future__ import annotations
import argparse
import os
import re
import subprocess
import sys
import time
import unicodedata
from pathlib import Path

import requests


def extract_channel_identifier(url_or_id: str) -> str:
    s = (url_or_id or '').strip()
    if 'youtube.com' in s or 'youtu.be' in s:
        if '/@' in s:
            return s.split('/@')[-1].split('/')[0].split('?')[0]
        elif '/channel/' in s:
            return s.split('/channel/')[-1].split('/')[0].split('?')[0]
        elif '/c/' in s:
            return s.split('/c/')[-1].split('/')[0].split('?')[0]
        elif '/user/' in s:
            return s.split('/user/')[-1].split('/')[0].split('?')[0]
    if s.startswith('@'):
        return s[1:]
    return s


def sanitize_filename(name: str, max_len: int = 200) -> str:
    if not name:
        return ''
    name = unicodedata.normalize('NFKD', name)
    # remove characters not allowed in Windows filenames and control chars
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '', name)
    # collapse whitespace and trim
    name = re.sub(r'\s+', ' ', name).strip()
    name = name.rstrip('.')
    if len(name) > max_len:
        name = name[:max_len].rstrip()
    return name


def get_video_title(video_id: str) -> str | None:
    """Try YouTube oEmbed to get the title (no API key required)."""
    try:
        resp = requests.get(
            'https://www.youtube.com/oembed',
            params={'url': f'https://www.youtube.com/watch?v={video_id}', 'format': 'json'},
            timeout=8,
        )
        if resp.status_code == 200:
            return resp.json().get('title')
    except Exception:
        return None
    return None


def main() -> None:
    parser = argparse.ArgumentParser(description='Batch run linkToJson.py for a channel')
    parser.add_argument('channel', help='channel URL, @handle, channel id, or channel filename (from videoKeys)')
    parser.add_argument('--video-keys-dir', default=os.path.normpath(os.path.join(os.path.dirname(__file__), '..', 'automation', 'videoKeys')),
                        help='directory containing videoKeys files (default: ../automation/videoKeys)')
    parser.add_argument('--out-dir', default=os.path.dirname(__file__), help='base folder to create channel folder in (default: this folder)')
    parser.add_argument('--delay', type=float, default=1.0, help='seconds to wait between each call to linkToJson.py')
    parser.add_argument('--overwrite', action='store_true', help='re-run linkToJson.py and overwrite existing json files')
    parser.add_argument('--limit', type=int, default=0, help='process at most N videos (0 = all)')
    args = parser.parse_args()

    script_dir = os.path.abspath(os.path.dirname(__file__))
    channel_id = extract_channel_identifier(args.channel)

    video_keys_dir = os.path.abspath(args.video_keys_dir)
    keys_file = os.path.join(video_keys_dir, f'{channel_id}.txt')

    if not os.path.exists(keys_file):
        print(f'Error: video keys file not found: {keys_file}')
        sys.exit(1)

    out_base = os.path.abspath(args.out_dir)
    channel_folder = os.path.join(out_base, channel_id)
    os.makedirs(channel_folder, exist_ok=True)

    # warn if secret.txt is missing (linkToJson.py needs it)
    secret_path = os.path.join(script_dir, 'secret.txt')
    if not os.path.exists(secret_path):
        print(f'Warning: secret.txt not found in {script_dir} — linkToJson.py may fail if OpenAI key is missing')

    with open(keys_file, 'r', encoding='utf-8') as fh:
        video_ids = [ln.strip() for ln in fh if ln.strip()]

    total = len(video_ids)
    processed = skipped = errors = 0

    link_script = os.path.join(script_dir, 'linkToJson.py')
    if not os.path.exists(link_script):
        print(f'Error: cannot find linkToJson.py at {link_script}')
        sys.exit(1)

    for idx, vid in enumerate(video_ids, start=1):
        if args.limit and processed >= args.limit:
            break

        print(f'[{idx}/{total}] {vid}')

        title = get_video_title(vid) or ''
        safe = sanitize_filename(title)
        if safe:
            filename = f"{safe} [{vid}].json"
        else:
            filename = f"{vid}.json"

        outpath = os.path.join(channel_folder, filename)

        if os.path.exists(outpath) and not args.overwrite:
            print(f'  → Skipping (already exists): {filename}')
            skipped += 1
            continue

        rel_out = os.path.relpath(outpath, script_dir)
        cmd = [sys.executable, link_script, vid, rel_out]

        print(f'  → Running: linkToJson.py {vid} -> {rel_out}')
        try:
            subprocess.run(cmd, cwd=script_dir, check=True)
            processed += 1
            print('  saved')
        except subprocess.CalledProcessError as e:
            print(f'  linkToJson.py failed (returncode={e.returncode})')
            errors += 1
        except Exception as e:
            print(f'  unexpected error: {e}')
            errors += 1

        time.sleep(args.delay)

    print('\nSummary:')
    print(f'  processed: {processed}\n  skipped:   {skipped}\n  errors:    {errors}')


if __name__ == '__main__':
    main()
