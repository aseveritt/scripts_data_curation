import psycopg2, time, bcrypt,smtplib
from datetime import datetime
import numpy as np
from sqlalchemy import *
from sqlalchemy_utils import database_exists, create_database
import pandas as pd
from df2gspread import gspread2df as g2d
from sqlalchemy.orm import sessionmaker
from email.mime.text import MIMEText
from email.header import Header
from connect_db import make_engine

def get_GS():
    # use full path to spreadsheet file
    Andy_cust_GS = "INSERT LINK TO EDITING" # FIX ME
    Andy_cust_name = "INSERT GS NAME" #FIX ME
    
    #Convert GS into pandas df
    andy_cust_df = g2d.download(Andy_cust_GS, Andy_cust_name, col_names = True, row_names = True)
    andy_cust_df['Kit ID'] = andy_cust_df.index
    andy_cust_df = andy_cust_df.reset_index(drop = True)
    
    #subset df and drop all rows which are missing Kit IDs
    df = andy_cust_df[['Kit ID', 'Customer name', 'Date Shipped', 'USPS Tracking', 'Return Mailer Tracking', 'emails', 'ID']]	
    df = df.loc[df['Kit ID'] != '']
	
    return df


def connect_LABWARE():
    
    engine = make_engine("Project_1.ini", "dev")
    
    if engine == None or engine == '':
        raise Exception("Error:engine is None!")

    samples = Table('sample', MetaData(bind=engine),
        Column('text_id', Integer, primary_key=True),
        Column('tracking_number', String),
        Column('ship_date', String),
        Column('return_tracking', String),
        Column('customer', String),
    )
    customers = Table('customer', MetaData(bind=engine),
        Column('name', String,primary_key=True),
	Column('x_user_name', String),
	Column('group_name', String),
	Column('removed', String),
    )

    return (samples,customers,engine)

def update_line(samples,engine,kit_id,case,var):
    if (case == 1):
        up = update(samples).where(samples.c.text_id == '{}'.format(kit_id)).values(tracking_number = '{}'.format(var))
    if (case == 2):
        up = update(samples).where(samples.c.text_id == '{}'.format(kit_id)).values(ship_date = '{}'.format(var))
    if (case == 3):
        up = update(samples).where(samples.c.text_id == '{}'.format(kit_id)).values(return_tracking = '{}'.format(var))
    if (case == 4):
        up = update(samples).where(samples.c.text_id == '{}'.format(kit_id)).values(customer = '{}'.format(var))
    engine.execute(up)


def update_samples(samples, engine, df):

    count = 0
    missing = []
    no_action = 0
    duplicate = []
    track_count = 0
    ship_count = 0
    rtrack_count = 0 
    id_count = 0
    urgent = set()

    for index, row in df.iterrows():
        count +=1
        kit_id, ship, track, rtrack, cust_id = row['Kit ID'],row['Date Shipped'],row['USPS Tracking'], row['Return Mailer Tracking'], row['ID']	
        if (ship != ""): ship = datetime.strptime("_".join([ship[0:4],ship[5:7],ship[8:10]]), '%Y_%m_%d')
      	if (cust_id == "not found"): cust_id = "" 

	s = samples.select(samples.c.text_id == '{}'.format(kit_id))
        if (s.scalar() == None):
            missing.append(kit_id)
        else:
            rs = s.execute()  
            for row in rs:
	    	if ( (track == row.tracking_number or (track == "" and row.tracking_number == None)) and \
		     (ship == row.ship_date or ( ship == "" and row.ship_date == None)) and \
		     (rtrack == row.return_tracking or (rtrack == "" and row.return_tracking == None)) and \
		     (cust_id == row.customer or (cust_id == "" and row.customer == None))):
		    no_action+=1

		if (track != "" and row.tracking_number == None):
                    update_line(samples,engine,kit_id,1,track)
                    track_count+=1
                elif (track != "" and row.tracking_number != None and row.tracking_number != track):
                    update_line(samples,engine,kit_id,1,track)
		    urgent.add("ERROR: Is Kit ID {} a duplicate? matches customer id {}".format(kit_id, cust_id))
                    duplicate.append("For Kit ID {} tracking numbers don't match.  {} --> {}".format(kit_id, row.tracking_number, track))

	    	if (ship != "" and row.ship_date == None):
                    update_line(samples,engine,kit_id,2,ship)
                    ship_count+=1 
                elif (ship != "" and row.ship_date != None and row.ship_date != ship):
                    update_line(samples,engine,kit_id,2,ship)
		    urgent.add("ERROR: Is Kit ID {} a duplicate? matches customer id {}".format(kit_id, cust_id))
                    duplicate.append("For Kit ID {} ship date don't match. {} --> {}".format(kit_id, row.ship_date, ship))
                
		if (rtrack != "" and row.return_tracking == None):
                    update_line(samples,engine,kit_id,3,rtrack)
                    rtrack_count+=1
                elif (row.return_tracking != rtrack):
                    update_line(samples,engine,kit_id,3,rtrack)
		    urgent.add("ERROR: Is Kit ID {} a duplicate? matches customer id {}".format(kit_id, cust_id))
                    duplicate.append("For Kit ID {} ship date don't match. {} --> {}".format(kit_id, row.return_tracking, rtrack))
                
		if (cust_id != "" and row.customer == None):
                    update_line(samples,engine,kit_id,4,cust_id)
                    id_count+=1
                elif (row.customer != cust_id):
		    urgent.add("ERROR: Is Kit ID {} a duplicate? matches customer id {}".format(kit_id, cust_id))
                    duplicate.append("For Kit ID {} short ids don't match. {} --> {}".format(kit_id, row.customer, cust_id))
                    update_line(samples,engine,kit_id,4,cust_id)

    return (count, missing, no_action, duplicate, track_count, ship_count, rtrack_count, id_count,urgent)


