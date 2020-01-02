import requests
import tqdm
import os
import re
import subprocess
from decimal import Decimal
from multiprocessing import Pool
# from ffmpy import FFmpeg
import time
import threading
from bs4 import BeautifulSoup

BASE_URL = "http://www.jav321.com"


def download_from_url(url, dst, _files_size=None):
    response = requests.get(url, stream=True)
    file_size = int(response.headers["content-length"])
    if (os.path.exists(dst)):
        first_byte = os.path.getsize(dst)
    else:
        first_byte = 0
    if first_byte >= file_size:
        return file_size
    print(file_size)
    if (_files_size is not None):
        file_size = _files_size
    if (file_size > 60 * 1024 * 1024):
        return False
    header = {"Range": f"bytes={first_byte}-{file_size}"}
    pbar = tqdm.tqdm(total=file_size, initial=first_byte, unit='B', unit_scale=True, desc=dst)
    req = requests.get(url, headers=header, stream=True)
    with(open(dst, "ab")) as f:
        for chunk in req.iter_content(chunk_size=1024):
            if chunk:
                f.write(chunk)
                pbar.update(1024)
    pbar.close()
    return file_size


# 获取视频的 duration 时长 长 宽
def get_video_length(file):
    process = subprocess.Popen(['ffmpeg', '-i', file],
                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    stdout, stderr = process.communicate()
    print(stdout)
    pattern_duration = re.compile("Duration:\s(\d+?):(\d+?):(\d+\.\d+?),")
    pattern_size = re.compile(",\s(\d{3,4})x(\d{3,4}),")
    matches = re.search(pattern_duration, stdout.decode('utf-8'))
    size = re.search(pattern_size, stdout.decode('utf-8'))
    print(size)
    if size:
        size = size.groups()
        print(size)
    if matches:
        matches = matches.groups()
        print(matches)
        hours = Decimal(matches[0])
        minutes = Decimal(matches[1])
        seconds = Decimal(matches[2])  # 处理为十进制，避免小数点报错
        total = 0
        total += 60 * 60 * hours
        total += 60 * minutes
        total += seconds
        if size is not None:
            width = size[0]
            height = size[1]
        else:
            width = 0
            height = 0
        process.kill()
        return {
            'total': total,
            'width': width,
            'height': height
        }


def cutVideo(startPoint, file, endPoint, newFile):
    command = ['ffmpeg', '-ss', startPoint, '-i', file, '-acodec', 'copy', '-vcodec', 'copy', '-t',
               endPoint, newFile]
    print(command)
    process = subprocess.Popen(command,
                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    stdout, stderr = process.communicate()
    print(stdout)
    print(stderr)
    process.kill()


def download_page(url):
    '''
     用于下载页面
     '''
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:61.0) Gecko/20100101 Firefox/61.0"}
    r = requests.get(url, headers=headers)
    r.encoding = 'utf8'
    return r.text


def get_video(link, text):
    '''
    获取当前页面的图片,并保存
    '''
    # link = BASE_URL + link
    # print(link)
    html = download_page(link)  # 下载界面
    print("**************")
    print(link)
    print("**************")

    soup = BeautifulSoup(html, 'html.parser')
    print(soup)
    video_list = soup.find_all('video')  # 找到界面所有视频标签
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:61.0) Gecko/20100101 Firefox/61.0"}
    create_dir('video/{}'.format(text))
    for i in video_list:
        print(i)
        vid_link = i.find('source').get('src')  # 拿到视频的具体 url
        download_from_url(vid_link, vid_link[vid_link.rfind('/') + 1:])


def get_video_list(link, text):
    '''
    获取当前页面的视频地址,并保存
    '''

    link = BASE_URL + link
    html = download_page(link)  # 下载界面
    soup = BeautifulSoup(html, 'html.parser')
    vid_list = soup.find("body").find('div', class_='panel-body').find_all('a',
                                                                           href=re.compile("/video/"))  # 找到界面所有子页面链接
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:61.0) Gecko/20100101 Firefox/61.0"}
    create_dir('series/{}'.format(text))
    has_next = True
    for i in vid_list:
        vid_link = ""
        vid_link = BASE_URL + i["href"]  # 拿到视频的具体 url
        text = i.text
        print(vid_link)
        get_video(vid_link, text)


def create_dir(name):
    if not os.path.exists(name):
        os.makedirs(name)


def execute(url):
    # 得到页面
    page_html = download_page(url)
    print(page_html)
    soup = BeautifulSoup(page_html, 'html.parser')
    series_list = soup.find('body').find("div", class_='col-md-10').find_all('a', href=re.compile(
        "/series/*/?"))  # 找到界面所有子页面链接
    print("%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%")
    print(series_list)
    for i in series_list:
        print(i)
        vid_link = i["href"]  # 拿到视频的具体 url
        print(vid_link)
        text = i.text
        print(text)
        get_video_list(vid_link, text)

    # get_video("http://www.jav321.com/video/mimk00022","tetee")


def main():
    create_dir('video')
    # 系列总共129页
    queue = [i for i in range(1, 129)]  # 构造 url 链接 页码。
    threads = []
    while len(queue) > 0:
        for thread in threads:
            if not thread.is_alive():
                threads.remove(thread)
        while len(threads) < 5 and len(queue) > 0:  # 最大线程数设置为 5
            cur_page = queue.pop(0)
            url = BASE_URL + '/series_title_list/{}'.format(cur_page)
            thread = threading.Thread(target=execute, args=(url,))
            thread.setDaemon(True)
            thread.start()
            print('{}正在下载{}页'.format(threading.current_thread().name, cur_page))
            threads.append(thread)

# if __name__ == '__main__':
#     # main()
#     # url = BASE_URL + '/series_title_list/{}'.format(1)
#     # execute(url)
