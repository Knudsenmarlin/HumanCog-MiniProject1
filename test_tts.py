# import pyttsx3
# import time

# engine = pyttsx3.init()

# for text in ["A", "car", "42"]:
#     print("speaking:", text)

#     engine.say(text)
#     engine.runAndWait()

#     print("finished:", text)

#     time.sleep(1)

import time
import win32com.client

voice = win32com.client.Dispatch("SAPI.SpVoice")

# Range is roughly -10 to +10
voice.Rate = 0

for text in ["A", "car", "42"]:
    print("speaking:", text)

    voice.Speak(text)

    print("finished:", text)

    time.sleep(1)