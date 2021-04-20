import datetime
import os
import re
import shutil
import subprocess


def get_date_regex(fname):
    match = re.search('\d{4}-\d{2}-\d{2}', fname)
    if match:
        return match.group(0)


def make_dirs(camdir_abspath, year, month, day):
    year_path = os.path.join(camdir_abspath, year)
    if not os.path.isdir(year_path):
        os.mkdir(year_path)

    month_path = os.path.join(year_path, month)
    if not os.path.isdir(month_path):
        os.mkdir(month_path)

    day_path = os.path.join(month_path, day)
    if not os.path.isdir(day_path):
        os.mkdir(day_path)

    move_path = day_path

    return move_path


def test_absfpath(camdir_abspath, fname):
    srcfname_abspath = os.path.join(camdir_abspath, fname)
    if os.path.isfile(srcfname_abspath):
        return srcfname_abspath


if __name__ == '__main__':
    import argparse
    import sys

    parser = argparse.ArgumentParser()
    parser.add_argument('camdir_path', help='path to the camera directory that needs reorg')

    args = parser.parse_args()
    camdir_abspath = os.path.abspath(args.camdir_path)

    #print(camdir_abspath)
    skip_date = datetime.datetime.now().strftime('%Y-%m-%d')

    for fname in os.listdir(camdir_abspath):
        # Only try to move mp4's
        if not fname.lower().endswith('.jpg') and not fname.lower().endswith('.mp4'):
            continue

        # Get the date out of the filename, such as 2019-03-19
        match = get_date_regex(fname)
        if not match:
            continue
        # Try not to move files that might be currently be recording
        if skip_date == match:
            continue

        # Make a directory structure camdir/year/month/day/
        year, month, day = match.split('-')
        move_path = make_dirs(camdir_abspath, year, month, day)
        if not move_path:
            print('ERROR: no move path parsed')
            continue

        # Make sure the src file exists and then move it into the new directory
        srcfname_abspath = test_absfpath(camdir_abspath, fname)
        if srcfname_abspath:
            print('Moving {} -> {}'.format(srcfname_abspath, move_path))
            shutil.move(srcfname_abspath, move_path)

    sys.exit(0)
