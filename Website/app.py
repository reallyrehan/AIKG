# -*- coding: utf-8 -*-
"""
    :author: Grey Li <withlihui@gmail.com>
    :copyright: (c) 2020 by Grey Li.
    :license: MIT, see LICENSE for more details.
"""
from flask import Flask, render_template,request, jsonify, session
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired
from flask_ckeditor import CKEditor, CKEditorField
import os
import pandas as pd
import pandasql as ps
from flask_fontawesome import FontAwesome
import sqlparse
from datetime import datetime
from pretty_html_table import build_table
from werkzeug.utils import secure_filename
import re
import json
from neo4j.graph import Node


### RECOMMENDER CODE

# General Packages
import numpy as np
import pandas as pd
import os
import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns

# Iterators
from collections import Counter
from itertools import islice
from operator import itemgetter
from tqdm import tqdm

# Text
import re
from textblob import TextBlob
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize, wordpunct_tokenize, MWETokenizer
from nltk.stem import porter, WordNetLemmatizer
from nltk.corpus import stopwords
from nltk.util import ngrams

# Scikit-Learn
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.decomposition import LatentDirichletAllocation, TruncatedSVD, NMF
from sklearn.preprocessing import StandardScaler, Normalizer
from sklearn.neighbors import NearestNeighbors

# Serialization
import joblib 

# Warnings
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning) 

# %%time
vectorizer = joblib.load('../data_files/vectorizer.joblib') 
print(type(vectorizer))

LDA_obj = joblib.load('../data_files/LDA_obj.joblib') 
print(type(LDA_obj))

LDA_data = joblib.load('../data_files/LDA_data.joblib') 
print(type(LDA_data))

topic_names = joblib.load('../data_files/topic_names.joblib') 
print(type(topic_names))

papers = pd.read_csv('../data_files/final_dataset.csv')
print(f'papers.shape: {papers.shape}')
papers.drop(columns='Unnamed: 0', inplace=True)
papers.drop_duplicates(subset='title', inplace=True)
papers.drop_duplicates(subset='abstract', inplace=True)
papers.reset_index(inplace=True, drop=True)
papers['abstract'] = papers['abstract'].astype(str)
print(f'papers.shape: {papers.shape}')
# papers.head(3)

def get_recommendation(INPUT_STRING, 
                       NUM_RECOMMENDATIONS = 5,
                       vectorizer = vectorizer,
                       LDA_obj = LDA_obj,
                       LDA_data = LDA_data,
                       topic_names = topic_names,
                       papers = papers):
    
    '''
    Requires the following previous objects from this notebook:
    1. Trained vectorizer
    2. Trained LDA_obj
    3. Converted LDA_data
    4. topic_names (list with the modeled topic for each TED Talk)
    5. ted_transcripts dataframe contaning both CSVs already merged
    '''
    
    # Vectorize the input string
    target_vector = vectorizer.transform([INPUT_STRING])
    
    # Model the vector with the trained LDA_Obj
    target_modeled = LDA_obj.transform(target_vector)
    
    # Fit a KNN algorithm on the whole dataset modeled with LDA
    NN = NearestNeighbors(n_neighbors=NUM_RECOMMENDATIONS, metric='cosine', algorithm='brute', n_jobs=-1)
    NN.fit(LDA_data)
    
    # Find the nearest neighbords for the LDA vector correspondent to the input string
    results = NN.kneighbors(target_modeled)
    recommend_list = results[1][0]
    cosine_distance = results[0][0]

    # Loop to extract revelant information about the recommendations
    titles, modeled_topics, citations = [], [] ,[]
    for idx in recommend_list:
        titles.append(papers.loc[idx,'title'])
        modeled_topics.append(topic_names.iloc[idx,0])
        citations.append(papers.loc[idx,'citationVelocity'])

    # Put recommendations in a dataframe for outputting
    output_df = pd.DataFrame({'ID': recommend_list,
                              'Cosine Distance': cosine_distance,
                              'Title': titles,
                              'Modeled Topic': modeled_topics,
                              'Citations': citations})
    
    # Customize index to start at 1 
    custom_index = np.arange(1, NUM_RECOMMENDATIONS+1).tolist()
    output_df.set_index([custom_index], inplace=True)
    
    return output_df




# INPUT_STRING = "Neural Network"

# output = get_recommendation(INPUT_STRING, 
#                    NUM_RECOMMENDATIONS=10,
#                    vectorizer = vectorizer,
#                    LDA_obj = LDA_obj,
#                    LDA_data = LDA_data,
#                    topic_names = topic_names,
#                    papers = papers)




app = Flask(__name__)
fa = FontAwesome(app)


app.secret_key='my_secret'

testing = True

if testing:
    sheet_list = [{"path":"files/Technical case study for Fatima Zain.xlsx","type":"excel","sheet_name":"Data dump","name":"Data_dump"}]
else:
    sheet_list = [{"path":"files/Technical case study for Fatima Zain.xlsx","type":"excel","sheet_name":"Data dump","name":"Data_dump"},
        {"path":"files/case study.xlsx","type":"excel","sheet_name":"Orders","name":"Orders"},
        {"path":"files/case study.xlsx","type":"excel","sheet_name":"Returns","name":"Returns"}]




