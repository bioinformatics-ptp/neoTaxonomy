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
    __properties = ["tax_id", "hidden_flag"]
    __labels = ["rank"]
    
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
        
        # define labels and properties
        labels = [getattr(self, label) for label in self.__labels]
        properties = {}

        for key in self.__properties:
            properties[key] = getattr(self, key)
        
        node = py2neo.Node(*labels, **properties)
        
        return node
        
class Nodefile:
    """Una classe per gestire il file nodes.dmp"""
    
    def __init__(self, graph):
        """Instance the class. Need a py2neo Graph instance"""
        
        if not isinstance(graph, py2neo.database.Graph):
            raise Exception("Need a 'py2neo.database.Graph' instance")
        
        # set graph
        self.graph = graph
            
        # When do a transaction
        self.iter = 100
        
        # record relations in a dictionary (node -> parent)
        self.all_relations = {}
    
    def insertFrom(self, dmp_file="nodes.dmp", limit=None):
        """Open a file to read nodes"""
        
        # open a file in reading mode
        handle = open(dmp_file)
        
        # get a transaction
        tx = self.graph.begin()
        
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
            self.all_relations[(my_node.rank, my_node.tax_id)] = my_node.parent

            # test for limit
            if limit is not None and i >= (limit-1):
                tx.commit()
                logger.info("% limit reached. %s nodes added" %(limit, i+1))
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
        
        for (rank, tax_id), parent_tax_id in self.all_relations.iteritems():
            neo_nodes = selector.select(rank, tax_id=tax_id)
            
            for neo_node in list(neo_nodes):
                # search parent
                neo_parents = selector.select(tax_id=parent_tax_id)
                
                for neo_parent in neo_parents:
                    if neo_parent == neo_node:
                        logger.warn("Ignoring relationship between %s and %s" %(neo_node, neo_parent))
                        continue
                    
                    count += 1
                    relationship = py2neo.Relationship(neo_parent, "PARENT", neo_node)
                    
                    # add it to database
                    tx.create(relationship)
                    
            # commit
            if count % self.iter == 0:
                tx.commit()
                logger.debug("%s iterations added" %(count+1))
                tx = self.graph.begin()
                
        # final transaction
        if count % self.iter != 0:
            tx.commit()
            logger.debug("%s iterations added" %(count+1))
            
        #debug
        logger.info("Completed!")
                
    