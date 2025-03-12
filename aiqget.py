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
import userio
from datetime import datetime,timedelta

aiqget='1.0'

validoptions={'serialnumbers':'str',
              'debug':'bool',
              'restdebug':'bool',
              'days':'int',
              'customer':'str'}

requiredoptions=['serialnumbers','customer']

usage="Version " + aiqget + "\n" + \
      "aiqget --serialnumbers\n" + \
      "         (List of serial numbers provided as comma separeted list)\n" + \
      "         \n" + \
      "       --customer\n" + \
      "         (Customer identifier that will be added as a prefix to the generated HTML file)\n\n" + \
      "       [--days]\n" + \
      "         (optional. Number of days to compute CPU headroom average)\n" + \
      "         (Default to 31 days before current date\n\n" + \
      "       [--debug]\n" + \
      "         (optional. Show debug output)\n\n" + \
      "       [--restdebug]\n" + \
      "         (optional. Show REST API calls and responses)\n\n" 

myopts=userio.validateoptions(sys.argv,validoptions,usage=usage,required=requiredoptions)

serialnumbers=myopts.serialnumbers.split(',')

customer=myopts.customer

days=myopts.days
if days is not None:
    days=int(days)
else:
    days=31

debug=0
if 'debug' in myopts:
    debug=debug+1

if myopts.restdebug:
    debug=debug+2

userio.message("Refresh AIQ access token...")
tokens=refreshToken("api.activeiq.netapp.com",refresh_Token="eyJraWQiOiJkRUxjVkNzSmZ4MkFrZm1zYzdFNV9tVkhqQ2l1VUM2SDZ0cFhhY2NTMFhNIiwidmVyIjoiMS4wIiwiemlwIjoiRGVmbGF0ZSIsInNlciI6IjEuMCJ9.QjGw8IeLroyGt_ISkEGqIBXn4yJm54mlc6RUqL9oq3uxGXGMNK91tyX0ndwlaWeXCqqk1SXd5KsBX2_hzQHzo__vKYhXYU47VWRM7i9OjRbvsRnVFCT1m5TpItfzB2kgn2Z0Rs3N_CiVeTcujo3H_L_knlECl6q7LHJ7mVp6bTc-5YHLngxSvTc02lbLFFjSKlCb9qej3RLgLbyx5xDysbLxQ8oRFFqPl5zKTtyAnwyLWECSwG79pLVTT_FbvbhTShtDlBmaSlqz7AtaKljRgo_7lCWmBNQOBTW6hGm4p8MU1x_MxcxsJdzdhTig-krcpvyU-ZX4m2biSoeO-FUeuA.2Zj-ruRCCCxbUAGl.D8-gUL9u8VgTtG9UQ9I-qb2_BbjvhALNA6B0gTYdilLru_fvPA3sJb3CnBoMi-NobeFxMREshSkHSeuxusuMh6JPwWXbls1B22-963CXTDHAziypGWv6qix3TqMw_SKmYWvffH2y19wH-zv1r60OvNxT-Jfpmx7QaNKJFU1-ESLJoNiWIVJetTfPG5PLiS_nd7blBhNBvzOcuEOIopQb4iMPZGqyz_gRPVbvMTvWcDT85c_--cZlrSfk0QWNyFPl1Dnnij_mD9LqbH-hWZ9BVY3EX1gkbAV2MpktEBl3awf2KtlPlsU34vdiPTEGdV42VmRqM0bMg0EoF57U_LxWTER8i85v8odAIzuTQF5sjzReNcTaRbuoI4eXtth9xnC-dy9vPWy19XQlbaKyvyRsNH45fM3DK-S15eiecj9eJ8dESzbY-YVTUIL6V7pxkOgImnt1wyixefh_mf4T49jvSRvvVDdDNZ30spnD9Iqau2nrSY4-V8pqe8RN81ljPbLta3QGXG3xGIrqItkHx20LKWfTe3H-7YAab_qONn3KNBpkX_HYC9m-wjHkrPU1pCsIUkp9K2SpfEMM5m80XdK1B5KYXvgejZg6hMIw57dKDYLfvNyO8WyiYuZasTkVdkee_r8mgcKuH9TcWeb074qgjBBMQd9c0LGRuFMOLn3JGLHu5L57vPb1TBJ3my_IcUQ4ixlM22pfI2ASgIy7ttvYdUNrURYkDYZN6zGdeTk2WKGehBUCSNKsnOH5k-g.KsywiNSbnEU8P2IKBQNgng",debug=debug)
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

userio.message("Aggregate all information...")
wholeNumbers=Efficiency.aggrEfficiency.copy()
for serial in Efficiency.aggrEfficiency.keys():
    wholeNumbers[serial].update(Capacity.aggrCapacity[serial])
    wholeNumbers[serial].update(Headroom.aggrHeadroom[serial])

#print(wholeNumbers)    

# Create HTML output
html_content = """
<!DOCTYPE html>
<html>
<head>
    <title>AIQ Get Results</title>
    <style>
        table {
            border-collapse: collapse;
            width: 100%;
            margin: 20px 0;
        }
        th, td {
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }
        th {
            background-color: #0066cc;
            color: white;
        }
        tr:nth-child(even) {
            background-color: #f2f2f2;
        }
    </style>
</head>
<body>
    <h1>AIQ Get Results</h1>
    <table>
"""

# Get all possible keys from all dictionaries to create headers
all_keys = set()
for serial_data in wholeNumbers.values():
    all_keys.update(serial_data.keys())

# Create table headers
html_content += "<tr><th>Serial Number</th>"
for key in sorted(all_keys):
    html_content += f"<th>{key}</th>"
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
output_file = customer+"_aiqget_results.html"

if os.path.exists(output_file):
    today_date = datetime.now().strftime('%d_%m_%Y_%H%M')
    new_name = f"aiqget_results_{today_date}.html"
    os.rename(output_file, new_name)
    userio.message(f"Existing file renamed to {new_name}")

with open(output_file, "w") as f:
    f.write(html_content)

userio.message(f"Results have been saved to {output_file}")