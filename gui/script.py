# import sys

# print("Python script started")
# sys.stdout.flush()  # Ensure Java gets output immediately

# while True:
#     user_input = input()
#     if user_input.lower() == "exit":
#         print("Python script exiting...")
#         sys.stdout.flush()
#         break
#     print(f"Python received: {user_input}")
#     sys.stdout.flush()


import speech_recognition as sr

def listen_for_input():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening for your input...")
        recognizer.adjust_for_ambient_noise(source, duration=1)
        audio = recognizer.listen(source, timeout=10)
    
    try:
        user_input = recognizer.recognize_google(audio, language="en-US")
        print(f"You said: {user_input}")
        return user_input
    except sr.UnknownValueError:
        print("Sorry, I could not understand the audio.")
        return "I couldn't hear you clearly. Could you please repeat that?"
    except sr.RequestError as e:
        print(f"There was an issue with the speech recognition service: {e}")
        return "I'm having trouble with my hearing. Let's try again."
    except Exception as e:
        print(f"Error in speech recognition: {str(e)}")
        return "There was a problem with the speech recognition. Let's try again."

# Test the function
listen_for_input()