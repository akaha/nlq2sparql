import argparse
import json
from Levenshtein import distance
import operator
import re
import string
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


class Entity:
    def __init__(self, uri, letter):
        self.uri = uri
        self.letter = letter


def toNSpMRow (lcQuad):
    concatLists = lambda prevList, list : prevList + list
    entityList = set(reduce(concatLists, extractEntities(lcQuad), []))
    entities = map(lambda (uri, letter) : Entity(uri, letter), zip(entityList, string.ascii_uppercase))
    nlQuestion = extractNLTemplateQuestion(getattr(lcQuad, 'verbalizedQuestion'), entities)  # TODO: use correctedQuestion instead of verbalized question
    sparqlQuery = extractSparqlTemplateQuery(getattr(lcQuad, 'sparqlQuery'), entities)
    sparqlGeneratorQuery = extractGeneratorQuery(sparqlQuery, lcQuad)
    row = [nlQuestion, sparqlQuery, sparqlGeneratorQuery]
    return row


def extractNLTemplateQuestion (question, entities):
    wordsInBrackets = set(extractWordsInBrackets(question))
    placeholders = map(lambda entity : mostSimilarPlaceholder(wordsInBrackets, getattr(entity, 'uri')), entities) #TODO: with label instead of uri
    for bracketWord in wordsInBrackets:
        if bracketWord in placeholders:
            upperLetter = getattr(entities[placeholders.index(bracketWord)], 'letter')
            question = string.replace(question, bracketWord, upperLetter)
        else:
            withBrackets = '<' + bracketWord + '>'
            withoutBrackets = bracketWord
            question = string.replace(question, withBrackets, withoutBrackets)

    return question


def extractSparqlTemplateQuery (query, entities):

    def replaceEntityWithLetter (query, entity):
        entityString = re.compile(getattr(entity, 'uri'), re.IGNORECASE)
        replacement = entityString.sub('<' + getattr(entity, 'letter') + '>', query)
        return replacement

    replaceEntitiesWithLetters = lambda query : reduce(replaceEntityWithLetter, entities, query)
    replaceRdfTypeProperty = lambda query : string.replace(query, '<https://www.w3.org/1999/02/22-rdf-syntax-ns#type>', 'a')
    templateQuery= shortenVariableNames(replaceRdfTypeProperty(replaceEntitiesWithLetters(string.lower(query))))
    return templateQuery


def extractGeneratorQuery (query, quad):
    # TODO
    return ''


def shortenVariableNames (query):
    variablePattern = r'\s+?(\?\w+)'
    variables = set(re.findall(variablePattern, query))
    replacement = reduce(lambda query, (variable, letter) : string.replace(query, variable, '?' + letter), zip(variables, ['x', 'y', 'z', 'u', 'v', 'w', 'm', 'n']), query)
    return replacement


def mostSimilarPlaceholder (words, label):
    wordsWithLevenshteinDistance = map(lambda word : tuple([word, distance(word, label)]), words)
    mostSimilarWord = min(wordsWithLevenshteinDistance, key=operator.itemgetter(1))[0]
    return mostSimilarWord


def extractWordsInBrackets (question):
    bracketPattern = r'\<(.*?)\>'
    wordsInBrackets = re.findall(bracketPattern, question)
    return wordsInBrackets


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