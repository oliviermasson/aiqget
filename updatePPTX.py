from pptx import Presentation
from pptx.util import Pt
import copy
import six
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE_TYPE
from bs4 import BeautifulSoup
import os
from datetime import datetime

def parse_percentage(text):
    try:
        # Récupère uniquement le premier nombre dans la chaîne
        import re
        match = re.search(r'^(\d+\.?\d*)', text.strip())
        if match:
            # Convertit en float le premier groupe capturé
            return float(match.group(1))
        return None
    except (ValueError, AttributeError):
        # En cas d'erreur, retourne None
        return None
    
def add_new_slide(pres, date, new_ppt_path=None):
    # on recopie la derniere slide présente car c'est toujours la up to date slide
    source_slide = pres.slides[-1]

    # Blank slide layout is usually the last layout in the list
    try:
        blank_slide_layout = pres.slide_layouts[-1]
    except:
        blank_slide_layout = pres.slide_layouts[len(pres.slide_layouts)]

    new_slide = pres.slides.add_slide(blank_slide_layout)

    import io

    for shape in source_slide.shapes:
        el = shape.element
        if not "image" in dir(shape): 
            newel = copy.deepcopy(el)
            new_slide.shapes._spTree.insert_element_before(newel, 'p:extLst')
            #print(f"Shape copied: {shape.name}")
            #pres.save(new_ppt_path)
        if "image" in dir(shape):
            img = io.BytesIO(shape.image.blob)
            new_shape_img = new_slide.shapes.add_picture(image_file = img,
                                            left = shape.left,
                                            top = shape.top,
                                            width = shape.width,
                                            height = shape.height)
            new_shape_img.name = shape.name
            #print(f"Image copied: {shape.name}")
            
    for shape in new_slide.shapes:
        if shape.name == "date_slide":
            if shape.text_frame.paragraphs[0].font.size:
                font_size = shape.text_frame.paragraphs[0].font.size
            else:
                font_size = Pt(12)   
            shape.text_frame.text = str(date)
            shape.text_frame.paragraphs[0].font.size = font_size
            shape.text_frame.paragraphs[0].font.bold = True
            shape.text_frame.paragraphs[0].font.color.rgb = RGBColor(0, 0, 0)
    
    # We need to copy the relationships from the source slide to the new slide

    for _, value in six.iteritems(source_slide.part.rels):
        # Make sure we don't copy a notesSlide relation as that won't exist
        if "notesSlide" not in value.reltype:
            new_slide.part.rels.get_or_add(
                value.reltype,
                value._target
            )

    return new_slide

def modif_textbox(shape,value,textvalue,warning,error):
    if shape.text_frame.paragraphs[0].font.size:
        font_size = shape.text_frame.paragraphs[0].font.size
    else:
        font_size = Pt(6)  
    shape.text_frame.text = str(textvalue+'%')
    shape.text_frame.paragraphs[0].font.size = font_size
    color_text = None
    if not value == None:
        if value >=warning:
            color_text= RGBColor(255, 255, 0)  # Yellow
        if value >=error:    
            color_text= RGBColor(192, 0, 0)  # Dark Red
        shape.text_frame.paragraphs[0].font.bold = True
        if color_text:
            shape.text_frame.paragraphs[0].font.color.rgb = color_text    

def update_ppt_from_html(ppt_path, html_path, slide_index=0):
    # Charger la présentation PowerPoint
    prs = Presentation(ppt_path)
    
    # Lire et parser le fichier HTML
    with open(html_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # Recuperer la date de modification du fichier HTML
    file_time = os.path.getmtime(html_path)
    file_date = datetime.fromtimestamp(file_time).strftime('%m/%d/%Y')

    # Enregistrer les modifications
    #new_ppt_path = ppt_path.replace('.pptx', '_updated.pptx')
    

    # Ajouter une nouvelle slide pour la date de modification
    #new_slide = add_new_slide(prs, file_date, new_ppt_path)
    new_slide = add_new_slide(prs, file_date, ppt_path)
   
    # Parser le contenu HTML pour trouver le tableau
    soup = BeautifulSoup(html_content, 'html.parser')
    table = soup.find('table')
    
    # Vérifier si un tableau a été trouvé
    if not table:
        raise ValueError("Aucun tableau trouvé dans le fichier HTML")
    
    # Parcourir les lignes du tableau
    for row in table.find_all('tr'):
        if row.next.name == 'th':
            continue        
        cells = row.find_all(['td', 'th'])
        
        # Vérifier qu'il y a au moins 11 colonnes
        if len(cells) >= 11:
            nodename = cells[4].get_text().strip()
            capacity_percentage = cells[2].get_text().strip()
            headroom_percentage = cells[9].get_text().strip()
            float_value_capacity = parse_percentage(capacity_percentage)
            float_value_headroom = parse_percentage(headroom_percentage)
            
            # Rechercher la TextBox correspondante et mettre à jour le texte si necessaire
            for shape in new_slide.shapes:
                #print(f"Shape found: {shape.name}")
                if shape.shape_type == MSO_SHAPE_TYPE.GROUP:
                    #print("Shape is a group, digging deeper...")
                    for sub_shape in shape.shapes:
                        #print(f"\tSub Shape found: {sub_shape.name}")
                        if sub_shape.name == str("capacity_" + nodename) and sub_shape.has_text_frame:
                            sub_shape_value = parse_percentage(sub_shape.text_frame.text)
                            if sub_shape_value != float_value_capacity:
                                modif_textbox(sub_shape, float_value_capacity, str(float_value_capacity), 70, 80)
                                print(f"\tUpdate capacity: {nodename} from {str(sub_shape_value)}% => {str(float_value_capacity)}%")
                            break
                        if sub_shape.name == str("headroom_" + nodename) and sub_shape.has_text_frame:
                            sub_shape_value = parse_percentage(sub_shape.text_frame.text)
                            if sub_shape_value != float_value_headroom:
                                modif_textbox(sub_shape, float_value_headroom, str(float_value_headroom), 80, 90)
                                print(f"\tUpdate headroom: {nodename} from {str(sub_shape_value)}% => {str(float_value_headroom)}%")
                            break
                if shape.name == str("capacity_" + nodename) and shape.has_text_frame:
                    shape_value = parse_percentage(shape.text_frame.text)
                    if shape_value != float_value_capacity:
                        modif_textbox(shape, float_value_capacity, str(float_value_capacity), 70, 80)
                        print(f"Update capacity: {nodename} from {str(shape_value)}% => {str(float_value_capacity)}%")
                    break
                if shape.name == str("headroom_" + nodename) and shape.has_text_frame:
                    shape_value = parse_percentage(shape.text_frame.text)
                    if shape_value != float_value_headroom:
                        modif_textbox(shape, float_value_headroom, str(float_value_headroom), 80, 90)
                        print(f"Update headroom: {nodename} from {str(shape_value)}% => {str(float_value_headroom)}%")
                    break
        else:
            print(f"row ignored, less than 11 columns: {row.get_text(strip=True)}")
    
    prs.save(ppt_path)
    print(f"\nPresentation updated and saved as: {ppt_path}")

# Exemple d'utilisation
if __name__ == "__main__":
    ppt_file = "/mnt/c/Users/masson/OneDrive - NetApp Inc/Client/CNP/Etat des lieux/test_automation.pptx"  # Chemin vers votre fichier PowerPoint
    html_file = "/mnt/c/Users/masson/OneDrive - NetApp Inc/GitHub/aiqget/CNP_aiqget_results.html"          # Chemin vers votre fichier HTML
    
    update_ppt_from_html(ppt_file, html_file, slide_index=0)
