import datetime

def insert_all(tests, results, engine, case, test_num, result_num, row, sample_num):
        """
        CALLED BY: main()
        FUNCTION: Establish all labware defaults for test table, depending on which case is provided, add test and ALL associated results
	INPUT: test table structure, result table structure, labware engine, integer representing which analysis, integer: test number, integer: result number,
		list: dataframe row, integer: sample number
	RETURNS:  Nothing
        """
        info = { "version": "1" , "analysis_count": "1", "group_name": "DEFAULT", "replicate_count": "1", "old_status": "I", \
                    "batch_parent_test" : "0" , "batch_sibling_test" : "0", "parent_test":"0", "prep":"F", "replicate_test":"F", \
                    "test_priority": "0", "in_spec": "T", "in_cal" :"T", "resolve_reqd" : "F", "changed_on" : "{}".format(str(datetime.datetime.now())),\
                    "stage":"NONE", "primary_in_spec": "F", "in_control" :"T", "test_list": "STOOL_RNA_LIB", "re_tested" : "F", "modified_results":"F", \
                    "aliquoted_to" : "0", "on_worksheet" : "F", "display_results" :"T", "split_replicates" :"F", "cross_sample":"F", \
                    "released" : "F", "double_entry" : "F", "child_out_spec": "F", "charge_entry": "0", "signed": "F", "batch_original_test" :"0", \
                    "test_sequence_no" : "0", \
  		    "sample_number":"{}".format(sample_num), "test_number": "{}".format(test_num), \
               	    "original_test": "{}".format(test_num), "aliquot_group":"VIOMEALQ"\
		}
	if ((row['date_received']) != "NONE"):
		info['date_received'] = row['date_received']

        #FOR ALL POSSIBLE TEST AND RESULT PAIRS-- INSERT THEM
        if (case == 1):    #RIBO GREEN - 1 result
                if (isFloat(row['rna_conc'])): stat = "C"     #if there is a result, make it complete
                else: stat = "I"
                info.update({"analysis": "RIBO_GREEN","order_number": "1", "reported_name": "Ribo Green", "status":"{}".format(stat)})
                ins = tests.insert().values(info)
                insert_results(results, engine, 1, sample_num, test_num, result_num, row)

        elif (case == 2):    #PICO GREEN - 1 result
                if (isFloat(row['qubit_conc'])): stat = "C"     #if there is a result, make it complete
                else: stat = "I"
                info.update({"analysis": "PICO_GREEN","order_number": "2", "reported_name": "Pico Green", "status":"{}".format(stat)})
                ins = tests.insert().values(info)
                insert_results(results, engine, 2, sample_num, test_num,result_num, row)

        elif (case == 3):    #FRAGMENT ANALYZER - 2 results
                if (isFloat(row['lib_len']) and row['dna_fa']): stat = "C"     #if there is a result, make it complete
                else: stat = "I"
                info.update({"analysis":"FRAGMENT_ANALYZER","order_number": "3", "reported_name": "Fragment Analyzer", "status":"{}".format(stat)})
                ins = tests.insert().values(info)
                insert_results(results, engine, 3, sample_num, test_num,result_num, row)
                result_num +=1
                insert_results(results, engine, 4, sample_num, test_num,result_num, row)

        elif (case == 4):    #PICO GREEN2 - 1 result
		if (isFloat(row['second_pico'])) : stat = "C"
		else: stat = "I"
                info.update({"analysis": "PICO_GREEN_2", "order_number": "4", "reported_name": "Pico Green 2", "status":"{}".format(stat)})
                ins = tests.insert().values(info)
                insert_results(results, engine, 5, sample_num, test_num, result_num, row)

        elif (case == 5): #NANOMOLAR_CONC - 1 result
                if (isFloat(row['lib_len']) and isFloat(row['second_pico'])): stat = "C"
                else: stat = "I"
                info.update({"analysis": "NANOMOLAR_CONC", "order_number": "5", "reported_name": "Nanomolar Concentration", "status":"{}".format(stat)})
                ins = tests.insert().values(info)
                insert_results(results, engine, 6, sample_num, test_num, result_num, row)

        elif (case == 6):   #SEQUENCING - 10 results
                if (row['seq_start'] and row['seq_finish'] and row['pre_seq_QC'] and row['post_seq_QC']) : stat = "C"
                else: stat = "I"
		info.update({"analysis": "SEQUENCING", "order_number": "5", "reported_name": "Sequencing", "status":"{}".format(stat)})
                ins = tests.insert().values(info)
                for i in range(7,17):
                        insert_results(results, engine, i, sample_num, test_num, result_num, row)
                        result_num +=1

        elif (case == 7):  #DEMULTIPLEX - 2 results
                info.update({"analysis":"DEMULTIPLEXING_RPT", "order_number": "6", "reported_name": "Demultiplexing", "status":"I"})
                ins = tests.insert().values(info)
                insert_results(results, engine, 17, sample_num, test_num, result_num, row)
                result_num += 1
                insert_results(results, engine, 18, sample_num, test_num, result_num, row)

        elif (case == 8):  #STORAGE1 - 0 result
                info.update({"analysis": "STORAGE1", "order_number": "7", "reported_name": "Storage1", "status":"C", "aliquot_group": "STORAGE1"})
                ins = tests.insert().values(info)

        elif (case == 9):  #STORAGE2 - 0 result
                info.update({"analysis": "STORAGE2", "order_number": "8", "reported_name": "Storage2", "status":"C", "aliquot_group":"STORAGE2"})
                ins = tests.insert().values(info)

        engine.execute(ins)


