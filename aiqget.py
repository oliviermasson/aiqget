#! /usr/bin/python3

import sys

pythonversion=sys.version_info
if pythonversion[0] != 3 or (pythonversion[1] < 6 or pythonversion[1] > 11):
    userio.message("This script requires Python 3.6 through 3.11")
    sys.exit(1)
sys.path.append(sys.path[0] + "/NTAPlib")
import time
import getopt
import json
import os
import doREST
from refreshToken import refreshToken
from getEfficiency import getEfficiency
from getCapacity import getCapacity
from getHeadroom import getHeadroom
from getProtocolsIOPS import getProtocolsIOPS
from getOverallIOPS import getOverallIOPS
from getBandwidth import getBandwidth
import userio
from datetime import datetime,timedelta

aiqget='1.0'

validoptions={'serialnumbers':'str',
              'refresh_Token':'str',
              'debug':'bool',
              'restdebug':'bool',
              'days':'int',
              'customer':'str',
              'protoIOPS': 'bool',
              'bandwidth': 'bool',
              'overallIOPS': 'bool'}

requiredoptions=['serialnumbers','customer','refreshToken']

usage="Version " + aiqget + "\n" + \
      "aiqget --serialnumbers\n" + \
      "         (Required. List of serial numbers provided as comma separeted list)\n" + \
      "         \n" + \
      "       --customer\n" + \
      "         (Required. Customer identifier that will be added as a prefix to the generated HTML file)\n\n" + \
      "       --refresh_Token\n" + \
      "         (Required. The refresh token for AIQ access)\n\n" + \
      "       [--days]\n" + \
      "         (optional. Number of days to compute all performances metrics average)\n" + \
      "         (Default to 31 days before current date)\n\n" + \
      "       [--protoIOPS]\n" + \
      "         (optional. retrieve Protocols IOPS)\n\n" + \
      "       [--overallIOPS]\n" + \
      "         (optional. retrieve total IOPS)\n\n" + \
      "       [--bandwidth]\n" + \
      "         (optional. retrieve bandwidth)\n\n" + \
      "       [--debug]\n" + \
      "         (optional. Show debug output)\n\n" + \
      "       [--restdebug]\n" + \
      "         (optional. Show REST API calls and responses)\n\n" 

myopts=userio.validateoptions(sys.argv,validoptions,usage=usage,required=requiredoptions)

serialnumbers=myopts.serialnumbers.split(',')

customer=myopts.customer

days=myopts.days

refresh_Token=myopts.refresh_Token

if days is not None:
    days=int(days)
else:
    days=31

debug=0
if 'debug' in myopts:
    debug=debug+1

if myopts.restdebug:
    debug=debug+2

try:
    protoIOPS=myopts.protoIOPS
except:
    protoIOPS=False

try:
    overallIOPS=myopts.overallIOPS
except:
    overallIOPS=False

try:
    bandwidth=myopts.bandwidth  
except:
    bandwidth=False


userio.message("Refresh AIQ access token...")
tokens=refreshToken("api.activeiq.netapp.com",refresh_Token=refresh_Token,debug=debug)
if not tokens.go():
    tokens.showDebug()

