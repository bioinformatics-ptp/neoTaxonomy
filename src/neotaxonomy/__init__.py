# -*- coding: utf-8 -*-
"""
Created on Tue Nov 29 12:47:56 2016

@author: Paolo Cozzi <paolo.cozzi@ptp.it>
"""

__author__ = "Paolo Cozzi"
__copyright__ = "Copyright 2016, Paolo Cozzi"
__credits__ = ["Paolo Cozzi"]
__license__ = "GNU GPLv3"
__version__ = "0.1.0"
__maintainer__ = "Paolo Cozzi"
__email__ = "paolo.cozzi@ptp.it"
__status__ = "alfa"

from neotaxonomy.Neo4j import TaxGraph, TaxNode, TaxNodefile, TaxName, TaxNamefile

# All libraries imported with import *
__all__ = ["TaxGraph", "TaxNode", "TaxNodefile", "TaxName", "TaxNamefile"]

# Example package with a console entry point
#def main():
#    print "Hello World"
