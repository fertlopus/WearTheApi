import pandas as pd
from pprint import pprint
import json

file_path = "./raw/ClothingImagesDBextended.csv"
clothing_data = pd.read_csv(file_path)


def preprocess_to_json(dataframe: pd.DataFrame):
    json_data = []
    for _, row in dataframe.iterrows():
        entry = {
            "AssetName": row["AssetName"],
            "OutfitPart": row["OutfitPart"],
            "Color": row["Color"],
            "Style": row["Style"].split(", "),
            "Gender": row["Gender"],
            "Fit": row["Fit"],
            "Season": row["Season"].split(", "),
            "Condition": row["Condition"].split(", "),
            "TempRange": {"Min": row["TempMin"],
                          "Max": row["TempMax"]},
            "Wind": row["Wind"],
            "Rain": row["Rain"],
            "Snow": row["Snow"]
        }
        json_data.append(entry)
    return json_data

output_json = preprocess_to_json(clothing_data)
output_path = "./preprocessed/clothing_data.json"
with open(output_path, "w") as json_file:
    json.dump(output_json, json_file, indent=4)