def loadSheets():
    global sheet_list

    for s in sheet_list:
        if s["type"]=="excel":
            globals()[s["name"]] = pd.read_excel(s["path"],sheet_name=s["sheet_name"])

# file_name = "files/Technical case study for Fatima Zain.xlsx"
# sheet_type = "xlsx"
# sheet_name = "Data dump"
# old_sheet_name = sheet_name

# sheet_name = sheet_name.replace(" ","_")
# globals()[sheet_name] = pd.read_excel(file_name,sheet_name=old_sheet_name)
# dtypes = globals()[sheet_name].dtypes



class PostForm(FlaskForm):
    title = TextAreaField('Title',validators=[DataRequired()])
    submit = SubmitField('Submit')


with open('../data/Neo4J Queries.txt') as f:
    t=f.read()
    f.close()
    ls_t = t.split('_____')

def getTableCols():
    global ls_t

    q_num = 1
    ans_global =""
    for i in ls_t[0:10]:
        query_name = i.replace('\n',' ').split('MATCH')[0][3:].strip()
        query = 'MATCH '+i.replace('\n',' ').split('MATCH')[1]

        ans='<div class = "row ml-2"><br><button class = "btn btn-light btn-block text-left"  id ="query__NUMBER__"><small>__NAME__</small><p id = "query__NUMBER___hidden" style = "display:none">__QUERY__</p></button></div>'
        ans = ans.replace('__NUMBER__',str(q_num))
        ans = ans.replace('__NAME__',query_name)
        ans = ans.replace('__QUERY__',query)

        ans_global+=ans
        q_num+=1

    return( ans_global)



def addColor(p):
    txt = str(p)
    color = "black"
    
    if p.is_whitespace:
        return " "
    
    
    if p.is_keyword:    
        color = "blue"
        txt = txt.upper() 
    else:
        
        if str(p)=="*" or str(p)==";":
            color="black"
        else:
            color = "black"
            
    return ' <span style = "color:'+color+';">'+txt+'</span>'

def sqlHighlighter(query):
    try:
        ans = ""
        parsed = sqlparse.parse(query)[0]
        
        for p in parsed.tokens:
            # print(str(p.is_keyword)+" " +str(type(p))+" "+str(p))
            if p.is_group:
                
                for x in p.flatten():
                    ans = ans +addColor(x)
                continue

            ans = ans +addColor(p)
    except:
        ans = query
    return ans

def queryTransform(query):
    return query.replace("\n"," ")

def getTableResults(query):

    sql_formatted = sqlHighlighter(query)
 
    res_html = """
    <div class="card mt-4" style="border-top:solid grey;">
    <div class="card-body">
    <button class = "btn btn-light tablefull" ><i class= "fa fa-times"></i></button> 
    <br>
    __QUERY__ 
    <hr>
        <div class ="tablediv" style="ml-4 mr-4 overflow-x:auto; overflow-y:auto; __HEIGHT__"> 
        
        __RESULT_ANSWER__ </div>
        <div class = "d-flex">
        <p class="card-text mt-2 mr-auto"><small class="text-muted ">Results: __TOTAL__</small></p>
        <p class="card-text mt-2 ml-auto mr-auto"><small class="text-muted "> __NUMBER__</small></p>
                <p class="card-text mt-2 ml-auto"><small class="text-muted ">Executed at __TIME__</small></p></div>
                

    </div>

    </div><hr>"""

    result = None
    print(queryTransform(query))
    try:
        result = ps.sqldf(queryTransform(query), globals())
        res = build_table(result.loc[0:10], 'grey_dark',text_align='center')[3:-4]
        
        # res = result.to_html(max_rows=30,border=0,classes=["table-striped","table-hover","table-responsive"])
        height_limit = True
        num_length=len(result)
    except Exception as e:
        height_limit = False
        num_length=0
        if result == None:
            res  = '<p class = "text-danger"> Failed to Parse Query</p>'
        else:
            res  = '<p class = "text-danger"> ERROR'+str(e)+'</p>'


    res_html = res_html.replace("__RESULT_ANSWER__",res)
    res_html = res_html.replace("__QUERY__",sql_formatted)
    res_html = res_html.replace("__TIME__",str(datetime.now()))
    res_html = res_html.replace("__TOTAL__",str(num_length))
    res_html = res_html.replace("__NUMBER__",str(session["query_count"]))

    if height_limit:
        res_html = res_html.replace("__HEIGHT__","height:800px;")
    else:
        res_html = res_html.replace("__HEIGHT__","")
    


    return res_html
    
    

@app.route('/', methods=['GET', 'POST'])
def index():

    session["query_count"]=0

    form = PostForm()

    col_html = getTableCols()

    result = ""
    title = ""
    

    # if request.method=="POST":
    # #if form.validate_on_submit():
    #     title = form.title.data
    #     result = getTableResults(title)

        
        



    return render_template('index.html', form=form,col_html=col_html,title = title,result = result)


# @app.route("/api/calc")
# def processing_query():


#     # # TESTING


#     session["query_count"]= session["query_count"]+1

#     query_input = request.args.get('query', 0)

#     #title = form.title.data
#     result = getTableResults(query_input)

#     #print(result)


#     return jsonify({
 
#         "txt":result,
     
#     })

@app.route("/api/tables")
def getTables():

    table_dict={}

    for s in sheet_list:
        table_dict[s["name"]]=list(globals()[s["name"]].columns)

    


    return jsonify({
        "result":table_dict
    })


