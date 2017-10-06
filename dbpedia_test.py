import os

from dbpedia import DBPedia

def testCaching():
    tempFile ='test_cache.json'
    dbpedia = DBPedia(tempFile)
    dbpedia.queryLabel = lambda x : 'askedDBPedia'
    dbpedia.cache = dict({
        "http://dbpedia.org/resource/Gibson_Les_Paul": "Gibson Les Paul"
    })

    assert dbpedia.getLabel('http://dbpedia.org/resource/Gibson_Les_Paul') == 'Gibson Les Paul'
    assert dbpedia.getLabel('foo') == 'askedDBPedia'

    dbpedia.cache['foo'] = 'askedCache'

    assert dbpedia.getLabel('foo') == 'askedCache'

    os.remove(tempFile)