from openai import OpenAI
import os
from dotenv import load_dotenv
import re
import json
import base64
import requests
from io import BytesIO
from PIL import Image  
import subprocess
from mutagen.mp3 import MP3
from moviepy.editor import *


temp_response = """
        1. ["1", "You wake up in an unfamiliar, dimly lit room. There's a door and a window.", "2", "Take a look out the window", "3", "Open the door"]
        2. ["2", "Outside the window, you see a narrow ledge leading to another window.", "4", "Climb out the window and shimmy towards the other window", "1", "Decide against the risky action and turn back"]
        3. ["3", "The door creaks open to a dark corridor, on your left side is a staircase going up.", "5", "Explore the dark corridor", "6", "Climb the staircase"]
        4. ["4", "The ledge is slippery and a fall would be lethal. You see a fire escape ladder.", "7", "Climb the ladder", "2", "Climb back inside through the window"]
        5. ["5", "As you move further into the corridor, it splits into two paths.", "8", "Take the left path", "9", "Take the right path"]
        6. ["6", "The staircase leads to a lush rooftop, with a helicopter in landing pad.", "10", "Investigate the helicopter", "11", "Search the rooftop"]
        7. ["7", "The ladder leads down to a narrow alley where you see a motorbike.", "12", "Take the motorbike", "1", "Decide it's too risky and climb back up"]
        8. ["8", "The left path leads to a room filled with people who seem to be in a meeting. They look dangerous.", "13", "Introduce yourself to the people", "14", "Sneak out without being seen"]
        9. ["9", "The right path leads to a room with a large map of the city. There's a marked location.", "15", "Examine the map", "5", "Go back to the junction"]
        10. ["10", "The helicopter seems ready to fly, but it certainly require skills.", "16", "Attempt to fly the helicopter", "6", "Going back to searching the rooftop"]
        11. ["11", "You find a trap door that leads to a hidden passage.", "17", "Descend the passage", "6", "Return to the rooftop"]
        12. ["12", "You zoom away on the motorbike, but soon there's a chasing van behind you.", "18", "Speed up and try to lose the van", "19", "Find a place to abandon the motorbike and hide"]
        13. ["13", "The people are startled. They pull out their weapons.", "20", "Attempt to negotiate with them", "21", "Try to fight them off"]
        14. ["14", "You successfully sneak out, finding a hidden exit leads to the outside.", "22", "Take the exit to outside", "8", "Go back to the room"]
        15. ["15", "The map reveals the location of a secret safehouse.", "23", "Head to the safehouse", "9", "Leave the room and go back to the corridor"]
        16. ["16", "You successfully lift off. The city is beneath you.", "24", "Fly towards the marked location on map", "25", "Land the helicopter back on the rooftop"]
        17. ["17", "The hidden passage leads to the control room. Alert lights are flashing.", "24", "Examine the control panel", "11", "Go back to the rooftop"]
        18. ["18", "You swerve through the city's traffic, but the van continues to chase.", "12", "Keep trying to lose the van", "19", "Find a safe place and make a run for it"]
        19. ["19", "You ditch the motorbike down an alley and hide in a trash bin.", "7", "Go back, when the coast is clear retry your escape", "1", "Wait until morning in the trash bin"]
        20. ["20", "You try to reason with them but they seems skeptical.", "8", "Try to escape the room", "21", "Start a fight"]
        21. ["21", "You throw the first punch, but they unfortunately outnumber you.", "13", "Attempt to negotiate again", "1", "Get captured and wake up in the starting room"]
        22. ["22", "You step outside, and you're in the business district of the city.", "12", "Try stealing a vehicle to escape", "1", "Get captured and wake up in the starting room"]
        23. ["23", "The safehouse is equipped with maps, cash, and a new identity.", "24", "Start a new life with the new identity", "15", "Go back and continue exploring"]
        24. ["24", "You have escaped with a new identity / flying towards a new life / control the whole operation.", "25", "The adventure ends, you made it", "1", "But an unexpected event sends you back to beginning"]
        25. ["25", "Congratulations, you've managed to finally safely escape. The End.", "-", "-", "-", "-"]
    """



load_dotenv() 

# OPEN AI RELATED FUNCTIONS
openai = OpenAI(
    api_key = os.environ.get("OPENAI_API_KEY")
)

# give chat gpt a promt and get a response back
# used to prompt for story and recieves the actual story beats
def ask_chat_gpt(querry: str):
    message = {
        "role": "user",
        "content": querry
    }

    response = openai.chat.completions.create(
        messages= [message],
        model = "gpt-4"
    )

    return response.choices[0].message.content