def getFileType(fileName):
    sp = fileName.split(".")
    try:
        fname = sp[0]
        fname = re.sub(r"[^a-zA-Z0-9]+", '_', fname)

        fext = sp[-1]
    except:
        print("INCORRECT FILE NAME OR TYPE")
        return fname,-1


    print(fext)
    if fext =="csv":
        return fname,0
    elif fext in ['xlsx', 'xlsm', 'xlsb', 'xltx', 'xltm', 'xls', 'xlt', 'xls', 'xml', 'xml', 'xlam', 'xla', 'xlw', 'xlr']:
        return fname,1
    else:
        return fname,-1


@app.route('/upload', methods = ['GET', 'POST'])
def uploadFile():
    sample_txt = """
    
    <div class="row mt-2" style="background-color: rgb(236, 235, 235);padding-top:10px;">
        <div class = "col-2" >__FILENO__</div>
        <div class = "col-2"><p>__FILENAME__</p></div>
        <div class = "col-2"><p>__FILETYPE__</p></div>
        <div class="col-2">
            <input class="btn btn-sm " style="text-align:left;background-color: white;" type="text" name ="__FILENO__name" value="__SHEETNAME__" __TEXTDISABLE__>
        </div>
        <div class="col-2">

            <div class="form-check form-check-inline">
                <input class="form-check-input ml-4" type="checkbox" id="inlineCheckbox2" name="__FILENO__check1" value="option2" __DISABLED__>
                <label class="form-check-label" for="inlineCheckbox2"></label>
            </div>


        </div>
        <div class="col-2">
            <div class="form-check form-check-inline">
                <input class="form-check-input" type="checkbox" id="inlineCheckbox1"  name="__FILENO__check2" value="option1" __DISABLED__>
                <label class="form-check-label" for="inlineCheckbox1"></label>
            </div>

        </div>

    </div>
    """

    all_txt = ""

    if request.method == 'POST':

        files = request.files.getlist('files[]') 
        fileNo=0
        text=""
        for file in files:
            fupload = os.path.join("files",file.filename)

            if secure_filename(file.filename):
                try:
                    file.save(fupload)    
                    print(file.filename + ' Uploaded')
                    text = text + file.filename + ' Uploaded<br>'

                    fileNo = fileNo +1

                    fname,fileType = getFileType(file.filename)
                    print(fname)
                    print(fileType)

                    modal_txt = sample_txt[:]
                    modal_txt = modal_txt.replace("__FILENO__",str(fileNo))
                    modal_txt = modal_txt.replace("__FILENAME__",file.filename)
                    modal_txt = modal_txt.replace("__SHEETNAME__",fname)

                    if fileType == 0:
                        modal_txt = modal_txt.replace("__FILETYPE__","CSV")
                        modal_txt = modal_txt.replace("__DISABLED__","disabled")
                        modal_txt = modal_txt.replace("__TEXTDISABLE__",'')
                    elif fileType == 1:
                        modal_txt = modal_txt.replace("__DISABLED__","")
                        modal_txt = modal_txt.replace("__FILETYPE__","Excel")
                        modal_txt = modal_txt.replace("__TEXTDISABLE__",'')
                    else:
                        modal_txt = modal_txt.replace("__DISABLED__","disabled")
                        modal_txt = modal_txt.replace("__FILETYPE__",'<span style="color:red;">Not Supported</span>')
                        modal_txt = modal_txt.replace("__TEXTDISABLE__",'disabled')

                    


                    all_txt = all_txt+modal_txt


                    
                except Exception as e:
                    print(file.filename + ' Failed with Exception '+str(e))
                    text = text + file.filename + ' Failed with Exception '+str(e) + '<br>'

                    continue
            else:
                print(file.filename + ' Failed because File Already Exists or File Type Issue')
                text = text + file.filename + ' Failed because File Already Exists or File Type not secure <br>'

            

    return jsonify({
        "result":all_txt
    })





@app.route("/lda")
def returnLDA():
    return render_template('lda.html',result ="") 

@app.route("/page.html")
def returnPage():
    return render_template('page.html',result ="")


@app.route("/api/format")
def formatting_query():
    query_input = request.args.get('query', 0)

    sql_formatted = (sqlparse.format(query_input, reindent=True, keyword_case='upper'))

    #title = form.title.data

    #print(result)


    return jsonify({
 
        "txt":sql_formatted,
     
    })




#### NEO4j
from neo4j import GraphDatabase
class Neo4jConnection:
    
    def __init__(self, uri, user, pwd):
        self.__uri = uri
        self.__user = user
        self.__pwd = pwd
        self.__driver = None
        try:
            self.__driver = GraphDatabase.driver(self.__uri, auth=(self.__user, self.__pwd))
        except Exception as e:
            print("Failed to create the driver:", e)
        
    def close(self):
        if self.__driver is not None:
            self.__driver.close()
        
    def query(self, query, db=None):
        assert self.__driver is not None, "Driver not initialized!"
        session = None
        response = None
        try: 
            session = self.__driver.session(database=db) if db is not None else self.__driver.session() 
            response = list(session.run(query))
        except Exception as e:
            print("Query failed:", e)
        finally: 
            if session is not None:
                session.close()
        return response

# Get Paper Properties

# Get Paper Properties

