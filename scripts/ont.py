#!/usr/bin/env python3

import pronto

print('loading')
#ont = pronto.Ontology('taxslim.owl')
ont = pronto.Ontology('ncbitaxon.obo')
print('loaded')

id = 'NCBITaxon:562'
print('"{}" in ont = {}'.format(id, id in ont))

print(ont[id])

print('children = {}'.format(len(ont[id].rchildren())))
print(ont[id].rchildren())
