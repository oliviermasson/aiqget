#! /usr/bin/python3.12

import sys

sys.path.append(sys.path[0] + "/NTAPlib")
import time
import getopt
import json
import os
import doREST
from refreshToken import refreshToken
from getEfficiency import getEfficiency
from getCapacity import getCapacity
from getInformation import getInformation
from getHeadroom import getHeadroom
from getClientID import getClientID
from getProtocolsIOPS import getProtocolsIOPS
from getOverallIOPS import getOverallIOPS
from getBandwidth import getBandwidth
import userio
from datetime import datetime,timedelta
import re
from bs4 import BeautifulSoup  

# Fonction pour analyser le tableau HTML existant
def parse_existing_table(file_path):
    if not os.path.exists(file_path):
        return {}
    userio.message(f"Comparing results with previous file [{file_path}]...")
    with open(file_path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")

    table = soup.find("table")
    if not table:
        return {}

    data = {}
    headers = [th.text.strip() for th in table.find_all("th")]
    rows = table.find_all("tr")[1:]  # Ignorer la ligne des en-têtes

    for row in rows:
        cells = row.find_all("td")
        serial = cells[0].text.strip()
        data[serial] = {}
        for i, cell in enumerate(cells[1:], start=1):
            # Supprimer les variations entre crochets (e.g., [10%])
            value = re.sub(r"\[.*?\]", "", cell.text.strip()).strip()
            data[serial][headers[i]] = value

    return data

aiqget='1.0'

validoptions={'serialnumbers':'str',
              'refresh_Token':'str',
              'debug':'bool',
              'restdebug':'bool',
              'days':'int',
              'customer':'str',
              'customer_name':'str',
              'protoIOPS': 'bool',
              'bandwidth': 'bool',
              'previous_file': 'str',
              'overallIOPS': 'bool',
              'access_Token': 'str'}

#requiredoptions=['refreshToken']
#requiredoptions=['access_Token']
mutexoptions=['serialnumbers', 'customer_name']
dependentoptions={'customer':'serialnumbers'}

usage="Version " + aiqget + "\n" + \
      "aiqget --serialnumbers\n" + \
      "         (List of serial numbers provided as comma separeted list)\n" + \
      "         \n" + \
      "       --customer_name\n" + \
      "         (customer name from which we will retrieve all ontap serialnumbers)\n" + \
      "         (serialnumbers and customer_name are mutualy exclusive, you need to provide only one or the other\n" + \
      "         \n" + \
      "       --customer\n" + \
      "         (Required. Customer identifier that will be added as a prefix to the generated HTML file)\n\n" + \
      "       --refresh_Token\n" + \
      "         (Required. The refresh token for AIQ access)\n\n" + \
      "       [--days]\n" + \
      "         (optional. Number of days to compute all performances metrics average)\n" + \
      "         (Default to 31 days before current date)\n\n" + \
      "       [--previous_file]\n" + \
      "         (optional. previous generated HMTL report to compage actual values with)\n\n" + \
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

#myopts=userio.validateoptions(sys.argv,validoptions,usage=usage,required=requiredoptions,mutex=mutexoptions,dependent=dependentoptions)
myopts=userio.validateoptions(sys.argv,validoptions,usage=usage,mutex=mutexoptions,dependent=dependentoptions)

try:
    serialnumbers=myopts.serialnumbers.split(',')
except:
    serialnumbers=None

try:
    customer=myopts.customer
except:
    customer=None

try:
    customer_name=myopts.customer_name
except:
    customer_name=None

try:
    days=myopts.days
except:
    days=None
try:
    refresh_Token=myopts.refresh_Token
except:
    refresh_Token=None

try:
    access_Token=myopts.access_Token 
    tokens={'access_Token': access_Token} 
except:
    access_Token=None

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

try:
    previous_file = myopts.previous_file
    userio.message(f"previous_file passed {previous_file}")
except:
    previous_file = None

if customer is not None:
    if previous_file is None:
        if bandwidth or overallIOPS or protoIOPS:
            previous_file = customer+"_Perf_aiqget_results.html"
        else:
            previous_file = customer+"_aiqget_results.html"
        userio.message(f"previous_file generated {previous_file}")
else:
    if previous_file is None:
        if bandwidth or overallIOPS or protoIOPS:
            previous_file = customer_name+"_Perf_aiqget_results.html"
        else:
            previous_file = customer_name+"_aiqget_results.html"
        userio.message(f"previous_file generated {previous_file}")   

if(access_Token is None):
    userio.message("Refresh AIQ access token...")
    tokens=refreshToken("api.activeiq.netapp.com",refresh_Token=refresh_Token,debug=debug)
    if not tokens.go():
        tokens.showDebug()
else:
    userio.message("Using provided AIQ access_Token...")
    class tokens:

        def __init__(self,access_token):
            self.access_Token = access_token
    
    tokens=tokens(access_token=access_Token)

today=datetime.now().strftime('%Y-%m-%d')
before=(datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

if customer_name is not None:
    userio.message("Retrieve ClientID and associated ONTAP serialnumbers for customer [" + customer_name + "]...")
    ClientID=getClientID("api.activeiq.netapp.com",access_token=tokens.access_Token,customer_name=customer_name,debug=debug)
    if not ClientID.go():
        ClientID.showDebug()
        exit(1)
    serialnumbers=ClientID.listSerialNumbers

if(len(serialnumbers) == 0):
    userio.message("No serialnumbers provided, exiting...")
    exit(0)

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

userio.message("Retrieve Node Information...")
Information=getInformation("api.activeiq.netapp.com",access_token=tokens.access_Token,serialnumbers=serialnumbers,start=before,end=today,debug=debug)        
if not Information.go():
    Information.showDebug()

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
wholeNumbers=Capacity.aggrCapacity.copy()
for serial in Capacity.aggrCapacity.keys():
    try:
        wholeNumbers[serial].update(Headroom.aggrHeadroom[serial])
    except:
        userio.message(f"Warning: Headroom data not available for {serial}.")
    try:
        wholeNumbers[serial].update(Efficiency.aggrEfficiency[serial])
    except:
        userio.message(f"Warning: Efficiency data not available for {serial}.")
    try:
        wholeNumbers[serial].update(Information.aggrInformation[serial])
    except:
        userio.message(f"Warning: Information data not available for {serial}.")
    if protoIOPS:
        try:
            wholeNumbers[serial].update(ProtocolsIOPS.aggrProtoIOPS[serial])
        except:
            userio.message(f"Warning: Protocols IOPS data not available for {serial}.")
    if overallIOPS:
        try:
            wholeNumbers[serial].update(avgIOPS.aggrOverall[serial])
        except:
            userio.message(f"Warning: Overall IOPS data not available for {serial}.")
    if bandwidth:
        try:
            wholeNumbers[serial].update(avgBandwidth.aggrBandwidth[serial])
        except:
            userio.message(f"Warning: Bandwidth data not available for {serial}.")

#print(wholeNumbers)    

# Create HTML output
current_datetime = datetime.now().strftime('%d-%m-%Y %H:%M')

# Charger les données du tableau précédent si le fichier existe
previous_data = {}
compared_with = ""
if previous_file:
    if os.path.exists(previous_file):
        previous_data = parse_existing_table(previous_file) 
        file_time = os.path.getmtime(previous_file)
        creation_date = datetime.fromtimestamp(file_time).strftime('%d-%m-%Y %H:%M')
        compared_with=f" (compared with {previous_file} last modified on {creation_date})"

html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>AIQ Get Results - {current_datetime}{compared_with}</title>
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
        .positive {{
            color: green;
        }}
        .negative {{
            color: orange;
        }}
    </style>
    <script>
        function extractNumber(cellContent) {{
            let match = cellContent.replace(',', '.').match(/-?\d+(\.\d+)?/);
            return match ? parseFloat(match[0]) : NaN;
        }}

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

                    let xNum = extractNumber(xContent);
                    let yNum = extractNumber(yContent);
                    if (!isNaN(xNum) && !isNaN(yNum)) {{
                        xContent = xNum;
                        yContent = yNum;
                    }} else {{
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
    <h1>AIQ Get Results - {current_datetime}{compared_with}</h1>
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

# Ajouter les lignes de données avec comparaison
for serial, data in wholeNumbers.items():
    html_content += f"<tr><td>{serial}</td>"
    for key in sorted(all_keys):
        current_value = data.get(key, "N/A")
        previous_value = previous_data.get(serial, {}).get(key, None)

        # Comparer les colonnes spécifiées
        if key not in ["Serial Number", "clusterName", "hostName", "effRatio", "model", "release", "site_name"] and previous_value is not None:
            try:
                # Convertir les valeurs en float pour la comparaison
                current_value_float = float(current_value)
                previous_value_float = float(previous_value)

                # Calculer la variation en pourcentage
                try:
                    variation = ((current_value_float - previous_value_float) / previous_value_float) * 100
                except:
                    variation = 0

                # Formater la variation avec une couleur
                if variation > 0:
                    variation_html = f'<span class="positive">[+{variation:.2f}%]</span>'
                else:
                    variation_html = f'<span class="negative">[{variation:.2f}%]</span>'

                # Ajouter la variation à la valeur actuelle
                if variation != 0:
                    html_content += f"<td>{current_value} {variation_html}</td>"
                else:
                    html_content += f"<td>{current_value}</td>"
            except ValueError:
                # Si la conversion échoue, afficher uniquement la valeur actuelle
                html_content += f"<td>{current_value}</td>"
        else:
            # Pas de comparaison, afficher uniquement la valeur actuelle
            html_content += f"<td>{current_value}</td>"
    html_content += "</tr>"

html_content += """
    </table>
</body>
</html>
"""

# Write the HTML file
if customer_name is not None:
    customer = customer_name
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