def getPaper(conn,search_property,search_term):
    dc = {}
    query_string = '''
    MATCH (n:ns0__ScholarlyArticle {__PROPERTY__:'__TERM__'}) RETURN n LIMIT 1'''
    
    query_string = query_string.replace('__PROPERTY__',search_property)
    query_string = query_string.replace('__TERM__',search_term)
    res = conn.query(query_string, db='neo4j')
    
    dc['info'] = res
    
    query_string = '''
    MATCH
    (:ns0__ScholarlyArticle {__PROPERTY__:'__TERM__'})-[r:ns1__references]->(n)
    RETURN n.ns0__headline,n.ns1__doi,n.uri
    '''
    query_string = query_string.replace('__PROPERTY__',search_property)
    query_string = query_string.replace('__TERM__',search_term)
    dc['references'] = conn.query(query_string, db='neo4j')

    query_string = '''
    MATCH
    (:ns0__ScholarlyArticle {__PROPERTY__:'__TERM__'})-[r:ns0__citation]->(n)
    RETURN n.ns0__headline,n.ns1__doi,n.uri
    '''
    query_string = query_string.replace('__PROPERTY__',search_property)
    query_string = query_string.replace('__TERM__',search_term)
    dc['citations'] = conn.query(query_string, db='neo4j')



    query_string = '''
    MATCH
    (:ns0__ScholarlyArticle {__PROPERTY__:'__TERM__'})-[r:ns0__creditText]->(n)
    RETURN n.ns0__headline,n.ns1__doi,n.uri
    '''
    query_string = query_string.replace('__PROPERTY__',search_property)
    query_string = query_string.replace('__TERM__',search_term)
    dc['creditText'] = conn.query(query_string, db='neo4j')



    query_string = '''
    MATCH
    (:ns0__ScholarlyArticle {__PROPERTY__:'__TERM__'})-[r:ns0__author]->(n)
    RETURN n
    '''
    query_string = query_string.replace('__PROPERTY__',search_property)
    query_string = query_string.replace('__TERM__',search_term)
    dc['authors'] = conn.query(query_string, db='neo4j')

    query_string = '''
    MATCH
    (:ns0__ScholarlyArticle {__PROPERTY__:'__TERM__'})-[r:ns0__genre]->(n)
    RETURN n
    '''
    query_string = query_string.replace('__PROPERTY__',search_property)
    query_string = query_string.replace('__TERM__',search_term)
    dc['genres'] = conn.query(query_string, db='neo4j')

    query_string = '''
    MATCH
    (:ns0__ScholarlyArticle {__PROPERTY__:'__TERM__'})-[r:ns0__publisher]->(n)
    RETURN n
    '''
    query_string = query_string.replace('__PROPERTY__',search_property)
    query_string = query_string.replace('__TERM__',search_term)
    dc['publisher'] = conn.query(query_string, db='neo4j')
    
    return dc



conn = None

def getDbConnection():
    global conn

    if not conn:
        conn = Neo4jConnection(uri="bolt://localhost:11009", user="neo4j", pwd="abc123")

    return conn


card_text_or = """						<div class="card" style="border-top:solid grey;">
								<div class="card-body">
								<br>
								<div class = "row">
									<div class = "col-2">
								<small class ="mr-4">Title</small>
							</div>

							<div class = "col-10"  >
								<h3>
__TITLE__</h3>
</div>
								<hr>
                                __PROPERTIES__
							</div>


									<div class = "d-flex">
									<p class="card-text mt-2 mr-auto"><small class="text-muted ">Results: __TOTAL__</small></p>
									<p class="card-text mt-2 ml-auto mr-auto"><small class="text-muted "> __NUMBER__</small></p>
											<p class="card-text mt-2 ml-auto"><small class="text-muted ">Executed at __TIME__</small></p></div>
											
							
								</div>
							
								</div><hr>"""



def unescape(s):
    s = s.replace("&lt;", "<")
    s = s.replace("&gt;", ">")
    # this has to be last:
    s = s.replace("&amp;", "&")
    return s