def update_customers(customers, engine, df):
	
    count = 0 	
    missing = []
    no_action = 0 
    missing_id = 0
    name_count = 0 
    urgent = []
    #REMEMBER THAT CUSTOMER NAME = CUST_ID
    #REMEMBER THAT CUSTOMER USER.NAME = CUST_NAME

    for index,row in df.iterrows():
    	count +=1 
        cust_id, cust_name = row['ID'], row['Customer name']
	if any(ord(char) > 126 for char in cust_name): 
	    urgent.append("ERROR: Please remove special charcter from name: {}".format(cust_id))
	elif (cust_id == "not found"): 
	    missing_id += 1
	else:
            s = customers.select(customers.c.name== '{}'.format(cust_id))            #for entry which matches line from df
	    if (s.scalar() == None):  #no entry yet
                missing.append(cust_id)
                up = customers.insert().values(name = '{}'.format(cust_id), x_user_name = '{}'.format(cust_name), group_name = "DEFAULT", removed = "F")
                engine.execute(up)	
            else:
               rs = s.execute()
	       for row in rs:     #for entry which matches line from dataframe
                   if (row.x_user_name != cust_name):
                       up = update(customers).where(customers.c.name== '{}'.format(cust_id)).values(x_user_name = '{}'.format(cust_name), group_name = "DEFAULT", removed = "F")
                       engine.execute(up)
                       name_count += 1
    		   elif (row.x_user_name == cust_name):
		   	no_action += 1
    return (count, missing, no_action, missing_id, name_count, urgent)

	
def save_file(msg):
    name = time.strftime("\update_%Y_%m_%d__%H_%M")
    cwd = "ADD ONE" # FIX ME
    with open(cwd+name, "w") as outfile:
        outfile.write(msg)

def main():			
    df = get_GS()
    samples,customers, engine = connect_LABWARE()
    count_s, missing_s, no_action_s, duplicate, track_count, ship_count, rtrack_count, id_count, urgent_s = update_samples(samples, engine, df)
    count_c, missing_c, no_action_c, missing_id, name_count, urgent_c = update_customers(customers, engine, df)

    msg = ("UPDATES ABOUT GS -> LABWARE DATA MIGRATION (prod)\n\n"
		+"\n\nREGARDING CUSTOMER TABLE\n\n"
		+"      -{} entries in the GS\n".format(count_c)
	        +"      -{} entries were up-to-date\n".format(no_action_c)
		+"      -{} do not have customer id fields, so no action was taken\n".format(missing_id)
 	        +"      -{} name fields were updated\n".format(name_count)
		+"      -{} customers were added, (only name and id):\n{}\n".format(len(missing_c), (",".join(missing_c)))
		+"      -{} urgent issues with customer names:\n{}".format(len(urgent_c), ("\n".join(urgent_c)))

		+"\n\nREGARDING SAMPLE TABLE\n\n"
       	        +"	-{} entries in the Google Sheet 'Andy's Customers'\n".format(count_s)
	        +"	-{} entries were up-to-date\n".format(no_action_s)
		+"	-{} entries were updated\n".format(count_s - no_action_s - len(missing_s))
		+"		-{} empty tracking fields were filled\n".format(track_count)
		+"		-{} empty ship date fields were filled\n".format(ship_count)
		+"		-{} empty return tracking fields were filled\n".format(rtrack_count)
		+"		-{} empty customer id fields were filled\n".format(id_count)
		+"		-{} filled fields  were overwritten by GS information (listed below)\n".format(len(duplicate))
		+"	-{} Kit IDs were not found in Labware:\n{}".format(len(missing_s), (",".join(missing_s)))
		+"	\n\n\n-{} urgent issues need to be addressed:\n{}".format(len(urgent_s), ("\n".join(str(i) for i in urgent_s)))
	        +"	\n-Entries overwritten by new GS information: \n{}".format(("\n".join(duplicate)))
		)
	
    save_file(msg)
    out = open("out", "a")
    out.write(msg)
main()
