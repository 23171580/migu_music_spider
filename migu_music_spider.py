# -*- coding: utf-8 -*-
import requests
from bs4 import BeautifulSoup
import re
import json
import os
from multiprocessing import Pool
import random
import time

test_header = {'Referer': 'http://music.migu.cn/v2/player/audio',
               'Connection': 'keep-alive',
               'Pragma': 'no-cache',
               'Cookie': 'player_stop_open=0; playlist_overlay=0; add_play_now=1; audioplayer_new=0; audioplayer_open=1; playlist_change=0; playlist_adding=0; audioplayer_exist=1',
               'Range': 'bytes=0-',
               'User-Agent': 'Chrome/67.0.3396.99 Safari/537.36'}


headers = {'User-Agent': 'Chrome/67.0.3396.99 Safari/537.36'}


def html_get(url, header):
    with requests.Session() as s:
        sleep_time = random.randint(1, 3)
        time.sleep(sleep_time)
        print('延时：%ds' % sleep_time)
        try:
            res_get = s.get(url, headers=header, timeout=None)
            # , stream=True
            return res_get
        except Exception as e:
            print(e)
            print('下载出错： %s' % url)
            return 0


def json_get_item(key, json_obj):
    if json_obj[key] == "None":
        print("%s为空" % key)
        return 'None'
    else:
        return json_obj[key]


def save_file(suffix, name, write_way, dir_now, data):
    file_dir = dir_now + '\\' + str(name) + suffix
    if write_way == 'wb+':
        with open(file_dir, write_way) as f:
            f.write(data)
            f.close()
    elif write_way == 'w+':
        with open(file_dir, write_way, encoding='utf-8') as f:
            f.write(data)
            f.close()


def song_download_save(song_link):
    # de_link_s = link_s.decode('utf8')//如果有中文，需要注意
    link_num_find = re.findall(r"/\d+", song_link)
    # print(link_num_find)
    song_json_url = "http://music.migu.cn/v2/async/audioplayer/playurl" + link_num_find[0]
    u_json = json.loads(html_get(song_json_url, headers).text)
    # albumId = json_get_item('albumId', u_json)
    # albumName = json_get_item('albumName', u_json)
    music_id = json_get_item('musicId', u_json)
    music_name = json_get_item('musicName', u_json)
    # lyricWriter = json_get_item('lyricWriter', u_json)
    # composer = json_get_item('composer', u_json)
    song_url = json_get_item('songAuditionUrl', u_json)
    lyric = json_get_item('dynamicLyric', u_json)
    large_pic = json_get_item('largePic', u_json)
    # 创建下载文件夹
    dir_create = str(music_name) + str(music_id)
    os.mkdir(dir_create)
    dir_now = str(os.getcwd()) + '\\' + dir_create
    # 下载歌曲
    print("开始下载:%s" % music_name)
    save_file('.mp3', music_name, 'wb+', dir_now, html_get(song_url, test_header).content)
    # 下载图片
    save_file('.jpg', music_name, 'wb+', dir_now, html_get(large_pic, test_header).content)
    # 保存歌词
    save_file('.lrc', music_name, 'w+', dir_now, str(lyric))


def song_list(song_list_html_soup):
    # 批量获取歌曲名&歌曲ID下载地址
    # 获取歌曲后半部分链接
    song_urls_2 = song_list_html_soup.select("span.song-name-text a")
    song_link_list = []
    for song_url_2 in song_urls_2:
        if song_url_2['href'] == 'javascript:;':
            print("《%s》没有版权~\n" % song_url_2.text)
        else:
            song_link_list.append(song_url_2['href'])
            print("新增加《%s》的地址：" % song_url_2.text)
            print("http://music.migu.cn%s\n" % song_url_2['href'])
    # 从当前页面的每个歌曲地址获取歌曲id，拼接组合得到歌曲的json下载地址
    # for i in range(len(song_link_list)):
    pool = Pool()
    pool.map(song_download_save, [song_link_list[i] for i in range(len(song_link_list))])


def json_make_soup(strings, feature):
    return BeautifulSoup(strings, feature)


def get_next_page(next_page_res):
    song_html_soup = json_make_soup(next_page_res, 'lxml')
    # 获取下一页链接
    song_url_next = song_html_soup.find("a", attrs={"class": "page-c iconfont cf-next-page"})
    if song_url_next is None:
        print('未获取到下一页\n')
        song_list(song_html_soup)
        print('资源下载完毕\n程序运行结束')
    else:
        song_next_page_url = "http://music.migu.cn" + song_url_next['href']
        print("获取到下一页地址：%s\n" % song_next_page_url)
        song_list(song_html_soup)
        get_next_page(html_get(song_next_page_url, headers).text)


def if_have_main_page(search_str):
    main_page_res = json_make_soup(search_str, 'lxml').find("div", attrs={"class": "artist-name"})
    if main_page_res is None:
        print("无资源获取")
    else:
        artist_main_page_url = 'http://music.migu.cn' + main_page_res.a['href'] + '?tab=song&page=1'
        print("歌手歌曲主页地址: %s" % artist_main_page_url)
        get_next_page(html_get(artist_main_page_url, headers).text)


def start_get_songs():
    search_key_word = input("输入歌曲搜索关键字：")
    search_url = 'http://music.migu.cn/v2/search?keyword=' + str(search_key_word)
    search_str = html_get(search_url, headers).text
    if_have_main_page(search_str)


if __name__ == '__main__':
    start_get_songs()
