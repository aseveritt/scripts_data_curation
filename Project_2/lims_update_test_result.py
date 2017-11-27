import psycopg2, bcrypt, gspread, datetime, sys, re, time
import argparse
import pandas as pd
import numpy as np
from sqlalchemy import *
from sqlalchemy_utils import database_exists, create_database
from sqlalchemy.sql.expression import func
from sqlalchemy.orm import sessionmaker
from df2gspread import gspread2df as g2d
from oauth2client.service_account import ServiceAccountCredentials
pd.options.mode.chained_assignment = None

from table_structure import insert_all, insert_results, insert_batches, insert_batch_object 
from connect_labware import connect_LABWARE

def get_GS():
	"""
	CALLED BY: main()
	FUNCTION: Calls three functions to grab required data from Insight google sheet and Manual LIMS google sheet. 
		  Merges the seperate dataframes on the sampleID (aka LabelID), but retains any inconsistnecies between dataframes.
	RETURNS:  A pandas dataframe with 19 columns 
	"""

        df1 = get_insight_GS()
        print ("Done collecting data from insight gs")

        df2 = get_manual_GS()
        print ("Done collecting data from manual gs")

        df = pd.merge(df1,df2, on='sampleID', how = 'outer') #merge on outer so that all samples are kept
	df = df.head(n=15)
	#df = df[2878:] 

	print ("Curating Data frame ....")
	df = clean_df(df)

        return (df)

def get_insight_GS():
	"""
        CALLED BY: get_GS()
        FUNCTION: Using df2gspread module, it uploads all Insight google sheet information into a pandas dataframe.
		  The data frame column names are removed, renamed with static names, and subset into needed data
		  Removes any row with a blank sampleID field
        RETURNS:  A pandas dataframe with 9 columns
        """

	#LOAD DATA
	
	Insight_GS = '' #FIX ME ADD LINK EDITING INFO
	Insight_name = '' #FIX ME ADD GOOGLE SHEET NAME
	insight_df = g2d.download(Insight_GS, Insight_name)   #upload df
	
	#SUBSET DATA NEEDED
	insight_df.drop( insight_df.index[0], inplace = True)  #drop column names
	insight_df.columns = ['A','B','C','D','E','F','G','H','I','J','K','L','M','N']  #rename columns to match GS
	df = insight_df[['B','E','F','G','H','I','J','K','L']]   #subset
	df.columns = ['sampleID','pre_seq_QC', 'seq_start','seq_finish','post_seq_QC', 'reseq_start','reseq_finish', 'reseq_QC','reason']
		
	#CLEAN DATA
	df = df.loc[df['sampleID'] != ""]   #missing sample ID

	return (df)

def get_manual_GS():
        """
        CALLED BY: get_GS()
        FUNCTION: Using df2gspread module, it uploads all Manual google sheet information into a pandas dataframe.
                  The data frame column names are removed, renamed with static names, and subset into needed data
                  Removes any row with a blank sampleID field
		  Adds a generated index column, which reflects the index used on the google sheet originally -- needed later for fetching hyperlink data
        RETURNS:  A pandas dataframe with 11 columns
        """

	#LOAD DATA
	Manual_GS = '' #FIX ME ADD LINK EDITING INFO
	Manual_name = '' #FIX ME ADD GOOGLE SHEET NAME
        manual_df = g2d.download(Manual_GS, Manual_name)
	
	#SUBSET DATA NEEDED
	manual_df.drop( manual_df.index[0], inplace = True)  #drop column names
	manual_df.columns = ['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z','AA','AB','AC','AD','AE']
        df = manual_df[['A','B','C','E','G', 'I','P','Q','S','X']]
        df.columns = ['batch','date_received', 'sampleID','status','barcode_set', 'rna_conc','qubit_conc','second_pico','lib_len','dna_fa']
	
	#CLEAN DATA
	df['index'] = df.index + 1 #so now its like GS   #need true index to fetch hyperlink, important to include step here so that index is not skewed in merging
	df = df.loc[df['sampleID'] != ""] #missing sample ID

        return (df)