# WRITTEN STORY FUNCTIONS

# one page of the choose your own adventure story
class StoryEvent:
    def __init__(self, num, text, option_1, option_1_text, option_2, option_2_text):
        self.num = num
        self.text = text 
        self.option_1 = option_1
        self.option_2 = option_2
        self.option_1_text = option_1_text
        self.option_2_text = option_2_text

# the entre story comprised of all the story events
class Story:
    def __init__(self, story_events):
        self.events = story_events

# parse the actual gpt response into story events and create the overall story
def parse_gpt_response(response):
    pattern = r'(\d+)\.\s*\["(\d+)",\s*"([^"]+)",\s*"(\d+)",\s*"([^"]+)",\s*"(\d+)",\s*"([^"]+)"\]'
    
    # Find all matches in the input string
    matches = re.findall(pattern, response)
    
    # Parse the matches into a list of dictionaries
    parsed_data = []
    for match in matches:
        parsed_data.append({
            '_': int(match[0]),
            'n1': int(match[1]),
            't1': match[2],
            'n2': int(match[3]),
            't2': match[4],
            'n3': int(match[5]),
            't3': match[6],
        })
    
    events = []
    for x in parsed_data:
        events.append(StoryEvent(x["n1"], x["t1"], x["n2"], x["t2"], x["n3"], x["t3"]))

    story = Story(events)

    return story

# prompt gpt with the text of the story event to recieve the image for the video
def generate_image(prompt, num):
    n = 1
    size = "1024x1024"
    images_response = openai.images.generate(
        prompt=prompt,
        n=n,
        size=size,
        response_format="b64_json"
    )

    image_url_list = []
    image_data_list = []
    img_filename = "sp"
    for image in images_response.data:
        image_url_list.append(image.model_dump()["url"])
        image_data_list.append(image.model_dump()["b64_json"])

    # Initialize an empty list to store the Image objects
    image_objects = []

    # Check whether lists contain urls that must be downloaded or b64_json images
    if image_url_list and all(image_url_list):
        # Download images from the urls
        for i, url in enumerate(image_url_list):
            while True:
                try:
                    print(f"getting URL: {url}")
                    response = requests.get(url)
                    response.raise_for_status()  # Raises stored HTTPError, if one occurred.
                except requests.HTTPError as e:
                    print(f"Failed to download image from {url}. Error: {e.response.status_code}")
                    retry = input("Retry? (y/n): ")  # ask script user if image url is bad
                    if retry.lower() in ["n", "no"]:  # could wait a bit if not ready
                        raise
                    else:
                        continue
                break
            image_objects.append(Image.open(BytesIO(response.content)))  # Append the Image object to the list
            image_objects[i].save(f"story_pics/sp_{num}.png")
            print(f"{img_filename}_{i}.png was saved")
    elif image_data_list and all(image_data_list):  # if there is b64 data
        # Convert "b64_json" data to png file
        for i, data in enumerate(image_data_list):
            image_objects.append(Image.open(BytesIO(base64.b64decode(data))))  # Append the Image object to the list
            image_objects[i].save(f"story_pics/sp_{num}.png")
            print(f"story_pics/sp_{num}.png was saved")
    else:
        print("No image data was obtained. Maybe bad code?")

# generate the audio file from the text and options from the story event
def generate_audio(event):
    complete = event.text + " Will you A:" + event.option_1_text + ". Or B: " + event.option_2_text + ". Swipe left and see where your decision leads."
    initial = event.text
    option_a = "Will you A: " + event.option_1_text
    option_b = "Or B, " + event.option_2_text
    ender = "Swipe left and see where your decision leads."
    
    audio = openai.audio.speech.create(
        model="tts-1",
        voice="fable",
        input=initial
    )
    audio.write_to_file(f"audio_files/af_initial_{event.num}.mp3")

    audio = openai.audio.speech.create(
        model="tts-1",
        voice="fable",
        input=option_a
    )
    audio.write_to_file(f"audio_files/af_option_a_{event.num}.mp3")

    audio = openai.audio.speech.create(
        model="tts-1",
        voice="fable",
        input=option_b
    )
    audio.write_to_file(f"audio_files/af_option_b_{event.num}.mp3")

    audio = openai.audio.speech.create(
        model="tts-1",
        voice="fable",
        input=ender
    )
    audio.write_to_file(f"audio_files/af_ender_{event.num}.mp3")

