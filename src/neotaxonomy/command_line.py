#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Tue Dec 13 15:19:11 2016

@author: Paolo Cozzi <paolo.cozzi@ptp.it>
"""

import os
import sys
import logging
import argparse

from neotaxonomy import TaxGraph, TaxNodefile, TaxNamefile

# programname
program_name = os.path.basename(sys.argv[0])

# get a logger with a defined name
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)
logging.getLogger("httpstream").setLevel(logging.WARNING)
logging.getLogger("neo4j.bolt").setLevel(logging.WARNING)
logger = logging.getLogger(program_name)

# a function to fill taxonomy database
def fillTaxonomyDB():
    """Fill taxonomy database when files are provided"""
    
    parser = argparse.ArgumentParser(description='Load taxonomy data into database')
    parser.add_argument("--nodes", help="input node file", required=True, type=str)
    parser.add_argument("--names", help="input name file", required=True, type=str)
    parser.add_argument("--host", help="Database host (def '%(default)s')", type=str, required=False, default=TaxGraph.host)
    parser.add_argument("--user", help="Database user (def '%(default)s')", type=str, required=False, default=TaxGraph.user)
    parser.add_argument("--password", help="Database password (def '%(default)s')", type=str, required=False, default=TaxGraph.password)
    parser.add_argument("--http_port", help="Database http port (def '%(default)s')", type=str, required=False, default=TaxGraph.http_port)
    parser.add_argument("--https_port", help="Database https port (def '%(default)s')", type=str, required=False, default=TaxGraph.https_port)
    parser.add_argument("--bolt_port", help="Database bold port (def '%(default)s')", type=str, required=False, default=TaxGraph.bolt_port)
    args = parser.parse_args()
    
    # debug
    logger.info("%s started" %(program_name))
    
    # get a nodefile object
    logger.info("Loading nodes...")
    nodefile = TaxNodefile(host=args.host, user=args.user, password=args.password, http_port=args.http_port, https_port=args.https_port, bolt_port=args.bolt_port)
    nodefile.connect()
    nodefile.insertFrom(dmp_file=args.nodes)
    
    # get a namefile object
    logger.info("Loading names...")
    namefile = TaxNamefile(host=args.host, user=args.user, password=args.password, http_port=args.http_port, https_port=args.https_port, bolt_port=args.bolt_port)
    namefile.connect()
    namefile.insertFrom(dmp_file=args.names)
    
    #debug
    logger.info("%s finished" %(program_name))
    