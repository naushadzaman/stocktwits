import re 
import os 
import sys 
import json 
import requests
from collections import Counter 

headers = {
    'Content-Type': "application/json",
    'User-Agent': "BlackbirdAPI",
    'Accept': "*/*",
    'Cache-Control': "no-cache",
    'Accept-Encoding': "gzip, deflate",
    'Connection': "keep-alive",
    'cache-control': "no-cache"
    }

def get_api_result(host, payload):
    """
    time curl -H "Content-Type: application/json" -XPOST --data '{
    "text": "are you fucking kidding me"
    }' http://localhost:8080/analyze/text/ | json_pp
    """
    r = requests.request("POST", host, data=json.dumps(payload), headers=headers)
    return json.loads(r.text)

if __name__ == "__main__": 
    _texts = []
    entities_result = Counter()
    for i,line in enumerate(open(sys.argv[1])): 
        line = json.loads(line)
        
        # _texts.append(line["body"])
        # if i % 100 == 0:
        #     host = "http://master.apiblackbird.com//analyze/text"
        #     payload = { "texts": _texts, "classifiers":"entity", "token":"blackbirdinternal-PdB72rtMS94UWteyWP"}
        #     _results = get_api_result(host, payload)
        #     for x in _results["results"]:
        #         ents = list(x["entity"]["entities"].keys()) # + list(x["entity"]["NER"].keys())
        #         # print(ents)
        #         ents = [x for x in ents if len(x.split()) > 1]
        #         entities_result.update(ents)
        #     _texts = []
        #     print(i,entities_result.most_common(20))
        #     # break 