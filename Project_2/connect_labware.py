import psycopg2, bcrypt
from sqlalchemy import *
from sqlalchemy_utils import database_exists, create_database
from sqlalchemy.orm import sessionmaker
from oauth2client.service_account import ServiceAccountCredentials

from connect_db import make_engine

def connect_LABWARE(p_commit=False):
        

	engine = make_engine("C:\Users\Administrator\Documents\LABWARE_updates\MANUAL_LIMS\\viome_dbs_test.ini", "prod", p_commit)
	#AMANDA LOCAL engine = make_engine("/Users/aseveritt/Documents/01_LIMS/viome_dbs_test.ini", "test", p_commit)

	if engine == None or engine == '':
                raise Exception("Error:engine is None!")

        samples = Table('sample', MetaData(bind=engine),
                Column('sample_number', String, primary_key = True),
                Column('label_id', String),
                Column('text_id', String),
		Column('status', String),
		Column('description', String),
		Column('aliquot', String),
        )
        tests = Table('test', MetaData(bind=engine),
                Column('sample_number', Integer, primary_key = True),
                Column('test_number', Integer),
                Column('order_number', Integer),
                Column('analysis', String, ),
                Column('version',Integer),
                Column('analysis_count', Integer),
                Column('group_name', String),
                Column('reported_name', String),
                Column('replicate_count', Integer),
                Column('status', String),
                Column('old_status', String),
                Column('batch_parent_test', Integer),
                Column('batch_sibling_test', Integer),
                Column('parent_test', Integer),
                Column('original_test', Integer),
                Column('date_received', String),
                Column('prep', String),
                Column('replicate_test', String),
                Column('test_priority', Integer),
                Column('in_spec', String),
                Column('in_cal', String),
                Column('resolve_reqd', String),
                Column('changed_on', String),
                Column('stage', String),
                Column('primary_in_spec', String),
                Column('in_control', String),
                Column('test_list', String),
                Column('re_tested', String),
                Column('modified_results', String),
                Column('aliquoted_to', Integer),
                Column('on_worksheet', String),
                Column('display_results', String),
                Column('split_replicates', String),
                Column('cross_sample', String),
                Column('released', String),
                Column('double_entry', String),
                Column('child_out_spec', String),
                Column('charge_entry', String),
                Column('signed', String),
                Column('batch_original_test', Integer),
                Column('test_sequence_no', Integer),
                Column('aliquot_group', String),
        )
        results = Table('result', MetaData(bind=engine),
                Column('sample_number', Integer, primary_key = True),
                Column('test_number', Integer),
                Column('result_number', Integer),
                Column('order_number', Integer),
                Column('analysis', Integer),
                Column('name', String),
                Column('reported_name', String),
                Column('replicate_count', Integer),
                Column('result_type', String),
                Column('status', String),
                Column('old_status', String),
                Column('modified_result', String),
                Column('minimum', Integer),
                Column('allow_out', String),
                Column('entry', String),
                Column('formatted_entry', String),
                Column('units', String),
                Column('round', String),
                Column('places', Integer),
                Column('in_spec', String),
                Column('primary_in_spec', String),
                Column('uses_instrument', String),
                Column('uses_codes', String),
                Column('in_cal', String),
                Column('auto_calc', String),
		Column('list_key', String),
                Column('allow_cancel', String),
                Column('link_size', Integer),
                Column('reportable', String),
                Column('optional', String),
                Column('code_entered', String),
                Column('changed_on', String),
                Column('std_reag_sample', Integer),
                Column('has_attributes', String),
                Column('factor_value', Integer),
                Column('in_control', String),
                Column('displayed', String),
                Column('spec_override', String),
        )

        increments = Table('increments', MetaData(bind=engine),
                Column('name', String, primary_key = True),
                Column('value', Integer),
                )

	batch_objects = Table('batch_objects', MetaData(bind = engine),
		Column('batch', Integer, primary_key = True),
		Column('object_id', Integer ),
		Column('order_number', String),
		Column('sample_number', Integer),
		Column('sample_type', String),
		)
	batches = Table('batch', MetaData(bind=engine),
		Column('name', String, primary_key = True),
		Column('object_class', String),
		Column('group_name', String),
		Column('template', String),
		Column('changed_on', String),
		Column('date_created', String),
		Column('owner', String),
		Column('template_version', Integer),
		Column('assign_to_objects',String),
		Column('closed',String),
		Column('change_link_key', String),
		Column('signed', String),
		Column('investigated', String),
		)


	return (engine, samples, tests, results, increments, batch_objects, batches)
