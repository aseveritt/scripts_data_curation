#!/usr/bin/env python

""" Desc: returns engine for database
          TODO: we might want to implement this on the connect_db object from the pipeline
"""

from __future__ import print_function
import psycopg2
import argparse
import ConfigParser

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy_utils import database_exists

import logging
logger = logging.getLogger(__name__)


def load_configs(config_file=None):
        configs = ConfigParser.RawConfigParser(allow_no_value=True)
        configs.read(config_file)
        return configs

def make_engine(config_file, db, p_commit):
        configs = load_configs(config_file)
        connection = create_engine("postgresql://"+configs.get(db, 'user')+":"+configs.get(db,'pw')+\
                "@"+configs.get(db,'host')+"/"+\
                configs.get(db,'dbname')+"?sslmode=verify-full&sslrootcert="+configs.get(db,'pem_file'), execution_options={"autocommit": p_commit})
        return connection
