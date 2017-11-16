import argparse
import copy
import json
import math
from Levenshtein import distance
import logging
import operator
import re
import string

from dbpedia import DBPedia
from utils import extractTriples, extractSelect

logging.basicConfig(filename='templates.log', level=logging.DEBUG)


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
    def __init__(self, uri, letter, dbpedia=None):
        self.uri = uri
        self.placeholder = '<' + letter + '>'
        self.variable = '?' + string.lower(letter)
        uriName = nameFromUri(uri)
        if dbpedia != None:
            names = dbpedia.getNames(uri)
            self.names = names if len(names) > 0 else [uriName]
        else:
            self.names = [uriName]

class SparqlQuery:
    def __init__(self, query):
        self.query = query
        self.selectClause = extractSelect(query)
        self.whereClauseTriples = extractTriples(query)
    def __str__(self):
        tripleToString = lambda triple : ' '.join(map(lambda key : triple[key], ['subject', 'predicate', 'object']))
        return self.selectClause + ' where { ' + ' . '.join(map(tripleToString, self.whereClauseTriples)) + ' }'


def toNSpMRow (lcQuad, dbpedia=None):
    concatLists = lambda prevList, list : prevList + list
    entityList = set(reduce(concatLists, extractEntities(lcQuad), []))
    entities = map(lambda (uri, letter) : Entity(uri, letter, dbpedia), zip(entityList, string.ascii_uppercase))
    nlQuestion = extractNLTemplateQuestionFromCorrectedQuestion(lcQuad, entities)
    if not nlQuestion:
        nlQuestion = extractNLTemplateQuestionFromVerbalizedQuestion(lcQuad, entities)
    sparqlQuery = extractSparqlTemplateQuery(getattr(lcQuad, 'sparqlQuery'), entities)
    sparqlGeneratorQuery = extractGeneratorQuery(sparqlQuery, entities)
    row = [nlQuestion, sparqlQuery, sparqlGeneratorQuery]
    return row


def extractNLTemplateQuestionFromCorrectedQuestion (lcQuad, entities):
    question = getattr(lcQuad, 'correctedQuestion')
    compare = lambda name, names : reduce(lambda prev, nameItem : compareStrings(name, nameItem) if prev == 0 else prev, names, 0)
    compareNames = lambda names1, names2 : reduce(lambda prev, name : compare(name, names2) if prev == 0 else prev, names1, 0)
    compareEntities = lambda entity1, entity2 : compareNames(getattr(entity1, 'names'), getattr(entity2, 'names'))

    sortedEntities = sorted(entities, cmp=compareEntities)

    for entity in sortedEntities:
        names = getattr(entity, 'names')
        escapedNames = map(re.escape, names)
        placeholder = getattr(entity, 'placeholder')
        matchInQuestion = re.search(r'(' + '|'.join(escapedNames) + r')s?', question, flags=re.IGNORECASE)
        if (matchInQuestion):
            question = string.replace(question, matchInQuestion.group(0), placeholder)
        else:
            logging.debug('Fuzzy search necessary for: "' + ' | '.join(names) + '" in: ' + question + ', ' + str(getattr(lcQuad, 'id')))
            fuzzySearchMatch = fuzzySearch(names, question)
            if (fuzzySearchMatch):
                question = string.replace(question, fuzzySearchMatch.group(0), placeholder)
            else:
                logging.debug('Fuzzy entity detection failed for: "' + ' | '.join(names) + '" in: ' + question + ', ' + str(getattr(lcQuad, 'id')))
                return None

    return question


def extractNLTemplateQuestionFromVerbalizedQuestion (lcQuad, entities):
    question = getattr(lcQuad, 'verbalizedQuestion')
    wordsInBrackets = set(extractWordsInBrackets(question))
    sortedWordsInBrackets = sorted(wordsInBrackets, cmp=compareStrings)
    placeholders = map(lambda entity : mostSimilarPlaceholder(sortedWordsInBrackets, getattr(entity, 'names')), entities)

    for bracketWord in sortedWordsInBrackets:
        withBrackets = '<' + bracketWord + '>'
        withoutBrackets = bracketWord
        replacement = getattr(entities[placeholders.index(bracketWord)], 'placeholder') if bracketWord in placeholders else withoutBrackets
        question = string.replace(question, withBrackets, replacement)

    return question


def fuzzySearch (names, question ):
    wordsInNames = map(lambda name : re.split(r'\W+', name), names)
    wordsInQuestion = re.split(r'\W+', question)
    maxSequenceLength = max(map(len, wordsInNames))
    subsequences = buildSubsequences(wordsInQuestion, maxSequenceLength)
    minDistance = lambda string, stringList : min(map(lambda stringItem : [distance(string, stringItem), stringItem], stringList), key=operator.itemgetter(0))
    subsequencesWithLevenshteinDistance = map(lambda sequence: [sequence] + minDistance(' '.join(sequence), names), subsequences)
    mostSimilar = min(subsequencesWithLevenshteinDistance, key=operator.itemgetter(1))
    mostSimilarSequence = mostSimilar[0]
    mostSimilarDistance = mostSimilar[1]
    mostSimilarName = mostSimilar[2]
    tolerance = math.ceil(len(mostSimilarName) / 2)
    if (mostSimilarDistance <= tolerance):
        sequencePattern = '\W+'.join(map(re.escape, mostSimilarSequence))
        sequenceInQuestionMatch = re.search(sequencePattern, question)
        if (not sequenceInQuestionMatch):
            logging.debug('Failed to retransform: ' + str(sequencePattern))

        return sequenceInQuestionMatch
    else:
        logging.debug(str(mostSimilarDistance) + ' as distance value seems too high: ' + ' '.join(mostSimilarSequence) + ' == ' + mostSimilarName + ' ?')
        return None


