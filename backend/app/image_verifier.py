from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS

def get_exif_data(image_path):
    """Extract EXIF data including GPS coordinates and timestamp."""
    image = Image.open(image_path)
    exif_data = image._getexif()
    if not exif_data:
        return {"error": "No EXIF metadata found"}
    
    extracted = {}
    for tag, value in exif_data.items():
        tag_name = TAGS.get(tag, tag)
        if tag_name == "GPSInfo":
            gps_data = {}
            for gps_tag in value:
                sub_tag = GPSTAGS.get(gps_tag, gps_tag)
                gps_data[sub_tag] = value[gps_tag]
            extracted["GPSInfo"] = gps_data
        else:
            extracted[tag_name] = value
            
    return extracted