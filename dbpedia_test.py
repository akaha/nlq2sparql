import os

from dbpedia import DBPedia

def testCaching():
    tempFile ='test_cache.json'
    dbpedia = DBPedia(tempFile)
    dbpedia.query = lambda x : ['askedDBPedia']
    dbpedia.cache = dict({
        "<http://dbpedia.org/resource/Gibson_Les_Paul>": ["Gibson Les Paul", "Les Paul"]
    })

    assert dbpedia.getNames('<http://dbpedia.org/resource/Gibson_Les_Paul>') == ['Gibson Les Paul', 'Les Paul']
    assert dbpedia.getNames('foo') == ['askedDBPedia']

    dbpedia.cache['foo'] = ['askedCache']

    assert dbpedia.getNames('foo') == ['askedCache']

    os.remove(tempFile)