def clean_df(df):
        """
        CALLED BY: get_GS()
        FUNCTION: Takes in required pandas data frame and removes any rows missing status fields, replaces 'too low' entries with 0.0, 
		  makes the accepted, pass, and batch status consistent across df, removes rows that occur twice or are the second aloquot (only 6 cases),
		  and finally fetches the hyperlink for required columns
        INPUT: A pandas dataframe with 19 columns
	RETURNS:  A pandas dataframe with 19 columns
        """
	#FILL NAN WITH ACCEPTABLE FILLER	
	df = df.replace(np.nan, "", regex=True)

        #REMOVE IF NO RECEIVED STATUS OR SAMPLE ID
        df = df.loc[df['status'] != ""]

        #MAKE ANY "TOO LOW" VALUES, INTO NUMERIC 0.0
        mapping = {'too low': float(0.0), 'Too low': float(0.0), 'Too Low' :float(0.0)}
        df = df.replace({'rna_conc': mapping, 'lib_len': mapping, 'qubit_conc':mapping})

        #STANDARDIZE ACCEPTED STATUS  #rejected is actually cancelled in manual lims
        mapping = {'Accepted' :"A", 'Rejected' : "R", 'REJECTED': "R"}
        df = df.replace({'status': mapping})

        #STANDARDIZE PASS STATUS
        mapping = {'Pass' : "PASS", 'Fail' :"FAIL"}
        df = df.replace({'pre_seq_QC':mapping, 'post_seq_QC' : mapping})

        #STANDARDIZE BATCH STATUS
        df['batch'] = df.apply(lambda row: fix_batch(row['batch']), axis = 1)

	#FILL EMPTY REASON and BARCODE SETS
	df['barcode_set'] = df['barcode_set'].replace("n", "", regex = True)
	df['reason'] = df['reason'].replace(to_replace = "", value="None provided")
	
	##IMPROVE ME
	#REMOVE SPECIAL CASES UNTIL ANDY SPECIFIES HOW HE WOULD LIKE ME TO HANDLE THEM
	df= df[df['sampleID'].isin(df['sampleID'].value_counts()[df['sampleID'].value_counts()==1].index)]  #remove the 1 entry that occurs twice
	df = df[~df['sampleID'].str.contains('_')]    #remove the 5 entries that have underscores in the name 

	#GET HYPERLINKS FOR DNA_FA
        df = get_hyperlink(df)

	return (df)

def fix_batch(x): 
        """
        CALLED BY: clean_df()
        FUNCTION: extracts numeric values from string
	INPUT: String
	RETURNS: Integer
	"""
	x = str(x)
        numbers = re.findall(r'\d+',x)  #grab all numbers from string
        if (len(numbers) == 0):
                return ("")
        else:
                for i in numbers:
			i = int(i)
			if (i >= 10 and i != 11): #WHAT TO DO WITH BATCH 11
				return (str(i)+"-N88")
			elif (i < 10) :
				return (str(i)+"-N56")
			else:
                        	return (str(i))

def get_hyperlink(df):
        """
        CALLED BY: clean_df()
        FUNCTION: using gs_spread modole, loads the manual google sheet as a 'worksheet'. retrieves forumula value for every cell in column X where the value
                  is not Cancelled or empty
        INPUT: pandas df with 'dna_fa' column
        RETURNS: String
        """
        #USE GS_SPREAD TO GET HYPERLINK (NO WAY WITH DF2GSPREAD)
        scope = ['https://spreadsheets.google.com/feeds']
	credentials = ServiceAccountCredentials.from_json_keyfile_name('ABSOLUTE PATH TO CLIENT_SERVER.JSON FILE',scope)  #FIX ME

        gc = gspread.authorize(credentials)
        w = gc.open_by_key('INTEGERS LINKING TO EDITING INFO').worksheet("GS NAME") #FIX ME

        #ITERATE THROUGH AND GRAB HYPERLINKS IF NEEDED
        for index, row in df.iterrows():
                if "DNA" in str(row['dna_fa']).upper():
                        dna_link = (w.acell('X{}'.format(row['index'])).input_value).split('"')[1]
                        df.set_value(index,'dna_fa', dna_link)

        return (df)			

