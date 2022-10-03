import os
import re
import shutil
import configparser
import urllib.request
import tmdbsimple as tmdb
from datetime import datetime
from lxml import etree


config = configparser.ConfigParser()

tmdb.API_KEY = "b5387ae681ba752fdfde05251bc48724"
tmdb.REQUESTS_TIMEOUT = 5

# MOVIE_DIR_1 = "/Volumes/TOSHIBA R4/movie/1"
# MOVIE_DIR_2 = "/Volumes/TOSHIBA R4/movie/2.CHN"
# MOVIE_DIR_3 = "/Volumes/TOSHIBA R4/movie/3.HK"

MOVIE_DIR_1 = "E:\\movie\\1"
MOVIE_DIR_2 = "E:\\movie\\2.CHN"
MOVIE_DIR_3 = "E:\\movie\\3.HK"
MOVIE_DIR_5 = "E:\\movie\\5.KOR-JP"

IMAGE_HOST = "https://image.tmdb.org/t/p/original"


def str_remove_punctuation(target_str):

    if not type(target_str) == str:
        return target_str

    rule = re.compile("[^a-z^A-Z^0-9^\u4e00-\u9fa5]")
    return rule.sub('', target_str)


def scan(movie_dir_path):

    for file in os.listdir(movie_dir_path):

        # 跳过隐藏文件
        if file.startswith("."):
            continue

        # 跳过文件夹
        isDirectory = os.path.isdir(os.path.join(movie_dir_path, file))
        if isDirectory:
            continue

        print("=====================", file, "=====================")

        filename = os.path.splitext(file)[0]
        print("filename =", filename)

        zh_title = filename.split(".")[0]
        print("zh_title =", zh_title)

        suffix = os.path.splitext(file)[-1]
        print("suffix =", suffix)

        isMovieFile = suffix.lower().endswith((".mp4", ".mkv", ".avi"))
        if not isMovieFile:
            print("非视频文件，不处理\r\n")
            continue

        movieDir = os.path.join(movie_dir_path, filename)
        if os.path.exists(movieDir):
            shutil.rmtree(movieDir)
            print("已删除残留目录", movieDir)

        # 刮削
        search = tmdb.Search()
        search.movie(query=zh_title, language="zh")
        searchOk = len(search.results) > 0

        if not searchOk:
            print("搜索影片失败\r\n")
            continue
        else:
            print("搜索结果数量 =", len(search.results))

        target_r = None
        for r in search.results:
            _zh_title = r["title"]
            _release_date = r.get("release_date", "")
            _year = ""
            if len(_release_date) > 0:
                _year = str(datetime.strptime(_release_date, "%Y-%m-%d").year)

            is_filename_match = str_remove_punctuation(
                zh_title) == str_remove_punctuation(_zh_title)
            is_year_match = "." + _year + "." in filename
            is_match = is_filename_match and is_year_match
            print("匹配检查", _zh_title, _release_date, is_match)
            if is_match:  # 文件名 + 年份匹配
                target_r = r
                break

        if target_r is None:
            print("影片信息匹配失败\r\n")
            continue

        os.makedirs(movieDir)
        print("已新建影片目录 " + movieDir)

        # 解析元数据
        id = target_r["id"]
        movie = tmdb.Movies(id)
        en_info = movie.info(language="en")
        en_title = en_info["title"]
        zh_info = movie.info(language="zh")
        imdb_id = zh_info["imdb_id"]
        overview = zh_info["overview"]
        release_date = zh_info["release_date"]
        runtime = zh_info["runtime"]
        poster_path = zh_info["poster_path"]
        backdrop_path = zh_info["backdrop_path"]

        # credits = movie.credits(language="zh")
        # cast = credits["cast"]
        # for cast_item in cast:
        #     print(cast_item)

        # 解析年份
        year = str(datetime.strptime(release_date, "%Y-%m-%d").year)

        # 下载海报
        if poster_path is not None:
            print("poster_path =", poster_path)
            poster_url = IMAGE_HOST + poster_path
            poster_filename = os.path.basename(poster_path)
            _, poster_suffix = os.path.splitext(poster_filename)
            poster_loc = os.path.join(
                movie_dir_path, filename, "poster" + poster_suffix)
            urllib.request.urlretrieve(poster_url, poster_loc)
            print("已下载海报 ===>", poster_loc)

        # 下载背景图
        if backdrop_path is not None:
            print("backdrop_path =", backdrop_path)
            backdrop_url = IMAGE_HOST + backdrop_path
            backdrop_filename = os.path.basename(backdrop_path)
            _, backdrop_suffix = os.path.splitext(backdrop_filename)
            backdrop_loc = os.path.join(
                movie_dir_path, filename, "backdrop" + backdrop_suffix)
            urllib.request.urlretrieve(backdrop_url, backdrop_loc)
            print("已下载背景图 ===>", backdrop_loc)

        # 生成 nfo 文件
        nfoPath = os.path.join(movie_dir_path, filename, filename + ".nfo")
        movieEl = etree.Element("movie")
        etree.SubElement(movieEl, "plot").text = overview
        etree.SubElement(movieEl, "dateadded").text = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S")
        etree.SubElement(movieEl, "title").text = zh_title
        etree.SubElement(movieEl, "originaltitle").text = en_title
        etree.SubElement(movieEl, "year").text = year
        etree.SubElement(movieEl, "imdbid").text = imdb_id
        etree.SubElement(movieEl, "id").text = imdb_id
        etree.SubElement(movieEl, "premiered").text = release_date
        etree.SubElement(movieEl, "releasedate").text = release_date
        etree.SubElement(movieEl, "runtime").text = str(runtime)
        et = etree.ElementTree(movieEl)
        nfoPath = os.path.join(movie_dir_path, filename, filename + ".nfo")
        et.write(nfoPath, xml_declaration=True,
                 encoding="UTF-8", pretty_print=True)
        print("已生成nfo文件", "===>", nfoPath)

        # 移动视频文件
        videoPath = os.path.join(movie_dir_path, file)
        newVideoPath = os.path.join(movie_dir_path, movieDir, file)
        shutil.move(videoPath, newVideoPath)

        print("\r\n")


if __name__ == "__main__":
    scan(MOVIE_DIR_1)
    scan(MOVIE_DIR_2)
    scan(MOVIE_DIR_3)
    scan(MOVIE_DIR_5)
