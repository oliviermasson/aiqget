import sys

sys.path.append(sys.path[0] + "/NTAPlib")
import time
import getopt
import json
import os
import doREST
import doGRAPHQL
from refreshToken import refreshToken
from getEfficiency import getEfficiency
from getCapacity import getCapacity
from getClusterviewCapacity import getClusterviewCapacity
from getEseriesCapacity import getEseriesCapacity
from getEseriesInformation import getEseriesInformation
from getStorageGridInformation import getStorageGridInformation
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

aiqget='1.11'

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
              'clusterviewmode': 'bool',
              'access_Token': 'str'}

print(f"Running aiqget version {aiqget}\n")

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
if myopts.debug:
    debug=debug+1

if myopts.restdebug:
    debug=debug+2

try:
    clusterviewmode=myopts.clusterviewmode
except:
    clusterviewmode=False
    
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

# recherche le clientID et les serialnumbers associés à un cutomer_name
# pour l'instant serialnumbers ONTAP seulement...voir pour rajouter E-series et StorageGRID
if customer_name is not None:
    userio.message("Retrieve ClientID and associated ONTAP serialnumbers for customer [" + customer_name + "]...")
    ClientID=getClientID("api.activeiq.netapp.com",access_token=tokens.access_Token,customer_name=customer_name,debug=debug)
    if not ClientID.go():
        ClientID.showDebug()
        exit(1)
    serialnumbers=ClientID.listSerialNumbers
    serialnumbersEseries=ClientID.listSerialNumbersEseries
    serialnumbersStorageGrid=ClientID.listSerialNumbersStorageGrid
else:
    serialnumbersEseries=[]
    serialnumbersStorageGrid=[]

if(len(serialnumbers) == 0):
    userio.message("No Ontap serialnumbers provided, exiting...")

if(len(serialnumbersEseries) == 0):
    userio.message("No E-series serialnumbers provided, exiting...")
    
if(len(serialnumbersStorageGrid) == 0):
    userio.message("No StorageGRID serialnumbers provided, exiting...")

if (len(serialnumbers) == 0 and len(serialnumbersEseries) == 0 and len(serialnumbersStorageGrid) == 0):
    userio.message("No serialnumbers provided, exiting...")
    exit(1)

if(len(serialnumbersEseries) > 0):
    userio.message("Retrieve E-series Capacity...")
    EseriesCapacity=getEseriesCapacity("gql.aiq.netapp.com",access_token=tokens.access_Token,serialnumbers=serialnumbersEseries,debug=debug)
    if not EseriesCapacity.go():
        EseriesCapacity.showDebug()
        
    userio.message("Retrieve E-series Information... ")
    EseriesInformation=getEseriesInformation("gql.aiq.netapp.com",access_token=tokens.access_Token,serialnumbers=serialnumbersEseries,debug=debug)
    if not EseriesInformation.go():
        EseriesInformation.showDebug()

if(len(serialnumbersStorageGrid) > 0):
    userio.message("Retrieve StorageGRID Information...")
    StorageGridInformation=getStorageGridInformation("gql.aiq.netapp.com",access_token=tokens.access_Token,serialnumbers=serialnumbersStorageGrid,detailSG=ClientID.DetailsStorageGrid,debug=debug)
    if not StorageGridInformation.go():
        StorageGridInformation.showDebug()

      
# recuperation des valeurs d'efficiency
userio.message("Retrieve ONTAP Efficiency information...")
Efficiency=getEfficiency("api.activeiq.netapp.com",access_token=tokens.access_Token,serialnumbers=serialnumbers,debug=debug)
if not Efficiency.go():
    Efficiency.showDebug()

# recuperation des valeurs de capacity
userio.message("Retrieve ONTAP Node information...")
Capacity=getCapacity("api.activeiq.netapp.com",access_token=tokens.access_Token,serialnumbers=serialnumbers,clusterviewmode=clusterviewmode,debug=debug)        
if not Capacity.go():
    Capacity.showDebug()
    

# recuperation des capacity aggr via Cluster view API
# les valeurs sont plus fiables et correspondent exactement à ce qui est visible dans AGGR_INFO.XML
# que ce soit les chiffres de clusterview ou de capacity ils s'appuient tous les 2 sur le weekly asup
# donc a moins que le client ne genere un nouvel asup complet, les informations de capacité ne seront calculées qu'une fois par semaine
if clusterviewmode:
    userio.message("Retrieve ONTAP Clusterview Capacity information...")
    ClusterviewCapacity=getClusterviewCapacity("api.activeiq.netapp.com",access_token=tokens.access_Token,serialnumbers=serialnumbers,debug=debug)        
    if not ClusterviewCapacity.go():
        ClusterviewCapacity.showDebug()

