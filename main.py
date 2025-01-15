# Libraries
import hashlib
import json
import requests
import time
import traceback
import csv
from datetime import datetime
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter, Retry


# Constants (changing these will break the code)
INT_WAIT_TIME = 3
MEMBERS_CSV = "./input/members.csv"  # Can also be a remote location, e.g. https://example.com/members.csv
GIFT_CODES_CSV = "./input/gift_codes.csv"  # Can also be a remote location, e.g. https://example.com/gift_codes.csv
WOS_CORS = "https://wos-giftcode.centurygame.com"
API_WOS = "https://wos-giftcode-api.centurygame.com"
API_WOS_PLAYER = API_WOS + "/api/player"
API_WOS_GIFT = API_WOS + "/api/gift_code"
API_WOS_SECRET = "tB87#kPtkxqOS2"
HEADER_ACCEPT = "application/json, text/plain, */*"
HEADER_CONTENT_TYPE = "application/x-www-form-urlencoded"
HEADER_SEC = '"Chromium";v="128", "Not;A=Brand";v="24", "Google Chrome";v="128"'
HEADER_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
REQUESTS_RETRY_CONFIG = Retry(
    total=5,
    backoff_factor=1,
    status_forcelist=[429],
    allowed_methods=["POST"]
)

# Dictionary to dynamically add online sources to gather new gift codes from using any website using a CSS based search query
# key = website, value = search term (HTML tag attributes)
web_wos_rewards_online_sources = {
    "https://www.wosrewards.com": "font-bold mb-2 text-gray-900 dark:text-gray-100"
}


def exit_on_error(str_error):
    """Simple function to print a predefined text and exit the program prematurely.
    :param str_error: String containing error message
    :return: None
    """

    print("An unexpected error occurred: {}".format(str_error))
    print("Please contact the maintainer of this program. The program will now exit.")
    traceback.print_exc()
    exit()


def load_file_as_dict(str_filename: str):
    """Function to load data from a file or a remote URL.
    :param str_filename: String containing path to a CSV file (either local or remote)
    :return: Dictionary containing data
    """

    try:
        if str_filename.startswith("http"):
            response = requests.get(str_filename)
            response.raise_for_status()
            lines = response.text.splitlines()
            reader = csv.DictReader(lines)
            return [row for row in reader]
        else:
            # Open str_filename in "read-only" mode
            with open(str_filename) as file:
                # List Comprehension to iterate over each line and then split each line into words, return as List
                reader = csv.DictReader(file)
                return [row for row in reader]
    except Exception as error_message:
        exit_on_error(error_message)


def encode_data(data: dict):
    """Function to prepare and sign data for an API request to WOS.
    :param data: Dictionary containing fid, time, cdk keys for WOS
    :return: Dictionary that includes the signature and the original data
    """

    try:
        # Sorts the keys of the input dictionary data
        sorted_keys = sorted(data.keys())

        # The list comprehension inside "&".join(...) iterates over the sorted keys and constructs a string of key-value pairs
        # If a value is a dictionary, it is converted to a JSON string using json.dumps
        encoded_data = "&".join(
            [
                f"{key}={json.dumps(data[key]) if isinstance(data[key], dict) else data[key]}"
                for key in sorted_keys
            ]
        )

        # Concatenates the encoded data string with the secret key, encodes it, and generates an MD5 hash of the result and return dictionary
        sign = hashlib.md5(f"{encoded_data}{API_WOS_SECRET}".encode()).hexdigest()
        return {"sign": sign, **data}
    except Exception as error_message:
        exit_on_error(error_message)


def get_player_info(player_id: str):
    """Function to set up a session, prepare the necessary headers and get the specified player's information.
    :param player_id: String containing player ID
    :return: HTTP session and player information
    """

    try:
        # Create a new session to persist certain parameters across requests
        session = requests.Session()

        # Configure the session to retry requests in case of certain failures
        session.mount("https://", HTTPAdapter(max_retries=REQUESTS_RETRY_CONFIG))

        # Define the headers to be used in the request
        headers = {
            "accept": HEADER_ACCEPT,
            "accept-language": "en-US,en;q=0.9,nb-NO;q=0.8,nb;q=0.7",
            "content-type": HEADER_CONTENT_TYPE,
            "dnt": "1",
            "origin": WOS_CORS,
            "priority": "u=1, i",
            "referer": WOS_CORS,
            "sec-ch-ua": HEADER_SEC,
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "Windows",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
            "user-agent": HEADER_USER_AGENT,
        }

        # Prepare the data to be encoded and sent in the request
        data_to_encode = {
            "fid": f"{player_id}",
            "time": f"{int(time.time() * 1000)}"
        }

        # Encode data
        data = encode_data(data_to_encode)

        # Send a POST request to the API endpoint with the prepared headers and data
        player_info = session.post(
            API_WOS_PLAYER,
            headers=headers,
            data=data,
        )

        return session, player_info
    except Exception as error_message:
        exit_on_error(error_message)


