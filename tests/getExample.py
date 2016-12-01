#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Thu Dec  1 12:32:41 2016

@author: Paolo Cozzi <paolo.cozzi@ptp.it>
"""

import collections

class OrderedDefaultDict(collections.OrderedDict, collections.defaultdict):
    def __init__(self, default_factory=None, *args, **kwargs):
        #in python3 you can omit the args to super
        super(OrderedDefaultDict, self).__init__(*args, **kwargs)
        self.default_factory = default_factory

class Basefile():
    handle = None
    position = None
    columns = None
    internal = None
    line = None
    
    def __init__(self, myfile):
        self.handle = open(myfile, "rU")
        self.position = 0
        
    def readline(self):
        self.line = self.handle.readline()
        self.position = self.handle.tell()
        record = [el.strip() for el in self.line.split("|")]
        return self.internal._make(record[:-1])
        
    def __iter__(self):
        self.handle.seek(0)
        for line in self.handle:
            self.line = line
            record = [el.strip() for el in line.split("|")]
            self.position = self.handle.tell()
            yield self.internal._make(record[:-1])
            
    def getByTaxId(self, tax_id):
        for record in self.__iter__():
            if record.tax_id == str(tax_id):
                print("Found: %s" %(record.__str__()))
                return record
    

class Nodefile(Basefile):
    handle = None
    position = None
    columns = "tax_id parent_tax_id rank embl_code division_id inherited_div_flag genetic_code_id inherited_GC_flag mitochondrial_genetic_code_id inherited_MGC_flag GenBank_hidden_flag hidden_subtree_root_flag comments"

    internal = collections.namedtuple("Nodefile", columns)
    line = None
    
    def __init__(self, nodefile):
        Basefile.__init__(self, nodefile)
        
    def subsetByTaxID(self, tax_id):
        record = self.getByTaxId(tax_id)
        lines = collections.OrderedDict()
        lines[tax_id] = self.line
        
        while record.tax_id != str(1):
            record = self.getByTaxId(record.parent_tax_id)
            lines[record.tax_id] = self.line

        return lines

class Namefile(Basefile):
    handle = None
    position = None
    columns = "tax_id name_txt unique_name name_class"

    internal = collections.namedtuple("Namefile", columns)
    line = None
    
    def __init__(self, namefile):
        Basefile.__init__(self, namefile)
        
    def subsetByTaxIDs(self, tax_ids):
        lines = OrderedDefaultDict(list)
        
        for record in self.__iter__():
            if record.tax_id in tax_ids:
                print("Found: %s" %(record.__str__()))
                lines[record.tax_id].append(self.line)

        return lines
        
if __name__ == "__main__":
    nodefile = Nodefile("taxdump/nodes.dmp")
    namefile = Namefile("taxdump/names.dmp")
    
    # get node for e. coli
    nodes = nodefile.subsetByTaxID(562)
    tax_ids = nodes.keys()
    
    names = namefile.subsetByTaxIDs(tax_ids)
    
    # write files
    handle = open("tests/test_nodes.dmp", "w")
    for line in nodes.values():
        handle.write(line)
    handle.close()
    
    handle = open("tests/test_names.dmp", "w")
    for line in names.values():
        handle.writelines(line)
    handle.close()
    
    