# recuperation des valeurs du headroom CPU
userio.message("Retrieve ONTAP Headroom information...")
Headroom=getHeadroom("api.activeiq.netapp.com",access_token=tokens.access_Token,serialnumbers=serialnumbers,start=before,end=today,debug=debug)        
if not Headroom.go():
    Headroom.showDebug()

# recuperation des informations sur les nodes
userio.message("Retrieve ONTAP Node Information...")
Information=getInformation("api.activeiq.netapp.com",access_token=tokens.access_Token,serialnumbers=serialnumbers,start=before,end=today,debug=debug)        
if not Information.go():
    Information.showDebug()

# recuperation des valeurs de IOPS par protocol
if protoIOPS:
    userio.message("Retrieve ONTAP Protocols IOPS information...")
    ProtocolsIOPS=getProtocolsIOPS("api.activeiq.netapp.com",access_token=tokens.access_Token,serialnumbers=serialnumbers,start=before,end=today,debug=debug)        
    if not ProtocolsIOPS.go():
        ProtocolsIOPS.showDebug()

# recuperation des valeurs de IOPS globales
if overallIOPS:
    userio.message("Retrieve ONTAP avg IOPS information...")
    avgIOPS=getOverallIOPS("api.activeiq.netapp.com",access_token=tokens.access_Token,serialnumbers=serialnumbers,start=before,end=today,debug=debug)        
    if not avgIOPS.go():
        avgIOPS.showDebug()

# recuperation des valeurs de bande passante
if bandwidth:
    userio.message("Retrieve ONTAP Bandwidth information...")
    avgBandwidth=getBandwidth("api.activeiq.netapp.com",access_token=tokens.access_Token,serialnumbers=serialnumbers,start=before,end=today,debug=debug)        
    if not avgBandwidth.go():
        avgBandwidth.showDebug()

# assemblage de toutes les informations par serial number
userio.message("Aggregate all information...")
if clusterviewmode:
    wholeNumbers=ClusterviewCapacity.aggrClusterviewCapacity.copy()
    seriallist=list(ClusterviewCapacity.aggrClusterviewCapacity.keys())
else:
    wholeNumbers=Capacity.aggrCapacityNode.copy()
    seriallist=list(Capacity.aggrCapacityNode.keys())

for serial in seriallist:
    try:
        wholeNumbers[serial].update(Headroom.aggrHeadroom[serial])
    except:
        userio.message(f"Warning: ONTAP Headroom data not available for {serial}.")
        wholeNumbers[serial].update({'avgCPUheadroom%': 'unknow'})
        
    if clusterviewmode:
        try:
            wholeNumbers[serial].update(Capacity.aggrCapacityNode[serial])
        except:
            userio.message(f"Warning: ONTAP Capacity data not available for {serial}.")
    
    try:
        wholeNumbers[serial].update(Efficiency.aggrEfficiency[serial])
    except:
        userio.message(f"Warning: ONTAP Efficiency data not available for {serial}.")
        wholeNumbers[serial].update({'effRatio': 'unknow'})
        
    try:
        wholeNumbers[serial].update(Information.aggrInformation[serial])
    except:
        userio.message(f"Warning: ONTAP Information data not available for {serial}.")
        wholeNumbers[serial].update({'Site_Name': 'unknow', 'Model': 'unknow'})
        
    if protoIOPS:
        try:
            wholeNumbers[serial].update(ProtocolsIOPS.aggrProtoIOPS[serial])
        except:
            userio.message(f"Warning: ONTAP Protocols IOPS data not available for {serial}.")
    if overallIOPS:
        try:
            wholeNumbers[serial].update(avgIOPS.aggrOverall[serial])
        except:
            userio.message(f"Warning: ONTAP Overall IOPS data not available for {serial}.")
    if bandwidth:
        try:
            wholeNumbers[serial].update(avgBandwidth.aggrBandwidth[serial])
        except:
            userio.message(f"Warning: ONTAP Bandwidth data not available for {serial}.")

