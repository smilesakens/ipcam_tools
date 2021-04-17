import os
import sys
import json
import time
import pprint
import shutil
import getpass
import datetime
import requests
import configparser

import dahua_rpc


CHUNK_SZ = 1000
PARAMS = {
          'condition': {
                        'Channel': 0,
                        'Dirs': ['/mnt/sd'],
                        'Types': ['dav', 'jpg'],
                        'Order': 'Ascent',
                        'Redundant': 'Exclusion',
                        'Events': 'null',
                        #'StartTime': '2020-04-01 00:00:00',
                        'StartTime': '',
                        #'EndTime': '2021-04-01 23:59:59',
                        'EndTime': '',
                        'Flags': ['Timing', 'Event', 'Event', 'Manual']
                        }
          }


def get_cam_config(config_path):
    config = configparser.ConfigParser()
    config.read(config_path)
    ipaddr = config.get('DEFAULT', 'ip_address', fallback=None)
    username = config.get('DEFAULT', 'username', fallback=None)
    password = config.get('DEFAULT', 'password', fallback=None)

    return ipaddr, username, password


def get_media_storage_token(ipcam):
    token = ipcam.request('mediaFileFind.factory.create')
    token = token.get('result')
    if not token:
        print('[!!] Error getting token... Exiting!')
        sys.exit(1)

    return token


def get_time_window(event_timestamp, time_delta_mins):
    if not isinstance(time_delta_mins, int):
        raise TypeError('time_delta_mins must be an integer, but {} provided'.format(type(time_delta_mins)))
    if isinstance(event_timestamp, str):
        event_time = datetime.datetime.fromisoformat(event_timestamp)
    elif isinstance(event_timestamp, datetime.datetime):
        event_time = event_timestamp
    else:
        raise TypeError('event_timestamp must be a string or DateTime obj, but {} provided'.format(type(event_timestamp)))

    start_time = event_time - (event_time - datetime.datetime.min) % datetime.timedelta(minutes=time_delta_mins)
    end_time = event_time + (datetime.datetime.min - event_time) % datetime.timedelta(minutes=time_delta_mins)
    print(event_time)
    print('\tStart: {} - End: {}'.format(start_time, end_time))

    return event_time, start_time, end_time


def get_media_metadata(ipcam, params, query_chunk_size=CHUNK_SZ):
    token = get_media_storage_token(ipcam)
    # The findFile method gathers all the metadata related to the files matching the parameters provided
    # Depending on the timeframe used within params, findFile can take seconds to return
    result = ipcam.request('mediaFileFind.findFile', params=params, object_id=token)
    # After executing findFile, the findNextFile method returns chunks of metadata
    result = ipcam.request('mediaFileFind.findNextFile', params={"count":query_chunk_size}, object_id=token)
    # "found" is the value for the number of metadata elements returned in the result
    # If "found" matches the chunk size, you want to keep querying till you get fewer results than you chunk size
    found = result.get('params', {}).get('found', 0)
    print('[**] Found: {}'.format(found))
    if result.get('result') != True:
        print('[!!] Query failed...')
        pprint.pprint(result)
        sys.exit(1)

    yield result, token

    while found == query_chunk_size:
        result = ipcam.request('mediaFileFind.findNextFile', params={"count":query_chunk_size}, object_id=token)
        found = result.get('params', {}).get('found', 0)
        print('[**] Found: {}'.format(found))

        yield result, token


def list_media_files(media_metadata_chunk):
    if not media_metadata_chunk.get('params', {}).get('infos'):
        print('[!!] Result was malformed...')
        pprint.pprint(media_metadata_chunk)
        return
    for media_file in media_metadata_chunk['params']['infos']:
        print('\nFile: {}'.format(media_file.get('FilePath')))
        print('Start: {} - End: {}'.format(media_file.get('StartTime'), media_file.get('EndTime')))
        print('Duration: {} / Size: {}'.format(media_file.get('Duration'), media_file.get('Length')))


