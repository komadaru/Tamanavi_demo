import xmltodict
import datetime
import requests

def loadGpsLogs(file):
    with open(file, encoding="utf-8") as f:
        xml_data = f.read()
        dict_data = xmltodict.parse(xml_data)
        data = dict_data["gpx"]["trk"]["trkseg"]["trkpt"]
        data = [
            {
                "latitude": d["@lat"],
                "longitude": d["@lon"],
                "time": datetime.datetime.fromisoformat(d["time"].replace("Z",""))
            }
            for d in data]
    return data

def sendData(d):
    requests.get(
        "http://localhost:5000/gps/register",
        params = {
            "latitude": d["latitude"],
            "longitude": d["longitude"],
            "bus": "1",
            "accel" : "0",
            "time": d["time"]
        }
    )
    #time.sleep((data[i+1]["time"] - d["time"]).seconds)