if len(serialnumbersEseries) > 0:
    wholeNumbers.update(EseriesCapacity.aggrECapacity)
    for serial in EseriesCapacity.aggrECapacity.keys():
        try:
            wholeNumbers[serial].update(ClientID.serialnumbers.DetailsEseries[serial])
        except:
            userio.message(f"Warning: E-series Details data not available for {serial}.")
            wholeNumbers[serial].update({'Model': 'unknow', 'Release': 'unknow', 'HostName': 'unknow'})
        try:
            wholeNumbers[serial].update(EseriesInformation.aggrEInformation[serial])
        except:
            userio.message(f"Warning: E-series Information data not available for {serial}.")
            wholeNumbers[serial].update({'Site_Name': 'unknow', 'AgeInYears': 'unknow'})

if len(serialnumbersStorageGrid) > 0:
    wholeNumbers.update(StorageGridInformation.aggrSGInformation)

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
        th.filtered::after {{
            content: '🔍';
            position: absolute;
            right: 8px;
            color: white;
        }}
        .reset-filter {{
            margin: 10px 0;
            padding: 8px 12px;
            background-color: #0066cc;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
        }}
        .reset-filter:hover {{
            background-color: #0055aa;
        }}
        /* Styles pour le filtre dropdown */
        .dropdown-filter {{
            position: relative;
            display: inline-block;
        }}

        .dropdown-content {{
            display: none;
            position: absolute;
            background-color: white;
            min-width: 200px;
            max-height: 300px;
            overflow-y: auto;
            box-shadow: 0px 8px 16px 0px rgba(0,0,0,0.2);
            z-index: 1000;
            border: 1px solid #ddd;
            border-radius: 4px;
        }}

        .dropdown-content label {{
            display: block;
            padding: 8px 12px;
            cursor: pointer;
            color: black;
            font-weight: normal;
        }}

        .dropdown-content label:hover {{
            background-color: #f1f1f1;
        }}

        .dropdown-content input[type="checkbox"] {{
            margin-right: 8px;
        }}

        .filter-actions {{
            padding: 8px 12px;
            border-top: 1px solid #ddd;
            background-color: #f9f9f9;
        }}

        .filter-btn {{
            padding: 4px 8px;
            margin: 2px;
            background-color: #0066cc;
            color: white;
            border: none;
            border-radius: 3px;
            cursor: pointer;
            font-size: 12px;
        }}

        .filter-btn:hover {{
            background-color: #0055aa;
        }}

        .show {{
            display: block;
        }}
    </style>
    <script>
        let modelFilterActive = false;
        let hostNameFilterActive = false;
        let activeHostNameFilter = "";

        function showModelFilter(event) {{{{
            event.stopPropagation();
            let dropdown = document.getElementById("modelDropdownContent");
            
            if (!dropdown) {{{{
                console.log("Dropdown not found");
                return;
            }}}}
            
            if (!dropdown.classList.contains("show")) {{{{
                populateModelFilter();
                dropdown.classList.add("show");
            }}}} else {{{{
                dropdown.classList.remove("show");
            }}}}
        }}}}

        function populateModelFilter() {{{{
            const table = document.querySelector("table");
            const rows = table.getElementsByTagName("tr");
            const headerCells = rows[0].getElementsByTagName("th");
            
            // Recherche plus flexible de la colonne Model
            let modelIndex = -1;
            for (let i = 0; i < headerCells.length; i++) {{{{
                const headerText = headerCells[i].textContent.trim().toLowerCase();
                if (headerText.includes("model")) {{{{
                    modelIndex = i;
                    break;
                }}}}
            }}}}

            if (modelIndex === -1) return;
            
            // Collecter tous les modèles uniques
            const models = new Set();
            for (let i = 1; i < rows.length; i++) {{{{
                const modelCell = rows[i].getElementsByTagName("td")[modelIndex];
                if (modelCell) {{{{
                    let modelText = modelCell.textContent.trim();
                    // Nettoyer le texte (supprimer les variations si nécessaire)
                    modelText = modelText.replace(/\\[.*?\\]/g, '').trim();
                    if (modelText && modelText !== 'N/A' && modelText !== 'unknow') {{{{
                        models.add(modelText);
                    }}}}
                }}}}
            }}}}

            // Créer les options du dropdown
            const dropdown = document.getElementById("modelDropdownContent");
            dropdown.innerHTML = '';
            
            // Ajouter les checkboxes pour chaque modèle
            const sortedModels = Array.from(models).sort();
            sortedModels.forEach(model => {{{{
                const label = document.createElement('label');
                label.innerHTML = `
                    <input type="checkbox" value="${{model}}">
                    ${{model}}
                `;
                dropdown.appendChild(label);
            }}}});
            
            // Ajouter les boutons d'action
            const actions = document.createElement('div');
            actions.className = 'filter-actions';
            actions.innerHTML = `
                <button class="filter-btn" onclick="selectAllModels(event)">Select All</button>
                <button class="filter-btn" onclick="clearAllModels(event)">Clear All</button>
                <button class="filter-btn" onclick="applyModelFilterAndClose(event)">Apply Filter</button>
                <button class="filter-btn" onclick="closeModelFilter(event)">Cancel</button>
            `;
            dropdown.appendChild(actions);

            // Ajouter des gestionnaires d'événements pour empêcher la propagation des clics
            dropdown.addEventListener('click', function(event) {{{{
                event.stopPropagation();
            }}}});

            // Restaurer les sélections précédentes si elles existent
            restorePreviousModelSelections();
        }}}}

        function restorePreviousModelSelections() {{{{
            // Vérifier si un filtre modèle est actif
            if (!modelFilterActive) return;

            const table = document.querySelector("table");
            const rows = table.getElementsByTagName("tr");
            const headerCells = rows[0].getElementsByTagName("th");
            
            // Trouver l'index de la colonne Model
            let modelIndex = -1;
            for (let i = 0; i < headerCells.length; i++) {{{{
                if (headerCells[i].textContent.trim().toLowerCase().includes("model")) {{{{
                    modelIndex = i;
                    break;
                }}}}
            }}}}

            if (modelIndex === -1) return;

            // Collecter les modèles actuellement visibles
            const visibleModels = new Set();
            for (let i = 1; i < rows.length; i++) {{{{
                if (rows[i].style.display !== "none") {{{{
                    const modelCell = rows[i].getElementsByTagName("td")[modelIndex];
                    if (modelCell) {{{{
                        let modelText = modelCell.textContent.trim().replace(/\\[.*?\\]/g, '').trim();
                        visibleModels.add(modelText);
                    }}}}
                }}}}
            }}}}

            // Pré-sélectionner les checkboxes correspondantes
            const checkboxes = document.querySelectorAll('#modelDropdownContent input[type="checkbox"]');
            checkboxes.forEach(checkbox => {{{{
                if (visibleModels.has(checkbox.value)) {{{{
                    checkbox.checked = true;
                }}}}
            }}}});
        }}}}

        function selectAllModels(event) {{{{
            if (event) event.stopPropagation();
            const checkboxes = document.querySelectorAll('#modelDropdownContent input[type="checkbox"]');
            checkboxes.forEach(checkbox => {{{{
                checkbox.checked = true;
            }}}});
        }}}}

        function clearAllModels(event) {{{{
            if (event) event.stopPropagation();
            const checkboxes = document.querySelectorAll('#modelDropdownContent input[type="checkbox"]');
            checkboxes.forEach(checkbox => {{{{
                checkbox.checked = false;
            }}}});
        }}}}

        function applyModelFilterAndClose(event) {{{{
            if (event) event.stopPropagation();
            applyAllFilters();
            closeModelFilter();
        }}}}

        function closeModelFilter(event) {{{{
            if (event) event.stopPropagation();
            const dropdown = document.getElementById("modelDropdownContent");
            if (dropdown) {{{{
                dropdown.classList.remove("show");
            }}}}
        }}}}

        function filterByHostName() {{{{
            const searchValue = prompt("Filter by HostName (leave empty to reset filter):");
            if (searchValue === null) return; // L'utilisateur a annulé
            
            activeHostNameFilter = searchValue || "";
            applyAllFilters();
        }}}}

        function applyAllFilters() {{{{
            const table = document.querySelector("table");
            const rows = table.getElementsByTagName("tr");
            const headerCells = rows[0].getElementsByTagName("th");
            
            // Recherche flexible des colonnes
            let modelIndex = -1;
            let hostNameIndex = -1;
            
            for (let i = 0; i < headerCells.length; i++) {{{{
                const headerText = headerCells[i].textContent.trim().toLowerCase();
                if (headerText.includes("model")) {{{{
                    modelIndex = i;
                }}}}
                if (headerText.includes("hostname")) {{{{
                    hostNameIndex = i;
                }}}}
            }}}}
            
            // Obtenir les modèles sélectionnés
            const modelCheckboxes = document.querySelectorAll('#modelDropdownContent input[type="checkbox"]:checked');
            const selectedModels = Array.from(modelCheckboxes).map(cb => cb.value);
            
            let visibleCount = 0;
            
            // Appliquer tous les filtres combinés
            for (let i = 1; i < rows.length; i++) {{{{
                const row = rows[i];
                let showRow = true;
                
                // Filtre par modèle
                if (modelIndex !== -1 && selectedModels.length > 0) {{{{
                    const modelCell = row.getElementsByTagName("td")[modelIndex];
                    if (modelCell) {{{{
                        let modelText = modelCell.textContent.trim().replace(/\\[.*?\\]/g, '').trim();
                        if (!selectedModels.includes(modelText)) {{{{
                            showRow = false;
                        }}}}
                    }}}}
                }}}}
                
                // Filtre par hostname
                if (hostNameIndex !== -1 && activeHostNameFilter !== "") {{{{
                    const hostNameCell = row.getElementsByTagName("td")[hostNameIndex];
                    if (hostNameCell) {{{{
                        if (!hostNameCell.textContent.toLowerCase().includes(activeHostNameFilter.toLowerCase())) {{{{
                            showRow = false;
                        }}}}
                    }}}}
                }}}}
                
                // Appliquer la visibilité
                if (showRow) {{{{
                    row.style.display = "";
                    visibleCount++;
                }}}} else {{{{
                    row.style.display = "none";
                }}}}
            }}}}
            
            // Mettre à jour les indicateurs visuels
            updateFilterIndicators(selectedModels, modelIndex, hostNameIndex, headerCells);
        }}}}

        function updateFilterIndicators(selectedModels, modelIndex, hostNameIndex, headerCells) {{{{
            // Reset all filter indicators
            for (let i = 0; i < headerCells.length; i++) {{{{
                headerCells[i].classList.remove("filtered");
            }}}}
            
            // Model filter indicator
            if (modelIndex !== -1 && selectedModels.length > 0) {{{{
                const totalModels = document.querySelectorAll('#modelDropdownContent input[type="checkbox"]').length;
                if (selectedModels.length < totalModels) {{{{
                    headerCells[modelIndex].classList.add("filtered");
                    modelFilterActive = true;
                }}}} else {{{{
                    modelFilterActive = false;
                }}}}
            }}}} else {{{{
                modelFilterActive = false;
            }}}}
            
            // HostName filter indicator
            if (hostNameIndex !== -1 && activeHostNameFilter !== "") {{{{
                headerCells[hostNameIndex].classList.add("filtered");
                hostNameFilterActive = true;
            }}}} else {{{{
                hostNameFilterActive = false;
            }}}}
        }}}}

        function resetAllFilters() {{{{
            // Reset model filter
            const checkboxes = document.querySelectorAll('#modelDropdownContent input[type="checkbox"]');
            checkboxes.forEach(checkbox => {{{{
                checkbox.checked = false;
            }}}});
            
            // Reset hostname filter
            activeHostNameFilter = "";
            
            // Reset filter states
            modelFilterActive = false;
            hostNameFilterActive = false;
            
            // Apply filters (will show all rows)
            applyAllFilters();
            
            closeModelFilter();
        }}}}

        function resetFilter() {{{{
            resetAllFilters();
        }}}}

        function testFilters() {{{{
            console.log("=== DEBUG INFO ===");
            const table = document.querySelector("table");
            const rows = table.getElementsByTagName("tr");
            const headerCells = rows[0].getElementsByTagName("th");
            
            console.log("Table found:", !!table);
            console.log("Rows count:", rows.length);
            console.log("Headers count:", headerCells.length);
            
            for (let i = 0; i < headerCells.length; i++) {{{{
                console.log(`Header ${{i}}: "${{headerCells[i].textContent.trim()}}"`);
            }}}}
            
            const dropdown = document.getElementById("modelDropdownContent");
            console.log("Dropdown found:", !!dropdown);
            
            const checkboxes = document.querySelectorAll('#modelDropdownContent input[type="checkbox"]');
            console.log("Checkboxes count:", checkboxes.length);
            console.log("Selected models:", Array.from(document.querySelectorAll('#modelDropdownContent input[type="checkbox"]:checked')).map(cb => cb.value));
        }}}}

        // Fermer le dropdown et appliquer le filtre si on clique ailleurs
        document.addEventListener('click', function(event) {{{{
            const dropdown = document.getElementById("modelDropdownContent");
            if (!dropdown) return;
            
            const isClickInsideDropdown = dropdown.contains(event.target);
            const isClickOnHeader = event.target.closest('th') && 
                                  event.target.closest('th').textContent.toLowerCase().includes('model');

            if (!isClickInsideDropdown && !isClickOnHeader && dropdown.classList.contains("show")) {{{{
                // Fermer sans appliquer le filtre
                dropdown.classList.remove("show");
            }}}}
        }}}});

        function extractNumber(cellContent) {{{{
            let match = cellContent.replace(',', '.').match(/-?\\d+(\\.\\d+)?/);
            return match ? parseFloat(match[0]) : NaN;
        }}}}

        function sortTable(n) {{{{
            var table, rows, switching, i, x, y, shouldSwitch, dir, switchcount = 0;
            table = document.querySelector("table");
            switching = true;
            dir = "asc";
            
            // Remove sorting indicators from all headers
            var headers = table.getElementsByTagName("th");
            for (i = 0; i < headers.length; i++) {{{{
                headers[i].classList.remove("asc", "desc");
            }}}}  
            
            // Add sorting indicator to clicked header
            headers[n].classList.add(dir);
            
            while (switching) {{{{
                switching = false;
                rows = table.rows;
                
                for (i = 1; i < (rows.length - 1); i++) {{{{
                    shouldSwitch = false;
                    x = rows[i].getElementsByTagName("td")[n];
                    y = rows[i + 1].getElementsByTagName("td")[n];
                    
                    // Convert to number if possible and handle decimal numbers
                    let xContent = x.innerHTML.trim();
                    let yContent = y.innerHTML.trim();

                    let xNum = extractNumber(xContent);
                    let yNum = extractNumber(yContent);
                    if (!isNaN(xNum) && !isNaN(yNum)) {{{{
                        xContent = xNum;
                        yContent = yNum;
                    }}}} else {{{{
                        xContent = xContent.toLowerCase();
                        yContent = yContent.toLowerCase();
                    }}}}

                    if (dir == "asc") {{{{
                        if (xContent > yContent) {{{{
                            shouldSwitch = true;
                            break;
                        }}}}
                    }}}} else if (dir == "desc") {{{{
                        if (xContent < yContent) {{{{
                            shouldSwitch = true;
                            break;
                        }}}}
                    }}}}
                }}}}
                
                if (shouldSwitch) {{{{
                    rows[i].parentNode.insertBefore(rows[i + 1], rows[i]);
                    switching = true;
                    switchcount++;
                }}}} else {{{{
                    if (switchcount == 0 && dir == "asc") {{{{
                        dir = "desc";
                        headers[n].classList.remove("asc");
                        headers[n].classList.add("desc");
                        switching = true;
                    }}}}
                }}}}
            }}}}
        }}}}

        window.testFilters = testFilters;
    </script>
