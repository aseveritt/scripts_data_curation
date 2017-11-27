import pandas as pd
import numpy as np
from sqlalchemy import *
from sqlalchemy_utils import database_exists, create_database
from sqlalchemy.sql.expression import func
from sqlalchemy.orm import sessionmaker
from connect_db import make_engine
from oauth2client.service_account import ServiceAccountCredentials
import bcrypt

def connect():

        engine = make_engine("project_1.ini", "V")
        engine_phi = make_engine("project_1.ini", "V_phi")
        engine_labware = make_engine("project_1.ini", "dev")

    	users= Table('user', MetaData(bind=engine),
		Column('firstName', String, primary_key=True), 
		Column('lastName', String),
		Column('userID', String),
		)

	users_phi = Table('USER', MetaData(bind=engine_phi),
		Column('id', Integer, primary_key = True),
		Column('uuid', String),
		)
	customers = Table('customer', MetaData(bind=engine_labware),
		Column('name', String,primary_key=True),
		Column('x_user_name', String),
		)

	return (engine_labware, users, users_phi, customers)

def fetch_id(users, users_phi):
	count_v = 0
	count_missing_phi = 0
	info = []
	
	s = select([users.c.firstName, users.c.lastName, users.c.userID])
	for row in s.execute().fetchall():
		if (row['firstName'] != " " and row['lastName'] != " "):	
			count_v +=1
			hashed = HASHED KEY #FIX ME
			t = users_phi.select(users_phi.c.uuid == '{}'.format(hashed))
			custid = t.scalar()
			if (custid == None):
				count_missing_phi += 1	
				print ("Cannot find id for name:", row.userID)
			else:
				name = row['firstName'].strip() + " " + row['lastName'].strip()
				info.append({'Name': name,'ID': custid })
	df = pd.DataFrame(info)	
	return (df, count_v, count_missing_phi)

def update_labware(df, customers, engine_labware):
        count_df = 0
	count_up_to_date = 0
	count_name_updated = []
        count_inserted = 0
	urgent = []
	#remember
	#customer.name == id
	#customer.x_user_name == name

        for index, row in df.iterrows():
                count_df +=1
		id, name = row['ID'], (row['Name']).lower().strip() 
		s = customers.select(customers.c.name == '{}'.format(id))
                if (s.scalar() == None):
			if any(ord(char) > 126 for char in name):
				urgent.append("ERROR: Please remove special charcter from name associated with id: {}".format(id))
			else:
				count_inserted += 1
				ins = customers.insert().values(name = '{}'.format(id), x_user_name = '{}'.format(name))
				engine_labware.execute(ins)
                else:
                        for i in s.execute():
				if ((i['x_user_name']).lower() == name):
					count_up_to_date += 1
				else:
					count_name_updated.append("For customer id {}, the name in the labware.customer table is {} whereas the name in the datbase is {}.".format(int(id), i['x_user_name'], name))

        return (count_df, count_up_to_date, count_name_updated, count_inserted, urgent)

	

def main():
	engine_labware, users, users_phi, customers = connect()
	df, count_v, count_missing_phi = fetch_id(users,users_phi)

	count_df, count_up_to_date, count_name_updated, count_inserted, urgent = update_labware(df, customers, engine_labware)
	msg = ("UPDATES ABOUT SERVERS -> LABWARE DATA MIGRATION (prod)\n\n"
                +"      -{} names in , ({} IDs missing in phi)\n\n".format(count_v, count_missing_phi)
                +"      -{} total name/id pairs\n".format(count_df)
                +"      -{} pairs were up to date in customer table\n".format(count_up_to_date)
                +"      -{} pairs were inserted in customer table\n".format(count_inserted)
                +"      -{} pairs could not be inserted because of a special character in name- no action taken\n".format(len(urgent))
                +"      -{} pairs need the name updated in customer table-- no action taken\n\n{}\n{}\n\n".format(len(count_name_updated), "\n".join(count_name_updated), "\n".join(urgent))
                )	
	out = open("out", "w")
	out.write(msg)

main()
