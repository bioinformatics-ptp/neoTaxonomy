#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Tue Dec  6 15:03:39 2016

@author: Paolo Cozzi <paolo.cozzi@ptp.it>
"""

class NeoTaxonomyError(Exception):
    """Base class for neotaxonomy exceptions"""
    
    pass

class TaxGraphError(NeoTaxonomyError):
    """Error for TaxGraph classes"""
    
    pass
