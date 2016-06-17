[![Build Status](https://travis-ci.org/NLNOG/bgpfu.svg?branch=master)](https://travis-ci.org/NLNOG/bgpfu)

# BGP FU

BGP FU is a toolbelt to assist with the automatic creation of safe prefix-filters.

BGP FU can ingest data from various sources such as IRRs/RPKI/other, transpose those
according to your policy preferences, and generate partial router configurations.

The jinja2 templating language is used to describe vendor specific output.
