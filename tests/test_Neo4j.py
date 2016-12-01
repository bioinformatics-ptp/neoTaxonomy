#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Thu Dec  1 14:55:02 2016

@author: Paolo Cozzi <paolo.cozzi@ptp.it>
"""
import py2neo
import unittest
import neotaxonomy

class TaxGraphTest(unittest.TestCase):
    """A class to test GenericThread classes"""
    
    def test_connect(self):
       taxgraph = neotaxonomy.TaxGraph(host="localhost")
       taxgraph.connect(user="neo4j", password="password")
       self.assertIsInstance(taxgraph.graph, py2neo.database.Graph)

# testing library
if __name__ == "__main__":
    unittest.main()