import json
import time
from opensubtitlescom import OpenSubtitles
import pickle
import os
from difflib import SequenceMatcher
import base64


class subtitles_maneger:
    def __init__(self):
        with open("utilities/accounts.json", 'r') as file:
            self.subtitle_accounts = json.load(file)
            self.num_accounts = len(self.subtitle_accounts["accounts"])

        self.accounts = []
        self.save_account_data()


    def save_account_data(self):
        if not os.path.exists("utilities/accounts.pkl"):
            for i in self.subtitle_accounts["accounts"]:
                self.accounts.append(OpenSubtitles(i['app'], i['key']))
                self.accounts[-1].login(i['username'], i['password'])
                time.sleep(2)
            with open("utilities/accounts.pkl", "wb") as f:
                pickle.dump(self.accounts,f)
        else:
            with open("utilities/accounts.pkl", "rb") as f:
                self.accounts = pickle.load(f)

    def convert_to_vtt(self,srt):
        def format_timedelta(td):
            total_seconds = int(td.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60
            milliseconds = td.microseconds // 1000
            return f"{hours:02}:{minutes:02}:{seconds:02}.{milliseconds:03}"

        vtt_content = "WEBVTT\n\n"
        for subtitle in srt:
            start = format_timedelta(subtitle.start)
            end = format_timedelta(subtitle.end)
            vtt_content += f"{subtitle.index}\n{start} --> {end}\n{subtitle.content}\n\n"
        return vtt_content


    def download(self,query):
        path = f"static/subtitles/{query}0.vtt"
        index = next((i for i, acc in enumerate(self.accounts) if acc.user_info()["data"]["remaining_downloads"] > 0), None)
        if os.path.exists(path) or index == None: return 0

        subtitles_list = []
        subtitles_score = []


        query_decode = base64.b64decode(query).decode('utf-8')
        response = self.accounts[index].search(query=query_decode, languages="he", order_by="downloads").data
        count = -1
        if response:
            for i,x in enumerate(response[:5]):
                while i != count:
                    try:
                        srt = self.accounts[index].download_and_parse(x)
                        subtitles_list.append(self.convert_to_vtt(srt))
                        subtitles_score.append(SequenceMatcher(None,query_decode, x.file_name).ratio())
                        count+=1
                    except:
                        if index+1 <= self.num_accounts-1:
                            index +=1
                        else:
                            break
                else: continue
                break

            sorted_data = [x for _, x in sorted(zip(subtitles_score, subtitles_list), reverse=True)]
            for index, item in enumerate(sorted_data):
                vtt_file_path = f"static/subtitles/{query}{index}.vtt"

                # Write the subtitles to a VTT file
                with open(vtt_file_path, "w", encoding="utf-8") as file:
                    file.write(item)

