#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Импортируем Flask для web-сервера
from flask import Flask, send_file

import time
import subprocess  # Будет запускать omxplayer и управять им вместо нас
import re  # Регулярные выражения — гибкие, но сложные конструкции для поиска в тексте по шаблону
import os, os.path  # Помогут в работе с файлами и папками на диске
import string  # Поможет в небольших манипуляциях с именами файлов

app = Flask(__name__)

# Задаём в массиве типы фйлов, которые сможем воспроизвести

PLAYABLE_TYPES = [
    ".264",
    ".avi",
    ".bin",
    ".divx",
    ".f4v",
    ".h264",
    ".m4e",
    ".m4v",
    ".m4a",
    ".mkv",
    ".mov",
    ".mp4",
    ".mp4v",
    ".mpe",
    ".mpeg",
    ".mpeg4",
    ".mpg",
    ".mpg2",
    ".mpv",
    ".mpv2",
    ".mqv",
    ".mvp",
    ".ogm",
    ".ogv",
    ".qt",
    ".qtm",
    ".rm",
    ".rts",
    ".scm",
    ".scn",
    ".smk",
    ".swf",
    ".vob",
    ".wmv",
    ".xvid",
    ".x264",
    ".mp3",
    ".flac",
    ".ogg",
    ".wav",
    ".flv",
    ".mkv",
]

# Склеим полные пути к файлам: ярлыку на папку с фильмами, папке с интерфейсом
MEDIA_RDIR = app.root_path + "/" + "media/"
PAGE_FOLDER = app.root_path + "/" + "omxfront/"
PAGE_NAME = "interface.htm"

play_list = []

# Переменная, в которой будет храниться процесс omxplayer
omxproc = None

# Словарь команд управления плеером
command_send = {
    "speedup": "1",
    "speeddown": "2",
    "nextaudio": "k",
    "prevaudio": "j",
    "nextchapter": "o",
    "prevchapter": "i",
    "nextsubs": "m",
    "prevsubs": "n",
    "togglesubs": "s",
    "stop": "q",
    "pause": "p",
    "volumedown": "-",
    "volumeup": "+",
    "languagedown": "j",
    "languageup": "k",
    "subtitledown": "n",
    "subtitleup": "m",
    "seek-30": "\x1b\x5b\x44",
    "seek+30": "\x1b\x5b\x43",
    "seek-600": "\x1b\x5b\x42",
    "seek+600": "\x1b\x5b\x41",
    "seekb": "\x1b\x5b\x44",
    "seekf": "\x1b\x5b\x43",
    "seekbl": "\x1b\x5b\x42",
    "seekfl": "\x1b\x5b\x41",
}


@app.route("/")
def Interface():
    return send_file(PAGE_FOLDER + PAGE_NAME)


@app.route("/play/<file>")
def Play(file):
    omx_play(file)
    return '[{"message":"OK"}]'


@app.route("/playlist/<item>")
def Playlist(item):
    if not item == "":
        play_list.append(item)
    output = "[/n"
    for i, part in enumerate(play_list):
        output = (
            output
            + '{"'
            + i
            + '":'
            + string.capwords(os.path.splitext(part)[0])
            + '"}\n'
        )
    output = output + "]"
    return output


@app.route("/path/", defaults={"path": ""})
@app.route("/path/<path>")
def Path(path):
    itemlist = []
    if path.startswith(".."):
        path = ""
    # Проводим манипуляции с файлами и папка в системе: выделяем имена, расширения из полного пути
    for item in os.listdir(os.path.join(MEDIA_RDIR, path)):
        if os.path.isfile(os.path.join(MEDIA_RDIR, path, item)):
            fname = os.path.splitext(item)[0]
            fname = re.sub("[^a-zA-Z0-9\[\]\(\)\{\}]+", " ", fname)
            fname = re.sub("\s+", " ", fname)
            fname = string.capwords(fname.strip())
            singletuple = (os.path.join(path, item), fname, "file")
        else:
            fname = re.sub("[^a-zA-Z0-9']+", " ", item)
            fname = re.sub("\s+", " ", fname)
            fname = string.capwords(fname.strip())
            singletuple = (os.path.join(path, item), fname, "dir")
        itemlist.append(singletuple)
    itemlist = [f for f in itemlist if not os.path.split(f[0])[1].startswith(".")]
    itemlist = [
        f
        for f in itemlist
        if os.path.splitext(f[0])[1].lower() in PLAYABLE_TYPES or f[2] == "dir"
    ]
    list.sort(itemlist, key=lambda alpha: alpha[1])
    list.sort(itemlist, key=lambda dirs: dirs[2])
    outputlist = []
    # Формируем ответ из списка файлов и папок
    for line in itemlist:
        outputlist.append(
            '{"path":"'
            + line[0]
            + '", "name":"'
            + line[1]
            + '", "type":"'
            + line[2]
            + '"}'
        )
    return "[\n" + ",\n".join(outputlist) + "]"


@app.route("/<name>")
def other(name):
    if not name == "":
        if name in command_send:
            omx_send(command_send[name])
            return '[{"message":"OK"}]'
        else:
            if os.path.exists(os.path.join(PAGE_FOLDER, name)):
                return send_file(PAGE_FOLDER + name)
            return '[{"message":"FAIL"}]'
    print("Incorrect capture!")
    return '[{"message":"ERROR!!!"}]'


def omx_send(data):
    global omxproc
    if omxproc is not None:
        # Если omxplayer запущен, можно отправлять команды
        if omxproc.poll() is None:
            try:
                omxproc.stdin.write(data.encode("utf-8"))
                # Если поступила команда на выключение
                if data == "q":
                    # Дадим плееру 5 секунд на отключение.
                    omxproc.wait(timeout=5)
                    omxproc = None
            # Если плеер не завершает работу, выключим принудительно
            except subprocess.TimeoutExpired:
                print(
                    "Closing timeout is over. The process will be terminated forcibly."
                )
                subprocess.Popen("killall omxplayer.bin", shell=True)
                omxproc = None
            # Если возникнет какая-то другая ошибка, выведем информацию о ней
            except OSError as err:
                print("Error: ", err)
        else:
            omxproc = None


# Включаем воспроизведеине файла
def omx_play(filename):
    global omxproc
    # Закрываем все плееры
    subprocess.Popen("killall omxplayer.bin", stderr=subprocess.DEVNULL, shell=True)
    # Полный путь к видеофайлу
    filepath = os.path.join(MEDIA_RDIR, filename)
    # Запускаем плеер
    # -o local — выводит звук на разъём Jack 3.5
    # -o hdmi — выводит звук на динамики телевизора (если они есть)
    # -o both — выводит звук и на Jack 3.5, и на телевизор
    omxproc = subprocess.Popen(
        "omxplayer -o hdmi " + filepath, stdin=subprocess.PIPE, bufsize=0, shell=True
    )
    omx_send("")


if __name__ == "__main__":
    app.run(port=8080, host="0.0.0.0", threaded=True)

# Во время отладки консоль может выводить сообщение «».
# Это означает, что сокеты заняты другой программой. Чтобы их освободить, выполни команду в консоли
# sudo fuser 8080/tcp -k
