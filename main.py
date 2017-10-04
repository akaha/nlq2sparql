import argparse
import copy
import json
from Levenshtein import distance
import operator
import re
import string
from utils import extractTriples, extractSelect


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
        self.variable = '?' + string.lower(letter)


class SparqlQuery:
    def __init__(self, query):
        self.query = query
        self.selectClause = extractSelect(query)
        self.whereClauseTriples = extractTriples(query)
    def __str__(self):
        tripleToString = lambda triple : ' '.join(map(lambda key : triple[key], ['subject', 'predicate', 'object']))
        return self.selectClause + ' where { ' + ' . '.join(map(tripleToString, self.whereClauseTriples)) + ' }'


def toNSpMRow (lcQuad):
    concatLists = lambda prevList, list : prevList + list
    entityList = set(reduce(concatLists, extractEntities(lcQuad), []))
    entities = map(lambda (uri, letter) : Entity(uri, letter), zip(entityList, string.ascii_uppercase))
    nlQuestion = extractNLTemplateQuestion(getattr(lcQuad, 'verbalizedQuestion'), entities)  # TODO: use correctedQuestion instead of verbalized question
    sparqlQuery = extractSparqlTemplateQuery(getattr(lcQuad, 'sparqlQuery'), entities)
    sparqlGeneratorQuery = extractGeneratorQuery(sparqlQuery, entities)
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
    def replaceEntityWithLetter (sparqlQuery, entity):
        entityString = re.compile(getattr(entity, 'uri'), re.IGNORECASE)
        triples = getattr(sparqlQuery, 'whereClauseTriples')
        letter = '<' + getattr(entity, 'letter') + '>'
        for triple in triples:
            triple['subject'] = entityString.sub(letter, triple['subject'])
            triple['object'] = entityString.sub(letter, triple['object'])
        setattr(sparqlQuery, 'selectClause', entityString.sub(letter, getattr(sparqlQuery, 'selectClause')))
        return sparqlQuery

    def replaceRdfTypeProperty (sparqlQuery):
        triples = getattr(sparqlQuery, 'whereClauseTriples')
        for triple in triples:
            triple['predicate'] = string.replace(triple['predicate'], '<https://www.w3.org/1999/02/22-rdf-syntax-ns#type>', 'a')
        return sparqlQuery

    replaceEntitiesWithLetters = lambda sparqlQuery : reduce(replaceEntityWithLetter, entities, sparqlQuery)
    templateQuery = replaceRdfTypeProperty(replaceEntitiesWithLetters(SparqlQuery(query)))
    return templateQuery


def extractGeneratorQuery (sparqlQuery, entities):
    def replaceLetterWithVariable (triple, entity):
        for key in ['subject', 'object']:
            if triple[key] == '<' + getattr(entity, 'letter') + '>':
                triple[key] = getattr(entity, 'variable')
        return triple

    query = copy.deepcopy(sparqlQuery)
    triples = getattr(query, 'whereClauseTriples')
    for triple in triples:
        for entity in entities:
            triple = replaceLetterWithVariable(triple, entity)

    variables = map(lambda entity : getattr(entity, 'variable'), entities)
    generatorSelectClause = 'select distinct ' + ', '.join(variables)
    setattr(query, 'selectClause', generatorSelectClause)

    return query


def shortenVariableNames (queryString):
    variablePattern = r'\s+?(\?\w+)'
    variables = set(re.findall(variablePattern, queryString))
    replacement = reduce(lambda query, (variable, letter) : string.replace(query, variable, '?' + letter), zip(variables, ['x', 'y', 'z', 'u', 'v', 'w', 'm', 'n']), queryString)
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
        else:
            # in case of misformed templates
            print getattr(quad, 'id'), getattr(quad, 'sparqlTemplateID')
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
    # extractedEntities = map(extractEntities, quadsWithTemplates)
    # print extractedEntities
    for quad in quadsWithTemplates:
        row = toNSpMRow(quad)
        nlQuestion = row[0]
        sparqlQuery = str(row[1])
        generatorQuery = str(row[2])
        print "%s\t%s\t%s" % (nlQuestion, sparqlQuery, generatorQuery)