def insert_results(results, engine, case, sample_num, test_num, result_num, row):
        """
        CALLED BY: insert_all()
        FUNCTION: Establish all labware defaults for result table, depending on which case is provided, add result and correct entry from dataframe
        INPUT: result test table, labware engine, integer representing which result component, integer: test number, integer: result number, list: dataframe row
	RETURNS:  Nothing
        """
        default = { "replicate_count": "0" , "status":"N", "old_status":"N", "modified_result":"N", "allow_out":"T",\
                    "round":"F", "places":"1", "in_spec":"T", "primary_in_spec":"T", "uses_instrument":"F",\
                    "uses_codes":"F", "in_cal":"T", "auto_calc":"T", "allow_cancel":"F", "link_size":"0", "reportable":"T", \
                    "optional":"F", "code_entered":"F", "changed_on":"{}".format(datetime.datetime.now()), "std_reag_sample":"0",\
                    "has_attributes":"F", "factor_value":"0", "in_control":"T", "displayed":"T", "spec_override":"F", \
                    }

        default_s = {"sample_number":"{}".format(sample_num), "test_number": "{}".format(test_num),"result_number": "{}".format(result_num)}
        info = dict(default, **default_s)

        if (case == 1):    #RIBO GREEN
                entry = row['rna_conc']
                if (isFloat(entry)): stat = "E"     #if there is a result, make it complete
                else: stat = "N"
                info.update({"order_number": "1", "analysis": "RIBO_GREEN", "name": "Concentration", "reported_name": "Concentration", \
                                "result_type": "N", "units":"NG_UL", "entry":"{}".format(entry), "status":"{}".format(stat), \
				"formatted_entry":"{}".format(entry)} )
                ins = results.insert().values(info)
        
	elif (case == 2): #PICO GREEN
                entry = row['qubit_conc']
                if (isFloat(entry)): stat = "E"     #if there is a result, make it complete
                else: stat = "N"
                info.update({"order_number": "1", "analysis": "PICO_GREEN", "name": "Concentration", "reported_name": "Concentration", \
                        	"result_type": "N", "units":"NG_UL", "entry":"{}".format(entry), "status":"{}".format(stat), \
				"formatted_entry":"{}".format(entry)} )
                ins = results.insert().values(info)

        elif (case == 3): #FRAGMENT ANALYZER - LIB size
                entry = row['lib_len']
                if (isFloat(entry)): stat = "E"
                else: stat = "N"
                info.update( {"order_number": "1", "analysis": "FRAGMENT_ANALYZER", "name": "Average Library Size", "reported_name": "Average Library Size", \
                        	"result_type": "N", "units":"BP", "entry":"{}".format(entry), "status":"{}".format(stat),\
				"formatted_entry":"{}".format(entry)} )
                ins = results.insert().values(info)

        elif (case == 4): #FRAGMENT ANALYZER -DNA_FA
                entry = row['dna_fa']
                if (entry): stat = "E"
                else: stat = "N"
                info.update(  {"order_number": "2", "analysis": "FRAGMENT_ANALYZER", "name": "DNA_FA", "reported_name": "DNA_FA",\
                         	"result_type": "T", "units":"NONE", "entry":"{}".format(entry), "status":"{}".format(stat),\
				"formatted_entry":"{}".format(entry)} )
                ins = results.insert().values(info)

        elif (case == 5): # SECOND PICO
                entry = row['second_pico']
                if (isFloat(entry)): stat = "E"
                else: stat = "N"
                info.update( {"order_number": "1", "analysis": "PICO_GREEN_2", "name": "Concentration", "reported_name": "Concentration",\
                         	"result_type": "N", "units":"NG_UL", "entry":"{}".format(entry), "status":"{}".format(stat), \
				"formatted_entry":"{}".format(entry)} )
                ins = results.insert().values(info)

        elif (case == 6): #NANOMOLAR CONC
		if (isFloat(row['second_pico']) and isFloat(row['lib_len'])):
			entry = (float(row['second_pico']) * 1000000) / (float(row['lib_len']) * 660)
			entry = float("%.10f" % entry)
			stat = "C"
                else: 
			entry = ""
			stat = "N"
                info.update( {"order_number": "1", "analysis": "NANOMOLAR_CONC", "name": "concentration", "reported_name": "concentration",\
                         	"result_type": "K", "units":"NANO_MOLAR", "entry":"{}".format(entry), "status":"{}".format(stat), \
				"formatted_entry":"{}".format(entry)} )
                ins = results.insert().values(info)

	elif (case == 7): #SEQUENCING-preseq QC
                entry = row['pre_seq_QC']
                if (entry != ""): stat = "E" 
                else: stat = "N"
                info.update( {"order_number": "1", "analysis": "SEQUENCING", "name": "Pre-sequencing QC", "reported_name": "Pre-sequencing QC",\
                         	"result_type": "L", "units":"NONE", "entry":"{}".format(entry), "status":"{}".format(stat),\
				"formatted_entry":"{}".format(entry), "list_key":"P_F"} )
                ins = results.insert().values(info)

        elif (case == 8): #SEQUENCING-preseq reason
		if (row['pre_seq_QC'] == "FAIL"):
			entry = row['reason']
			stat = "E"
                	info.update( {"order_number": "2", "analysis": "SEQUENCING", "name": "Pre-sequencing Reason", "reported_name": "Pre-sequencing Reason",\
                         	"result_type": "T", "units":"NONE", "status":"{}".format(stat), "entry":"{}".format(entry),\
				"formatted_entry":"{}".format(entry)} )
                else:
			info.update( {"order_number": "2", "analysis": "SEQUENCING", "name": "Pre-sequencing Reason", "reported_name": "Pre-sequencing Reason",\
                                "result_type": "T", "units":"NONE", "status":"N"} )
		ins = results.insert().values(info)
        
	elif (case == 9): #SEQUENCING-start date
                entry = row['seq_start']
                if (entry != ""): stat = "E"
                else: stat = "N"
                info.update( {"order_number": "3", "analysis": "SEQUENCING", "name": "Sequencing Start Date", "reported_name": "Sequencing Start Date",\
                         	"result_type": "D", "units":"NONE", "entry":"{}".format(entry), "status":"{}".format(stat), \
				"formatted_entry":"{}".format(entry)} )
                ins = results.insert().values(info)

        elif (case == 10): #SEQUENCING-end date
                entry = row['seq_finish']
                if (entry != ""): stat = "E"
                else: stat = "N"
                info.update( {"order_number": "4", "analysis": "SEQUENCING", "name": "Sequencing Finish Date", "reported_name": "Sequencing Finish Date",\
                         "result_type": "D", "units":"NONE", "entry":"{}".format(entry), "status":"{}".format(stat), "formatted_entry":"{}".format(entry)} )
                ins = results.insert().values(info)

        elif (case == 11): #SEQUENCING-post seq QC
                entry = row['post_seq_QC']
                if (entry != ""): stat = "E"
                else: stat = "N"
                info.update( {"order_number": "5", "analysis": "SEQUENCING", "name": "Post-sequencing QC", "reported_name": "Post-sequencing QC",\
                         "result_type": "L", "units":"NONE", "entry":"{}".format(entry), "status":"{}".format(stat), "formatted_entry":"{}".format(entry), "list_key":"P_F"} )
                ins = results.insert().values(info)

        elif (case == 12): #SEQUENCING-reseq reason
		if (row['post_seq_QC'] == "FAIL"):
			entry = row['reason']
			if (entry != ""): stat =  "E"
                        else: 
                                entry = "None provided"
                                stat = "N"
			info.update( {"order_number": "6", "analysis": "SEQUENCING", "name": "Post-sequencing Reason", "reported_name": "Post-sequencing Reason",\
                         	"result_type": "T", "units":"NONE", "status":"{}".format(stat), "entry":"{}".format(entry), "formatted_entry":"{}".format(entry)} )
		else:
                	info.update( {"order_number": "6", "analysis": "SEQUENCING", "name": "Post-sequencing Reason", "reported_name": "Post-sequencing Reason",\
                         	"result_type": "T", "units":"NONE", "status":"N"} )
                ins = results.insert().values(info)

        elif (case == 13): #SEQUENCING-reseq start
                entry = row['reseq_start']
                if (entry != ""): stat = "E"
                else: stat = "N"
                info.update( {"order_number": "7", "analysis": "SEQUENCING", "name": "Resequencing Start Date", "reported_name": "Resequencing Start Date",\
                         "result_type": "D", "units":"NONE", "entry":"{}".format(entry), "status":"{}".format(stat), "formatted_entry":"{}".format(entry)} )
                ins = results.insert().values(info)

        elif (case == 14): #SEQUENCING-reseq finish
                entry = row['reseq_finish']
                if (entry != ""): stat = "E"
                else: stat = "N"
                info.update( {"order_number": "8", "analysis": "SEQUENCING", "name": "Resequencing Finish Date", "reported_name": "Resequencing Finish Date",\
                         "result_type": "D", "units":"NONE", "entry":"{}".format(entry), "status":"{}".format(stat), "formatted_entry":"{}".format(entry)} )
                ins = results.insert().values(info)

	elif (case == 15): #SEQUENCING-post reseq qc
                entry = row['reseq_QC']
                if (entry != ""): stat = "E"
                else: stat = "N"
                info.update( {"order_number": "9", "analysis": "SEQUENCING", "name": "Post-resequencing QC", "reported_name": "Post-resequencing QC",\
                         "result_type": "L", "units":"NONE", "entry":"{}".format(entry), "status":"{}".format(stat), "formatted_entry":"{}".format(entry),"list_key":"P_F"})
                ins = results.insert().values(info)

	elif (case == 16): #SEQUENCING-post reseq reason
                if (row['reseq_QC'] == "FAIL"):
			entry = row['reason']
			if (entry != ""): stat =  "E"
                        else:
                                entry = "None provided"
                                stat = "N"
			info.update( {"order_number": "10", "analysis": "SEQUENCING", "name": "Post-resequencing Reason", "reported_name": "Post-resequencing Reason",\
                         		"result_type": "T", "units":"NONE", "status":"{}".format(stat), "entry":"{}".format(entry), "formatted_entry":"{}".format(entry)} )
                else:
			info.update( {"order_number": "10", "analysis": "SEQUENCING", "name": "Post-resequencing Reason", "reported_name": "Post-resequencing Reason",\
                                        "result_type": "T", "units":"NONE", "status":"N"} )
		ins = results.insert().values(info)

	elif (case == 17):  #DEMULTIPLEXING-biome yields
                info.update( {"order_number": "1", "analysis": "DEMULTIPLEXING_RPT", "name": "Biome Yield (Mbps)", "reported_name": "Biome Yield (Mbps)",\
                         "result_type": "N", "units":"MBP", "status":"N"} )
                ins = results.insert().values(info)

        elif (case == 18):  #DEMULTIPLEXING-ipc reads
                info.update( {"order_number": "2", "analysis": "DEMULTIPLEXING_RPT", "name": "IPC reads (RPMbps)", "reported_name": "IPC reads (RPMbps)",\
                         "result_type": "N", "units":"RPM", "status":"N"} )
                ins = results.insert().values(info)
        engine.execute(ins)