def compareStrings(x, y ):
    x_isSubstringOf_y = y.find(x) > -1
    y_isSubstringOf_x = x.find(y) > -1
    if x_isSubstringOf_y:
        return 1
    if y_isSubstringOf_x:
        return -1
    return 0


def buildSubsequences (sequence, maxLength):
    subsequences = set()
    for sequenceLength in range(1, maxLength + 1):
        for startIndex in range(0, len(sequence) - sequenceLength + 1):
            endIndex = startIndex + sequenceLength
            subsequence = sequence[startIndex:endIndex]
            subsequences.add(tuple(subsequence))
    return subsequences


def extractSparqlTemplateQuery (query, entities):
    def replaceEntityWithPlaceholder (sparqlQuery, entity):
        entityString = re.compile(re.escape(getattr(entity, 'uri')), re.IGNORECASE)
        triples = getattr(sparqlQuery, 'whereClauseTriples')
        placeholder = getattr(entity, 'placeholder')
        for triple in triples:
            triple['subject'] = entityString.sub(placeholder, triple['subject'])
            triple['object'] = entityString.sub(placeholder, triple['object'])
        setattr(sparqlQuery, 'selectClause', entityString.sub(placeholder, getattr(sparqlQuery, 'selectClause')))
        return sparqlQuery

    def replaceRdfTypeProperty (sparqlQuery):
        triples = getattr(sparqlQuery, 'whereClauseTriples')
        for triple in triples:
            triple['predicate'] = string.replace(triple['predicate'], '<https://www.w3.org/1999/02/22-rdf-syntax-ns#type>', 'a')
        return sparqlQuery

    replaceEntitiesWithPlaceholders = lambda sparqlQuery : reduce(replaceEntityWithPlaceholder, entities, sparqlQuery)
    templateQuery = replaceRdfTypeProperty(replaceEntitiesWithPlaceholders(SparqlQuery(query)))
    return templateQuery


def extractGeneratorQuery (sparqlQuery, entities):
    def replacePlaceholderWithVariable (triple, entity):
        for key in ['subject', 'object']:
            if triple[key] == getattr(entity, 'placeholder'):
                triple[key] = getattr(entity, 'variable')
        return triple

    query = copy.deepcopy(sparqlQuery)
    triples = getattr(query, 'whereClauseTriples')
    for triple in triples:
        for entity in entities:
            triple = replacePlaceholderWithVariable(triple, entity)

    variables = map(lambda entity : getattr(entity, 'variable'), entities)
    generatorSelectClause = 'select distinct ' + ', '.join(variables)
    setattr(query, 'selectClause', generatorSelectClause)

    return query


def extractGeneratorQueryOnlyFromTemplateQuery (sparqlQuery):
    def extractPlaceholderPlaceholders(query):
        placeholders = []
        variable_pattern_a = r'<A>'
        variable_pattern_b = r'<B>'
        variable_pattern_c = r'<C>'
        variable_match_a = re.search(variable_pattern_a, query, re.IGNORECASE)
        variable_match_b = re.search(variable_pattern_b, query, re.IGNORECASE)
        variable_match_c = re.search(variable_pattern_c, query, re.IGNORECASE)
        if variable_match_a:
            placeholders.append('<A>')
        if variable_match_b:
            placeholders.append('<B>')
        if variable_match_c:
            placeholders.append('<C>')
        return placeholders

    placeholders = extractPlaceholderPlaceholders(sparqlQuery)
    whereStatementPattern = r'{(.*?)}'
    whereStatementMatch = re.search(whereStatementPattern, sparqlQuery)
    whereStatement = whereStatementMatch.group(1)

    if whereStatement:
        variables = []
        for placeholder in placeholders:
            variable = '?' + str.lower(placeholder[1])
            variables.append(variable)
            whereStatement = whereStatement.replace(placeholder, variable)
        generatorSelectClause = 'select distinct ' + ', '.join(variables)
        return '{} where {{ {} }}'.format(generatorSelectClause, whereStatement)
    else:
        return ''


def shortenVariableNames (queryString):
    variablePattern = r'\s+?(\?\w+)'
    variables = set(re.findall(variablePattern, queryString))
    replacement = reduce(lambda query, (variable, letter) : string.replace(query, variable, '?' + letter), zip(variables, ['x', 'y', 'z', 'u', 'v', 'w', 'm', 'n']), queryString)
    return replacement


def nameFromUri (uri):
    stripPrefix = lambda s : s.replace('<http://dbpedia.org/resource/', '')
    stripEndTag = lambda s : s.replace('>', '')
    removeBrackets = lambda s : re.sub(r'\(.*?\)', '', s)
    replaceUnderscores = lambda s : s.replace('_', ' ')
    return string.strip(replaceUnderscores(removeBrackets(stripEndTag(stripPrefix(uri)))))


def mostSimilarPlaceholder (words, names):
    minDistance = lambda word, names : min(map(lambda name : distance(word, name), names))
    wordsWithLevenshteinDistance = map(lambda word : tuple([word, minDistance(word, names)]), words)
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
    dbpedia = DBPedia()
    try:
        for quad in quadsWithTemplates:
            row = toNSpMRow(quad, dbpedia)
            nlQuestion = row[0]
            sparqlQuery = str(row[1])
            generatorQuery = str(row[2])
            id = getattr(quad, 'id')
            print "%s\t%s\t%s\t%s" % (nlQuestion, sparqlQuery, generatorQuery, id)

    finally:
        dbpedia.saveCache()