def isFloat(string):
        """
        CALLED BY: update_labware(), insert_all_tests(), insert_all_results()
	INPUT: String
        RETURNS:  True if string can be converted to float, False if string cannot
        """
	try:
        	float(string)
        	return True
    	except ValueError:
        	return False


def update_labware(df, tests, results, engine, samples, batches, batch_objects):
        """
        CALLED BY: main()
	CALLS: get_sample_numbers(), insert_all(), find_missing_tests(), check_for_updates(), delete_tests(), update_sample_status(), update_batch_status()
	FUNCTION: For every row in the pandas dataframe, retrieve all tests associated with the three aloquots associated with the parent sample (row['sampleID']),
		  If there are NO tests associated, add all 9 test and 15 results
		  If there are tests associated, check to make sure they are none missing (if there are missing, insert them, if there are extra-- print error message),
		  If all tests are found, check to make sure entries for results are correct (if not, delete tests/results and reinsert ones with correct values
		  Update sample status for all three aloquots
		  Update batch_object table for all three aloquots and parent sample
        INPUT: pandas dataframe, test table structure, result table structure, labware engine, sample table structure, batch table structure, batch objects table structure
	RETURNS: 
	"""
	count = 0
	add_all =  0
	add_some = 0
	errors = []
	up_to_date = 0
	updated = 0
	batch_count = 0
	batch_o_count = 0
	

        default_analysis = {"RIBO_GREEN":1, "PICO_GREEN":2, "FRAGMENT_ANALYZER":3, "PICO_GREEN_2":4,\
                        "NANOMOLAR_CONC":5, "SEQUENCING":6, "DEMULTIPLEXING_RPT":7, "STORAGE1":8, "STORAGE2":9}

	#FOR EVERY SAMPLE
	for index,row in df.iterrows():
		count += 1
		al1, al2, al3, parent_num = get_sample_numbers(row['sampleID'], samples)  #get sample numbers associated with all aloquots from base
		if (al1 == 0):
			errors.append("BREAKING AND NOT EVALUATING LABEL ID {}".format(row['sampleID'])) #RENE
			continue
		print (al1, al2, al3, row['sampleID'])
		#print (row['sampleID'])
		s = select([tests.c.analysis], tests.c.sample_number.in_((al1,al2,al3)))
		
		#IF SAMPLE HAS NO TESTS,  ADD THEM ALL
		if (s.scalar() == None):
			add_all += 1
			for i in range(1,8):   #because 9 tests under aloquot 1
				insert_all(tests, results, engine, i, get_test_num(tests), get_result_num(results), row, al1)
			insert_all(tests, results, engine, 8, get_test_num(tests), get_result_num(results), row, al2) 		#add storage 1 under al2 
			insert_all(tests, results, engine, 9, get_test_num(tests), get_result_num(results), row, al3)		#add storage 2 under al3
		else:
			missing_set, default_set = find_missing_tests(s, engine, default_analysis)		#function: check for any missing/unexpected tests
		
			#IF SAMPLE IS MISSING TESTS, ADD THE TESTS/RESULTS NEEDED
			if (len(missing_set) != 0):
				for i in missing_set:			#for each missing test (in set)
                			if (i in default_set): 		#is test is in missing default(so missing test that should be there)
                        			j = default_analysis[i]	#get key from dict, so that you can insert the test, here j is the integer specifying which test to add	
						if (j < 8): insert_all(tests, results, engine, j, get_test_num(tests), get_result_num(results), row, al1) 
						if (j == 8): insert_all(tests, results, engine, 8, get_test_num(tests), get_result_num(results), row, al2)
						if (j == 9): insert_all(tests, results, engine, 9, get_test_num(tests), get_result_num(results), row, al3)
						add_some +=1
                			else:
                        			errors.append("ERROR: sample number {} has unexpected test {} -- no action taken".format(sample_num, i))		
			
			#IF SAMPLE HAS ALL TESTS, CHECK IF THE RESULTS ARE UP-TO-DATE
			else:
				need_to_update = check_for_updates(results, al1, row)  #function: check for inconsistent results under aloquot 1, return list of analysis
				#print ("the list of results with different values are:", need_to_update)
                                if (len(need_to_update) == 0):		up_to_date +=1
                                else:   
                                        updated +=1
                                        for i in need_to_update:	#for every test that the results need to be updated
                    			        engine.execute(tests.delete().where(tests.c.sample_number == '{}'.format(al1)).where(tests.c.analysis == '{}'.format(i)))
        					engine.execute(results.delete().where(results.c.sample_number == '{}'.format(al1)).where(results.c.analysis == '{}'.format(i)))
                                                insert_all(tests, results, engine, default_analysis[i], get_test_num(tests), get_result_num(results), row, al1) 		#insert new test
	
		
		#UPDATE SAMPLE STATUS
		update_sample_status(parent_num, al1, al2, al3, row, samples,engine)		
	
		#UPDATE BATCH TABLE							#function: checks if each aloquot and parent are listed in batch_objects table	
		i_batch, i_batch_o = update_batch_status(batches, batch_objects, engine, row, al1)
		batch_count = batch_count + i_batch
		batch_o_count = batch_o_count + i_batch_o
		
	return (count, up_to_date, add_all, add_some, updated, errors, batch_count, batch_o_count)