def isFloat(string):
    try:
        float(string)
        return True
    except ValueError:
        return False

def insert_batches(batches, engine, batch_num):
        """
        CALLED BY: main()
        FUNCTION: Establish all labware defaults for batch table, insert new batch number with all default values
        INPUT: batch table structure, labware engine, integer: batch number
	RETURNS:  Nothing
        """
        info = {"object_class":"SAMPLE", "group_name":"DEFAULT", "template":"RNA_STOOL", "changed_on":"{}".format(str(datetime.datetime.now())), \
		"date_created":"{}".format(datetime.datetime.now()), "owner":"SYSTEM", "template_version": "1", \
		"assign_to_objects":"T", "closed":"T", "change_link_key":"F", "signed":"F", "investigated":"F", "name":"{}".format(batch_num)}

	ins = batches.insert().values(info)
	engine.execute(ins)

def insert_batch_object(batch_objects, engine, sample_num, batch, order_num):
        """
        CALLED BY: update_labware()
	FUNCTION: Establish all labware defaults for batch objects table, insert new batch objects for all 
	INPUT: batch objects table structure, labware engine, list: row from dataframe        
	RETURNS:  Nothing
        """
	#remember that object id == sample number
	info  = {"sample_type":"SAMPLE", "sample_number":"{}".format(sample_num), \
		"order_number": "{}".format(order_num), "object_id":"{}".format(sample_num), \
		"batch":"{}".format(batch) }
	ins = batch_objects.insert().values(info)
	engine.execute(ins)



