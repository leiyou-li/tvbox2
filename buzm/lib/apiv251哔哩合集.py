# coding = utf-8
#!/usr/bin/python

from Crypto.Util.Padding import unpad, pad
from urllib.parse import unquote, quote
from Crypto.Cipher import ARC4, AES
from base.spider import Spider
from bs4 import BeautifulSoup
import requests
import base64
import json
import time
import sys
import re

sys.path.append('..')

xurl = "https://api.bilibili.com"

headerx = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36 Edg/134.0.0.0',
    'Referer': 'https://www.bilibili.com',
    'Cookie': '_uuid=563F11078-8DB6-9AE10-61F3-1B348A13E6CD47773infoc;'  # 添加必要的Cookie
}

class Spider(Spider):
    def getName(self):
        return "首页"

    def init(self, extend):
        pass

    def isVideoFormat(self, url):
        pass

    def manualVideoCheck(self):
        pass

    def homeContent(self, filter):
        # 修改搜索分类的生成方式为 ['名称', 's_分类'] 形式
        classes = [
            {"type_id": "1001", "type_name": "影视"},
            
            # 搜索分类改为 ['名称', 's_分类'] 形式
            ["热门", "s_热门"],
            ["沙雕动画", "s_沙雕动画"],
            ["沙雕动漫", "s_沙雕动漫"], 
            ["搞笑", "s_搞笑"],
            ["8k", "s_8k"],
            ["8k演唱会", "s_8k演唱会"],
            ["8k风景", "s_8k风景"],
            ["12k", "s_12k"],
            ["4k户外", "s_4k户外"],
            ["MV", "s_MV"],
            ["短剧", "s_短剧"],
            ["演唱会", "s_演唱会"],
            ["粤语", "s_粤语"],
            ["美食", "s_美食"],
            
            # 其他分类
            {"type_id": "1002", "type_name": "娱乐"},
            {"type_id": "1003", "type_name": "音乐"},
            {"type_id": "1004", "type_name": "舞蹈"},
            {"type_id": "1005", "type_name": "动画"},
            {"type_id": "1006", "type_name": "绘画"},
            {"type_id": "1007", "type_name": "鬼畜"},
            {"type_id": "1008", "type_name": "游戏"},
            {"type_id": "1009", "type_name": "资讯"},
            {"type_id": "1010", "type_name": "知识"},
            {"type_id": "1011", "type_name": "人工智能"},
            {"type_id": "1012", "type_name": "科技数码"},
            {"type_id": "1013", "type_name": "汽车"},
            {"type_id": "1014", "type_name": "时尚美妆"},
            {"type_id": "1015", "type_name": "家装房产"},
            {"type_id": "1016", "type_name": "户外潮流"},
            {"type_id": "1017", "type_name": "健身"},
            {"type_id": "1018", "type_name": "体育运动"},
            {"type_id": "1019", "type_name": "手工"},
            {"type_id": "1020", "type_name": "美食"},
            {"type_id": "1021", "type_name": "小剧场"},
            {"type_id": "1022", "type_name": "旅游出行"},
            {"type_id": "1023", "type_name": "三农"},
            {"type_id": "1024", "type_name": "动物"},
            {"type_id": "1025", "type_name": "亲子"},
            {"type_id": "1026", "type_name": "健康"},
            {"type_id": "1027", "type_name": "情感"},
            {"type_id": "1028", "type_name": "神秘学"},
            {"type_id": "1030", "type_name": "生活兴趣"},
            {"type_id": "1031", "type_name": "生活经验"}
        ]
        
        # 将列表中的搜索分类转换为字典格式，并添加🔥符号
        processed_classes = []
        for item in classes:
            if isinstance(item, list):
                # 搜索分类：['名称', 's_分类'] -> 转换为字典
                processed_classes.append({
                    "type_id": item[1],
                    "type_name": f"🔥{item[0]}"
                })
            else:
                # 普通分类直接添加
                processed_classes.append(item)
                
        return {"class": processed_classes}

    def categoryContent(self, cid, pg, filter, ext):
        # 修改判断条件为"s_"开头
        if cid.startswith("s_"):
            keyword = cid.split("_", 1)[1]
            return self.searchContentPage(keyword, False, pg)

        url = f"{xurl}/x/web-interface/region/feed/rcmd?display_id={pg}&request_cnt=15&from_region={cid}"
        res = requests.get(url=url, headers=headerx).json()
        videos = []
        for item in res["data"]["archives"]:
            video = {
                "vod_id": item["bvid"],
                "vod_name": item["title"],
                "vod_pic": item["cover"],
                "vod_remarks": f"播放量：{self.format_views(item['stat']['view'])}",
            }
            videos.append(video)
        return {
            "list": videos,
            "page": pg,
            "pagecount": 9999,
            "limit": 90,
            "total": 999999,
        }

    def format_views(self, num):
        return f"{num / 10000:.1f}万" if num >= 10000 else str(num)

    def detailContent(self, ids):
        result = {}
        videos = []
        did = ids[0]
        url = f"https://www.bilibili.com/video/{did}"
        res = requests.get(url=url, headers=headerx)
        res.encoding = "utf-8"
        res_text = res.text

        start_str, end_str = "window.__INITIAL_STATE__=", "}};"
        s_idx = res_text.find(start_str)
        if s_idx > -1:
            s_idx += len(start_str)
            e_idx = res_text.find(end_str, s_idx)
            if e_idx > -1:
                kjson_text = res_text[s_idx:e_idx] + "}}"
        kjson = json.loads(kjson_text)

        video_data = kjson.get("videoData", {})
        name = video_data.get("title", "未知标题")
        remarks = video_data.get("tname", "")
        director = video_data.get("owner", {}).get("name", "未知作者")
        content = video_data.get("desc", "")

        play_url = ""
        for i in kjson.get("availableVideoList", [{}])[0].get("list", []):
            title = i.get("title", "未知")
            p_num = i.get("p", 1)
            play_url += f"{title}${url}?p={p_num}#"
        play_url = play_url.rstrip("#")

        video = {
            "vod_id": did,
            "vod_name": name,
            "vod_actor": "",
            "vod_director": director,
            "vod_content": content,
            "vod_remarks": remarks,
            "vod_year": "",
            "vod_area": "",
            "vod_play_from": "B站",
            "vod_play_url": play_url,
        }
        videos.append(video)
        result["list"] = videos
        return result

    def playerContent(self, flag, id, vipFlags):
        try:
            # 解析URL中的参数
            from urllib.parse import parse_qs, urlparse
            parsed = urlparse(id)
            params = parse_qs(parsed.query)
            bvid = parsed.path.split('/')[-1] if 'bvid' not in params else params['bvid'][0]
            pn = params.get('pn', ['1'])[0]
            
            # 使用B站API获取播放地址
            api_url = f"https://api.bilibili.com/x/player/playurl?bvid={bvid}&pn={pn}"
            response = requests.get(api_url, headers=headerx)
            data = response.json()

            if data.get("code") == 0:
                # 提取视频URL
                video_url = data["data"]["durl"][0]["url"]
                return {
                    "parse": 0,
                    "url": video_url,
                    "header": headerx,
                }
        except Exception as e:
            pass

        # 如果API失败，则使用原始URL
        return {
            "parse": 1,
            "jx": 1,
            "url": id,
            "header": headerx,
        }

    def searchContentPage(self, key, quick, page):
        # 使用B站官方搜索API
        api_url = "https://api.bilibili.com/x/web-interface/search/type"
        params = {
            "keyword": key,
            "page": page,
            "search_type": "video",
            "pagesize": 20
        }
        
        try:
            response = requests.get(api_url, params=params, headers=headerx)
            data = response.json()
            
            if data.get("code") != 0:
                return {"list": [], "page": page, "pagecount": 1, "total": 0}
                
            result = data.get("data", {})
            videos = []
            
            for item in result.get("result", []):
                # 清理标题中的HTML标签
                title = item.get("title", "")
                title = re.sub(r'<[^>]+>', '', title)
                
                # 构建视频信息
                video = {
                    "vod_id": item.get("bvid", ""),
                    "vod_name": title,
                    "vod_pic": self.fix_url(item.get("pic", "")),
                    "vod_remarks": self.format_search_remarks(item)
                }
                videos.append(video)
            
            # 计算分页信息
            total = result.get("numResults", 0)
            pagecount = (total + 19) // 20  # 每页20条，计算总页数
            
            return {
                "list": videos,
                "page": int(page),
                "pagecount": pagecount,
                "limit": 20,
                "total": total
            }
            
        except Exception as e:
            print(f"搜索失败: {str(e)}")
            return {"list": [], "page": page, "pagecount": 1, "total": 0}

    def format_search_remarks(self, item):
        """格式化搜索结果的备注信息"""
        parts = []
        
        # 时长
        duration = item.get("duration")
        if duration:
            parts.append(f"时长: {duration}")
        
        # 播放量
        play = item.get("play", 0)
        parts.append(f"播放: {self.format_views(play)}")
        
        # UP主
        author = item.get("author")
        if author:
            parts.append(f"UP: {author}")
        
        # 发布时间
        pubdate = item.get("pubdate")
        if pubdate:
            year = time.strftime("%Y", time.localtime(pubdate))
            parts.append(f"{year}年")
        
        return " · ".join(parts)

    def fix_url(self, url):
        """修复URL格式"""
        if url.startswith("//"):
            return "https:" + url
        return url

    def searchContent(self, key, quick, pg="1"):
        return self.searchContentPage(key, quick, pg)

    def localProxy(self, params):
        if params['type'] == "m3u8":
            return self.proxyM3u8(params)
        elif params['type'] == "media":
            return self.proxyMedia(params)
        elif params['type'] == "ts":
            return self.proxyTs(params)
        return None