def get_sample_numbers(base, samples):
        """
        CALLED BY: update_labware()
        FUNCTION:  For base, aloquot 1, aloquot 2, and aloqot 3 retrieve their sample number from sample table
        INPUT: integer corresponding to parent samples text ID and the sample table structure
        RETURNS: Four integers
        """
	alo_1, alo_2, alo_3, parent_num = "a","b","c","d"   #purposely incorrect
	s = samples.select(samples.c.label_id == '{}'.format(base))
	for row in s.execute():
                text_id = row['text_id']
               	sample_num = row['sample_number']
               	if text_id.endswith('-1'):
               		alo_1 = sample_num
		elif text_id.endswith('-2'):
               		alo_2 = sample_num
		elif text_id.endswith('-3'):
               		alo_3 = sample_num
		else:
               		parent_num = sample_num
	if (isFloat(alo_1) and isFloat(alo_2) and isFloat(alo_3) and isFloat(parent_num)):
		return (alo_1, alo_2, alo_3, parent_num)
	else:
		print ("ERROR: UNABLE TO FIND ALIQUOTS ASSOCIATED WITH LABEL ID {}".format(base))
		return (0,0,0, parent_num)

def find_missing_tests(s, engine, default_analysis): 
        """
        CALLED BY: update_labware()
        FUNCTION: Constructs a dictionary which contains all the tests associated with all 3 aloquots. Converts this dictionary into a set, 
		  Produces a set which is contains all the differences between the expected and observed sets
	INPUT: Three select statements, labware engine, and a dictionary of expected analysis: value pairs
	RETURNS:  A set with keys representing analysis names that are missing, a set with keys representing the expected analysis names
        """
	analysis = {}
	for row in s.execute():
		analysis[row.analysis] = 0

	expected= set(default_analysis.keys())
	observed  = set(analysis.keys())
	missing_set = expected.symmetric_difference(observed) #set of all the key differences
	return (missing_set, expected)


