import requests
import pyttsx3
import pyaudio
import json
import datetime
import vosk


# Загрузка модели
model = vosk.Model("vosk-model-small-ru-0.22")  # Путь к модели Vosk для русского языка
rec = vosk.KaldiRecognizer(model, 16000)
print('Загружено')

# Настройка языка
engine = pyttsx3.init('sapi5')
voices = engine.getProperty('voices')


found = None
# Попробовать установить предпочтительный голос
for voice in voices:
    if voice.name == 'Microsoft Irina Desktop - Russian':
        engine.setProperty('voice', voice.id)
        break

if found is None:
    print('Голос не найден! Установите русский голос')
    exit()

# Скорость и громкость
engine.setProperty("rate", 80)
engine.setProperty("volume", 80)


# Функция для произнесения текста
def speak(text):
    engine.say(text)
    engine.runAndWait()


def get_holidays(year, country_code):
    # Формирование URL для получения данных о праздниках
    url = f"https://date.nager.at/api/v2/publicholidays/{year}/{country_code}"

    # Отправка GET-запроса по указанному URL
    response = requests.get(url)

    # Извлечение данных о праздниках из ответа в формате JSON
    holidays = response.json()
    return holidays


def process_command(command, holidays):
    # Если команда - "перечислить", произнести названия праздников
    if command == "перечислить":
        names = [holiday["name"] for holiday in holidays]
        speak(" ".join(names))
    # Если команда - "сохранить", сохранить названия праздников в файл
    elif command == "сохранить":
        names = [holiday["name"] for holiday in holidays]
        with open("holiday_names.txt", "w") as file:
            file.write("\n".join(names))
        speak("Файл сохранен.")
    # Если команда - "даты", сохранить даты и названия праздников в файл
    elif command == "даты":
        with open("holiday_dates.txt", "w") as file:
            for holiday in holidays:
                date = holiday["date"]
                name = holiday["name"]
                file.write(f"{date}: {name}\n")
        speak("Файл сохранен.")

    # Если команда - "ближайший", найти и произнести ближайший праздник
    elif command == "ближайший":
        today = datetime.date.today()
        upcoming_holidays = [holiday for holiday in holidays if datetime.date.fromisoformat(holiday["date"]) >= today]
        upcoming_holidays.sort(key=lambda holiday: datetime.date.fromisoformat(holiday["date"]))
        if upcoming_holidays:
            next_holiday = upcoming_holidays[0]
            speak(f"Ближайший праздник - {next_holiday['name']}, {next_holiday['date']}")
        else:
            speak("Нет ближайших праздников.")
    # Если команда - "количество", произнести общее количество праздников
    elif command == "количество":
        speak(f"Всего праздников: {len(holidays)}")
    # Иначе - ошибка
    else:
        speak("Команда не распознана.")


def record_audio():
    CHUNK = 1024  # Количество фреймов для чтения за одну итерацию
    FORMAT = pyaudio.paInt16  # Формат аудио (16 бит, знаковое целое число)
    CHANNELS = 1  # Количество аудиоканалов (моно)
    RATE = 16000  # Частота дискретизации (16 кГц)
    RECORD_SECONDS = 5  # Продолжительность записи в секундах

    p = pyaudio.PyAudio()  # Создание объекта для работы с аудио

    stream = p.open(
        format=FORMAT,
        channels=CHANNELS,
        rate=RATE,
        input=True,
        frames_per_buffer=CHUNK
    )  # Открытие аудиострима для записи звука с микрофона

    frames = []  # Список для хранения фреймов аудио

    # Цикл записи аудио
    for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
        data = stream.read(CHUNK)  # Чтение фрейма аудио
        frames.append(data)  # Добавление фрейма в список фреймов

    stream.stop_stream()  # Остановка записи
    stream.close()  # Закрытие аудиострима
    p.terminate()  # Завершение работы объекта для работы с аудио

    audio_data = b''.join(frames)  # Конкатенация фреймов в одно аудио
    return audio_data  # Возвращение аудиоданных


def recognize_speech(audio_data):
    rec.AcceptWaveform(audio_data)  # Передача аудиоданных в распознаватель речи
    result = json.loads(rec.FinalResult())  # Получение результата распознавания в формате JSON
    text = result["text"]  # Извлечение текста из результата распознавания
    return text  # Возвращение распознанного текста


def main():
    holidays = get_holidays(2020, "GB")  # Получение данных о праздниках

    while True:
        audio_data = record_audio()  # Запись аудио с микрофона
        command = recognize_speech(audio_data)  # Распознавание речи
        print(command)
        if command:
            process_command(command, holidays)  # Обработка команд ассистента
        else:
            speak("Ошибка в распознавании речи.")


if __name__ == "__main__":
    main()
