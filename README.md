# Overview
This is a poc tool for querying metadata from the media storage on Dahua IP Cameras

# Installation
```
python3 -m pip install -r requirements.txt
```

# Configuration
Define the camera IP address, username, and password to use.

`cam.config` format:
```
[DEFAULT]
ip_address = 192.168.1.108
username = admin
password = mycoolpassword
```

# Usage
```
python3 cam_query.py

2021-04-14 19:26:46
[**] Found: 1000
{'id': 6,
 'params': {'found': 1000,
            'infos': [{'Channel': 0,
                       'Cluster': 0,
                       'Compressed': False,
                       'CutLength': 618363,
                       'Disk': 0,
                       'Duration': 0,
                       'EndTime': '2021-04-04 12:24:31',
                       'Events': ['VideoMotion'],
                       'FilePath': '/mnt/sd/2021-04-04/001/jpg/12/24/31[M][0@0][0][31736].jpg',
                       'Flags': ['Event'],
                       'Length': 618363,
                       'Overwrites': 0,
                       'Partition': 0,
                       'PicIndex': 0,
                       'Redundant': False,
                       'Repeat': 0,
                       'StartTime': '2021-04-04 12:24:31',
                       'Summary': {'TrafficCar': {'PlateColor': 'Yellow',
                                                  'PlateNumber': ' ',
                                                  'PlateType': 'Yellow',
                                                  'Speed': 60,
                                                  'VehicleColor': 'White'}},
                       'SummaryOffset': 0,
                       'Type': 'jpg',
                       'VideoStream': 'Main',
                       'WorkDir': '/mnt/sd',
                       'WorkDirSN': 0},
                      {'Channel': 0,
                       'Cluster': 0,
                       'Compressed': False,
                       'CutLength': 9077968,
                       'Disk': 0,
                       'Duration': 38,
                       'EndTime': '2021-04-04 12:52:19',
                       'Events': ['VideoMotion'],
                       'FilePath': '/mnt/sd/2021-04-04/001/dav/12/12.51.41-12.52.19[M][0@0][0].dav',
                       'Flags': ['Event'],
                       'Length': 9077968,
                       'Overwrites': 0,
                       'Partition': 0,
                       'PicIndex': 0,
                       'Redundant': False,
                       'Repeat': 0,
                       'StartTime': '2021-04-04 12:51:41',
                       'Summary': {'TrafficCar': {'PlateColor': 'Yellow',
                                                  'PlateNumber': ' ',
                                                  'PlateType': 'Yellow',
                                                  'Speed': 60,
                                                  'VehicleColor': 'White'}},
                       'SummaryOffset': 0,
                       'Type': 'dav',
                       'VideoStream': 'Main',
                       'WorkDir': '/mnt/sd',
                       'WorkDirSN': 0},
<--TRUNCATED-->
```