def getPaperCard(search_choice,search_term):
    conn = getDbConnection()
    card_text = card_text_or[:]


    if search_choice in [2,3]:

        if search_choice == 3:
            search_property = 'ns1__doi'
        else:
            search_property = 'uri'
            search_term = 'file:///Users/rehanahmed/Documents/USC/DSCI-558%20Project/notebooks/'+search_term

        # search_term = '10.1109/ICCV.2019.00500'

        paper_dict = getPaper(conn,search_property,search_term)
        # print(paper_dict)

        if len(paper_dict['info'])>0:
            uri = paper_dict['info'][0]['n']['uri'].split('/')[-1]

            try:
                doi = paper_dict['info'][0]['n']['ns1__doi']
            except:
                doi = None

            try:
                title = paper_dict['info'][0]['n']['ns0__headline']
            except:
                title = None

            property_text = '<div class = "col-2"><small >URI</small></div><div class = "col-10"><span class="badge badge-info mr-4">'+str(uri)+'</span></div>'

            for i in paper_dict['info'][0]['n']:
                if i not in ["uri","ns0__abstract","ns0__headline"]:
                    if '__url' in i:
                        property_text+= '<div class = "col-2"><small >'+i+'</small></div><div class = "col-10"><span class="badge badge-info mr-4"><a href ="'+paper_dict['info'][0]['n'][i]+'" style="color:white;" target = "_blank">'+str(paper_dict['info'][0]['n'][i])+'</a></span></div>'
                    else:
                        property_text+= '<div class = "col-2"><small >'+i+'</small></div><div class = "col-10"><span class="badge badge-info mr-4">'+str(paper_dict['info'][0]['n'][i])+'</span></div>'


            if len(paper_dict['authors'])>0:
                property_text+= """<div class = "col-2"><small >Authors</small></div><div class = "col-10">"""
                for a,b in [(i['n']['uri'],i['n']['ns0__name']) for i in paper_dict['authors']]:
                    property_text+='<span class="badge badge-info mr-4"><a style = "color:white;" target="_blank" href="/page/5/'+a.split("/")[-1]+'">'+b+'</a></span>'
                property_text+='</div>'
            if len(paper_dict['genres'])>0:
                property_text+= """<div class = "col-2"><small >Genres</small></div><div class = "col-10">"""
                for a in [i['n']['ns0__name'] for i in paper_dict['genres']]:
                    property_text+='<span class="badge badge-info mr-4">'+a+'</span>'
                property_text+='</div>'

            if "ns0__abstract" in paper_dict['info'][0]['n']:
                property_text+= '<div class = "col-2 mt-4"><small >Abstract</small></div><div class = "col-10 mt-4"><p">'+paper_dict['info'][0]['n']['ns0__abstract']+'</p></div>'

            cite_text = '<div class = "col-2"><small>Citations</small></div><div class = "col-10"><p><button class="btn btn-block btn-secondary" data-toggle="collapse" href="#collapseExampleC'+str(session["query_count"])+'" role="button" aria-expanded="false" aria-controls="collapseExample">'+str(len(paper_dict['citations']))+'</button ></p><div class="collapse" id="collapseExampleC'+str(session["query_count"])+'"><div class="card card-body mb-4">__CITETEXT__</div></div></div>'

            if len(paper_dict['citations'])>0:
                c_text = "<ul>"
                for i in paper_dict['citations']:
                    c_text+= '<li><span class = "badge badge-primary mr-4" ><a style="color:white;" target = "_blank" href="/page/2/'+i['n.uri'].split("/")[-1]+'">'+i['n.uri'].split("/")[-1]+'</a></span>'
                    if i['n.ns0__headline']:
                        c_text+=i['n.ns0__headline']+'</li>'
                    else:
                        c_text+='</li>'

                c_text+="</ul>"
                cite_text_2 = cite_text.replace('__CITETEXT__',c_text)
                property_text+=cite_text_2

            cite_text = '<div class = "col-2"><small>References</small></div><div class = "col-10"><p><button class="btn btn-block btn-secondary" data-toggle="collapse" href="#collapseExampleR'+str(session["query_count"])+'" role="button" aria-expanded="false" aria-controls="collapseExample">'+str(len(paper_dict['references']))+'</button ></p><div class="collapse" id="collapseExampleR'+str(session["query_count"])+'"><div class="card card-body mb-4">__CITETEXT__</div></div></div>'

            if len(paper_dict['references'])>0:
                c_text = "<ul>"
                for i in paper_dict['references']:
                    c_text+= '<li><span class = "badge badge-primary mr-4" ><a style="color:white;" target = "_blank" href="/page/2/'+i['n.uri'].split("/")[-1]+'">'+i['n.uri'].split("/")[-1]+'</a></span>'
                    if i['n.ns0__headline']:
                        c_text+=i['n.ns0__headline']+'</li>'
                    else:
                        c_text+='</li>'

                c_text+="</ul>"
                cite_text_2 = cite_text.replace('__CITETEXT__',c_text)
                property_text+=cite_text_2

            cite_text = '<div class = "col-2"><small>creditText</small></div><div class = "col-10"><p><button class="btn btn-block btn-secondary" data-toggle="collapse" href="#collapseExampleX'+str(session["query_count"])+'" role="button" aria-expanded="false" aria-controls="collapseExample">'+str(len(paper_dict['creditText']))+'</button ></p><div class="collapse" id="collapseExampleX'+str(session["query_count"])+'"><div class="card card-body mb-4">__CITETEXT__</div></div></div>'

            if len(paper_dict['creditText'])>0:
                c_text = "<ul>"
                for i in paper_dict['creditText']:
                    c_text+= '<li><span class = "badge badge-primary mr-4" ><a style="color:white;" target = "_blank" href="/page/2/'+i['n.uri'].split("/")[-1]+'">'+i['n.uri'].split("/")[-1]+'</a></span>'
                    if i['n.ns0__headline']:
                        c_text+=i['n.ns0__headline']+'</li>'
                    else:
                        c_text+='</li>'

                c_text+="</ul>"
                cite_text_2 = cite_text.replace('__CITETEXT__',c_text)
                property_text+=cite_text_2





            try:
                card_text = card_text.replace('__TITLE__',title)
            except:
                card_text = card_text.replace('__TITLE__',"-")
            card_text = card_text.replace('__PROPERTIES__',property_text)
        else:
            card_text = card_text.replace('__TITLE__',"No Results")
            card_text = card_text.replace('Title',"Error")

            card_text = card_text.replace('__PROPERTIES__',"")


        card_text = card_text.replace('__TOTAL__',str(1))

    elif search_choice == 0:


        INPUT_STRING = search_term

        recommend_df = get_recommendation(INPUT_STRING, 
                        NUM_RECOMMENDATIONS=10,
                        vectorizer = vectorizer,
                        LDA_obj = LDA_obj,
                        LDA_data = LDA_data,
                        topic_names = topic_names,
                        papers = papers)


        uri_text = 'file:///Users/rehanahmed/Documents/USC/DSCI-558%20Project/notebooks/'

        ans = ""
        for i in list(recommend_df['ID']):
            ans = ans+"','"+uri_text+str(i)
            

        # print(ans[2:]+"'")

        query_string = """MATCH (n:ns0__ScholarlyArticle)
        WHERE n.uri IN [__LIST__]
        RETURN n"""
        query_string = query_string.replace('__LIST__',ans[2:]+"'")


        res = conn.query(query_string, db='neo4j')

        recommend_df['neo_result'] = ''
        for r in res:
            # print('hi')
            ind = recommend_df[recommend_df['ID']==int(r['n']['uri'].split('/')[-1])].index[0]
            recommend_df.at[ind,'neo_result'] = r['n']
        

        card_text = card_text_or[:] 

        property_text = '<hr class="mt-4">'

        c_r = 0
        for _,row in recommend_df.iterrows():
            property_text+= '<div class = "col-12"><p><button class="btn btn-block btn-light text-left" data-toggle="collapse" href="#collapseExampleC'+str(session["query_count"])+'_'+str(c_r)+'" role="button" aria-expanded="false" aria-controls="collapseExample">‣ '+row['Title']+'</button ></p><div class="collapse" id="collapseExampleC'+str(session["query_count"])+'_'+str(c_r)+'"><div class="card card-body mb-4">'
            c_r+=1
            # property_text+= '<div class = "row"><div class = "col-2"><small >uri</small></div><div class = "col-10"><span class="badge badge-info mr-4"><a style="color:white;" target="_blank" href="/page/2/'+str(row['ID'])+'">'+str(row['ID'])+'</a></span></div></div>'
            property_text+= '<div class = "row"><div class = "col-2"><small >Cosine Distance</small></div><div class = "col-10"><span class="badge badge-info mr-4">'+str(row['Cosine Distance'])+'</span></div></div>'
            property_text+= '<div class = "row"><div class = "col-2"><small >Modeled Topics</small></div><div class = "col-10"><span class="badge badge-info mr-4">'+str(row['Modeled Topic'])+'</span></div></div>'

            for i in row['neo_result']:
                if i not in ["uri","ns0__abstract","ns0__headline"]:
                    # property_text+= '<div class = "row"><div class = "col-2"><small >'+i+'</small></div><div class = "col-10"><span class="badge badge-info mr-4">'+str(r['n'][i])+'</span></div></div>'
                    if '__url' in i:
                        property_text+= '<div class = "row"><div class = "col-2"><small >'+i+'</small></div><div class = "col-10"><span class="badge badge-info mr-4"><a href ="'+str(r['n'][i])+'" style="color:white;" target = "_blank">'+str(r['n'][i])+'</a></span></div></div>'
                    else:
                        property_text+= '<div class = "row"><div class = "col-2"><small >'+i+'</small></div><div class = "col-10"><span class="badge badge-info mr-4">'+str(r['n'][i])+'</span></div></div>'
            




            property_text+='</div></div></div>'
            
            
        card_text = card_text.replace('Title','Search Title')
        card_text = card_text.replace('__TITLE__',search_term)
        card_text = card_text.replace('__PROPERTIES__',property_text)
        card_text = card_text.replace('__TOTAL__',str(len(res)))
    elif search_choice == 1:
        query_string = """MATCH (n:ns0__ScholarlyArticle {})
        WHERE toLower(n.ns0__headline) CONTAINS toLower('__SEARCHTERM__')
        RETURN n limit 10"""


        query_string = query_string.replace('__SEARCHTERM__',search_term.replace('\n',' ').strip())

        res = conn.query(query_string, db='neo4j')
        card_text = card_text_or[:] 

        property_text = '<hr class="mt-4">'
        c_r = 0
        for r in res:
            property_text+= '<div class = "col-12"><p><button class="btn btn-block btn-light text-left" data-toggle="collapse" href="#collapseExampleC'+str(session["query_count"])+'_'+str(c_r)+'" role="button" aria-expanded="false" aria-controls="collapseExample">‣ '+r['n']['ns0__headline']+'</button ></p><div class="collapse" id="collapseExampleC'+str(session["query_count"])+'_'+str(c_r)+'"><div class="card card-body mb-4">'
            c_r+=1
            property_text+= '<div class = "row"><div class = "col-2"><small >uri</small></div><div class = "col-10"><span class="badge badge-info mr-4"><a style="color:white;" target="_blank" href="/page/2/'+str(r['n']['uri'].split("/")[-1])+'">'+str(r['n']['uri'].split("/")[-1])+'</a></span></div></div>'

            for i in r['n']:
                if i not in ["uri","ns0__abstract","ns0__headline"]:
                    # property_text+= '<div class = "row"><div class = "col-2"><small >'+i+'</small></div><div class = "col-10"><span class="badge badge-info mr-4">'+str(r['n'][i])+'</span></div></div>'
                    if '__url' in i:
                        property_text+= '<div class = "row"><div class = "col-2"><small >'+i+'</small></div><div class = "col-10"><span class="badge badge-info mr-4"><a href ="'+str(r['n'][i])+'" style="color:white;" target = "_blank">'+str(r['n'][i])+'</a></span></div></div>'
                    else:
                        property_text+= '<div class = "row"><div class = "col-2"><small >'+i+'</small></div><div class = "col-10"><span class="badge badge-info mr-4">'+str(r['n'][i])+'</span></div></div>'


            
            
            property_text+='</div></div></div>'
            
        card_text = card_text.replace('Title','Search Title')
        card_text = card_text.replace('__TITLE__',search_term)
        card_text = card_text.replace('__PROPERTIES__',property_text)
        card_text = card_text.replace('__TOTAL__',str(len(res)))
    elif search_choice == 4:
        query_string = """MATCH (n:ns0__Person {})
        WHERE toLower(n.ns0__name) CONTAINS toLower('__SEARCHTERM__')
        RETURN n limit 10"""

        query_string = query_string.replace('__SEARCHTERM__',search_term)

        res = conn.query(query_string, db='neo4j')
        card_text = card_text_or[:] 

        property_text = '<hr class="mt-4">'
        c_r = 0
        for r in res:
            property_text+= '<div class = "col-12"><p><button class="btn btn-block btn-light text-left" data-toggle="collapse" href="#collapseExampleC'+str(session["query_count"])+'_'+str(c_r)+'" role="button" aria-expanded="false" aria-controls="collapseExample">‣ '+r['n']['ns0__name']+'</button ></p><div class="collapse" id="collapseExampleC'+str(session["query_count"])+'_'+str(c_r)+'"><div class="card card-body mb-4">'
            c_r+=1
            property_text+= '<div class = "row"><div class = "col-2"><small >uri</small></div><div class = "col-10"><span class="badge badge-info mr-4"><a style="color:white;" target="_blank" href="/page/5/'+str(r['n']['uri'].split("/")[-1])+'">'+str(r['n']['uri'].split("/")[-1])+'</a></span></div></div>'

            for i in r['n']:
                if i not in ["uri","ns0__name"]:
                    # property_text+= '<div class = "row"><div class = "col-2"><small >'+i+'</small></div><div class = "col-10"><span class="badge badge-info mr-4">'+str(r['n'][i])+'</span></div></div>'
                    if '__url' in i:
                        property_text+= '<div class = "row"><div class = "col-2"><small >'+i+'</small></div><div class = "col-10"><span class="badge badge-info mr-4"><a href ="'+str(r['n'][i])+'" style="color:white;" target = "_blank">'+str(r['n'][i])+'</a></span></div></div>'
                    else:
                        property_text+= '<div class = "row"><div class = "col-2"><small >'+i+'</small></div><div class = "col-10"><span class="badge badge-info mr-4">'+str(r['n'][i])+'</span></div></div>'

            
            
            property_text+='</div></div></div>'

        card_text = card_text.replace('Title','Search Title')
        card_text = card_text.replace('__TITLE__',search_term)
        card_text = card_text.replace('__PROPERTIES__',property_text)
        card_text = card_text.replace('__TOTAL__',str(len(res)))

    elif search_choice == 5:
        query_string = """MATCH
        (n:ns0__Person {uri:'__TERM__'})
        RETURN n limit 10"""

        query_string = query_string.replace('__TERM__',"file:///Users/rehanahmed/Documents/USC/DSCI-558%20Project/notebooks/"+str(search_term))


        res = conn.query(query_string, db='neo4j')
        card_text = card_text_or[:] 

        property_text = '<hr class="mt-4">'
        
        try:
            r = res[0]

            property_text+= '<div class = "card card-body mb-4"><small class="badge badge-dark" style="position:absolute; margin-top:-30px; margin-left:-10px;">Info</small>'
            property_text+= '<div class = "row"><div class = "col-2"><small >uri</small></div><div class = "col-10"><span class="badge badge-info mr-4"><a style="color:white;" target="_blank" href="/page/5/'+str(r['n']['uri'].split("/")[-1])+'">'+str(r['n']['uri'].split("/")[-1])+'</a></span></div></div>'

            for i in r['n']:
                if i not in ["uri","ns0__name"]:
                    # property_text+= '<div class = "row"><div class = "col-2"><small >'+i+'</small></div><div class = "col-10"><span class="badge badge-info mr-4">'+str(r['n'][i])+'</span></div></div>'
                    if '__url' in i:
                        property_text+= '<div class = "row"><div class = "col-2"><small >'+i+'</small></div><div class = "col-10"><span class="badge badge-info mr-4"><a href ="'+str(r['n'][i])+'" style="color:white;" target = "_blank">'+str(r['n'][i])+'</a></span></div></div>'
                    else:
                        property_text+= '<div class = "row"><div class = "col-2"><small >'+i+'</small></div><div class = "col-10"><span class="badge badge-info mr-4">'+str(r['n'][i])+'</span></div></div>'

            property_text+='</div><hr>'


            card_text = card_text.replace('Title','Author')
            card_text = card_text.replace('__TITLE__',r['n']['ns0__name'])
            # card_text = card_text.replace('__PROPERTIES__',property_text)
            property_text_1 = property_text[:]

            query_string = '''
            MATCH
            (x:ns0__Person {uri:'__TERM__'})<-[r:ns0__author]-(n)
            RETURN n
            '''
            query_string = query_string.replace('__TERM__',"file:///Users/rehanahmed/Documents/USC/DSCI-558%20Project/notebooks/"+str(search_term))
            res = conn.query(query_string, db='neo4j')

            property_text = '<hr class="mt-4">'
            c_r = 0
            for r in res:
                property_text+= '<div class = "col-12"><p><button class="btn btn-block btn-light text-left" data-toggle="collapse" href="#collapseExampleC'+str(session["query_count"])+'_'+str(c_r)+'" role="button" aria-expanded="false" aria-controls="collapseExample">‣ '+r['n']['ns0__headline']+'</button ></p><div class="collapse" id="collapseExampleC'+str(session["query_count"])+'_'+str(c_r)+'"><div class="card card-body mb-4">'
                c_r+=1
                property_text+= '<div class = "row"><div class = "col-2"><small >uri</small></div><div class = "col-10"><span class="badge badge-info mr-4"><a style="color:white;" target="_blank" href="/page/2/'+str(r['n']['uri'].split("/")[-1])+'">'+str(r['n']['uri'].split("/")[-1])+'</a></span></div></div>'

                for i in r['n']:
                    if i not in ["uri","ns0__abstract","ns0__headline"]:
                        
                        # property_text+= '<div class = "row"><div class = "col-2"><small >'+i+'</small></div><div class = "col-10"><span class="badge badge-info mr-4">'+str(r['n'][i])+'</span></div></div>'
                        if '__url' in i:
                            property_text+= '<div class = "row"><div class = "col-2"><small >'+i+'</small></div><div class = "col-10"><span class="badge badge-info mr-4"><a href ="'+str(r['n'][i])+'" style="color:white;" target = "_blank">'+str(r['n'][i])+'</a></span></div></div>'
                        else:
                            property_text+= '<div class = "row"><div class = "col-2"><small >'+i+'</small></div><div class = "col-10"><span class="badge badge-info mr-4">'+str(r['n'][i])+'</span></div></div>'

                property_text+='</div></div></div>'

            property_text_1+=property_text

            card_text = card_text.replace('__PROPERTIES__',property_text_1)
            card_text = card_text.replace('__TOTAL__',str(len(res)))
        except:
            card_text = card_text.replace('__PROPERTIES__',"")
            card_text = card_text.replace('__TOTAL__',str(0))
            card_text = card_text.replace('Title','Author')
            card_text = card_text.replace('__TITLE__',search_term)


    elif search_choice == 6:
        query_string = search_term

        res = conn.query(query_string.replace('&gt;','>'), db='neo4j')
        card_text = card_text_or[:] 

        property_text = '<hr class="mt-4">'
        property_text+= '<div class="card card-body" >'

        if res:

            
            if len(res)>15:
                property_text+='<div class = "container" style="overflow-x:scroll; overflow-y:scroll; height:500px;">'
            else:
                property_text+='<div class = "container" style="overflow-x:scroll; ">'
            c_r = 0
            c=0

            ans_dict = {}
            for i in res:
                ans_dict[c]={}
                for j in i.keys():
                    ans_dict[c][j]={}
                    if isinstance(i[j],Node):
                        for k in i[j]:
                            ans_dict[c][j][k] = i[j][k]
                    else:
                        ans_dict[c][j] = unescape(str(i[j]))
                c+=1
            ans_text =  json.dumps(ans_dict,indent=2).replace('\n','<br>')

            property_text+='<div class = "row"  >'+(ans_text)+'</div></div></div>'
            # for r in res:
            #     c_r+=1
            #     property_text+='<div class = "row"  ><xmp>'+str(c_r)+'   '+str(r)+'</xmp></div>'
            # property_text+='</div></div>'

            card_text = card_text.replace('Title','Query')
            card_text = card_text.replace('__PROPERTIES__',property_text)
            card_text = card_text.replace('__TOTAL__',str(len(res)))

        else:
            if isinstance(res,list):
                card_text = card_text.replace('__PROPERTIES__','<div class="card card-body" >No Results</div>')
            else:
                card_text = card_text.replace('__PROPERTIES__','<div class="card card-body" >Error: Incorrect Query</div>')
            card_text = card_text.replace('__TOTAL__',str(0))

        query_title = search_term[:]
        query_title = query_title.replace('(','<br>(')

        card_text = card_text.replace('__TITLE__',query_title)






    card_text = card_text.replace('__NUMBER__',str(session["query_count"]))
    card_text = card_text.replace('__TIME__',str(datetime.now()))
    return card_text



@app.route("/page/<var1>/<var2>")
def processing_page(var1,var2):
    global card_text_or



    search_choice = int(var1)
    search_term = var2

    return render_template('page.html',result=getPaperCard(search_choice,search_term)) 


@app.route("/api/calc")
def processing_query():
    global card_text_or
    conn = getDbConnection()
    card_text = card_text_or[:]

    # # TESTING
    search_choice = int(request.args.get('radio',0))

    session["query_count"]= session["query_count"]+1

    search_term = request.args.get('query', 0)


    card_text = getPaperCard(search_choice,search_term)

    return jsonify({
 
        "txt":card_text,
     
    })

if __name__ == '__main__':
    loadSheets()

    if testing:
        app.run(debug=True)
    else:
        app.run()
