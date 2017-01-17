#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""

neoTaxonomy - A python API to deal with NCBI taxonomy in a neo4j database
Copyright (C) 2016-2017 Paolo Cozzi <paolo.cozzi@ptp.it>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.


Created on Tue Dec 13 15:19:11 2016

@author: Paolo Cozzi <paolo.cozzi@ptp.it>
"""

import os
import sys
import logging
import argparse

from neotaxonomy import TaxGraph, TaxNodefile, TaxNamefile, TaxGraphError

# programname
program_name = os.path.basename(sys.argv[0])

# get a logger with a defined name
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logging.getLogger("httpstream").setLevel(logging.WARNING)
logging.getLogger("neo4j.bolt").setLevel(logging.WARNING)
logger = logging.getLogger(program_name)

def deleteall(taxgraph):
    """Delete all node and relations in database. Inspired from 
    https://neo4j.com/developer/kb/large-delete-transaction-best-practices-in-neo4j/"""
    
    progressive = 0
    
    query = """
// Remove TaxNode
MATCH (n:TaxNode)

// Take the first 1k nodes and their rels (if more than 100 rels / node on average lower this number)
WITH n LIMIT 1000
DETACH DELETE n
RETURN count(*)
"""
    
    # execute query
    cursor = taxgraph.graph.run(query)
    
    # get counts
    counts = cursor.evaluate()
    
    while counts != 0:
        progressive += counts
        logger.debug("%s TaxNodes deleted" %(progressive))
        cursor = taxgraph.graph.run(query)
        counts = cursor.evaluate()
        
    progressive = 0
        
    # now a query for name
    query = """
// Remove TaxName
MATCH (n:TaxName)

// Take the first 1k nodes and their rels (if more than 100 rels / node on average lower this number)
WITH n LIMIT 1000
DETACH DELETE n
RETURN count(*)
"""
    
    # execute query
    cursor = taxgraph.graph.run(query)
    
    # get counts
    counts = cursor.evaluate()
    
    while counts != 0:
        progressive += counts
        logger.debug("%s TaxNames deleted" %(progressive))
        cursor = taxgraph.graph.run(query)
        counts = cursor.evaluate()

# a function to fill taxonomy database
def fillTaxonomyDB():
    """Fill taxonomy database when files are provided"""
    
    parser = argparse.ArgumentParser(description='Load taxonomy data into database')
    parser.add_argument("--nodes", help="input node file", required=True, type=str)
    parser.add_argument("--names", help="input name file", required=True, type=str)
    parser.add_argument("--host", help="Database host (def '%(default)s')", type=str, required=False, default=TaxGraph.host)
    parser.add_argument("--user", help="Database user (def '%(default)s')", type=str, required=False, default=TaxGraph.user)
    parser.add_argument("--password", help="Database password (def '%(default)s')", type=str, required=False, default=TaxGraph.password)
    parser.add_argument("--http_port", help="Database http port (def '%(default)s')", type=int, required=False, default=TaxGraph.http_port)
    parser.add_argument("--https_port", help="Database https port (def '%(default)s')", type=int, required=False, default=TaxGraph.https_port)
    parser.add_argument("--bolt_port", help="Database bold port (def '%(default)s')", type=int, required=False, default=TaxGraph.bolt_port)
    parser.add_argument("--drop_all", help="Drop all TaxNodes and TaxNames in database", action='store_true', default=False)
    args = parser.parse_args()
    
    # debug
    logger.info("%s started" %(program_name))
    
    # erasing data if necessary
    if args.drop_all is True:
        response = raw_input('This will erase all TaxNodes and Taxnames (and their relations). Proceed [Y/n]? ')
        if response == "Y":
            taxgraph = TaxGraph(host=args.host, user=args.user, password=args.password, http_port=args.http_port, https_port=args.https_port, bolt_port=args.bolt_port)
            taxgraph.connect()
            deleteall(taxgraph)
            
        elif response.lower() == "n":
            logger.info("No changes made. Exiting")
            return
        
        else:
            logger.error("Only [Y/n] values allowed. Aborted")
            return
    
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

# a function to get taxonomies from input
def taxaid2Lineage():
    """Get lineage from taxa id(s)"""

    parser = argparse.ArgumentParser(description='Get lineage from taxa id(s)')
    parser.add_argument("--host", help="Database host (def '%(default)s')", type=str, required=False, default=TaxGraph.host)
    parser.add_argument("--user", help="Database user (def '%(default)s')", type=str, required=False, default=TaxGraph.user)
    parser.add_argument("--password", help="Database password (def '%(default)s')", type=str, required=False, default=TaxGraph.password)
    parser.add_argument("--http_port", help="Database http port (def '%(default)s')", type=int, required=False, default=TaxGraph.http_port)
    parser.add_argument("--https_port", help="Database https port (def '%(default)s')", type=int, required=False, default=TaxGraph.https_port)
    parser.add_argument("--bolt_port", help="Database bold port (def '%(default)s')", type=int, required=False, default=TaxGraph.bolt_port)
    parser.add_argument("--full", help="Get NCBI full taxonomy", action='store_true', default=False)
    parser.add_argument("--abbreviated", help="Get NCBI abbreviated taxonomy", action='store_true', default=False)
    parser.add_argument("--no_root", help="Exclude root node from NCBI taxonomy", action="store_true", default=False)
    parser.add_argument('taxa', nargs='+', help='taxa id (or ids)')
    args = parser.parse_args()
    
    # debug
    logger.info("%s started" %(program_name))
    
    db = TaxGraph(host=args.host, user=args.user, password=args.password, http_port=args.http_port, https_port=args.https_port, bolt_port=args.bolt_port)
    db.connect()
    
    for taxa in args.taxa:
        lineage = []
        
        try:
            # check if I need NCBI taxonomy
            if args.full is True or args.abbreviated is True:
                lineage = db.getFullLineage(taxa, args.abbreviated)
                
                if args.no_root is True:
                    lineage.remove("root")
                
            else:
                lineage = db.getLineage(taxa)
                
        except TaxGraphError, message:
            logger.error(message)
            
        print "%s\t" %(taxa) + ";".join(lineage)
        
    # debug
    logger.info("%s finished" %(program_name))
    
    
        