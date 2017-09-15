import argparse
import json
from utils import extractTriples


class LCQuad:
    def __init__(self, jsonQuad):
        self.jsonQuad = jsonQuad
        self.verbalizedQuestion = jsonQuad['verbalized_question']
        self.correctedQuestion = jsonQuad['corrected_question']
        self.id = jsonQuad['_id']
        self.sparqlTemplateID = jsonQuad['sparql_template_id']
        self.sparqlTemplate = None
        self.sparqlQuery = jsonQuad['sparql_query']
        self.sparqlQueryTriples = None


def extractEntities (quad):
    queryTriples = extractTriples(getattr(quad, 'sparqlQuery'))
    setattr(quad, 'sparqlQueryTriples', queryTriples)
    possiblePositionsForLCQuadQueries = ['subject', 'object']
    placeholderPositions = getPlaceholderPositions(getattr(quad, 'sparqlTemplate'), possiblePositionsForLCQuadQueries)
    entities = []
    for index in range(len(queryTriples)):
        triple = queryTriples[index]
        if len(placeholderPositions) > index:
            positions = placeholderPositions[index]
            tripleEntities = map(lambda position : triple[position], positions)
            entities.append(tripleEntities)
        # TODO: why are there sparql queries with more triples than their templates?
        # else:
        #     print getattr(quad, 'id'), getattr(quad, 'sparqlTemplateID')
    return entities

def getPlaceholderPositions (template, possiblePlaceholderPositions=None):
    if possiblePlaceholderPositions is None:
        possiblePlaceholderPositions = ['subject', 'predicate', 'object']
    placeholders = template['placeholders']
    findPostitions = lambda triple : filter(lambda key : triple[key] in placeholders, possiblePlaceholderPositions)
    positions = map(findPostitions, template['triples'])
    return positions


def readQuads (file):
    jsonList = json.loads(open(file).read())
    quadList = map(LCQuad, jsonList)
    return quadList


def setSparqlTemplates (lcQuads, templateFile):
    templates = json.loads(open(templateFile).read())
    map(lambda quad : setattr(quad, 'sparqlTemplate', findTemplate(templates, quad)), lcQuads)
    return lcQuads


def findTemplate (templates, quad):
    haveSameId = lambda template : template['id'] == getattr(quad, 'sparqlTemplateID')
    matchingTemplates = filter(haveSameId, templates)
    firstMatch = matchingTemplates[0] if len(matchingTemplates) > 0 else None
    return firstMatch

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--quads', dest='dataset', metavar='quadFile', help='LC Quad dataset')
    parser.add_argument('--templates', dest='templates', metavar='templateFile', help='templates')
    args = parser.parse_args()
    quadFile = args.dataset
    templateFile = args.templates

    rawQuads = readQuads(quadFile)
    quads = setSparqlTemplates(rawQuads, templateFile)
    quadsWithTemplates = filter(lambda quad: getattr(quad, 'sparqlTemplate') != None, quads)
    extractedEntities = map(extractEntities, quadsWithTemplates)
    print extractedEntities