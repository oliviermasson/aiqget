# AIQget

AIQget is a Python CLI which retreive information from ActiveIQ.NetApp.com for ONTAP serialnumber

AIQget is a python script which retreive the following information from AIQ:

    average current CPU Headroom for the last 31 days (default)
    efficiency ratio
    % capacity used
    capacity available

All columns are sortable

It use Python 3.10.

You just need to provide a comma-separated list of the serialnumber you want:

example: 
`python3 aiget.py --serialnumber 211941000138,211941000137 --customer ACME --refresh_Token <your refresh token>`

It will then generate an HTML file with associated results named : 

`ACME_aiqget_results.html`

Script will also rename existing HTML file

`refresh_Token` is a required parameter

You must register ActiveIQ API services to get a refresh_Token before running this script.  
Go to [activeiq.netapp.com/api](https://activeiq.netapp.com/api)  
Click on generate token and respond the questions  
![alt text](image.png)  
To obtain your access_Token and refresh_Token

If the script find a previous version of HTML results, it will parse it and add to the new generated file,\
the percentage of variation for each counter.\
Which will help you quickly see the trend for each serialnumber and each counter\

Example of basics results :
![alt text](image-1.png)

Example of results with all performances counters :
![alt text](image-3.png)

