#####
# Created by Blair Bilodeau
# Last modified May 11, 2020

#####
# Inspired by:
# https://pypi.org/project/arxiv-checker/
# https://github.com/mahdisadjadi/arxivscraper (more useful)

#####
# Resources:
# https://arxiv.org/help/api
# https://arxiv.org/help/oa/index
# http://www.openarchives.org/OAI/openarchivesprotocol.html

######################################################################

## packages
import pandas as pd
import datetime
import time
import sys
import string
import gc
import requests
import xml.etree.ElementTree as ET
from urllib.parse import urlencode
from urllib.request import urlopen
from urllib.error import HTTPError

#######
## Main function
## Parameters:
# sdate 	   - datetime object 		- starting date of search period 
# fdate 	   - datetime object 		- end date of search period
# kwd_req	   - list of str            - keywords that are required to be in the title or abstract
# kwd_exc	   - list of str            - keywords that must not be in the title or abstract
# kwd_one	   - list of lists of str   - keywords of which at least one must be included
# athr_req	   - list of str            - authors which are required
# athr_exc	   - list of str            - authors to exclude
# athr_one	   - list of lists of str   - authors of which one must be included
# subjects	   - list of str 			- subject options are:
#											astro-ph, cond-mat, gr-qc, hep-ex, hep-lat, hep-ph, hep-th, math-ph, nlin, nucl-ex, nucl-th, 
#											physics, quant-ph, math, cs, q-bio, q-fin, stat
# max_records  - int             		- maximum number of results to return
# max_time 	   - float           		- maximum amount of seconds to be spent searching 
# cols 		   - list            		- arxiv fields to extract
#				  							column options are:
#				  							id, url, title, authors, date, abstract, categories
# export       - str             		- folder location to dump results list in csv
# exportfile   - str			 		- by default the file name will be today's date, but you can override this with exportfile
# download     - str             		- folder location to dump returned pdfs into
#								 			(files named using year_lastname format)

