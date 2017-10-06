import json
from SPARQLWrapper import SPARQLWrapper, JSON

GET_LABEL_OF_RESOURCE = 'SELECT DISTINCT ?label WHERE { %(target_resource)s <http://www.w3.org/2000/01/rdf-schema#label> ?label . FILTER (langMatches(lang(?label),"en") || langMatches(lang(?label),""))	} '


class DBPedia:
    def __init__(self, file=None):
        self.file = file if file != None else 'cache.json'
        try:
            self.cache = json.loads(open(self.file).read())
        except:
            self.cache = dict()
            f = open(self.file, 'w+')
            f.close()

    def getLabel (self, resource):
        cachedLabel = self.checkCache(resource)
        if cachedLabel:
            return cachedLabel
        label = self.queryLabel(resource)
        if label:
            return label
        return None


    def checkCache (self, resource):
        try:
            cached = self.cache[resource]
        except:
            cached = None
        return cached

    def saveInCache (self, resource, result):
        self.cache[resource] = result
        with open(self.file, 'w') as outfile:
            json.dump(self.cache, outfile)

    def queryLabel (self, resource):
        sparql = SPARQLWrapper("http://dbpedia.org/sparql")
        sparql.setQuery(GET_LABEL_OF_RESOURCE % {'target_resource': resource})
        sparql.setReturnFormat(JSON)
        results = sparql.query().convert()
        if len(results["results"]["bindings"]) > 0:
            firstResult = results["results"]["bindings"][0]["label"]["value"]
            self.saveInCache(resource, firstResult)
            return firstResult
        return None