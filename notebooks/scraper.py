import os
import pandas as pd
import numpy as np 
import requests
import time

os.listdir("../data")

df=pd.read_csv('../data/semantic_scholar_articles_20000.csv',chunksize = 1)

def printPercent(line_c):
    global perc
    if line_c%25==0:
        perc = perc+0.125
        print(perc,end="%\n")

f = open("output.txt","a")
perc = -0.125
line_count = 0

for line in df:
    results = {"search_text":"","semantic_df_index":-1,"top_hits":{}}
    
    time.sleep(2)
    
    if line_count >20:
        break
        
    printPercent(line_count)
    line_count = line_count+1
    
    search_text = line['title'].iloc[0]

    response = requests.get("https://dblp.org/search/publ/api?q="+search_text+"&format=json")

    try:
        hit_json = response.json()['result']['hits']['hit']
    except:
        hit_json = []

    if len(hit_json)>0:
        cur_score = hit_json[0]["@score"]
        
        hit_count = 0
        
        for h in hit_json:
            
            if h["@score"]!=cur_score or hit_count>2:
                break
            else:
                cur_score = h["@score"]
                
            hit_count = hit_count+1
            
            try:
                doi_id = h['info']['doi']
            except:
                continue

            #CrossRef
            try:
                citations = requests.get("https://api.crossref.org/works/"+doi_id)
                h['references_crossref']=citations.json()['message']['reference']
            except:
                pass

            #OpenCitations
            try:
                citations_2 = requests.get("https://opencitations.net/index/api/v1/citations/"+doi_id+"?format=json&exclude=citing&sort=desc(creation)&")
                h['references_opencitations']=citations_2.json()
            except:
                pass

    try:
        results["search_text"] = search_text
    except:
        results["search_text"] = ""
    try:
        results["semantic_df_index"] = line.index[0]
    except:
        results["semantic_df_index"]= -1
    try:
        results["top_hits"] = hit_json 
    except:
        results["top_hits"] = {}
        
    f.write(json.dumps(results)+",")

f.close()