</head>
<body>
    <h1>AIQ Get Results - {current_datetime}{compared_with}</h1>
    <table>
"""

# Get all possible keys from all dictionaries to create headers
all_keys = set()
#print("Colonnes disponibles:", sorted(all_keys))
for serial_data in wholeNumbers.values():
    all_keys.update(serial_data.keys())


html_content += '''
    <div>
        <button class="reset-filter" onclick="resetAllFilters()">Reset All Filters</button>
    </div>
'''

# Create table headers
html_content += "<tr>"
html_content += '<th onclick="sortTable(0)">Serial Number</th>'
column_index = 1
for key in sorted(all_keys):
    if key == "HostName":
        html_content += f'<th onclick="filterByHostName()">{key}</th>'
    elif key == "Model":
        html_content += f'''<th onclick="showModelFilter(event)">{key}
            <div id="modelDropdown" class="dropdown-filter">
                <div id="modelDropdownContent" class="dropdown-content">
                </div>
            </div>
        </th>'''
    else:
        html_content += f'<th onclick="sortTable({column_index})">{key}</th>'
    column_index += 1
html_content += "</tr>"

# Ajouter les lignes de données avec comparaison
for serial, data in wholeNumbers.items():
    html_content += f"<tr><td>{serial}</td>"
    for key in sorted(all_keys):
        try:
            current_value = round(float(data.get(key, "N/A")),2)
        except (ValueError, TypeError):
            current_value = data.get(key, "N/A")
        try:
            previous_value = round(float(previous_data.get(serial, {}).get(key, None)),2)
        except (ValueError, TypeError):
            previous_value = previous_data.get(serial, {}).get(key, None)

        # Comparer les colonnes spécifiées
        if key not in ["Serial Number", "clusterName", "hostName", "effRatio", "model", "release", "site_name"] and previous_value is not None:
            try:
                # Convertir les valeurs en float pour la comparaison
                current_value_float = round(float(current_value),2)
                previous_value_float = round(float(previous_value),2)

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
        file_time = os.path.getmtime(output_file)
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

