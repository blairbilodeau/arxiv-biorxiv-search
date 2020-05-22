#####
# Created by Blair Bilodeau
# Last modified May 22, 2020

#####
# Examples of running arxiv_search_function.py
# Place file in the same folder as arxiv_search_function.py
# Can run each individually, or comment out all but 1 to run from command line

import arxiv_search_function as asf
import biorxiv_search_function as bsf
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
 	end_date = datetime.date.today(), 
	subjects = ['cs','stat'], 
	kwd_req = ['GAN', 'unsupervised'], 
	kwd_exc = [], 
	kwd_one = [['theory', 'impossibility', 'sample complexity', 'ycleGAN']], 
	max_records = 50, 
	max_time = 300,
	cols = ['id', 'title', 'categories', 'abstract', 'authors', 'date'])

records_df3 = bsf.biorxivsearch(
	start_date = datetime.date.today().replace(day=1), 
	end_date = datetime.date.today(), 
	journal = 'both',
	subjects = [], 
	kwd = ['domain', 'Single-Cell'], 
	kwd_type = 'all',
	abstracts=True,
	athr = [], 
	max_records = 50,
	max_time = 300)