def save_media_files(ipcam, media_metadata_chunk, output_path):
    if not media_metadata_chunk.get('params', {}).get('infos'):
        print('[!!] Result was malformed...')
        pprint.pprint(media_metadata_chunk)
        return
    session = requests.Session()
    for media_file in media_metadata_chunk['params']['infos']:
        cam_media_path = media_file.get('FilePath')
        file_ext = media_file.get('Type')
        start_time = datetime.datetime.fromisoformat(media_file.get('StartTime'))
        date = start_time.strftime('%Y-%m-%d')
        start_time = start_time.strftime('%H%M%S')
        end_time = datetime.datetime.fromisoformat(media_file.get('EndTime'))
        end_time = end_time.strftime('%H%M%S')
        if file_ext == 'dav':
            output_fpath = '{}_{}-{}.{}'.format(date, start_time, end_time, file_ext)
        elif file_ext == 'jpg':
            output_fpath = '{}_{}.{}'.format(date, start_time, file_ext)
        else:
            print('[!!] Unknown media type: {}'.format(file_ext))
        output_fpath = os.path.join(output_path, output_fpath)
        download_cam_media(session, ipcam, cam_media_path, output_fpath)


def download_cam_media(session, ipcam, cam_media_path, output_fpath):
    # Example of how to use the ipcam requests session to get one of the file paths returned from get_media_metadata()
    headers = {
               'Cookie': 'secure; username={}; DhWebClientSessionID={}'.format(ipcam.username, ipcam.session_id)
              }
    # Camera will close the connection if connections come in too rapidly
    time.sleep(1)
    resp = session.get('http://{}/RPC_Loadfile{}'.format(ipcam.host, cam_media_path),
                headers=headers,
                stream=True)
    with open(output_fpath, 'wb') as f:
        shutil.copyfileobj(resp.raw, f)
        print('[++] Saved: {}'.format(output_fpath))


if __name__ == '__main__':

    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', dest='config_path', default='cam.config', help='Config containing IP address, username and password')
    parser.add_argument('--host', dest='host', help='Camera hostname or IP address')
    parser.add_argument('-u', '--username', dest='username', help='Camera username')
    parser.add_argument('-p', '--password', action='store_true', dest='password', help='Camera password')
    parser.add_argument('-d', '--delta', dest='delta', default='5', type=int, help='Number of minutes to search before/after target_time')
    parser.add_argument('-t', '--target_time', dest='target_time', help='Target timestamp to search before/after (ISO Format)')
    parser.add_argument('-l', '--list', action='store_true', dest='list', help='List all media files within target time')
    parser.add_argument('--dump', action='store_true', dest='dump', help='Dump the raw result JSON')
    parser.add_argument('-o', dest='output_path', help='Directory to save media files')

    args = parser.parse_args()

    # Try to load from cam.config, then probe for args that override host/creds
    ipaddr, username, password = get_cam_config(args.config_path)
    if args.host:
        ipaddr = args.host
    if args.username:
        username = args.username
    if args.password:
        if args.password == True:
            password = getpass.getpass()
        else:
            password = args.password

    # IP/User/Password should have been populated via config or args, if not catch error here
    if not ipaddr or not username or not password:
        print('[!!] IP/User/Password missing... Specify them as arguments or within a config\n')
        parser.print_help()
        sys.exit(1)

    # This is the ipcam RPC handle using gxfxyz's Dahua RPC wrapper
    ipcam = dahua_rpc.DahuaRpc(host=ipaddr, username=username, password=password)
    # Execute login in order to populate the session_id (used by each method call)
    ipcam.login()

    if not args.target_time:
        target_time = ipcam.current_time()
    else:
        target_time = args.target_time

    event_time, start_time, end_time = get_time_window(target_time, args.delta)
    PARAMS['condition']['StartTime'] = start_time.strftime('%Y-%m-%d %H:%M:%S')
    PARAMS['condition']['EndTime'] = end_time.strftime('%Y-%m-%d %H:%M:%S')
    for media_metadata_chunk, token in get_media_metadata(ipcam, PARAMS):
        if args.list:
            list_media_files(media_metadata_chunk)
        if args.dump:
            pprint.pprint(media_metadata_chunk)
        if args.output_path:
            save_media_files(ipcam, media_metadata_chunk, args.output_path)
    resp = ipcam.request('mediaFileFind.destroy', object_id=token)
    resp = ipcam.request('global.logout')

