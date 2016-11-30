#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Tue Nov 29 14:02:14 2016

@author: Paolo Cozzi <paolo.cozzi@ptp.it>
"""

import types
import py2neo
import logging

# logger instance
logger = logging.getLogger(__name__)

class Graph():
    """A class to deal with database connections"""
    
    host = "localhost"
    user = "neo4j"
    password = "neo4j"
    http_port = 7474
    https_port = 7473
    bolt_port = 7687
    bolt = None
    
    graph = None
    
    def __init__(self, **kwargs):
        """Init class"""
        
        self.__set(**kwargs)
        
    def __set(self, **kwargs):
        """Set class attributes"""
        
        for k, v in kwargs.iteritems():
            setattr(self, k, v)
        
    def connect(self, **kwargs):
        """connect to database"""
        
        self.__set(**kwargs)
        
        # get a connection
        self.graph = py2neo.Graph(host=self.host, user=self.user, password=self.password, 
                                    http_port=self.http_port, https_port=self.https_port,
                                    bolt=self.bolt, bolt_port=self.bolt_port)
        

class Node():
    """A class to describe a single record in nodes.dmp
    
    tax_id					-- node id in GenBank taxonomy database
    parent tax_id				-- parent node id in GenBank taxonomy database
    rank					-- rank of this node (superkingdom, kingdom, ...) 
    embl code				-- locus-name prefix; not unique
    division id				-- see division.dmp file
    inherited div flag  (1 or 0)		-- 1 if node inherits division from parent
    genetic code id				-- see gencode.dmp file
    inherited GC  flag  (1 or 0)		-- 1 if node inherits genetic code from parent
    mitochondrial genetic code id		-- see gencode.dmp file
    inherited MGC flag  (1 or 0)		-- 1 if node inherits mitochondrial gencode from parent
    GenBank hidden flag (1 or 0)            -- 1 if name is suppressed in GenBank entry lineage
    hidden subtree root flag (1 or 0)       -- 1 if this subtree has no sequence data yet
    comments				-- free-text comments and citations
    
    """
    
    tax_id = None
    rank = None
    parent = None
    hidden_flag = None
    
    # a dictionary in which atrtribute per coulmn index is defined
    __attr_to_columns = {"tax_id":0, "parent": 1, "hidden_flag": 10, "rank":2}
    
    # the properties list
    properties = ["tax_id", "hidden_flag", "rank"]
    label = "Node"
    
    def __init__(self, record=None):
        """Initialize class. You could specify a row of nodes.dmp as a list"""
        
        if record != None:
            if type(record) == types.StringType:
                record = self.__parse(record)
            
            for key, index in self.__attr_to_columns.iteritems():
                value = record[index]
                setattr(self, key, value)
        
    def __repr__(self):
        """Return a string"""
        
        return "<{module}.Node(tax_id='{tax_id}', parent='{parent}', rank='{rank}', hidden_flag='{hidden_flag}')>".format(module=self.__module__, tax_id=self.tax_id, parent=self.parent, rank=self.rank, hidden_flag=self.hidden_flag)
        
    def __parse(self, record):
        """Parse a string, return a list"""
        
        return [el.strip() for el in record.split("|")]
        
    def getNeo4j(self):
        """Get a neo4j object"""
        
        # define properties
        properties = {}

        for key in self.properties:
            properties[key] = getattr(self, key)
        
        node = py2neo.Node(self.label, **properties)
        
        return node
        
class Nodefile(Graph):
    """Una classe per gestire il file nodes.dmp"""
    
    def __init__(self, **kwargs):
        """Instance the class. Need a py2neo Graph instance"""
        
        Graph.__init__(self, **kwargs)
            
        # When do a transaction
        self.iter = 1000
        
        # record relations in a dictionary (node -> parent)
        self.all_relations = {}

    def check_index(self):
        """Check that index are defined"""
        
        try:
            constraints = self.graph.schema.get_uniqueness_constraints(Node.label)
            
        except AttributeError, message:
            raise Exception("You need to connect to database before checking index: %s" %(message))
            
        if not "tax_id" in constraints:
            self.graph.schema.create_uniqueness_constraint(Node.label,"tax_id")
    
    def insertFrom(self, dmp_file="nodes.dmp", limit=1000):
        """Open a file to read nodes"""
        
        # open a file in reading mode
        handle = open(dmp_file)
        
        # get a transaction
        try:
            tx = self.graph.begin()
            
        except AttributeError, message:
            raise Exception("You need to connect to database before loading from file: %s" %(message))
        
        # debug
        logger.info("Adding nodes...")
        
        # process line ny line
        for i, record in enumerate(handle):
            # get a node element
            my_node = Node(record)
            neo_node = my_node.getNeo4j()
            
            # add it to database
            tx.create(neo_node)
            
            # record relationship
            self.all_relations[my_node.tax_id] = my_node.parent

            # test for limit
            if limit is not None and i >= (limit-1):
                tx.commit()
                logger.info("%s limit reached. %s nodes added" %(limit, i+1))
                break

            # commit data
            if (i+1) % self.iter == 0:
                tx.commit()
                logger.debug("%s nodes added" %(i+1))
                # a new transaction
                tx = self.graph.begin()
                
        # outside cicle
        if (i+1) % self.iter != 0:
            tx.commit()
            logger.debug("%s nodes added" %(i+1))
        
        # get a selector
        selector = py2neo.NodeSelector(self.graph)
            
        # now add relations. Count them
        count = 0
        
        # debug
        logger.info("Adding iterations...")
        
        # get a new transaction object
        tx = self.graph.begin()
        
        for tax_id, parent_tax_id in self.all_relations.iteritems():
            neo_nodes = selector.select(Node.label, tax_id=tax_id)
            
            # Reading from a list (tax_id are unique, so there are 1 results)
            for neo_node in list(neo_nodes):
                # search parent
                neo_parents = selector.select(Node.label, tax_id=parent_tax_id)
                
                for neo_parent in neo_parents:
                    count += 1
                    
                    if neo_parent == neo_node:
                        logger.warn("Ignoring relationship between %s and %s" %(neo_node, neo_parent))
                        continue
                    
                    relationship = py2neo.Relationship(neo_parent, "PARENT", neo_node)
                    
                    # add it to database
                    tx.create(relationship)
                    
            # commit
            if count % self.iter == 0:
                tx.commit()
                logger.debug("%s iterations processed" %(count))
                tx = self.graph.begin()
                
        # final transaction
        if count % self.iter != 0:
            tx.commit()
            logger.debug("%s iterations processed" %(count))
            
        #debug
        logger.info("Completed!")
                
    