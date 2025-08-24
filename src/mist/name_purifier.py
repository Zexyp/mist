import requests

def purify(videoId):
    json_data = {
        'videoId': videoId,
        'context': {
            'client': {
                'clientName': 'WEB_REMIX',
                'clientVersion': '1.20240617.01.00-canary_control_1.20240624.01.00',
            },
        },
    }

    response = requests.post('https://music.youtube.com/youtubei/v1/player', json=json_data)
    response_data = response.json()

    details = response_data["videoDetails"]
    microformat = response_data["microformat"]

    owner = microformat["microformatDataRenderer"]["pageOwnerDetails"]["name"]

    # TODO: seems redundant
    owner = owner.removesuffix(" - Topic") # fuck topics

    if details["author"] not in details["title"]:
        name = f"""{details["author"]} - {details["title"]}"""
    else:
        name = details["title"]

    if details["author"] != owner:
        name += f" [{owner}]"
    
    return name
