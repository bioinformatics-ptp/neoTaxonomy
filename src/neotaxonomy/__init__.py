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


Created on Tue Nov 29 12:47:56 2016

@author: Paolo Cozzi <paolo.cozzi@ptp.it>
"""

__author__ = "Paolo Cozzi"
__copyright__ = "Copyright 2016-2017, Paolo Cozzi"
__credits__ = ["Paolo Cozzi"]
__license__ = "GNU GPLv3"
__version__ = "0.1.1"
__maintainer__ = "Paolo Cozzi"
__email__ = "paolo.cozzi@ptp.it"
__status__ = "alfa"

from neotaxonomy.Neo4j import TaxGraph, TaxNode, TaxNodefile, TaxName, TaxNamefile
    
from neotaxonomy.exceptions import NeoTaxonomyError, TaxGraphError

# All libraries imported with import *
__all__ = ["TaxGraph", "TaxNode", "TaxNodefile", "TaxName", "TaxNamefile", "NeoTaxonomyError", 
           "TaxGraphError"]
           