def claim_gift_code(player_id: str, gift_code: str):
    """Function to redeem a gift code for a specified player.
    :param player_id: String containing player ID
    :param gift_code: String containing gift code
    :return: String containing status message
    """

    try:
        # Get player information using the player ID
        session, response_stove_info = get_player_info(player_id=player_id)

        # Check if the response indicates success
        if response_stove_info.json().get("msg") == "success":
            # Prepare the data to be encoded and sent in the request
            data_to_encode = {
                "fid": f"{player_id}",
                "cdk": f"{gift_code}",
                "time": f"{int(datetime.now().timestamp())}",
            }
            data = encode_data(data_to_encode)

            # Send a POST request to redeem the gift code
            response_gift_code = session.post(
                url=API_WOS_GIFT,
                data=data,
            )

            time.sleep(INT_WAIT_TIME)

            # Parse the response JSON
            response_json = response_gift_code.json()
            print(f"Code '{gift_code}' for '{response_stove_info.json()['data']['nickname']}' (ID: {player_id}): {response_json}")

            # Check the response message and return the appropriate status
            if response_json.get("msg") == "SUCCESS":
                return "SUCCESS"
            elif response_json.get("msg") == "RECEIVED." and response_json.get("err_code") == 40008:
                return "ALREADY_RECEIVED"
            elif response_json.get("msg") == "CDK NOT FOUND." and response_json.get("err_code") == 40014:
                return "CDK_NOT_FOUND"
            elif response_json.get("msg") == "SAME TYPE EXCHANGE." and response_json.get("err_code") == 40011:
                return "ALREADY_RECEIVED"
            elif response_json.get("msg") == "TIME ERROR." and response_json.get("err_code") == 40007:
                return "CODE_EXPIRED"
            else:
                return f"UNKNOWN_ERROR: {response_json.get('msg')}"
    except Exception as error_message:
        exit_on_error(error_message)


def gather_gift_codes():
    """Function to collect gift codes from various online sources.
    :return: List of gathered gift codes
    """

    try:
        # Define the headers to be used in the requests
        headers = {
            "accept": HEADER_ACCEPT,
            "content-type": HEADER_CONTENT_TYPE,
            "sec-ch-ua": HEADER_SEC,
            "user-agent": HEADER_USER_AGENT
        }

        # Initialize an empty list to store the gathered gift codes
        web_codes = []

        # Iterate over the online sources and their corresponding search keywords
        for dict_url, dict_search_keyword in web_wos_rewards_online_sources.items():
            try:
                # Send a GET request to the URL with the specified headers
                response = requests.get(dict_url, headers=headers)
                response.raise_for_status()  # Check if the request was successful

                # Check if the response content is JSON
                if response.headers.get('Content-Type') == 'application/json':
                    web_data = response.json()
                else:
                    web_data = response.text

                # Parse the response content using BeautifulSoup
                soup = BeautifulSoup(web_data, "lxml")
                # Extract and add the text of the elements matching the search keyword to the list
                web_codes.extend([online.get_text() for online in soup.find_all(class_=dict_search_keyword)])
            except requests.RequestException as request_message:
                # Handle any request-related errors
                print(f"An error occurred during the GET request: {request_message}")
                continue
            except json.JSONDecodeError as json_error:
                # Handle any JSON decoding errors
                print(f"JSON decode error: {json_error}")
                continue

        return web_codes
    except Exception as error_message:
        exit_on_error(error_message)


def check_code_expiration(gift_codes, members_list):
    """Function to verify all gift codes against the first player ID for expiration.
    :param gift_codes: List containing all gift codes for WOS
    :param members_list: List containing all members from the CSV file
    :return: List of valid gift codes
    """

    try:
        # Initialize an empty list to store valid gift codes
        codes = []

        # Print a message indicating the start of the validation process
        print("Checking if loaded codes are valid...")

        # Iterate over each gift code in the provided list
        for entry in gift_codes:
            # Check if the gift code is not expired by claiming it with the first player's ID
            if not claim_gift_code(members_list[0]["ID"], entry) == "CODE_EXPIRED":
                # If the code is valid, strip any leading/trailing whitespace and add it to the list
                codes.append(entry.strip())

        return codes
    except Exception as error_message:
        exit_on_error(error_message)


def main_program():
    """Function to run the main program code.
    :return: None
    """
    try:
        # Record the start time of the program
        start_time = time.time()

        # Load the list of members from the CSV file
        members_list = load_file_as_dict(MEMBERS_CSV)

        # Gather gift codes from online sources
        online_codes = gather_gift_codes()
        # Load gift codes from the local CSV file
        gift_codes = load_file_as_dict(GIFT_CODES_CSV)
        # Combine online and local gift codes into one list
        gift_codes = online_codes + [code["ID"] for code in gift_codes]
        # Remove duplicate gift codes
        gift_codes = list(set(gift_codes))
        # Check the expiration of the gift codes and get the valid ones
        valid_codes = check_code_expiration(gift_codes, members_list)

        # Print the list of valid gift codes
        print(f"Valid codes: {valid_codes}")

        # Iterate over the members, starting from the second member
        for member in members_list[1:]:
            # Skip members whose ID starts with a '#'
            if member["ID"][0] == "#":
                print(f"[WARN] SKIPPING PLAYER {member}")
            else:
                # Redeem each valid gift code for the current member
                for code in valid_codes:
                    claim_gift_code(member["ID"], code)

        # Print the current date
        print(f"Date: {datetime.today()}")
        # Print the start time of the program
        print(f"Start time: {start_time}")
        # Print the total execution time of the program
        print(f"--- %s seconds ---" % (time.time() - start_time))
        # Print the list of redeemed codes
        print(f"Redeemed codes: {valid_codes}")
        # Indicate that the gift code redemption process is finished
        print("Gift Code Redemption finished!")
    except Exception as error_message:
        exit_on_error(error_message)


# Ensure to run the program only if executed directly and not imported from another Python program
if __name__ == '__main__':
    main_program()
