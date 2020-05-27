#####
# Created by Blair Bilodeau
# Last modified May 22, 2020

#####
# Examples of running arxiv_search_function.py and biomedrxiv_search_function.py
# Place file in the same folder as function files
# Can run each individually, or comment out all but 1 to run from command line

import arxiv_search_function as asf
import biomedrxiv_search_function as bmsf
import datetime

records_df = asf.arxivsearch(
	start_date = datetime.date.today().replace(day=1), 
 	end_date = datetime.date.today(), 
	subjects = ['cs','stat'], 
	kwd_req = ['online', 'regret'], 
	kwd_exc = [], 
	kwd_one = [['adaptive','data-dependent']], 
	max_records = 50, 
	max_time = 300,
	cols = ['id', 'title', 'categories', 'abstract', 'authors', 'date'])

records_df2 = asf.arxivsearch(
	start_date = datetime.date.today().replace(day=1), 
 	end_date = datetime.date.today().replace(day=22), 
	subjects = ['cs','stat'], 
	kwd_req = ['GAN', 'unsupervised'], 
	kwd_exc = [], 
	kwd_one = [['theory', 'impossibility', 'sample complexity', 'ycleGAN']], 
	max_records = 50, 
	max_time = 300,
	cols = ['id', 'title', 'categories', 'abstract', 'authors', 'date'],
	export = '/Users/blairbilodeau/Desktop/arxiv/')

records_df3 = bmsf.biomedrxivsearch(
	start_date = datetime.date.today().replace(day=1), 
	end_date = datetime.date.today(), 
	journal = 'biorxiv',
	subjects = [], 
	kwd = ['domain', 'Single-Cell'], 
	kwd_type = 'all',
	abstracts=True,
	athr = [], 
	max_records = 50,
	max_time = 300)

records_df4 = bmsf.biomedrxivsearch(
	start_date = datetime.date(2020,5,1), 
	end_date = datetime.date(2020,5,12), 
	journal = 'medrxiv',
	subjects = ['Sports Medicine'], 
	kwd = ['brain'], 
	kwd_type = 'all',
	abstracts=True,
	athr = [], 
	max_records = 50,
	max_time = 300)