# generate the subtitles and video number in the top left
def generate_subtitles(story):
    subtitle_lines = [
        ('00:00:00,000', '00:00:04,000', 'This is the first line of the speech.'),
        ('00:00:04,000', '00:00:08,000', 'This is the second line of the speech.')
    ]

    output_path = f"subtitles/st_{story.events[2].num}.srt"
    with open(output_path, 'w') as f:
        for index, (start_time, end_time, text) in enumerate(subtitle_lines, start=1):
            f.write(f"{index}\n")
            f.write(f"{start_time} --> {end_time}\n")
            f.write(f"{text}\n\n")

# generate the video using the image, audio, and subtitle files
def generate_video(event):
    e = event
    n = e.num

    image_path = f"story_pics/sp_{n}.png"
    image = Image.open(image_path)

    audio_files = [f"audio_files/af_initial_{n}.mp3", f"audio_files/af_option_a_{n}.mp3", f"audio_files/af_option_b_{n}.mp3", f"audio_files/af_ender_{n}.mp3"]
    subtitles = [e.text, 
                 f"{e.option_1_text} (go to {e.option_1})", 
                 f"{e.option_1_text} (go to {e.option_1}), \n{e.option_2_text} (go to {e.option_2})", 
                 f"{e.option_1_text} (go to {e.option_1}), \n{e.option_2_text} (go to {e.option_2})" 
                ]

    # Create a video from the image
    image_clip = ImageClip(image_path)

    # Calculate the total duration of the audio files combined
    total_duration = sum(AudioFileClip(audio).duration for audio in audio_files)

    video_height = 1920
    video_width = int(video_height * 9 / 16)
    image = image.resize((video_width, video_height), Image.LANCZOS)
    image.save('resized_image.png')
    image_path = 'resized_image.png'
    image_clip = ImageClip(image_path)


    # Set the duration of the image clip to match the total duration of the audio
    image_clip = image_clip.set_duration(total_duration)

    # Concatenate the audio files
    audio_clips = [AudioFileClip(audio) for audio in audio_files]
    concatenated_audio = concatenate_audioclips(audio_clips)

    # Set the audio of the image clip to the concatenated audio
    video_clip = image_clip.set_audio(concatenated_audio)

    video_width = video_clip.w

    # Generate subtitles and add them to the video
    subtitle_clips = []
    current_time = 0

    for i, (audio, subtitle) in enumerate(zip(audio_clips, subtitles)):
        duration = audio.duration
        subtitle_clip = (TextClip(
            subtitle, 
            fontsize=48, 
            font='Verdana-Bold',
            color='coral', 
            bg_color='transparent', 
            method='caption',
            align='south',
            size=(video_width, None)
        ).set_position(('bottom')).set_start(current_time).set_duration(duration))
        subtitle_clips.append(subtitle_clip)
        current_time += duration

    top_left_text_clip = (TextClip(
        f"{n}", 
        fontsize=78, 
        font='Verdana-Bold',
        color='coral', 
        bg_color='transparent', 
        method='caption',
    ).set_position(('left', 'top'))
    .set_duration(total_duration))


    # Combine the video and subtitle clips
    final_clip = CompositeVideoClip([video_clip, top_left_text_clip] + subtitle_clips)

    # Save the final video
    output_path = f'story_vids/s{n}.mp4'
    final_clip.write_videofile(output_path, fps=24, codec='libx264')



# MAIN
if __name__ == "__main__":
    # gpt_prompt = """give me numbered parts of a choose-your-own-adventure 
    #     story where you start at 1 and different events that happen 
    #     take you to different numbers with their own events (maximum 25 events). 
        
    #     give me your response in the form:

    #     [number of story part, part of story, option1_number, what happens if you pick option1 number, option2_number, what happens if you pick option2 number]
    #     """
    # gpt_response = ask_chat_gpt(gpt_prompt)
    # print(gpt_response)
    

    story = parse_gpt_response(temp_response)
    print(story.events[2].text)

    # GENERATE IMAGES FROM STORY TEXTS
    # for event in story:
    #     pic = generate_image(event.text)

    #     for i, image in enumerate(pic):
    #         with open(f'story_pics/story_pic_{i}.png', 'wb') as file:
    #             file.write(image['image'])

    #image = generate_image(story.events[2].text[0], num=story.events[2].num[0])

    
    # GENERATE AUDIO FROM TEXT
    #generate_audio(story.events[2])

    # PUT IT ALL TOGETHER INTO ONE VIDEO
    generate_video(story.events[2])

    # print(TextClip.list('font'))
    # print(TextClip.list('color'))
