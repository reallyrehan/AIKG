'''
Matheus Schmitz
DSCI 558 | Building Knowledge Graphs
Homework 1
'''

# Imports
import scrapy
from scrapy.exceptions import CloseSpider
import re
import requests
import json
import time
import random



class Crawler(scrapy.Spider):

	# Crawler name, which has to be called when running the script: scrapy crawl arxiv_crawler -o arxiv_crawler.jl
	name = 'arxiv_crawler'

	# Set the number to pages to crawl before stopping, and slow the scraper not to get banned
	custom_settings = {'DOWNLOAD_DELAY': 1.000,
					   'CLOSESPIDER_ITEMCOUNT': 10000,
	              	   'CONCURRENT_ITEMS': 500,
	              	   'CONCURRENT_REQUESTS': 100} #'FEEDS': 'csv'

	def __init__(self, *args, **kwargs):

		self.ids_to_crawl = []

		with open('../Google_Scholar/articles_graphics.json') as f:
			articles = json.load(f)

		papers = []
		for i in range(len(articles)):
		    papers.append(articles[i]['title'])

		encoded_names = []
		for paper in papers:
		    encoded_names.append(paper.replace(' ', '+'))    
		del papers

		search_urls = []
		for paper in encoded_names:
		    search_urls.append(f'https://arxiv.org/search/?query="{paper}"&searchtype=all&abstracts=show&order=-announced_date_first&size=50')
		del encoded_names

		# Header
		headers = {"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:66.0) Gecko/20100101 Firefox/66.0", 
				"Accept-Encoding":"gzip, deflate", 
				"Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
				"DNT":"1","Connection":"close", "Upgrade-Insecure-Requests":"1"} 

		for arxiv_url in search_urls:
			arxiv_search = requests.get(arxiv_url, headers = headers)
			time.sleep(abs(random.gauss(1,1)))
			paper_ids = re.findall(r'(?<=<a href="https://arxiv.org/abs/)((.|\n|\s|\S)*?)(?=">arXiv:)', arxiv_search.text)
			paper_ids = [pid[0] for pid in paper_ids]
			self.ids_to_crawl.extend(paper_ids)
		del search_urls

		with open('dois_to_crawl.txt', 'w') as f_out:
			for item in self.ids_to_crawl:
				f_out.write(f'{str(item)}\n')

	# Parse arXiv extracting a specific set of papers based on their paper ids
	def start_requests(self):

		for paper_id in self.ids_to_crawl:

		    # Use the paper ID to go directly to arXiv's api queries
		    paper_xml = 'https://export.arxiv.org/api/query?id_list=' + paper_id

		    # Request that page and pass it to the find_biography
		    paper_details = scrapy.Request(url=paper_xml, callback=self.paper_parser)

		    # Then output a json (dict) to the linked json (.jl) file
		    yield  paper_details

	'''	
	# Parse arXiv starting from jan 01 2021 onwards              	 
	def start_requests(self):
		self.i = 0
		while True:

			# Request the desired page, the link already has a filter to select only comedy and drama genres
			response = requests.get(f'https://export.arxiv.org/list/cs/21?skip={self.i}&show=50')

			# Use regex to find the desired XML tag (xml parsing will not work as page's xml is broken)
			paper_paths = re.findall(r'(?<=<span class="list-identifier"><a href=").*?(?=" title="Abstract">)', response.text)

			# Loop through the papers
			for paper in paper_paths:

			    # Extract the paper id from the url
			    paper_id = paper.split('/')[-1]

			    # Use the paper ID to go directly to arXiv's api queries
			    paper_xml = 'https://export.arxiv.org/api/query?id_list=' + paper_id

			    # Request that page and pass it to the find_biography
			    paper_details = scrapy.Request(url=paper_xml, callback=self.paper_parser)

			    # Then output a json (dict) to the linked json (.jl) file
			    yield  paper_details

			# Whevever scrapy finishes extracting data from a set of pages, go to the next set
			self.i += 50
	'''
	
	def paper_parser(self, response):
		'''
		if self.i >= 150:
			raise CloseSpider('Crawling finished.')
		'''
		# Extract the data using regex on the XML tags, because everything else fails on this website's broken pages (if I sound frustrated, trust your insticts)
		url = re.findall(r'(?<=<id>)((.|\n|\s|\S)*?)(?=</id>)', response.text)
		updated = re.findall(r'(?<=<updated>)((.|\n|\s|\S)*?)(?=</updated>)', response.text)
		published = re.findall(r'(?<=<published>)((.|\n|\s|\S)*?)(?=</published>)', response.text)
		title = re.findall(r'(?<=<title>)((.|\n|\s|\S)*?)(?=</title>)', response.text)
		summary = re.findall(r'(?<=<summary>)((.|\n|\s|\S)*?)(?=</summary>)', response.text)
		authors = re.findall(r'(?<=<name>)((.|\n|\s|\S)*?)(?=</name>)', response.text)
		categories = re.findall(r'(?<=<category term=")((.|\n|\s|\S)*?)(?=" scheme="http://arxiv.org/schemas/atom"/>)', response.text)
		#((.|\n)*?)
		#[\s\S]*?
		#((.|\n|\s|\S)*?)

		# Filter results
		url = url[1][0]
		updated = updated[1][0]
		published = published[0][0]
		title = title[0][0].replace("\r", "").replace("\n", "")
		summary = summary[0][0].replace("\r", "").replace("\n", "")
		authors = [aut[0] for aut in authors]
		categories = [cat[0] for cat in categories]

		# Write to the csv file
		yield {'url': url,
				'updated': updated,
				'published': published,
				'title': title,
				'summary': summary,
				'authors': authors,
				'categories': categories}
		pass