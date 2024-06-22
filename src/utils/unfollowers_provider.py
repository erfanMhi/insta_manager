import json


FOLLOWERS_FILE = 'data/followers.json'
FOLLOWING_FILE = 'data/following.json'


def get_ids_from_file(file_path: str):
    # Read the JSON file
    with open(file_path, 'r') as file:
        data = json.load(file)

    # Print the contents of the JSON file

    if 'following' in file_path:
        data = data['relationships_following']

    # Extract all values from the JSON file
    values = []
    for item in data:
        string_list_data = item.get('string_list_data', [])
        for string_data in string_list_data:
            value = string_data.get('value')
            if value:
                values.append(value)
    # Print the extracted values
    return values


def get_followers():
    return get_ids_from_file(FOLLOWERS_FILE)


def get_following():
    return get_ids_from_file(FOLLOWING_FILE)


def get_unfollowers():
    followers = get_followers()
    following = get_following()
    return list(set(following) - set(followers))

