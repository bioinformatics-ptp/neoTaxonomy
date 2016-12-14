neoTaxonomy
===========

.. image:: https://travis-ci.org/bioinformatics-ptp/neoTaxonomy.svg?branch=master
    :target: https://travis-ci.org/bioinformatics-ptp/neoTaxonomy
    :alt: Build Status

``neoTaxonomy`` is python API to deal with NCBI taxonomy in a neo4j database.

License
-------

neoTaxonomy - A python API to deal with NCBI taxonomy in a neo4j database

Copyright (C) 2016 Paolo Cozzi <paolo.cozzi@ptp.it>

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

Dependencies
------------

neoTaxonomy depends on a local installation of `neo4j <http://neo4j.com/docs/operations-manual/current/>`_.
You should consider to provide an installation on neo4j using `docker <https://neo4j.com/developer/docker/>`_
like this:

.. code:: bash

  $ docker pull neo4j:3.1
  $ docker run -d --publish=7474:7474 --publish=7687:7687 --name neo4j --env=NEO4J_AUTH=<user>/<password> neo4j:3.1

This will download and run the latest `neo4j image <https://hub.docker.com/_/neo4j/>`_, publishing the standard HTTP and BOLT port on your host

Installation
------------

`Download <https://github.com/bioinformatics-ptp/neoTaxonomy.git>`_ code from GitHub, then install using pip:

.. code:: bash

  $ git clone https://github.com/bioinformatics-ptp/neoTaxonomy.git
  $ cd neoTaxonomy
  $ pip install .

Usage
-----

Loading data into database
``````````````````````````

Download taxdump data from `NCBI taxonomy`_, and unpack archive:

.. code:: bash

  $ mkdir taxdump
  $ cd taxdump
  $ wget ftp://ftp.ncbi.nih.gov/pub/taxonomy/taxdump.tar.gz
  $ tar -xvzf taxdump.tar.gz

.. _`NCBI taxonomy`: ftp://ftp.ncbi.nih.gov/pub/taxonomy/

Then upload ``nodes.dmp`` and ``names.dmp`` with ``fillTaxonomyDB``. You need to provide
parameters for database connection, like this:

.. code:: bash

  $ fillTaxonomyDB --nodes nodes.dmp --names names.dmp --host <host> --password=<password>

Using neoTaxonomy in scripts
````````````````````````````

An example of python program to get lineage by taxon_id:

.. code:: python

  from neotaxonomy import TaxGraph
  db = TaxGraph(host='localhost', user='neo4j', password='password')
  db.connect()

  # 562 is the E. Coli taxon id
  print db.getLineage(562)
  # [u'k__Bacteria', u'p__Proteobacteria', u'c__Gammaproteobacteria', u'o__Enterobacterales', u'f__Enterobacteriaceae', u'g__Escherichia', u's__coli']