def arxivsearch(start_date = datetime.date.today().replace(day=1), 
	end_date = datetime.date.today(), 
	kwd_req = [], 
	kwd_exc = [], 
	kwd_one = [],
	athr_req = [], 
	athr_exc = [], 
	athr_one = [], 
	subjects = ['cs'], 
	max_records = 50, 
	max_time = 300,
	cols = ['id', 'title', 'authors', 'date', 'categories', 'abstract'],
	export = '',
	exportfile = '',
	download = ''):

	## keep track of timing
	overall_time = time.time()

	## urls
	OAI = '{http://www.openarchives.org/OAI/2.0/}'
	ARXIV = '{http://arxiv.org/OAI/arXiv/}'
	BASE = 'http://export.arxiv.org/oai2?verb=ListRecords&'

	## format dates
	start_date = str(start_date)
	end_date = str(end_date)

	## format inputs
	kwd_req = set([keyword.lower() for keyword in kwd_req]) 
	kwd_exc = set([keyword.lower() for keyword in kwd_exc]) 
	kwd_one = [set([keyword.lower() for keyword in kwd_one_list]) for kwd_one_list in kwd_one]

	athr_req = set([author.lower() for author in athr_req]) 
	athr_exc = set([author.lower() for author in athr_exc]) 
	athr_one = [set([author.lower() for author in athr_one_list]) for athr_one_list in athr_one]  

	## dataframe to store results
	if download != '' and 'date' not in cols:
		cols = cols + ['date'] # make sure date is stored if downloading PDFs
	records_df = pd.DataFrame(columns=cols)

	## loop over all subjects
	for subject in subjects:

		subject_time = time.time()

		# set url to extract papers from this subject
		subject = subject.lower()
		url = BASE + 'from=' + start_date + '&until=' + end_date + '&metadataPrefix=arXiv&set=%s' %subject

		## OAI only lets you parse 1000 records at a time, so loop through these until parsed all records
		k = 1
		while True:

			# keep user aware of status
			print('Searching records {:d} to {:d} from {:s}...'.format(1000 * (k-1) + 1, 1000*k, str(subject))) 

			## error handling for opening and closing URL
			try:
				url_response = urlopen(url)
				xml = url_response.read() # get raw xml data from server
				gc.collect()
			except HTTPError as e:
				# handle service unavailable error for requesting too often
				if e.code == 503:
					retry_time = int(e.hdrs.get('retry-after', 30))
					print('Got 503. Retrying after {0:d} seconds.'.format(retry_time))
					time.sleep(retry_time + 1)
					continue
				# if it's a different error, just have to raise it
				else:
					raise

			k += 1

			xml_root = ET.fromstring(xml) # get root of xml hierarchy
			records = xml_root.findall(OAI + 'ListRecords/' + OAI + 'record') # list of all records from xml tree

			## extract metadata for each record
			metadata = [record.find(OAI + 'metadata').find(ARXIV + 'arXiv') for record in records]

			## use metadata to get info for each record
			titles = [meta.find(ARXIV + 'title').text.strip().lower().replace('\n', ' ') for meta in metadata]
			dates = [meta.find(ARXIV + 'created').text.strip() if meta.find(ARXIV + 'updated') is None else meta.find(ARXIV + 'updated').text.strip() for meta in metadata]
			ids = [meta.find(ARXIV + 'id').text.strip().lower().replace('\n', ' ') for meta in metadata]
			abstracts = [meta.find(ARXIV + 'abstract').text.strip().lower().replace('\n', ' ') for meta in metadata]
			category_lists = [meta.find(ARXIV + 'categories').text.strip().lower().replace('\n', ' ').split() for meta in metadata]
			urls = ['https://arxiv.org/abs/' + meta.find(ARXIV + 'id').text.strip().lower().replace('\n', ' ') for meta in metadata]
			author_lists = [meta.findall(ARXIV + 'authors/' + ARXIV + 'author') for meta in metadata]

			## extract first and last names, clean them, and put them together to make human readable
			last_name_lists = [[author.find(ARXIV + 'keyname').text.lower() for author in author_list] for author_list in author_lists]
			first_name_meta_lists = [[author.find(ARXIV + 'forenames') for author in author_list] for author_list in author_lists]
			first_name_lists = [['' if name == None else name.text.lower() for name in first_name_meta_list] for first_name_meta_list in first_name_meta_lists]
			full_name_temp_lists = [zip(a,b) for a,b in zip(first_name_lists, last_name_lists)]
			full_name_lists = [[a+' '+b for a,b in full_name_temp_list] for full_name_temp_list in full_name_temp_lists]

			## compile all info into big dataframe
			records_data = list(zip(titles, dates, ids, abstracts, category_lists, urls, full_name_lists))
			temp_df = pd.DataFrame(records_data,columns=['title','date','id','abstract','categories','url','authors'])

			### want to find only indices that correspond to desired papers
		
			## merge abstracts and titles into one big text blob without punctuation to search for keywords in
			abstract_title_concats = [title+'. '+abstract for title,abstract in zip(titles,abstracts)]
			
			### Choose indices to match keywords and authors

			## only abstracts and titles that have intersection with required categories
			if len(kwd_one) > 0:
				# for each kwd_one list take indexes such that title/abstract intersect with the list
				kwd_one_idxs_lists = [set([idx for idx,val in enumerate(list(map(lambda x: any([kwd in x for kwd in kwd_one_list]), abstract_title_concats))) if val]) for kwd_one_list in kwd_one]
				# take intersection of all the kwd_one index sets
				kwd_one_idxs = kwd_one_idxs_lists[0].intersection(*kwd_one_idxs_lists) 
			else:
				kwd_one_idxs = set(range(len(abstract_title_sets)))
			if len(kwd_req) > 0:
				kwd_req_idxs = set([idx for idx,val in enumerate(list(map(lambda x: all([kwd in x for kwd in kwd_req]), abstract_title_concats))) if val])
			else:
				kwd_req_idxs = set(range(len(abstract_title_sets)))
			if len(kwd_exc) > 0:
				kwd_exc_idxs = set([idx for idx,val in enumerate(list(map(lambda x: all([kwd not in x for kwd in kwd_exc]), abstract_title_concats))) if val])
			else:
				kwd_exc_idxs = set(range(len(abstract_title_sets)))

			## intersection of all keyword indices
			# annoying intersection syntax makes you pick a set to apply method to, arbitrarily chose kwd_one
			kwd_idxs = kwd_one_idxs.intersection(kwd_req_idxs, kwd_exc_idxs)

			## merge author names together into comma separated string
			full_name_concats = [(', ').join(full_name_list) for full_name_list in full_name_lists]

			## only authors that are specified as desired
			if len(athr_one) > 0:
				# for each athr_one list take indexes such that author list intersects with the list
				athr_one_idxs_lists = [set([idx for idx,val in enumerate(list(map(lambda x: any([athr in x for athr in athr_one_list]), full_name_concats))) if val]) for athr_one_list in athr_one]
				# take intersection of all the athr_one index sets
				athr_one_idxs = athr_one_idxs_lists[0].intersection(*athr_one_idxs_lists) 
			else:
				athr_one_idxs = set(range(len(full_name_sets)))
			if len(athr_req) > 0:
				athr_req_idxs = set([idx for idx,val in enumerate(list(map(lambda x: all([athr in x for athr in athr_req]), full_name_concats))) if val])
			else:
				athr_req_idxs = set(range(len(full_name_sets)))
			if len(athr_exc) > 0:
				athr_exc_idxs = set([idx for idx,val in enumerate(list(map(lambda x: all([athr not in x for athr in athr_exc]), full_name_concats))) if val])
			else:
				athr_exc_idxs = set(range(len(full_name_sets)))

			## intersection of all author indices
			# annoying intersection syntax makes you pick a set to apply method to, arbitrarily chose athr_one
			athr_idxs = athr_one_idxs.intersection(athr_req_idxs, athr_exc_idxs)
			
			## only take temp_df rows that match the desired indices for keywords and authors
			temp_df = temp_df.iloc[list(kwd_idxs.intersection(athr_idxs))]

			## merge new results into dataframe with old results, while dropping duplicate records
			records_df = pd.concat([records_df,temp_df],sort=True).drop_duplicates(subset='title', keep="first").reset_index(drop=True)[cols]

			### Ease of use handling

			## see if too much time has passed
			if time.time() - overall_time > max_time:
				print('Max time ({:.0f} seconds) reached. Fetched {:d} records from {:s} in {:.1f} seconds.'.format(max_time, len(records_df), str(subjects), time.time() - overall_time))
				return(records_df)

			## see if more records than desired have been pulled
			if len(records_df) > max_records:
				print('Max number of records ({:d}) reached. Fetched {:d} records from {:s} in {:.1f} seconds.'.format(max_records, len(records_df), str(subjects), time.time() - overall_time))
				return(records_df)

			## see if there are more records to pull in this category by checking resumptionToken
			try:
				token = xml_root.find(OAI + 'ListRecords').find(OAI + 'resumptionToken')
			except:
				break
			if token is None or token.text is None:
				break
			else:
				url = BASE + 'resumptionToken=%s' % token.text

		## keep user informed on how much time this subject has taken
		print('Fetching from {:s} is completed in {:.1f} seconds.'.format(str(subject), time.time() - subject_time))
	
	## keep user informed on how much time the whole process took
	print('Fetched {:d} records from {:s} in {:.1f} seconds.'.format(len(records_df), str(subjects), time.time() - overall_time))

	## check if user wants to export this dataframe
	if export != '':
		if exportfile == '':
			exportfile = datetime.date.today().strftime('%Y-%m-%d') + '-arxiv-metadata.csv'
		exportpath = export + exportfile
		print('Exporting records as csv to {:s}...'.format(exportpath))
		records_df.to_csv(exportpath, index=False)
		print('Export complete.')

	## check if user wants to download the pdfs
	if download != '':
		print('Downloading {:d} PDFs to {:s}...'.format(len(records_df), download))
		pdf_urls = ['https://arxiv.org/pdf/' + id + '.pdf' for id in records_df.id] # list of urls to pull pdfs from

		# create filenames to export pdfs to
		# currently setup in year_lastname format
		pdf_lastnames_full = ['_'.join([name.split()[-1] for name in namelist]) for namelist in records_df.authors] # pull out lastnames only
		pdf_lastnames = [name if len(name) < 200 else name.split('_')[0] + '_et_al' for name in pdf_lastnames_full] # make sure file names don't get longer than ~200 chars
		pdf_paths = [download + date + '_' + lastname + '.pdf' for date,lastname in zip(records_df.date, pdf_lastnames)] # full path for each file
		# export pdfs
		for paper_idx in range(len(pdf_urls)):
			response = requests.get(pdf_urls[paper_idx])
			file = open(pdf_paths[paper_idx], 'wb')
			file.write(response.content)
			file.close()
			gc.collect()
		print('Download complete.')

	## return dataframe with records and quit
	return(records_df)