"""
ChatBot class file
"""

import os
import re
from pathlib import Path

import backoff
import openai
from openai.error import RateLimitError, ServiceUnavailableError

from wastenot import Store
from wastenot.messaging import MessagingBot
from wastenot.models import Address


class ChatBot:
    """
    ChatBot
    """

    openai.api_key = os.getenv("OPENAI_API_KEY")
    start_sequence = "\nQ:"
    restart_sequence = "\nA: "
    success_string = "all the information I need"
    chats = []

    store = Store()

    def __init__(self):
        self.chats = []
        self.chats.append(
            "Hi, if you'd like to save the planet bite-by-bite, "
            "please let me know details about the food you'd like to donate!"
        )

        with open(Path(__file__).parent.joinpath("prompt.txt"), "r") as file:
            self.base_prompt = file.read()

    def build_prompt(self) -> str:
        """
        Build the prompt for the OpenAI API
        :return: Prompt string
        """

        formatted_strings = []
        for i, string in enumerate(self.chats):
            if i % 2 == 0:
                formatted_strings.append(self.start_sequence + string)
            else:
                formatted_strings.append(self.restart_sequence + string)

        return self.base_prompt + ("\n".join(formatted_strings)) + self.start_sequence

    @backoff.on_exception(backoff.expo, (RateLimitError, ServiceUnavailableError))
    def get_response(self, query: str) -> str:
        """
        Get the response from the OpenAI API
        :param query: Query string
        :return: Response string
        """

        self.chats.append(query)
        response = openai.Completion.create(
            model="text-davinci-003",
            prompt=self.build_prompt(),
            temperature=0.7,
            max_tokens=461,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
            stop=["A:"],
        )
        response = response.choices[0].text.strip()
        complete, error_list = self.check_if_completed(response)

        if complete:
            self.chats = []
            response = (
                "Thank you for your donation! we'll let you know when we're ready to pick it up! "
                "Is there anything else you'd like to donate today?"
            )
        if "information I need" in response and len(error_list) > 1:
            response = "Please confirm the following attributes for me: " + ", ".join(
                error_list
            )
        self.chats.append(response)
        return response

    def check_if_completed(self, response) -> (bool, list):
        """
        Check if the response contains the success string
        :param response: Response string
        :return: True if the conversation is complete
        """
        error_vals = []

        if self.success_string in response:
            pattern = r"([A-Za-z ]+): ([A-Za-z0-9# ]+)"
            matches = re.findall(pattern, response)
            variables = {}
            for match in matches:
                variables[match[0]] = match[1]

            type_of_food = variables.get("Type of food", "N/A")
            weight = variables.get("Weight", "N/A")
            street = variables.get("Street Address", "N/A")
            apt = variables.get("Apartment", "N/A")
            city = variables.get("City", "N/A")
            state = variables.get("State", "N/A")
            zip_code = variables.get("Zip", "N/A")
            phone = variables.get("Phone Number", "N/A")

            na_count = sum(
                value == "N/A" or value == "" or value == "NaN"
                for value in [
                    type_of_food,
                    weight,
                    street,
                    city,
                    state,
                    zip_code,
                    phone,
                ]
            )

            for key, value in [
                ("Type of Food", type_of_food),
                ("Weight", weight),
                ("Street 1", street),
                ("City", city),
                ("State", state),
                ("Zip", zip_code),
                ("Phone", phone),
            ]:
                if value == "N/A" or value == "" or value == "NaN":
                    error_vals.append(key)
            if na_count < 1:
                self.add_pickup_location(
                    type_of_food, weight, street, apt, city, state, zip_code, phone
                )
                return True, None
        return False, error_vals

    @staticmethod
    def add_pickup_location(
        type_of_food: str,
        weight: str,
        street1: str,
        street2: str,
        city: str,
        state: str,
        zip_code: str,
        phone: str,
    ):
        """
        Add a pickup location to the database
        :param type_of_food: Food type
        :param weight: Weight of food
        :param street1: Street address 1
        :param street2: Street address 2
        :param city: City
        :param state: State
        :param zip_code: Zip code (int parseable)
        :param phone: Phone number
        :return: None
        """

        try:
            weight = float(weight)
        except Exception as e:
            print(e)
            weight = 0

        ChatBot.store.add_pickup_location(
            phone, Address(street1, street2, city, state, zip_code), weight
        )

        MessagingBot().send_message(
            f"Thank you for your donation and saving {weight} pounds of food! "
            f"We will be in touch with you shortly to schedule a pickup.",
            phone,
        )

        print("Type of Food:", type_of_food)
        print("Weight:", weight)
        print("Street 1:", street1)
        print("Street 2:", street2)
        print("City:", city)
        print("State:", state)
        print("Zip:", zip_code)
        print("Phone:", phone)


if __name__ == "__main__":
    __bot = ChatBot()
    __query = "hi"
    while __query != "":
        __query = input("A: ")
        if __query != "":
            print(__bot.get_response(__query))
