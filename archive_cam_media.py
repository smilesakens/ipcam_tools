import os
import sys
import datetime
import json
import pprint
import shutil

import cam_query
import dahua_rpc



if __name__ == '__main__':

    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', dest='config_path', default='cam.config', help='Config containing IP address, username and password')
    parser.add_argument('-d', '--delta', dest='delta', default='5', type=int, help='Number of minutes to search before/after target_time')
    parser.add_argument('-t', '--target_time', dest='target_time', help='Target timestamp to search before/after (ISO Format)')
    parser.add_argument('--full_caps', dest='full_cap_path', required='true', help='Directory containing full capture files')
    parser.add_argument('-o', dest='output_path', required='true', help='Directory to save media files')

    args = parser.parse_args()

    ipaddr, username, password = cam_query.get_cam_config(args.config_path)

    ipcam = dahua_rpc.DahuaRpc(host=ipaddr, username=username, password=password)
    ipcam.login()

    if not args.target_time:
        target_time = ipcam.current_time()
    else:
        target_time = args.target_time
    prev_period = datetime.datetime.fromisoformat(target_time) - datetime.timedelta(minutes=2*args.delta)
    event_time, start_time, end_time = cam_query.get_time_window(prev_period.isoformat(), args.delta)

    cam_query.PARAMS['condition']['StartTime'] = start_time.strftime('%Y-%m-%d %H:%M:%S')
    cam_query.PARAMS['condition']['EndTime'] = end_time.strftime('%Y-%m-%d %H:%M:%S')

    results = []
    for media_metadata_chunk, token in cam_query.get_media_metadata(ipcam, cam_query.PARAMS):
        pprint.pprint(media_metadata_chunk)
        if media_metadata_chunk.get('result') == True:
            for media_item in media_metadata_chunk['params'].get('infos'):
                results.append(media_item)
    resp = ipcam.request('mediaFileFind.destroy', object_id=token)

    for media_file in results:
        output_fpath, media_bytez = cam_query.save_media_files(ipcam, media_file, args.output_path)
        cam_query.copy_file_obj(output_fpath, media_bytez)

    resp = ipcam.request('global.logout')

    for full_cap in [start_time.strftime('%Y-%m-%d_%H%M%S-full.mp4'), end_time.strftime('%Y-%m-%d_%H%M%S-full.mp4')]:
        full_cap_path = os.path.join(args.full_cap_path, full_cap)
        shutil.copy(full_cap_path, args.output_path)


