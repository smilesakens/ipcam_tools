import os
import shutil
import subprocess
import sys
import time


def format_dav_range(dav_range):
    fixed_dave_range = None

    if not len(dav_range.split('-')) == 2:
        print('[!!] Unexpected dav_range format: {}'.format(dav_range.split('-')))
        return fixed_dav_range

    range1, range2 = dav_range.split('-')
    range1 = '{:0>2}{:0>2}{:0>2}'.format(*range1.split('.'))
    range2 = '{:0>2}{:0>2}{:0>2}'.format(*range2.split('.'))
    fixed_dav_range = '{}-{}'.format(range1, range2)

    return fixed_dav_range


def fix_fname_format(cam_files_path, ppath, fname):
    fixed_fname = None

    if not fname.lower().endswith('.jpg') and not fname.lower().endswith('.dav'):
        # Fail fast if these arent the files we are looking for
        return fixed_fname

    ppath_parts = ppath.replace(cam_files_path, '').split(os.path.sep)
    if ppath_parts[0] == '':
        ppath_parts.pop(0)

    if fname.lower().endswith('.jpg'):
        if not len(ppath_parts) >= 5:
            print('[!!] Unexpected parent path format: {}'.format(ppath_parts))
            print('\t{}'.format(ppath))
            print('\tExample: ./2018-07-09/001/jpg/23/27/52[M][0@0][0].jpg')
            return fixed_fname
        # First two chars are the seconds timestamp
        # Last four chars are the file extension (and we want it lowercase)
        jpg_path = '{}{}'.format(fname[:2], fname[-4:].lower())
        hours, mins = ppath_parts[-2:]
        date = ppath_parts[-5]
        fixed_fname = '{}_{}{}{}'.format(date, hours, mins, jpg_path)
    elif fname.lower().endswith('.dav'):
        if not len(ppath_parts) >= 4:
            print('[!!] Unexpected parent path format: {}'.format(ppath_parts))
            print('\t{}'.format(ppath))
            print('\tExample: ./2018-07-09/001/dav/17/17.06.46-17.14.00[M][0@0][0].dav')
            return fixed_fname
        # First 16 chars are the event time range
        # Last four chars are the file extension (and we want it lowercase)
        dav_range = fname[:17]
        fixed_dav_range = format_dav_range(dav_range)
        if not fixed_dav_range:
            return fixed_fname

        dav_fname = '{}{}'.format(fixed_dav_range, fname[-4:].lower())
        date = ppath_parts[-4]
        fixed_fname = '{}_{}'.format(date, dav_fname)

    return fixed_fname


def find_cam_files(cam_files_path, target_date):
    if not os.path.isdir(cam_files_path):
        print('[!!] Cam files directory not found: {}'.format(cam_files_path))
        sys.exit(1)

    for ppath, dnames, fnames in os.walk(cam_files_path):
        if target_date and target_date in dnames:
            # Skip directory because it matched target_date
            # "dnames[:] =" changes the data in-place versus "dnames[] =" which rebinds it
            dnames[:] = [target_date]

        for fname in fnames:
            orig_fpath = os.path.join(ppath, fname)

            yield orig_fpath, fix_fname_format(cam_files_path, ppath, fname)


def encode_file(cam_file_in, cam_file_out, skip_audio=None):
    print('[**] Encoding: {}\n\t--> {}'.format(cam_file_in, cam_file_out))
    success = False
    try:
        if skip_audio:
            subprocess.check_output([
                                     'ffmpeg', '-loglevel', 'fatal',
                                     '-i', cam_file_in,
                                     '-vcodec', 'libx264', '-crf', '24',
                                     '-movflags', '+faststart',
                                     '-an',
                                     '-y',
                                     cam_file_out])
        else:
            subprocess.check_output([
                                     'ffmpeg', '-loglevel', 'fatal',
                                     '-i', cam_file_in,
                                     '-vcodec', 'libx264', '-crf', '24',
                                     '-movflags', '+faststart',
                                     '-y',
                                     cam_file_out])
        success = True
    except Exception as err:
        print('[!!] Failed encode: {}'.format(cam_file_in, err.__str__()))
        time.sleep(5)
    if success:
        os.unlink(cam_file_in)


def move_file(cam_file, output_path):
    print('[**] Moving: {}\n\t--> {}'.format(cam_file, output_path))
    try:
        shutil.move(cam_file, output_path)
    except FileNotFoundError:
        print('[!!] File not found: {}'.format(cam_file))


def encode_dir(cam_files_path, output_path, skip_audio):
    for cam_file in os.listdir(cam_files_path):
        if not cam_file.lower().endswith('.dav'):
            continue
        cam_file_in = os.path.join(cam_files_path, cam_file)
        cam_file_out = cam_file_in.replace('.dav', '.mp4')
        encode_file(cam_file_in, cam_file_out)


def process_cam_ftp_dir(cam_files_path, output_path, target_date, skip_audio):
    for orig_fpath, cam_file in find_cam_files(cam_files_path, target_date):
        if not cam_file:
            continue
        if cam_file.endswith('.jpg'):
            move_file(cam_file, output_path)

        if cam_file.endswith('dav'):
            mp4_path = '{}{}'.format(cam_file[:-4], '.mp4')
            mp4_path = os.path.join(output_path, mp4_path)
            encode_file(orig_fpath, mp4_path, skip_audio=skip_audio)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--cam_files', dest='cam_files_path', required='true', help='Parent directory containing DAV/JPG files')
    parser.add_argument('-o', dest='output_path', required='true', help='Archive directory to save media files')
    parser.add_argument('-t', '--target_date', dest='target_date', help='Only process files in the directories with the specified target name (e.g., 2021-04-17)')
    parser.add_argument('-e', '--encode_dir', dest='encode_dir', action='store_true', help='Re-encode DAV to MP4, any files with archive_cam_media format (e.g., 2021-04-17_054227-054319.dav)')
    parser.add_argument('--skip_audio', dest='skip_audio', action='store_true', help='Pass "-an" to ffmpeg in order to ignore the audio stream')

    args = parser.parse_args()

    if args.encode_dir:
        encode_dir(args.cam_files_path, args.output_path, args.skip_audio)
    else:
        process_cam_ftp_dir(args.cam_files_path, args.output_path, args.target_date, args.skip_audio)