today=datetime.now().strftime('%Y-%m-%d')
before=(datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')


userio.message("Retrieve Efficiency information...")
Efficiency=getEfficiency("api.activeiq.netapp.com",access_token=tokens.access_Token,serialnumbers=serialnumbers,debug=debug)
if not Efficiency.go():
    Efficiency.showDebug()

userio.message("Retrieve Capacity information...")
Capacity=getCapacity("api.activeiq.netapp.com",access_token=tokens.access_Token,serialnumbers=serialnumbers,debug=debug)        
if not Capacity.go():
    Capacity.showDebug()

userio.message("Retrieve Headroom information...")
Headroom=getHeadroom("api.activeiq.netapp.com",access_token=tokens.access_Token,serialnumbers=serialnumbers,start=before,end=today,debug=debug)        
if not Headroom.go():
    Headroom.showDebug()

if protoIOPS:
    userio.message("Retrieve Protocols IOPS information...")
    ProtocolsIOPS=getProtocolsIOPS("api.activeiq.netapp.com",access_token=tokens.access_Token,serialnumbers=serialnumbers,start=before,end=today,debug=debug)        
    if not ProtocolsIOPS.go():
        ProtocolsIOPS.showDebug()

if overallIOPS:
    userio.message("Retrieve avg IOPS information...")
    avgIOPS=getOverallIOPS("api.activeiq.netapp.com",access_token=tokens.access_Token,serialnumbers=serialnumbers,start=before,end=today,debug=debug)        
    if not avgIOPS.go():
        avgIOPS.showDebug()

if bandwidth:
    userio.message("Retrieve Bandwidth information...")
    avgBandwidth=getBandwidth("api.activeiq.netapp.com",access_token=tokens.access_Token,serialnumbers=serialnumbers,start=before,end=today,debug=debug)        
    if not avgBandwidth.go():
        avgBandwidth.showDebug()

userio.message("Aggregate all information...")
wholeNumbers=Efficiency.aggrEfficiency.copy()
for serial in Efficiency.aggrEfficiency.keys():
    wholeNumbers[serial].update(Capacity.aggrCapacity[serial])
    wholeNumbers[serial].update(Headroom.aggrHeadroom[serial])
    if protoIOPS:
        wholeNumbers[serial].update(ProtocolsIOPS.aggrProtoIOPS[serial])
    if overallIOPS:
        wholeNumbers[serial].update(avgIOPS.aggrOverall[serial])
    if bandwidth:
        wholeNumbers[serial].update(avgBandwidth.aggrBandwidth[serial])

#print(wholeNumbers)    

# Create HTML output
current_datetime = datetime.now().strftime('%d-%m-%Y %H:%M')

html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>AIQ Get Results - {current_datetime}</title>
    <style>
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 20px 0;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }}
        th {{
            background-color: #0066cc;
            color: white;
            cursor: pointer;
            position: relative;
        }}
        th::after {{
            content: '⇕';
            position: absolute;
            right: 8px;
            color: rgba(255,255,255,0.5);
        }}
        th.asc::after {{
            content: '↓';
            color: white;
        }}
        th.desc::after {{
            content: '↑';
            color: white;
        }}
        tr:nth-child(even) {{
            background-color: #f2f2f2;
        }}
    </style>
    <script>
        function sortTable(n) {{
            var table, rows, switching, i, x, y, shouldSwitch, dir, switchcount = 0;
            table = document.querySelector("table");
            switching = true;
            dir = "asc";
            
            // Remove sorting indicators from all headers
            var headers = table.getElementsByTagName("th");
            for (i = 0; i < headers.length; i++) {{
                headers[i].classList.remove("asc", "desc");
            }}  
            
            // Add sorting indicator to clicked header
            headers[n].classList.add(dir);
            
            while (switching) {{
                switching = false;
                rows = table.rows;
                
                for (i = 1; i < (rows.length - 1); i++) {{
                    shouldSwitch = false;
                    x = rows[i].getElementsByTagName("td")[n];
                    y = rows[i + 1].getElementsByTagName("td")[n];
                    
                    // Convert to number if possible and handle decimal numbers
                    let xContent = x.innerHTML.trim();
                    let yContent = y.innerHTML.trim();
                    
                    // Try to convert to numbers if they look like numbers
                    if (xContent.match(/^-?\d*\.?\d+$/) && yContent.match(/^-?\d*\.?\d+$/)) {{
                        xContent = parseFloat(xContent);
                        yContent = parseFloat(yContent);
                    }} else {{
                        // Case insensitive string comparison
                        xContent = xContent.toLowerCase();
                        yContent = yContent.toLowerCase();
                    }}
                    
                    
                    if (dir == "asc") {{
                        if (xContent > yContent) {{
                            shouldSwitch = true;
                            break;
                        }}
                    }} else if (dir == "desc") {{
                        if (xContent < yContent) {{
                            shouldSwitch = true;
                            break;
                        }}
                    }}
                }}
                
                if (shouldSwitch) {{
                    rows[i].parentNode.insertBefore(rows[i + 1], rows[i]);
                    switching = true;
                    switchcount++;
                }} else {{
                    if (switchcount == 0 && dir == "asc") {{
                        dir = "desc";
                        headers[n].classList.remove("asc");
                        headers[n].classList.add("desc");
                        switching = true;
                    }}
                }}
            }}
        }}
    </script>
</head>
<body>
    <h1>AIQ Get Results - {current_datetime}</h1>
    <table>
"""

# Get all possible keys from all dictionaries to create headers
all_keys = set()
for serial_data in wholeNumbers.values():
    all_keys.update(serial_data.keys())

# Create table headers
html_content += "<tr>"
html_content += '<th onclick="sortTable(0)">Serial Number</th>'
column_index = 1
for key in sorted(all_keys):
    html_content += f'<th onclick="sortTable({column_index})">{key}</th>'
    column_index += 1
html_content += "</tr>"

# Add data rows
for serial, data in wholeNumbers.items():
    html_content += f"<tr><td>{serial}</td>"
    for key in sorted(all_keys):
        value = data.get(key, "N/A")
        html_content += f"<td>{value}</td>"
    html_content += "</tr>"

html_content += """
    </table>
</body>
</html>
"""

# Write the HTML file
if bandwidth or overallIOPS or protoIOPS:
    output_file = customer+"_Perf_aiqget_results.html"
else:
    output_file = customer+"_aiqget_results.html"

try:
    if os.path.exists(output_file):
        # Get file creation time (using modification time as fallback)
        file_time = os.path.getctime(output_file)
        file_date = datetime.fromtimestamp(file_time).strftime('%Y%m%d_%H%M')
        if bandwidth or overallIOPS or protoIOPS:
            new_name = f"{customer}_Perf_aiqget_results_{file_date}.html"
        else:
            new_name = f"{customer}_aiqget_results_{file_date}.html"
        try:
            os.rename(output_file, new_name)
            userio.message(f"Existing file backed up to {new_name}")
        except OSError as e:
            userio.message(f"Warning: Could not rename existing file: {e}")

    with open(output_file, "w", encoding='utf-8') as f:
        f.write(html_content)
    userio.message(f"Results have been saved to {output_file}")

except (IOError, OSError) as e:
    userio.message(f"Error: Could not write results to file: {e}")