def check_for_updates(results, al1, row):
        """
        CALLED BY: update_labware()
        FUNCTION: For all analysis associated with aloquot 1, if the current results in labware DO NOT match the results shown in 
		  the dataframe from google sheets, then add a string (representing the analysis name) to a list.
		  FYI labware automatically rounds float to 10th place (hints the %.10f)
	INPUT: result table structure, aloquot 1 sample number, row of df
	RETURNS: List (containing analysis names)
	"""
	delete_list = []
	s = results.select(results.c.sample_number == '{}'.format(al1))
	for r in s.execute():
		if (r.entry != None):
			if (r.analysis == "RIBO_GREEN" and r.entry != row['rna_conc']):			delete_list.append("RIBO_GREEN")
			if (r.analysis == "PICO_GREEN" and r.entry != str(row['qubit_conc'])):		delete_list.append("PICO_GREEN")
			if (r.analysis == "FRAGMENT_ANALYZER" and r.entry != row['dna_fa'] and r.entry != row['lib_len']): 	delete_list.append("FRAGMENT_ANALYZER")
			if (r.analysis == "PICO_GREEN_2" and r.entry != row['second_pico']):		delete_list.append("PICO_GREEN_2")
			if (r.analysis == "NANOMOLAR_CONC" and isFloat(row['second_pico']) and \
				isFloat(row['lib_len']) and \
				float(r.entry) != float("%.10f" % ((float(row['second_pico']) * 1000000) / (float(row['lib_len']) * 660)))):	delete_list.append("NANOMOLAR_CONC")
			if (r.analysis == "SEQUENCING" and r.entry!= row['pre_seq_QC'] and \
				r.entry != row['seq_start'] and r.entry != row['seq_finish'] and \
				r.entry != row['post_seq_QC'] and r.entry != row['reseq_start'] and \
				r.entry != row['reseq_finish'] and r.entry != row['reseq_QC'] and \
				r.entry != row['reason']):		delete_list.append("SEQUENCING")
		
	return (delete_list)

def get_test_num(tests):
	"""
        CALLED BY: update_labware(), update_increment() 
	RETURNS:  Integer  (the max integer from test number column in labware test table)
        """
	x = (func.max(tests.c.test_number)).scalar()
	if x == None:
		return 1
	else:
		return x+1	


def get_result_num(results):
        """
        CALLED BY: update_labware(), update_increment()
        RETURNS:  Integer  (the max integer from result number column in labware test table)
        """
	x = (func.max(results.c.result_number)).scalar()
        if x == None:
                return 1
        else:
                return x+1 


def update_sample_status(parent, al1, al2, al3, row, samples, engine):
        """
        CALLED BY: update_labware()
	FUNCTION: For aloquot 1, set sample status to be In Progress, unless recieved status is Rejected. 
		  For aloquot 2 and 3, set sample status as Complete
	INPUT: Three integers, row of df, sample table structure, labware engine
        RETURNS: Nothing
	"""
	
	#three conditions that fail a sample
	if row['status'] == 'R' or row['pre_seq_QC'] == 'FAIL' or row['reseq_QC'] == 'FAIL':
		print ("FAILING PARENT AND ALIQUOT")
		engine.execute(update(samples).where(samples.c.sample_number == '{}'.format(al1)).values(status = 'R', description = '{}'.format(row['reason'])))
		engine.execute(update(samples).where(samples.c.sample_number == '{}'.format(parent)).values(status = 'R', description = '{}'.format(row['reason'])))
	else:
		engine.execute(update(samples).where(samples.c.sample_number == '{}'.format(al1)).values(status = 'P'))  #never complete bc demultiplex
		engine.execute(update(samples).where(samples.c.sample_number == '{}'.format(parent)).values(status = 'P'))
	
        engine.execute(update(samples).where(samples.c.sample_number == '{}'.format(al2)).values(status = 'C'))	
        engine.execute(update(samples).where(samples.c.sample_number == '{}'.format(al3)).values(status = 'C'))	

def update_batch_status(batches, batch_objects, engine, row, al1):
	"""
	CALLED BY: update_labware()
	FUNCTION: For row provided, check if batch number is in batch table, if not insert it
		  For row provided, check if all four sample number is in batch objects table, if not insert it
	INPUT: batch table structure, batch object structure, labware engine, list: dataframe row, four integers representing four possible sample numbers 
	RETURNS: two integer counts
	"""
	count_batch_objects = 0
        count_batches = 0
	batch_num, order_num = row['batch'], row['barcode_set']
	
	#ISFLOAT BARCODE SET WILL BRING UP ERRORS BECAUSE N AND BLANK
	if (batch_num and isFloat(order_num)):
		#CHECK FOR BATCH TABLE
		s = batches.select(batches.c.name == '{}'.format(batch_num))
		if (s.scalar() == None):   #if doesnt already exits
        		count_batches += 1
                	print ("NEED TO ENTER BATCH NUMBER:", batch_num)
                	insert_batches(batches, engine, batch_num)	

		#CHECK FOR BATCH OBJECTS
        	s = batch_objects.select(batch_objects.c.sample_number == '{}'.format(al1))
		if (s.scalar() == None):
			count_batch_objects += 1
               		#print ("NEED TO ENTER BATCH OBJECT FOR SAMPLE NUMBER:", al1)
	       		insert_batch_object(batch_objects, engine, al1, batch_num, order_num)
	return (count_batches, count_batch_objects)
		

	
