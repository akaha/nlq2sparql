import json
import logging
import re
from SPARQLWrapper import SPARQLWrapper, JSON
import string

GET_LABEL_AND_NAME_OF_RESOURCE = 'SELECT DISTINCT ?label, ?name WHERE { %(target_resource)s <http://www.w3.org/2000/01/rdf-schema#label> ?label . FILTER (langMatches(lang(?label),"en") || langMatches(lang(?label),"")) . optional { %(target_resource)s <http://xmlns.com/foaf/0.1/name> ?name . FILTER (langMatches(lang(?name),"en") || langMatches(lang(?name),"")) }}'


class DBPedia:
    def __init__(self, file=None):
        self.file = file if file != None else 'cache.json'
        try:
            self.cache = json.loads(open(self.file).read())
        except:
            self.cache = dict()
            f = open(self.file, 'w+')
            f.close()

    def getNames (self, resource):
        cachedNames = self.checkCache(resource)
        if cachedNames != None:
            return cachedNames
        names = self.query(resource)
        self.cache[resource] = names
        return names


    def checkCache (self, resource):
        cached = self.cache[resource] if resource in self.cache else None
        return cached


    def saveCache (self):
        with open(self.file, 'w') as outfile:
            json.dump(self.cache, outfile)


    def query (self, resource):
        sparql = SPARQLWrapper("http://dbpedia.org/sparql")
        sparql.setQuery(GET_LABEL_AND_NAME_OF_RESOURCE % {'target_resource': resource})
        sparql.setReturnFormat(JSON)
        logging.debug('DBPedia query for: ' + resource)
        results = sparql.query().convert()
        if len(results["results"]["bindings"]) > 0:
            firstResult = results["results"]["bindings"][0]
            label = firstResult["label"]["value"]
            names = [label]
            if "name" in firstResult:
                name = firstResult["name"]["value"]
                if name != label:
                    names.append(name)
            else:
                bracketMatch = re.search(r'\(.*?\)', label)
                if bracketMatch:
                    labelWithOutBracket = string.strip(string.replace(label, bracketMatch.group(0), ''))
                    names.append(labelWithOutBracket)
            return names
        return []