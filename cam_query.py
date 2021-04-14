import os
import sys
import pprint
import shutil
import configparser

import dahua_rpc


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


def get_media_metadata(ipcam, token, params, query_chunk_size):
    # The findFile method gathers all the metadata related to the files matching the parameters provided
    # Depending on the timeframe used within params, findFile can take seconds to return
    result = ipcam.request('mediaFileFind.findFile', params=params, object_id=token)
    # After executing findFile, the findNextFile method returns chunks of metadata
    result = ipcam.request('mediaFileFind.findNextFile', params={"count":query_chunk_size}, object_id=token)
    # "found" is the value for the number of metadata elements returned in the result
    # If "found" matches the chunk size, you want to keep querying till you get fewer results than you chunk size
    found = result.get('params', {}).get('found', 0)
    print('[**] Found: {}'.format(found))
    if found == 0:
        print('[!!] Result was malformed...')
        pprint.pprint(result)
        sys.exit(1)
    pprint.pprint(result)
    while found == query_chunk_size:
        result = ipcam.request('mediaFileFind.findNextFile', params={"count":query_chunk_size}, object_id=token)
        found = result.get('params', {}).get('found', 0)
        print('[**] Found: {}'.format(found))
        pprint.pprint(result)


if __name__ == '__main__':

    query_chunk_size = 1000
    # TODO: Need to change the StartTime and EndTime into a parameter we pass into the query
    params = {
              'condition': {
                            'Channel': 0,
                            'Dirs': ['/mnt/sd'],
                            'Types': ['dav', 'jpg'],
                            'Order': 'Ascent',
                            'Redundant': 'Exclusion',
                            'Events': 'null',
                            'StartTime': '2020-04-01 00:00:00',
                            'EndTime': '2021-04-14 23:59:59',
                            'Flags': ['Timing', 'Event', 'Event', 'Manual']
                            }
              }
    ipaddr, username, password = get_cam_config('cam.config')
    # This is the ipcam RPC handle using gxfxyz's Dahua RPC wrapper
    ipcam = dahua_rpc.DahuaRpc(host=ipaddr, username=username, password=password)
    # Execute login in order to populate the session_id
    ipcam.login()
    # Save the session_id for later use in RPC_Loadfile cookies
    session_id = ipcam.session_id
    headers = {'Cookie': 'secure; username={}; DhWebClientSessionID={}'.format('admin', session_id)}

    print(ipcam.current_time())
    token = get_media_storage_token(ipcam)
    get_media_metadata(ipcam, token, params, query_chunk_size)
    '''
    # Example of how to use the ipcam requests session to get one of the file paths returned from get_media_metadata()
    result = ipcam.s.get('http://{}/RPC_Loadfile/mnt/sd/2021-04-14/001/dav/09/09.14.14-09.15.51[M][0@0][0].dav'.format(ipaddr),
                         headers=headers,
                         stream=True)
    with open('derp.dav', 'wb') as f:
        shutil.copyfileobj(result.raw, f)
    result.close()
    '''
