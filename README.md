# AIQget

AIQget is a Python CLI which retreive information from ActiveIQ.NetApp.com for ONTAP serialnumber

AIQget is a python script which retreive the following information from AIQ:

    average current CPU Headroom for the last 31 days (default)
    efficiency ratio
    % capacity used
    capacity available

It use Python 3.10.

You just need to provide a comma-separated list of the serialnumber you want:

example: python3 aiget.py --serialnumber 211941000138,211941000137

It will then generate an HTML file with associated results