import re
import requests

class Spider:
    LOGO_BASE_URL = "https://logo.doube.eu.org/"  # 台标链接变量

    @staticmethod
    def natural_sort_key(s):
        return [
            int(part) if part.isdigit() else part.lower()
            for part in re.split(r'(\d+)', s)
        ]

    def cctv_sort_key(self, item):
        name = item.get("play_source_name", "")
        match = re.search(r'CCTV[-\s]?(\d+)', name, re.IGNORECASE)
        return int(match.group(1)) if match else float('inf')

    def process_channels(self):
        try:
            response = requests.get("https://kzb29rda.com/prod-api/iptv/getIptvList?liveType=0&deviceType=1")
            data = response.json().get('list', [])

            # 分类频道
            cctv_channels = []
            ws_channels = []
            for item in data:
                if re.search(r'CCTV', item.get("play_source_name", ""), re.IGNORECASE):
                    cctv_channels.append(item)
                else:
                    ws_channels.append(item)

            # 排序频道
            sorted_cctv = sorted(cctv_channels, key=self.cctv_sort_key)
            sorted_ws = sorted(ws_channels, key=lambda x: self.natural_sort_key(x.get("play_source_name", "")))

            return sorted_cctv, sorted_ws
        except Exception as e:
            raise Exception(f"数据获取失败: {str(e)}")

    def generate_files(self, cctv, ws):
        # 生成txt文件
        with open('tv.txt', 'w', encoding='utf-8') as f:
            f.write("央视频道,#genre#\n" + '\n'.join(
                [f"{item['play_source_name']},{item['play_source_url']}" for item in cctv]))
            f.write("\n\n卫视频道,#genre#\n" + '\n'.join(
                [f"{item['play_source_name']},{item['play_source_url']}" for item in ws]))

        # 生成m3u文件
        m3u_content = ['#EXTM3U']
        for group, channels in [('央视频道', cctv), ('卫视频道', ws)]:
            for item in channels:
                name = item['play_source_name']
                m3u_content.append(
                    f'#EXTINF:-1 tvg-id="{name}" tvg-name="{name}" '
                    f'tvg-logo="{self.LOGO_BASE_URL}{name}.png" '
                    f'group-title="{group}",{name}\n'
                    f"{item['play_source_url']}"
                )
        
        with open('tv.m3u', 'w', encoding='utf-8') as f:
            f.write('\n'.join(m3u_content))

    def execute(self):
        try:
            cctv, ws = self.process_channels()
            self.generate_files(cctv, ws)
            print("文件生成成功")
        except Exception as e:
            error = f"# ERROR: {str(e)}"
            with open('tv.txt', 'w') as f: f.write(error)
            with open('tv.m3u', 'w') as f: f.write('#EXTM3U\n' + error)

if __name__ == '__main__':
    Spider().execute()