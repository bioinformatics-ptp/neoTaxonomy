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


Created on Tue Nov 29 14:02:14 2016

@author: Paolo Cozzi <paolo.cozzi@ptp.it>
"""

import re
import time
import types
import py2neo
import logging

from neotaxonomy.exceptions import TaxGraphError

# logger instance
logger = logging.getLogger(__name__)

class TaxGraph():
    """A class to deal with database connections"""
    
    host = "localhost"
    user = "neo4j"
    password = "neo4j"
    http_port = 7474
    https_port = 7473
    bolt_port = 7687
    bolt = None
    
    graph = None
    transaction = None
    
    def __init__(self, **kwargs):
        """Init class"""
        
        self.__set(**kwargs)
        
        # in order to do reconnection
        self.max_attempts = 3
        self.time = 5
        
    def __set(self, **kwargs):
        """Set class attributes"""
        
        for k, v in kwargs.iteritems():
            setattr(self, k, v)
            
    def __repr__(self):
        """Return a string"""
        
        return "<{module}.TaxGraph(host='{host}', user='{user}')>".format(module=self.__module__, host=self.host, user=self.user)
        
    def connect(self, **kwargs):
        """connect to database"""
        
        self.__set(**kwargs)
        
        # test for connection
        try:
            # get a connection
            self.graph = py2neo.Graph(host=self.host, user=self.user, password=self.password, 
                                      http_port=self.http_port, https_port=self.https_port,
                                      bolt=self.bolt, bolt_port=self.bolt_port)
        
            self.graph.schema.get_indexes(TaxNode.label)
            
        except Exception, message:
            if kwargs.has_key("attempts"):
                kwargs["attempts"] += 1

            else:
                kwargs["attempts"] = 1

            logger.debug("Attempts done %s" %(kwargs["attempts"]))

            if kwargs["attempts"] <= self.max_attempts:
                logger.warn("Error while connecting to %s: %s" %(self.__repr__(), message))
                logger.warn("retring in %s seconds" %(self.time))
                time.sleep(self.time)
                self.connect(**kwargs)
                
            else:
                raise TaxGraphError("Max attempts reached: %s" %(message))
                
    def begin(self, autocommit=False):
        """Start a new transaction"""
        
        self.transaction = self.graph.begin(autocommit)
        
    def commit(self):
        """Commit a transaction"""
        
        try:
            self.transaction.commit()
            
        except Exception, message:
            raise TaxGraphError(message)
            
    # A function to get lineage from tax id
    def getLineage(self, taxon_id, ranks=["superKingdom", "Phylum", "Class", "Order", "Family", "Genus", "Species"]):
        """Get lineage from tax id. Only specified ranks will be returned. Each rank
        need to have a capital letter in order to by prefixed in name (eg. Species -> s__"""
        
        # I want to add a prefix for each order in scientific name. The prefix will be
        # the capital letter present in ranks
        # TODO: test for no capital letter in ranks
        pattern = re.compile("[A-Z]")
        matches = [re.search(pattern, rank) for rank in ranks]
        letters = [ranks[i][match.start()].lower() for i, match in enumerate(matches)]
        lineage = [u"%s__" %(letter) for letter in letters]
                   
        # lower ranks for semplicity
        ranks = [rank.lower() for rank in ranks]
        
        # call function to do query
        cursor = self.__query_lineage(taxon_id)
        
        # a flag for myself
        flag_taxon = False
        
        # count results processed
        count = 0
            
        # cicle amoung cursor
        for (tax_name, tax_rank, parent_rank, parent_name) in cursor:
            # count a result
            count += 1
            
            if flag_taxon == False:
                # consider specie and remove genere
                if tax_rank == u"species":
                    tax_name = tax_name.split()[-1]

                if tax_rank in ranks:
                    idx = ranks.index(tax_rank)
                    lineage[idx]= "%s__%s" %(letters[idx], tax_name)
                    # i found myself
                    flag_taxon = True
            
            # cicle for parent
            if parent_rank in ranks:
                idx = ranks.index(parent_rank)
                lineage[idx] = "%s__%s" %(letters[idx], parent_name)
                
        # closing cursor
        cursor.close()
        
        # check number of results
        if count == 0:
            raise TaxGraphError("No lineage found for %s" %(taxon_id))

        return lineage
        
    # A function to get full lineage
    def getFullLineage(self, taxon_id, abbreviated=False):
        """Get full lineage for a taxa id (abbreviated or not)"""
        
        # initalize variable
        lineage = []
        
        # call function to do query
        cursor = self.__query_lineage(taxon_id, abbreviated)
        
        # a flag for myself
        flag_taxon = False
        
        # count results processed
        count = 0
            
        # cicle amoung cursor
        for (tax_name, tax_rank, parent_rank, parent_name) in cursor:
            # count a result
            count += 1
            
            # insert the leaf node of lineage
            if flag_taxon == False:
                lineage.insert(0, tax_name)
                flag_taxon = True
            
            # process the parent
            lineage.insert(0, parent_name)
                
        # closing cursor
        cursor.close()
        
        # check number of results
        if count == 0:
            raise TaxGraphError("No lineage found for %s" %(taxon_id))

        return lineage
        
    def __query_lineage(self, taxon_id, abbreviated=False):
        """Internal query for a taxa"""
        
        # define query. Abbreviated or not (get full lineage or the impotant lineage)
        if abbreviated is True:
            query = """MATCH (specie:TaxName)<-[:SCIENTIFIC_NAME]-(organism:TaxNode)<-[:PARENT*]-(parent:TaxNode)-[:SCIENTIFIC_NAME]->(parent_name:TaxName) WHERE organism.tax_id = {taxon_id} AND parent.hidden_flag='0' RETURN specie.name_txt, organism.rank, parent.rank, parent_name.name_txt"""
        
        else:
            query = """MATCH (specie:TaxName)<-[:SCIENTIFIC_NAME]-(organism:TaxNode)<-[:PARENT*]-(parent:TaxNode)-[:SCIENTIFIC_NAME]->(parent_name:TaxName) WHERE organism.tax_id = {taxon_id} RETURN specie.name_txt, organism.rank, parent.rank, parent_name.name_txt"""
        
        # execute query
        try:
            cursor = self.graph.run(query, taxon_id=str(taxon_id))
        
        except AttributeError, message:
            raise TaxGraphError("You have to connect to database before serching for lineage: %s" %(message))
            
        return cursor
        

class TaxBase():
    """Base class for taxonomy elements"""
    
    attr_to_columns = {}
    properties = []
    label = None
    
    def __init__(self, record=None):
        """Initialize class. You could specify a list or a string"""
        
        if record != None:
            if type(record) == types.StringType:
                record = self.__parse(record)
            
            for key, index in self.attr_to_columns.iteritems():
                value = record[index]

                # TODO: insert null value?
                setattr(self, key, value)
                
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


class TaxNode(TaxBase):
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
    attr_to_columns = {"tax_id":0, "parent": 1, "hidden_flag": 10, "rank":2}
    
    # the properties list
    properties = ["tax_id", "hidden_flag", "rank"]
    label = "TaxNode"
    
    def __init__(self, record=None):
        """Initialize class. You could specify a row of nodes.dmp as a list"""
        
        TaxBase.__init__(self, record)
        
    def __repr__(self):
        """Return a string"""
        
        return "<{module}.TaxNode(tax_id='{tax_id}', parent='{parent}', rank='{rank}', hidden_flag='{hidden_flag}')>".format(module=self.__module__, tax_id=self.tax_id, parent=self.parent, rank=self.rank, hidden_flag=self.hidden_flag)


class TaxNodefile(TaxGraph):
    """Una classe per gestire il file nodes.dmp"""
    
    unique_index = "tax_id"
    
    def __init__(self, **kwargs):
        """Instance the class. Need a py2neo Graph instance"""
        
        TaxGraph.__init__(self, **kwargs)
            
        # When do a transaction
        self.iter = 1000
        
        # record relations in a dictionary (node -> parent)
        self.all_relations = {}

    @property
    def schema(self):
        return self.graph.schema
        
    def get_uniqueness_constraints(self, label):
        """get unique constraints"""
        
        return self.schema.get_uniqueness_constraints(label)

    def check_index(self):
        """Check that index are defined"""
        
        try:
            constraints = self.get_uniqueness_constraints(TaxNode.label)
            
        except AttributeError, message:
            raise TaxGraphError("You need to connect to database before checking index: %s" %(message))
            
        if not self.unique_index in constraints:
            logger.debug("Creating unique index ({label},{property_key})".format(label=TaxNode.label, property_key=self.unique_index))
            self.schema.create_uniqueness_constraint(TaxNode.label, self.unique_index)
    
    def insertFrom(self, dmp_file="nodes.dmp", limit=None):
        """Open a file to read nodes"""
        
        # open a file in reading mode
        handle = open(dmp_file)
        
        # get a transaction
        try:
            self.begin()
            self.check_index()
            
        except AttributeError, message:
            raise TaxGraphError("You need to connect to database before loading from file: %s" %(message))
        
        # debug
        logger.info("Adding nodes...")
        
        # process line ny line
        for i, record in enumerate(handle):
            # get a node element
            my_node = TaxNode(record)
            neo_node = my_node.getNeo4j()
            
            # add it to database
            self.transaction.create(neo_node)
            
            # record relationship
            self.all_relations[my_node.tax_id] = my_node.parent

            # test for limit
            if limit is not None and i >= (limit-1):
                self.commit()
                logger.info("%s limit reached. %s nodes added" %(limit, i+1))
                break

            # commit data
            if (i+1) % self.iter == 0:
                self.commit()
                logger.debug("%s nodes added" %(i+1))
                # a new transaction
                self.begin()
                
        # outside cicle
        if (i+1) % self.iter != 0:
            self.commit()
            logger.debug("%s nodes added" %(i+1))
            
        # closing file
        handle.close()
        
        # get a selector
        selector = py2neo.NodeSelector(self.graph)
            
        # now add relations. Count them
        count = 0
        
        # debug
        logger.info("Adding iterations...")
        
        # get a new transaction object
        self.begin()
        
        for tax_id, parent_tax_id in self.all_relations.iteritems():
            neo_nodes = selector.select(TaxNode.label, tax_id=tax_id)
            
            # Reading from a list (tax_id are unique, so there are 1 results)
            for neo_node in list(neo_nodes):
                # search parent
                neo_parents = selector.select(TaxNode.label, tax_id=parent_tax_id)
                
                for neo_parent in neo_parents:
                    count += 1
                    
                    if neo_parent == neo_node:
                        logger.warn("Ignoring relationship between %s and %s" %(neo_node, neo_parent))
                        continue
                    
                    relationship = py2neo.Relationship(neo_parent, "PARENT", neo_node)
                    
                    # add it to database
                    self.transaction.create(relationship)
                    
            # commit
            if count % self.iter == 0:
                self.commit()
                logger.debug("%s iterations processed" %(count))
                self.begin()
                
        # final transaction
        if count % self.iter != 0:
            self.commit()
            logger.debug("%s iterations processed" %(count))
            
        #debug
        logger.info("Loading nodes completed!")


class TaxName(TaxBase):
    """Deal with name records
        
    tax_id					-- the id of node associated with this name
    name_txt				-- name itself
    unique name				-- the unique variant of this name if name not unique
    name class				-- (synonym, common name, ...)
    """
    
    tax_id = None
    name_txt = None
    unique_name = None
    name_class = None
    index = None
    
    # a dictionary in which atrtribute per coulmn index is defined
    attr_to_columns = {"tax_id":0, "name_txt": 1, "unique_name": 2, "name_class":3}
    
    # the properties list
    properties = ["name_txt", "unique_name", "index"]
    label = "TaxName"
    
    def __init__(self, record=None):
        """Initialize class. You could specify a row of nodes.dmp as a list"""
        
        TaxBase.__init__(self, record)
        
        # add new property
        if self.unique_name == '':
            index = (self.tax_id, self.name_txt)
        
        else:
            index = (self.tax_id, self.unique_name)
        
        # create an unique index as (tax_id, name)
        self.index = str(index)
        
    def __repr__(self):
        """Return a string"""
        
        return "<{module}.TaxName(tax_id='{tax_id}', name_txt='{name_txt}', unique_name='{unique_name}', name_class='{name_class}')>".format(module=self.__module__, tax_id=self.tax_id, name_txt=self.name_txt, unique_name=self.unique_name, name_class=self.name_class)

class TaxNamefile(TaxGraph):
    """Deal with name.dmp file"""
    
    # Using a unique index as tax_id, unique_name
    unique_index = "index"
    indexes = ["name_txt"] 
    
    def __init__(self, **kwargs):
        """Instance the class. Need a py2neo Graph instance"""
        
        TaxGraph.__init__(self, **kwargs)
            
        # When do a transaction
        self.iter = 1000
        
    @property
    def schema(self):
        return self.graph.schema
        
    def get_uniqueness_constraints(self, label):
        """get unique constraints"""
        
        return self.schema.get_uniqueness_constraints(label)
        
    def get_indexes(self, label):
        """Get defined indexes"""
        
        return self.schema.get_indexes(label)

    def check_index(self):
        """Check that index are defined"""
        
        try:
            indexes = self.get_indexes(TaxName.label)
            constraints = self.get_uniqueness_constraints(TaxName.label)
            
        except AttributeError, message:
            raise TaxGraphError("You need to connect to database before checking index: %s" %(message))
            
        # add unique constraints
        if not self.unique_index in constraints:
            self.graph.schema.create_uniqueness_constraint(TaxName.label, self.unique_index)
        
        # check and create each name index. Pay attention that indexes contains unique constraints
        for index in self.indexes:
            if not index in indexes and index != self.unique_index:
                logger.debug("Creating index ({label},{property_key})".format(label=TaxName.label, property_key=index))
                self.schema.create_index(TaxName.label, index)

    def insertFrom(self, dmp_file="names.dmp", limit=None):
        """Open a file to read names"""
        
        # open a file in reading mode
        handle = open(dmp_file)
        
        # get a transaction
        try:
            self.begin()
            self.check_index()
            
        except AttributeError, message:
            raise TaxGraphError("You need to connect to database before loading from file: %s" %(message))
        
        # debug
        logger.info("Adding names...")
        
        # get a selector
        selector = py2neo.NodeSelector(self.graph)

        # process line ny line
        for i, record in enumerate(handle):
            # get a node element
            my_name = TaxName(record)
            neo_name = my_name.getNeo4j()
            
            # add it to database
            self.transaction.create(neo_name)
            
            # now search node by taxa id
            neo_nodes = selector.select(TaxNode.label, tax_id=my_name.tax_id)
            
            # get the relationship name from name class
            relationship_name = my_name.name_class.replace(" ", "_").upper()
            
            # Reading from a list (tax_id are unique, so there are 1 results)
            for neo_node in list(neo_nodes):
                # Now add a relationship
                try:
                    relationship = py2neo.Relationship(neo_node, relationship_name, neo_name)
                    
                except py2neo.ConstraintError, message:
                    logger.error("Error for {node}-{relationship}->{name}".format(node=neo_node, relationship=relationship_name, name=neo_name))
                    raise TaxGraphError(message)
                    
                # add it to database
                self.transaction.create(relationship)
            
            # test for limit
            if limit is not None and i >= (limit-1):
                self.commit()
                logger.info("%s limit reached. %s names added" %(limit, i+1))
                break

            # commit data
            if (i+1) % self.iter == 0:
                self.commit()
                logger.debug("%s names added" %(i+1))
                # a new transaction
                self.begin()
                
        # outside cicle
        if (i+1) % self.iter != 0:
            self.commit()
            logger.debug("%s names added" %(i+1))
            
        # closing file
        handle.close()
    
        #debug
        logger.info("Loading names completed!")


