import datetime
import re
import gradio as gr
import os
import sys
import openpyxl
import json
import pandas as pd

# Find the path to the 'modules' directory relative to the current file
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)  # Move up to the 'extensions' directory
base_dir = os.path.dirname(parent_dir)  # Move up to the base 'text-generation-webui' directory
modules_path = os.path.join(base_dir, 'modules')

if modules_path not in sys.path:
    sys.path.append(modules_path)

# Load the spreadsheet data into a pandas DataFrame
df = pd.read_excel(f'{current_dir}/weight_change.xlsx', sheet_name='Sheet1')

from chat import generate_chat_prompt

# extension parameters
params = {
    "display_name": "Character Stats",
    "is_tab": False
}

# Initialize the extension state
charUI_stats = {
    "inject": False,
    "char_name": "Maddy",
    "starting_weight": 145,
    "char_weight": 230,
    "char_calories": 0,
    "char_height": 67,
    "char_birth_year": 1997,
    "char_birth_month": 5,
    "char_birth_day": 13,
    "start_year": 2014,
    "start_month": 6,
    "start_day": 2,
    "current_year": 2016,
    "current_month": 9,
    "current_day": 2,
    "stat_prompt": False
}

class CharacterStats:
    SHIRT_SIZES = ["Medium", "Large", "X-Large", "2XL", "3XL", "4XL", "5XL", "6XL", "7XL", "8XL", "9XL", "10XL",
                   "11XL", "12XL", "13XL", "14L", "15XL"]

    def __init__(self):
        self.age = 19
        self.name = "Maddy"
        self.weight = 230  # lbs
        self.start_weight = 145
        self.height_inches = 67  # 5'7"
        self.current_calories = 0
        self.max_calories = 2100
        self.fullness = "Starving"
        self.current_date = datetime.datetime(2016, 6, 15)
        self.start_date = datetime.datetime(2016, 6, 15)
        self.update_clothing_sizes()
        self.birthday = datetime.datetime(1997, 2, 23)
        self.inject_stats = False  # Default value for the inject_stats property

    def add_calories(self, calories):
        self.current_calories += calories


    def calculate_bmi(self):
        bmi_value = (self.weight / (self.height_inches ** 2)) * 703
        categories = ["Healthy", "Overweight", "Chubby", "Obese", "Super Obese", "Hyper Obese"]
        thresholds = [18.5, 25, 30, 35, 40, 50]
        for i, threshold in enumerate(thresholds):
            if bmi_value < threshold:
                return f"{bmi_value:.1f} ({categories[i]})"
        return f"{bmi_value:.1f} ({categories[-1]})"

    def bmi_int(self):
        bmi_value = (self.weight / (self.height_inches ** 2)) * 703
        return int(bmi_value)

    def calculate_bmr(self):
        return 655 + (4.35 * self.weight) + (4.7 * self.height_inches) - (4.7 * self.age)

    def calculate_fullness(self):
        # Calculate the percentage of max_calories consumed
        fullness_percentage = (self.current_calories / self.max_calories) * 100

        # Determine fullness category
        if fullness_percentage <= 20:
            return "Starving"
        elif fullness_percentage <= 40:
            return "Hungry"
        elif fullness_percentage <= 60:
            return "Content"
        elif fullness_percentage <= 80:
            return "Satiated"
        elif fullness_percentage <= 100:
            return "Stuffed"
        else:
            return "Overfed"

    def end_day(self):
        self.current_date += datetime.timedelta(days=1)
        excess_calories = self.current_calories - self.calculate_bmr()
        if excess_calories > 500:
            self.weight += int(excess_calories / 500)  # Add 1 lb for every excess of 500 calories
        if self.current_date.month == self.birthday.month and self.current_date.day == self.birthday.day:
            self.set_age()
        self.current_calories = 0
        self.update_clothing_sizes()
        self.max_calories = self.calculate_bmr()

    def formatted_date(self):
        return self.current_date.strftime("%B %d, %Y")  # Format: "Month day, Year"

    def update_clothing_sizes(self):
        self.weight_diff = self.weight - self.start_weight  # Initial weight

        # Update shirt size and fit
        shirt_index = max(0, min(len(self.SHIRT_SIZES) - 1, self.weight_diff // 30))
        self.shirt_size = self.SHIRT_SIZES[int(shirt_index)]
        if self.weight_diff % 20 <= 10:
            self.shirt_fit = "Relaxed Fit"
        elif self.weight_diff % 20 <= 15:
            self.shirt_fit = "Standard Fit"
        else:
            self.shirt_fit = "Tight Fit"

        # Update pant size and fit
        self.pant_size = 14 + (
                    max(0, self.weight_diff // 20) * 2)  # Start from size 14 and increment by 2 for every 15 lbs
        if self.weight_diff % 20 <= 5:
            self.pant_fit = "Relaxed Fit"
        elif self.weight_diff % 20 <= 10:
            self.pant_fit = "Standard Fit"
        else:
            self.pant_fit = "Tight Fit"

    def set_inject_stats(self, inject):
        self.inject_stats = inject

    def set_weight(self, new_weight):
        self.weight = new_weight
        self.update_clothing_sizes()
        self.max_calories = self.calculate_bmr()

    def set_age(self):
        age = self.current_date.year - self.birthday.year - (
                    (self.current_date.month, self.current_date.day) < (self.birthday.month, self.birthday.day))
        self.age = age
        self.max_calories = self.calculate_bmr()
        return age

    def set_calories(self, new_calories):
        self.current_calories = new_calories

    def set_date(self, new_date):
        self.current_date = datetime.datetime.strptime(new_date, '%Y-%m-%d')

    def override_stats(self, name, start_weight, weight, height_inches, current_calories, current_year, current_month, current_day, start_year, start_month, start_day, birthday_year, birthday_month, birthday_day):
        self.name = name
        self.start_weight = start_weight
        self.weight = weight
        self.height_inches = height_inches
        self.current_calories = current_calories
        self.current_date = datetime.datetime(current_year, current_month, current_day)
        self.start_date = datetime.datetime(start_year, start_month, start_day)
        self.birthday = datetime.datetime(birthday_year, birthday_month, birthday_day)
        self.age = self.set_age()
        self.update_clothing_sizes()
        self.max_calories = self.calculate_bmr()
        self.calculate_bmi()
        self.fullness = self.calculate_fullness()

character_stats = CharacterStats()

def override_stats(
        name, start_weight, weight, height_inches, current_calories,
        current_year, current_month, current_day,
        start_year, start_month, start_day,
        birthday_year, birthday_month, birthday_day
):
    # Convert string inputs to appropriate types
    current_year = int(current_year)
    current_month = int(current_month)
    current_day = int(current_day)
    start_year = int(start_year)
    start_month = int(start_month)
    start_day = int(start_day)
    birthday_year = int(birthday_year)
    birthday_month = int(birthday_month)
    birthday_day = int(birthday_day)

    # Call the CharacterStats method to override stats
    character_stats.override_stats(
        name, start_weight, weight, height_inches, current_calories,
        current_year, current_month, current_day,
        start_year, start_month, start_day,
        birthday_year, birthday_month, birthday_day
    )
    return "Stats successfully updated!"

def inches_to_feet_and_inches(inches):
    feet = inches // 12
    remaining_inches = inches % 12
    return int(feet), int(remaining_inches)

def remove_bracketed_text(text):
    return re.sub(r'\[.*?\]', '', text)


def input_modifier(string, state, is_chat=False):
    if is_chat:
        if "==END_DAY==" in string:
            character_stats.end_day()
            string = re.sub(r"==END_DAY==", "", string).strip()

        if "==RESET==" in string:
            character_stats.reset_stats()
            string = re.sub(r"==RESET==", "", string).strip()

        food_matches = re.findall(r"\{([^}]+):(\d+)\}", string)
        for match in food_matches:
            _, cal = match
            character_stats.add_calories(int(cal))
            match_str = "{" + match[0] + ":" + str(cal) + "}"
            string = re.sub(re.escape(match_str), "", string).strip()

    return string

def stat_prompt():

    feet, inches = inches_to_feet_and_inches(character_stats.height_inches)
    stats_context = (
        f"""
        [{character_stats.name}'s Stats]
        [Date: {character_stats.formatted_date()}]
        [Age: {character_stats.age} years old]
        [Height: {feet}'{inches} inches tall]
        [Weight: {character_stats.weight} lbs]
        [BMI: {character_stats.calculate_bmi()}] 
        [Weight Gained: {int(character_stats.weight_diff)} lbs since {character_stats.start_date.strftime('%B %d, %Y')}]
        [Calories Consumed: {character_stats.current_calories} / {character_stats.max_calories} cal.]
        [Fullness: {character_stats.calculate_fullness()}]
        """
    )
    return stats_context

def history_modifier(history):

    # Convert the history to a string
    history_str = json.dumps(history)

    # Find the start and end positions of the "Maddy's Stats" block
    start_pos = history_str.find("\n        [Maddy's Stats]\n")
    end_pos = history_str.find("\n        \n", start_pos)

    if start_pos != -1 and end_pos != -1:
        # Remove the "Maddy's Stats" block
        history_str = history_str[:start_pos] + history_str[end_pos + 10:]

    # Find the start and end positions of the "Physical Appearance:" part
    start_pos = history_str.find("[Physical Appearance:")
    end_pos = history_str.find("]", start_pos)

    if start_pos != -1 and end_pos != -1:
        # Remove the "Physical Appearance:" part
        history_str = history_str[:start_pos] + history_str[end_pos + 1:]

    # Parse the modified history string back to its original structure
    history = json.loads(history_str)

    print(f'\n\n\nHere is what is in the history:\n\n\n{history}\n\n\n\nEnd of test')

    return history


def output_modifier(string, state, is_chat=False):
    food_matches = re.findall(r"\{([^}]+)\s*:\s*(\d+)\}", string)

    for food_item, calories in food_matches:
        character_stats.add_calories(int(calories))
        fullness_status = character_stats.calculate_fullness()

        string = f"""\n*[{character_stats.name} just ate {food_item}*\n*After eating this, {character_stats.name} is feeling {fullness_status}.*]
        [So far she has consumed {int(character_stats.current_calories)} out of {character_stats.max_calories} calories today]
        \n{string}"""

    return string


def chat_input_modifier(text, visible_text, state):
    is_new_chat = len(state['history']['internal']) == 1
    end_day_called = "==END_DAY==" in text
    food_matches = re.findall(r"\{([^}]+):(\d+)\}", text)
    is_story = "STORY:" in text

    # Process end day command
    end_day_message = []
    if end_day_called:
        character_stats.end_day()
        if character_stats.current_date.month == 4 and character_stats.current_date.day == 16:
            end_day_message.append(
                f"\n*It's the start of a new day... And it's {character_stats.name}'s birthday! You are now {character_stats.age}!*\n")
        else:
            end_day_message.append("\n*It's the start of a new day!*\n")
        visible_text = text.replace("==END_DAY==", "").strip()
        text = text.replace("==END_DAY==", "").strip()

    food_messages = []

    for food_item, calories in food_matches:
        character_stats.add_calories(int(calories))
        fullness_status = character_stats.calculate_fullness()
        food_messages.append(
            f"\n*[{character_stats.name} just ate {food_item}*\n*After eating this, {character_stats.name} is feeling {fullness_status}.*]")

    # Create stats context
    new_stats_context = stat_prompt()

    # Append food and end day messages to the new stats context
    if end_day_message:
        new_stats_context += "\n".join(end_day_message)

    if food_messages:
        new_stats_context += "\n".join(food_messages)

    bmi = character_stats.bmi_int()

    # Initialize physical_attributes with a default value
    physical_attributes = ""

    # Look up the row corresponding to the calculated BMI
    row = df.loc[df['BMI'] == int(bmi)]

    if not row.empty:
        # Extract the relevant data from the row
        data = row['Phys'].values[0]

        # Replace {character_stats.name} with the actual value
        physical = data.format(character_stats=character_stats)

        # Assign the data to physical_attributes
        physical_attributes = f"\n[Physical Appearance: {physical}]"

    # Check for story and modify text accordingly
    if is_new_chat or end_day_called or character_stats.inject_stats:
        modified_visible_text = f"{new_stats_context}\n{visible_text}"
    elif food_matches:
        modified_visible_text = f"{new_stats_context}\n{visible_text}"
    else:
        modified_visible_text = visible_text

    # Find the index of the last occurrence of square bracket content in text
    last_bracket_index = text.rfind('[')

    if last_bracket_index != -1:
        # Split the text into previous_text and current_prompt
        previous_text = text[:last_bracket_index]
        current_prompt = text[last_bracket_index:]

        # Remove square bracket content from the previous_text
        previous_text = re.sub(r'\[[^\]]*\]', '', previous_text)

        # Combine the previous_text, current_prompt, new_stats_context, and physical_attributes
        text = f"{new_stats_context}\n{physical_attributes}\n{previous_text}\n{current_prompt}"
    else:
        # If no square bracket content is found, append the new_stats_context and physical_attributes to the existing text
        text = f"{new_stats_context}\n{physical_attributes}\n{text}"

    visible_text = modified_visible_text

    print(f'\n\n\nHere is what the AI Sees:\n\n\n{text}\n\n\n\nEnd of test')
    print(f'\n\n\nHere is what you see:\n\n\n{visible_text}\n\n\n\nEnd of test')

    return text, visible_text

def ui():
    with gr.Blocks() as demo:
        with gr.Accordion(label="Character Stats", open=True):
            gr.Markdown(
                """Set these values to the desired settings 
                and press \'Commit Stat Change\' to update the stat prompt."""
            )

            inject_stats = gr.Checkbox(
                label="Inject Stats Into Prompt",
                value=charUI_stats['stat_prompt']
            )
            def set_inject_stats(inject):
                character_stats.set_inject_stats(inject)

            char_name = gr.Textbox(
                label="Character Name",
                value=charUI_stats['char_name'],
                placeholder="Enter your character's name here..."
            )
            starting_weight = gr.Number(
                label="Character Starting Weight",
                value=charUI_stats['char_weight']
            )
            char_weight = gr.Number(
                label="Character Current Weight",
                value=charUI_stats['char_weight']
            )
            char_calories = gr.Number(
                label="Calories Consumed",
                value=charUI_stats['char_calories']
            )
            char_height = gr.Number(
                label="Character Height",
                value=charUI_stats['char_height']
            )
            with gr.Row():
                starting_day = gr.Number(
                    label="Weight Gain Starting Day",
                    value=charUI_stats['start_day']
                )
                starting_month = gr.Number(
                    label="Weight Gain Starting Month",
                    value=charUI_stats['start_month']
                )
                starting_year = gr.Number(
                    label="Weight Gain Starting Year",
                    value=charUI_stats['start_year']
                )
            with gr.Row():
                current_day = gr.Number(
                    label="Current Day",
                    value=charUI_stats['current_day']
                )
                current_month = gr.Number(
                    label="Current Month",
                    value=charUI_stats['current_month']
                )
                current_year = gr.Number(
                    label="Current Year",
                    value=charUI_stats['current_year']
                )
            with gr.Row():
                char_birth_day = gr.Number(
                    label="Birth Day",
                    value=charUI_stats['char_birth_day']
                )
                char_birth_month = gr.Number(
                    label="Birth Month",
                    value=charUI_stats['char_birth_month']
                )
                char_birth_year = gr.Number(
                    label="Birth Year",
                    value=charUI_stats['char_birth_year']
                )
            # Button to override stats
            override_button = gr.Button("Commit Stat Change")

        # Function to handle the button click
        override_button.click(
            fn=override_stats,
            inputs=[
                char_name, starting_weight, char_weight, char_height, char_calories,
                current_year, current_month, current_day, starting_year, starting_month,
                starting_day, char_birth_year, char_birth_month, char_birth_day
            ],
            outputs=[]
        )

        inject_stats.change(
            set_inject_stats,
            inputs=[inject_stats],
            outputs=[]
        )

    return demo
# Launch the Gradio UI
if __name__ == "__main__":
    ui = ui()
    ui.launch()
