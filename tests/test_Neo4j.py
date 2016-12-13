#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Thu Dec  1 14:55:02 2016

@author: Paolo Cozzi <paolo.cozzi@ptp.it>
"""

import os
import py2neo
import logging
import unittest
import neotaxonomy

# getting module path
current_path = os.path.dirname(__file__)

# logger instance
logger = logging.getLogger(__name__)

# update py2neo verbosity
logging.getLogger("neo4j.bolt").setLevel(logging.WARNING)
logging.getLogger("httpstream").setLevel(logging.WARNING)

# a function to count how many lines has a file
# http://stackoverflow.com/questions/845058/how-to-get-line-count-cheaply-in-python
def file_len(fname):
    with open(fname) as f:
        for i, l in enumerate(f):
            pass
    return i + 1

class TaxGraphTest(unittest.TestCase):
    """A class to test Graph connection classes"""
    
    def test_connect(self):
        """Testing connection"""
        
        taxgraph = neotaxonomy.TaxGraph(host="localhost")
        taxgraph.connect(user="neo4j", password="password")
        self.assertIsInstance(taxgraph.graph, py2neo.database.Graph)
       
    def test_noConnect(self):
        """Testing no connection raise error"""
        
        taxgraph = neotaxonomy.TaxGraph(host="localhost")
        taxgraph.max_attempts = 1
        self.assertRaisesRegexp(neotaxonomy.TaxGraphError, "Max attempts reached", taxgraph.connect, user="neo4j", password="neo4j")
        
        # get lineage with no connection
        taxgraph = neotaxonomy.TaxGraph(host="localhost")
        self.assertRaisesRegexp(neotaxonomy.TaxGraphError, "You have to connect to database", taxgraph.getLineage, 562)
       
class TaxNodefileTest(unittest.TestCase):
    """A class to test node data load"""
    
    neo = None
    test_nodefile = os.path.join(current_path, "test_nodes.dmp")
    
    def setUp(self):
        self.neo = neotaxonomy.TaxNodefile(host="localhost", user="neo4j", password="password")
        self.neo.connect()
        
        # change number of iterations
        self.neo.iter = 5
        
    def tearDown(self):
        try:
            self.neo.graph.delete_all()
            
        except py2neo.GraphError, message:
            logger.error(message)
        
        # drop indexes if they exists
        try:
            self.neo.schema.drop_uniqueness_constraint(neotaxonomy.TaxNode.label, neotaxonomy.TaxNodefile.unique_index)
            
        except py2neo.GraphError, message:
            logger.error(message)
        
    def test_noConnection(self):
        # create a local instance
        neo = neotaxonomy.TaxNodefile(host="localhost", user="neo4j", password="password")
        self.assertRaisesRegexp(Exception, "You need to connect to database before checking index", neo.check_index)
        self.assertRaisesRegexp(Exception, "You need to connect to database before loading from file", neo.insertFrom, self.test_nodefile)
        
        
    def test_insertFrom(self):
        """Testing loading nodes"""
        
        self.neo.insertFrom(self.test_nodefile)
        ref_nodes = file_len(self.test_nodefile)
        test_nodes = len(list(self.neo.graph.find(neotaxonomy.TaxNode.label)))
        self.assertEqual(ref_nodes, test_nodes)
        
    def test_insertFromLimit(self):
        """Testing loading nodes with more transactions"""
        
        self.neo.insertFrom(self.test_nodefile, limit=5)
        test_nodes = len(list(self.neo.graph.find(neotaxonomy.TaxNode.label)))
        self.assertEqual(5, test_nodes)
        
    def test_insertFromRaises(self):
        """Insert already inserted nodes raises exception"""
        
        self.neo.insertFrom(self.test_nodefile)
        self.assertRaisesRegexp(neotaxonomy.TaxGraphError, "Node .* already exists", self.neo.insertFrom, self.test_nodefile)
        
class TaxNamefileTest(unittest.TestCase):
    """A class to test node data load"""
    
    neo = None
    test_namefile = os.path.join(current_path, "test_names.dmp")
    test_nodefile = os.path.join(current_path, "test_nodes.dmp")
    
    def setUp(self):
        # insert nodes before names
        neo = neotaxonomy.TaxNodefile(host="localhost", user="neo4j", password="password")
        neo.connect()
        neo.insertFrom(self.test_nodefile)
        
        # Ok now instantiate the object
        self.neo = neotaxonomy.TaxNamefile(host="localhost", user="neo4j", password="password")
        self.neo.connect()
        
        # change number of iterations
        self.neo.iter = 5
        
    def tearDown(self):
        try:
            self.neo.graph.delete_all()
            
        except py2neo.GraphError, message:
            logger.error(message)
        
        # drop indexes if they exists
        try:
            self.neo.schema.drop_uniqueness_constraint(neotaxonomy.TaxNode.label, neotaxonomy.TaxNodefile.unique_index)
            self.neo.schema.drop_uniqueness_constraint(neotaxonomy.TaxName.label, neotaxonomy.TaxNamefile.unique_index)
            
        except py2neo.GraphError, message:
            logger.error(message)
                
    def test_noConnection(self):
        # create a local instance
        neo = neotaxonomy.TaxNamefile(host="localhost", user="neo4j", password="password")
        self.assertRaisesRegexp(Exception, "You need to connect to database before checking index", neo.check_index)
        self.assertRaisesRegexp(Exception, "You need to connect to database before loading from file", neo.insertFrom, self.test_namefile)
        
    def test_insertFrom(self):
        """Testing loading names"""
        
        self.neo.insertFrom(self.test_namefile)
        ref_nodes = file_len(self.test_namefile)
        test_nodes = len(list(self.neo.graph.find(neotaxonomy.TaxName.label)))
        self.assertEqual(ref_nodes, test_nodes)
        
    def test_insertFromLimit(self):
        """Testing loading names with more transactions"""
        
        self.neo.insertFrom(self.test_namefile, limit=5)
        test_nodes = len(list(self.neo.graph.find(neotaxonomy.TaxName.label)))
        self.assertEqual(5, test_nodes)
        
    def test_insertFromRaises(self):
        """Testing insert already inserted names raises exception"""
        
        self.neo.insertFrom(self.test_namefile)
        self.assertRaisesRegexp(neotaxonomy.TaxGraphError, "Node .* already exists", self.neo.insertFrom, self.test_namefile)

# testing functions
class LineageTest(unittest.TestCase):
    """A class to lineage methods"""
    
    neo = None
    test_namefile = os.path.join(current_path, "test_names.dmp")
    test_nodefile = os.path.join(current_path, "test_nodes.dmp")
    
    def setUp(self):
        # insert nodes before names
        neo = neotaxonomy.TaxNodefile(host="localhost", user="neo4j", password="password")
        neo.connect()
        neo.insertFrom(self.test_nodefile)
        
        # insert names
        neo = neotaxonomy.TaxNamefile(host="localhost", user="neo4j", password="password")
        neo.connect()
        neo.insertFrom(self.test_namefile)
        
        # a taxgraph object
        self.neo = neotaxonomy.TaxNodefile(host="localhost", user="neo4j", password="password")
        
    def tearDown(self):
        try:
            self.neo.graph.delete_all()
            
        except py2neo.GraphError, message:
            logger.error(message)
        
        # drop indexes if they exists
        try:
            self.neo.schema.drop_uniqueness_constraint(neotaxonomy.TaxNode.label, neotaxonomy.TaxNodefile.unique_index)
            self.neo.schema.drop_uniqueness_constraint(neotaxonomy.TaxName.label, neotaxonomy.TaxNamefile.unique_index)
            
        except py2neo.GraphError, message:
            logger.error(message)
            
    def test_getLineage(self):
        
        tmp = u"""k__Bacteria; p__Proteobacteria; c__Gammaproteobacteria; o__Enterobacterales; f__Enterobacteriaceae; g__Escherichia; s__coli"""
        reference = [tax.strip() for tax in tmp.split(";")]
        
        # query the database for E.coli
        self.neo.connect()
        result = self.neo.getLineage(562)
        
        # testing lineage
        self.assertEqual(reference, result)
        
# testing library
if __name__ == "__main__":
    unittest.main()

