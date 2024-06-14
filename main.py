from openai import OpenAI
import os
from dotenv import load_dotenv
import re
import json
import base64
import requests
from io import BytesIO
from PIL import Image  
import moviepy





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

class StoryEvent:
    def __init__(self, num, text, option_1, option_1_text, option_2, option_2_text):
        self.num = num,
        self.text = text, 
        self.option_1 = option_1,
        self.option_2 = option_2,
        self.option_1_text = option_1_text,
        self.option_2_text = option_2_text,

class Story:
    def __init__(self, story_events):
        self.events = story_events

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

def generate_audio(event):
    complete_prompt = (event.text[0]+ " Will you A: " + event.option_1_text[0] + ", or B: " + event.option_2_text[0] + ". Swipe left and see where your decision leads.")
    print("audio script: " + complete_prompt)
    
    audio = openai.audio.speech.create(
        model="tts-1",
        voice="fable",
        input=complete_prompt
    )

    audio.write_to_file(f"audio_files/af_{event.num[0]}.mp3")

def generate_video(story):


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
    print(story.events[2].text[0])

    # GENERATE IMAGES FROM STORY TEXTS
    # for event in story:
    #     pic = generate_image(event.text)

    #     for i, image in enumerate(pic):
    #         with open(f'story_pics/story_pic_{i}.png', 'wb') as file:
    #             file.write(image['image'])

    #image = generate_image(story.events[2].text[0], num=story.events[2].num[0])

    
    # GENERATE AUDIO FROM TEXT
    # generate_audio(story.events[2])

    # PUT IT ALL TOGETHER INTO ONE VIDEO
    generate_video(story)