def update_increment(increments, engine, tests, results):
        """
        CALLED_BY: main()
        FUNCTION: retrieve the max test number and result number (from test and result table) and update the labware
                  increment table accordingly
        INPUT: increment table structure, labware engine, test table structure, result table structure
        RETURN: Nothing
        """
        engine.execute(update(increments).where(increments.c.name == 'TEST_NUMBER').values(value = '{}'.format(get_test_num(tests))))
        engine.execute(update(increments).where(increments.c.name == 'RESULT_NUMBER').values(value = '{}'.format(get_result_num(results))))



def add_test_to_unreceived(samples,tests,results,engine):
	d = {'date_received': ["NONE"], 'rna_conc': [""], 'qubit_conc':[""],'second_pico':[""],'lib_len':[""],'dna_fa': [""], 'pre_seq_QC': [""], 'seq_start': [""],'seq_finish': [""],'post_seq_QC': [""], 'reseq_start': [""],'reseq_finish': [""], 'reseq_QC': [""] ,'reason': [""]}
	temp_df = pd.DataFrame(data = d)
	s = samples.select(samples.c.status == 'U')
	for index, row in temp_df.iterrows():
		for r in s.execute():
			parent_num = r['sample_number']
			print (parent_num)
			engine.execute(tests.delete().where(tests.c.sample_number == '{}'.format(parent_num)))
			engine.execute(results.delete().where(results.c.sample_number == '{}'.format(parent_num)))
			for i in range(1,10):
				 insert_all(tests, results, engine, i, get_test_num(tests), get_result_num(results), row, parent_num)
			engine.execute(update(samples).where(samples.c.sample_number == '{}'.format(parent_num)).values(aliquot = 'T'))
			engine.execute(update(tests).where(tests.c.sample_number == '{}'.format(parent_num)).values(primary_in_spec = 'T'))


def main(p_commit=False):
	engine, samples, tests, results, increments, batch_objects, batches = connect_LABWARE(p_commit)
	print "connected to labware"
	#add_test_to_unreceived(samples,tests,results,engine)
	df = get_GS()	 
	print (len(df))
	count, up_to_date, add_all, add_some, updated, errors_t, batch_count, batch_o_count = update_labware(df,tests,results, engine, samples, batches, batch_objects) 
	print ("{} entries in Manual Lims\n".format(count)+
               "{} entries were up-to-date in test table\n".format(up_to_date) +
               "{} entries need all 8 tests and 15 results added to labware\n".format(add_all) +
               "{} entries need less than 8 tests and results added to labware\n".format(add_some) +
               "{} entries needed the the results fields updated\n".format(updated) +
	       "{} errors need to be addressed:\n{}".format(len(errors_t), ("\n".join(errors_t))) 
                )

	print ( "REGARDING BATCHES\n" +
		"{} batch object entries were inserted\n".format(batch_count) +
		"{} batch entries were inserted\n".format(batch_o_count)
		)	

	update_increment(increments, engine, tests, results)


if __name__ == '__main__':
	parser = argparse.ArgumentParser(
        	description=__doc__,
        	formatter_class=argparse.RawDescriptionHelpFormatter)
	parser.add_argument('-C', help='Commit changes to db', action='store_true', dest='commit', default=False)
	#parser.add_argument('-U', help='Add tests to unreceived samples', action='store_true', dest='commit', default=False)
	#POSSIBLE ADDITION
	args = parser.parse_args()
	main(args.commit)
