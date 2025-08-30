import pandas as pd
import re
import json
import requests
import gzip
import io
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta

def save_json_file(filename, data):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

class iptv_class:
    def __init__(self):

        # Create DataFrame
        self.cards_df = self.create_df()
        self.create_schedule()
        self.set_titles()


    def create_df(self):
        # Load the M3U content (you can also read from a file)
        with open('utilities\playlist.m3u', 'r', encoding='utf-8') as file:
            lines = file.readlines()

        channels = []
        line = 0
        for i in range(len(lines)):
            if lines[i].startswith("#EXTINF:"):
                # Extract channel name
                name_match = re.search(r",(.+)", lines[i])
                name = name_match.group(1).strip() if name_match else ""

                # Extract logo URL
                logo_match = re.search(r'tvg-logo="([^"]+)"', lines[i])
                logo_url = logo_match.group(1).strip() if logo_match else ""

                # Extract stream URL (next line)
                if i + 2 < len(lines):
                    stream_url = lines[i + 2].strip()
                    channels.append({
                        "index":line,
                        "id": stream_url[46:].split("/")[0],
                        "channel": name,
                        "title": "none",
                        "stream_url": stream_url,
                        "large_cover_image": logo_url #220X132
                    })
                    line+=1
        return pd.DataFrame(channels)

    def parse_epg(self):
        response = requests.get("https://play-berry.net/xmltv.xml.gz")
        with gzip.open(io.BytesIO(response.content), 'rt', encoding='utf-8') as f:
            xml_content = f.read()

        root = ET.fromstring(xml_content)
        programs = []
        for prog in root.findall('programme'):
            channel = prog.attrib['channel']
            if channel in self.cards_df.id.tolist():
                start = prog.attrib['start'][:14]
                stop = prog.attrib['stop'][:14]
                title = prog.findtext('title', '').strip()
                programs.append({
                    'channel': channel,
                    'start': start,
                    'stop': stop,
                    'title': title,
                })
        return programs

    def set_titles(self):
        now = datetime.utcnow() + timedelta(hours=3)
        self.schedule_df = pd.read_csv('utilities/schedule.csv')
        now = int(now.strftime('%Y%m%d%H%M%S'))
        for p in self.cards_df.id.tolist():
            try:
                title = self.schedule_df[
                    (self.schedule_df["channel"] == p) &
                    (self.schedule_df["start"] <= now) &
                    (now < self.schedule_df["stop"])
                    ].title.iloc[0]
            except:
                title = "none"

            self.cards_df.loc[self.cards_df['id'] == p, 'title'] = title

        channels = self.cards_df.to_dict(orient="records")
        save_json_file('utilities/channels.json', channels)

    def create_schedule(self):
        programs = self.parse_epg()
        now = datetime.utcnow() + timedelta(hours=3)
        def to_dt(timestr):
            return datetime.strptime(timestr, "%Y%m%d%H%M%S")
        rows = []
        for p in programs:
            if now < to_dt(p['stop']):
                rows.append({"channel": p['channel'],"title":p['title'],"start":p['start'],"stop":p['stop']})

        self.schedule_df = pd.DataFrame(rows)
        self.schedule_df.to_csv('utilities/schedule.csv', index=False)



