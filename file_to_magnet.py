import bencodepy
import hashlib
import urllib.parse


def torrent_to_magnet(torrent_file_path):
    with open(torrent_file_path, 'rb') as f:
        torrent_data = bencodepy.decode(f.read())

    info = torrent_data[b'info']

    # Calculate the torrent hash (info hash)
    info_hash = hashlib.sha1(bencodepy.encode(info)).hexdigest()

    # Get the display name
    display_name = info[b'name'].decode('utf-8')
    display_name_encoded = urllib.parse.quote(display_name)

    # Get the list of trackers
    trackers = []
    if b'announce' in torrent_data:
        trackers.append(torrent_data[b'announce'].decode('utf-8'))

    if b'announce-list' in torrent_data:
        for tier in torrent_data[b'announce-list']:
            for tracker in tier:
                trackers.append(tracker.decode('utf-8'))

    # Remove duplicates
    trackers = list(dict.fromkeys(trackers))

    # Remove slashes from trackers
    trackers = [tracker.replace('/', '%2F') for tracker in trackers]

    # Build the magnet link
    magnet_link = f"magnet:?xt=urn:btih:{info_hash}&dn={display_name_encoded}"

    for tracker in trackers:
        magnet_link += f"&tr={tracker}"

    return magnet_link




