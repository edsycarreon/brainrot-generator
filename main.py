import base64
import os
import re
import requests
import glob
import subprocess
import whisper

# Configuration
BASE_URL = "https://api16-normal-v6.tiktokv.com/media/api/text/speech/invoke"
DEFAULT_VOICE = "en_us_002"
SESSION_ID = "e245d3484f02b546e7b86a6fffb94dca"

def config(user_session_id, custom_base_url):
    global SESSION_ID, BASE_URL
    SESSION_ID = user_session_id
    if custom_base_url:
        BASE_URL = custom_base_url

def get_config():
    return {
        "BASE_URL": BASE_URL,
        "SESSION_ID": SESSION_ID
    }

def prepare_text(text):
    text = text.replace("+", "plus").replace(" ", "+").replace("&", "and")
    return text

def split_text(text, chunk_size=295):
    chunks = []
    while text:
        split_index = (text[:chunk_size].rfind('.') or text[:chunk_size].rfind(',') or text[:chunk_size].rfind(' ')) + 1
        if split_index == 0 or len(text) <= chunk_size:
            split_index = chunk_size
        chunks.append(text[:split_index])
        text = text[split_index:]
    return chunks

def delete_folder_contents(folder_path):
    if os.path.exists(folder_path):
        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                delete_folder_contents(file_path)
                os.rmdir(file_path)
    else:
        print("Directory not found: ", folder_path)

def get_mp3_files(directory_path):
    return sort_audio_files(glob.glob(os.path.join(directory_path, '*.mp3')))

def concatenate_audios(input_files, output_file):
    # Using ffmpeg command line tool, ensure it's installed
    command = ['ffmpeg', '-y', '-i']
    command += ['concat:' + '|'.join(input_files), '-acodec', 'copy', output_file]
    subprocess.run(command)
    
def sort_audio_files(file_list):
    def extract_number(file_name):
        # Extracting the number from the filename using a regular expression
        numbers = re.findall(r'\d+', file_name)
        return int(numbers[0]) if numbers else 0

    return sorted(file_list, key=extract_number)

def transcribe_audio(file_path):
    # Load the model (you can choose different models based on your requirement)
    model = whisper.load_model("base")

    # Transcribe the audio
    result = model.transcribe(file_path, word_timestamps=True)

    # Create subtitles
    subs = []
    for segment in result['segments']:
        for word in segment['words']:
            text = word['word']
            start = word['start']
            end = word['end']
            duration = end - start
            subs.append({"word": text, "start": start, "end": end, "duration": duration})
    
    print(subs)
    
    return result

def create_audio_from_text(texts, file_name="audio"):
    headers = {
        "User-Agent": "com.zhiliaoapp.musically/2022600030 (Linux; U; Android 7.1.2; es_ES; SM-G988N; Build/NRD90M;tt-ok/3.12.13.1)",
        "Cookie": f"sessionid={SESSION_ID}",
        "Accept-Encoding": "gzip,deflate,compress",
    }
    for i, text in enumerate(texts):
        req_text = prepare_text(text)
        url = f"{BASE_URL}/?text_speaker={DEFAULT_VOICE}&req_text={req_text}&speaker_map_type=0&aid=1233"
        response = requests.post(url, headers=headers)
        response_data = response.json()
        if response_data["status_code"] != 0:
            raise Exception(f"Error: {response_data['status_code']}")
        encoded_voice = response_data["data"]["v_str"]
        # Decode the base64 encoded string
        decoded_voice = base64.b64decode(encoded_voice)

        os.makedirs("audio", exist_ok=True)
        with open(f"audio/{file_name}_{i}.mp3", "wb") as f:
            f.write(decoded_voice)

# Example usage
def main():
    text = "Everything that you thought had meaning: every hope, dream, or moment of happiness. None of it matters as you lie bleeding out on the battlefield. None of it changes what a speeding rock does to a body, we all die. But does that mean our lives are meaningless? Does that mean that there was no point in our being born? Would you say that of our slain comrades? What about their lives? Were they meaningless?... They were not! Their memory serves as an example to us all! The courageous fallen! The anguished fallen! Their lives have meaning because we the living refuse to forget them! And as we ride to certain death, we trust our successors to do the same for us! Because my soldiers do not buckle or yield when faced with the cruelty of this world! My soldiers push forward! My soldiers scream out! My soldiers RAAAAAGE!"
    delete_folder_contents("audio")
    text_chunks = split_text(text)
    create_audio_from_text(text_chunks)
    mp3_files = get_mp3_files("audio")
    concatenate_audios(mp3_files, "output_audio.wav")
    transcription = transcribe_audio("output_audio.wav")
    # print(transcription)

if __name__ == "__main__":
    main()
