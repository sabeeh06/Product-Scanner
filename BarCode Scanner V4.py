import cv2
from pyzbar.pyzbar import decode
import sys
import urllib.request
import pprint
import json

class BarCode_Scanner():
    def __init__(self,Camera_Index = 0):
        self.cam = cv2.VideoCapture(Camera_Index)
        if not self.cam.isOpened():
            print("Error: Could not open camera.")
            sys.exit(1)

    def run(self):
        while self.cam.isOpened():
            suceess,frame = self.cam.read()
            frame = cv2.flip(frame,1)
            if not suceess:
                print("Warning: couldn't grab a frame")
                break

            barcodes = decode(frame)

            if not barcodes:
                pass
            else:
                for barcode in barcodes:
                    raw_text = barcode.data.decode('utf-8', errors='replace')
                    print(f"Raw data: {raw_text}")

                    # try to parse it as JSON
                    try:
                        obj = json.loads(raw_text)
                        print("Parsed JSON:", obj)
                    except json.JSONDecodeError:
                        print("→ Data is not valid JSON")

                    # Call the API search with the barcode value
                    self.search_api(raw_text)

                    break


            cv2.imshow('Barcode Scanner', frame)

            if cv2.waitKey(1) == 27:  
                break

        # clean up
        self.cam.release()
        cv2.destroyAllWindows()

    def search_api(self, barcode_value):
        api_key = "0679hdynayu05li2yowaxjz9alhhpv"
        url = f"https://api.barcodelookup.com/v3/products?barcode={barcode_value}&formatted=y&key={api_key}"

        try:
            with urllib.request.urlopen(url) as url_response:
                data = json.loads(url_response.read().decode())

                barcode = data["products"][0]["barcode_number"]
                print("Barcode Number: ", barcode, "\n")

                name = data["products"][0]["title"]
                print("Title: ", name, "\n")

                nurtional_value = data["products"][0]["nutrition_facts"]
                print("Nurtional Contents: ", nurtional_value,"\n")

                self.ingredents = data["products"][0]["ingredients"]
                print("ingredents Contents: ", self.ingredents,"\n")
                if isinstance(nurtional_value,dict):
                    for key,value in nurtional_value.items():
                        print(f"  {key}: {value}")
                else:
                    print(nurtional_value)
        except Exception as e:
            print("API request failed:", e)

        self.halal()

    def halal(self):
        haram_ingredients = [
                # Animal-Derived Fats & Emulsifiers
                "Gelatin",
                "Lard",
                "Suet",
                "Tallow",
                "Mono- and Diglycerides",
                "Glycerin",
                "Stearic Acid",
                "Calcium Stearate",
                "Sucrose Esters of Fatty Acids",
                
                # Animal-Derived Proteins & Enzymes
                "Rennet",
                "Chymosin",
                "L-Cysteine",
                "Pancreatin",
                "Trypsin",
                "Pepsin",
                
                # Colorants & Glazing Agents
                "Carmine",
                "Cochineal Extract",
                "Shellac",
                "Isinglass",
                
                # Alcohols & Fermented Products
                "Alcohol",
                "Ethanol",
                "Wine Vinegar",
                
                # Miscellaneous
                "Vitamin D3",
                "Refined Sugar (Bone Char Processed)"
            ]
        
        ingredients = self.ingredents.lower()
        found_haram = False
        for haram in haram_ingredients:
            if haram.lower() in ingredients:
             print(f"THIS ITEM CONTAINS HARAM INGREDIENT: {haram}")
             print("THIS ITEM IS NOT HALAL")
            found_haram = True
        if not found_haram:
            print("THIS ITEM APPEARS TO BE HALAL")


if __name__ == "__main__":
    scanner = BarCode_Scanner()
    scanner.run()
    