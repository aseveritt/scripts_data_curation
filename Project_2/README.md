1. Dependencies
# it needs python 2.7
pip install pyscopg2
pip install bcrypt
pip install gspread
pip install sqlalchemy_utils
pip install df2gspread

2. Required Files
(client_secret.json, client_server.json, permissions_file.pem, table_structure.py, connect_labware.py, connect_db.py)
(PRIVATE FILE test.ini required for passwords)

#to acess google sheets API:
#login into your google account
# go to https://console.developers.google.com
- select a project
- click credentials
- Download json for OAuth 2.0 client IDs and save file as "client_secret.json"
- Download json for Service Account Key (click three dots and select "Create Key") and save file as "client_server.json" 
- mkdir ~/.gdrive_private
- mv client_secret.json ~/.gdrive_private/
- mv client_server.json ~/.gdrive_private/
-  will ask you to login and ALLOW the account to access google sheets


# will need the pem file to access the DB:

#will need table_structure.py and connect_labware.py in current directory as well

3. Lines to possibly edit:
	- connect_labware.py line 12 (switch engine)
	- lims_update_test_result.py line 168 (switch credentials location)
 
4. ON LOCAL python lims_update_test_result.py -C
5. ON RDS C:/Users/Administrator/Documents/LABWARE_updates/02_test_result/run_script.cmd
