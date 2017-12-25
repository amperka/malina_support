# -*- coding: utf-8 -*-
import requests, json
import RPi.GPIO as GPIO
# Дополнительно импортируем функцию округления вниз из модуля math
from math import floor

GPIO.setmode(GPIO.BCM)
# храним светодиоды для "солнца" и "осадков" в разных массивах
precipitationLED = [10, 12, 14, 15, 17, 18, 21, 24, 26]
sunLED = [13, 16, 19]
# чтобы не писать цикл инициализации два раза,
# пробегаем по всем светодиодам в одном большом массиве,
# собранном из двух (precipitationLED + sunLED)
for led in precipitationLED + sunLED:
    GPIO.setup(led, GPIO.OUT)
    GPIO.output(led, GPIO.LOW)
    # print('init led', led)

url = 'http://api.openweathermap.org/data/2.5/forecast/'
# lat и lon — координаты Москвы
payload = {
    'lat': '55.75',
    'lon': '37.62',
    'units': 'metric',
    'appid': '' # вставь свой ключ от OpenWeatherMap
}

# Если ключ не задан, выходим из программы
if (payload['appid'] == ''):
    print('Error!')
    print('You have to setup API key first!')
    print('Open this file in editor and complete appid field.')
    quit()

# Среднее количество осадков в день (мм)
# Только для дней с осадками, а не всех дней в году/месяце
maxPrecipitationPerDay = 1.5
# Пропорция: сколько необходимо зажечь светодиодов, чтобы
# показать количество осадков
scalePrecipitation = maxPrecipitationPerDay / len(precipitationLED)

# Опытным путем подобрали коэффициент 25 для отображения «безоблачности»
# Математически верное число — 33.3 (максимум облачности 100% / число светодиодов 3)
scaleSun = 25

# Выполняем запрос к сервису погоды
res = requests.get(url, params=payload)
data = json.loads(res.text)
forecast = data['list']

# Сервис openweathermap не предоставляет прогноз погоды на день бесплатно
# Поэтому делаем хак: складываем прогнозы погоды на каждые 3 часа на ближайшие сутки
# Итого, нужно сложить количество осадков и усреднить облачность в первых 8 элементах массива ['list']
precipitation = 0.0
clouds = 0.0
# Для каждого элемента из диапазона ['list'][0]…['list'][7]
# Складываем количество осадков и облачность
for threeHours in range(8):
    weather = forecast[threeHours]
    if ('rain' in weather):
        precipitation = precipitation + weather['rain']['3h']
    if ('snow' in weather):
        precipitation = precipitation + weather['snow']['3h']
    if ('clouds' in weather):
        clouds = clouds + weather['clouds']['all']

# Чтобы получить среднюю облачность, делим сумму на количество слагаемых
clouds = clouds / 8
print('Cloudness:', clouds)

print('Precipitation per day:', precipitation)
# Зная количество осадков, сколько светодиодов нужно зажечь?
totalLED = int(floor(precipitation / scalePrecipitation))
# Если осадков так много, что не хватает светодиодов, зажём только те, что есть.
# Иначе получим ошибку в программе и она аварийно завершится
if totalLED > len(precipitationLED):
	totalLED = len(precipitationLED)

for led in range(totalLED):
    GPIO.output(precipitationLED[led], GPIO.HIGH)
    print(precipitationLED[led])

# Зная облачность, сколько светодиодов нужно зажечь, показав «безоблачность»?
totalLED = int(floor((100 - clouds) / scaleSun))

for led in range(totalLED):
    GPIO.output(sunLED[led], GPIO.HIGH)
    print(sunLED[led])
