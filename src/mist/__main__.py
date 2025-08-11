import os
import collections
import traceback
import configparser

from yt_dlp import YoutubeDL

from . import name_purifier

MAX_DURATION = 600

def shrimplify_name(entry):
    if entry['channel'] is None:
        print('channel none at \'' + entry['id'] + '\'')

    name = name_purifier.purify(entry['id'])

    return name

def sanitize_name(name):
    replacement_char = '_'
    return name.replace('\\', replacement_char).replace('/', replacement_char).replace('*', replacement_char).replace('?', replacement_char).replace('"', replacement_char).replace('<', replacement_char).replace('>', replacement_char).replace('|', replacement_char)

def fix_names():
    for filename in [f for f in os.listdir(DIRECTORY_OUTPUT) if os.path.isfile(os.path.join(DIRECTORY_OUTPUT, f))]:
        ext = os.path.splitext(filename)[1]
        ytid = filename.split('.')[-2]
        print(f"fixing {ytid}")
        new_name = name_purifier.purify(ytid)
        new_name = sanitize_name(new_name)
        os.rename(os.path.join(DIRECTORY_OUTPUT, filename), os.path.join(DIRECTORY_OUTPUT, f"{new_name}.{ytid}{ext}"))

def get_remote_list(url):
    list_options = {
        'extract_flat': True,
        'download': False,
        #'playliststart': 0,
        #'playlistend': 10,
        #'ignore_no_formats_error': True,
        'quiet': True,
    }

    print("downloading list...")

    with YoutubeDL(list_options) as ytdl:
        data = ytdl.extract_info(url)
    
    return data['entries']

def get_local_ids(directory):
    print("reading local ids...")
    
    return [f.split('.')[-2] for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]

def detect_duplicate(items):
    print("checking duplicates...")
    
    # shrimple detect
    duplicates = [item for item, count in collections.Counter(items).items() if count > 1]
    if duplicates:
        print("\n".join([f"    {d}" for d in duplicates]))

def process_entry(entry, out_directory):    
    video_options = {
        'format': 'bestaudio',
        'outtmpl': '',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
        }],
        'quiet': True,
    }
    
    if MAX_DURATION is not None and entry['duration'] > MAX_DURATION:
        print(f"skipping '{entry['id']}' (duration restriction)")
        return

    name = shrimplify_name(entry)

    print(f"downloading '{entry['id']}' {name}")

    video_options['outtmpl'] = os.path.join(out_directory, sanitize_name(name) + '.' + entry['id'] + '.%(ext)s')
    
    with YoutubeDL(video_options) as ytdl:
        data = ytdl.download('http://www.youtube.com/watch?v=' + entry['id'])

def old_main():
    config = configparser.ConfigParser()
    config.read('config.ini')
    DIRECTORY_OUTPUT = config["section"]["output_directory"]
    URL_PLAYLIST = config["section"]["playlist_url"]

    assert os.path.isdir(DIRECTORY_OUTPUT)

    remote_entries = get_remote_list(URL_PLAYLIST)

    
    remote_ids = [e['id'] for e in remote_entries]
    print("remote duplicates:")
    detect_duplicate(remote_ids)
    remote_ids = {*remote_ids}

    local_ids = get_local_ids(DIRECTORY_OUTPUT)
    print("local duplicates (variations):")
    detect_duplicate(local_ids)
    local_ids = {*local_ids}

    missing = remote_ids - local_ids
    leftovers = local_ids - remote_ids
    print("missing:")
    print("\n".join([f"    {i}" for i in missing]))
    print("leftovers:")
    print("\n".join([f"    {i}" for i in leftovers]))

    entries_to_download = [entry for entry in remote_entries if entry['id'] in missing]

    with open("../../error.log", "w") as error_log:
        for entry in entries_to_download:
            try:
                process_entry(entry, DIRECTORY_OUTPUT)
            except KeyboardInterrupt:
                print("stopped")
                break
            except Exception as e:
                print(traceback.format_exc())
                
                name = shrimplify_name(entry)
                error_log.write(f"{entry['id']}: {name}\n")


def main():
    from . import cli
    cli.run()
    
if __name__ == "__main__":
    main()
