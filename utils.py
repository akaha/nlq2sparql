import json
import re

def extractSelect (sparqlQuery):
    selectStatementPattern = r'(.*?)\swhere'
    selectStatementMatch = re.search(selectStatementPattern, sparqlQuery, re.IGNORECASE)
    selectStatement = selectStatementMatch.group(1)
    return selectStatement


def extractTriples (sparqlQuery):
    whereStatementPattern = r'{(.*?)}'
    whereStatementMatch = re.search(whereStatementPattern, sparqlQuery)
    whereStatement = whereStatementMatch.group(1)
    triples = splitIntoTriples(whereStatement)
    return triples


def splitIntoTriples (whereStatement):
    tripleAndSeparators = re.split('(\.[\s\?\<$])', whereStatement)
    trimmed = map(lambda str : str.strip(), tripleAndSeparators)

    def repair (list, element):
        if element not in ['.', '.?', '.<']:
            previousElement = list[-1]
            del list[-1]
            if previousElement in ['.', '.?', '.<']:
                cutoff = previousElement[1] if previousElement in ['.?', '.<'] else ''
                list.append(cutoff + element)
            else:
                list.append(previousElement + ' ' + element)
        else:
            list.append(element)

        return list

    tripleStatements = reduce(repair, trimmed, [''])
    triplesWithNones = map(splitIntoTripleParts, tripleStatements)
    triples = filter(lambda triple : triple != None, triplesWithNones)
    return triples


def splitIntoTripleParts (triple):
    statementPattern = r'(\S+)\s+(\S+)\s+(\S+)'
    statementPatternMatch = re.search(statementPattern, triple)

    if statementPatternMatch:
        return {
            'subject': statementPatternMatch.group(1),
            'predicate': statementPatternMatch.group(2),
            'object': statementPatternMatch.group(3)
        }
    else:
        return None


def enhanceTemplateInformation ():
    'Used to prefill the file enhanced_templates.json from templates.json. But manual review is necessary!'
    templates = json.loads(open('templates.json').read())
    triples = map(lambda item : extractTriples(item['template']), templates)
    possiblePlaceholderPositions = ['subject', 'object']
    placeholders = map(lambda template : extractPlaceholders(template, possiblePlaceholderPositions), templates)
    for index in range(len(templates)):
        templates[index]['triples'] = triples[index]
        templates[index]['placeholders'] = placeholders[index]
    print json.JSONEncoder().encode(templates)


def extractPlaceholders (template, possiblePlaceholderPositions=None):
    if possiblePlaceholderPositions is None:
        possiblePlaceholderPositions = ['subject', 'predicate', 'object']
    templateTriples = extractTriples(template['template'])
    firstStatement = templateTriples[0]
    possiblePositionsInFirstStatement = filter(lambda triplePart : couldBePlaceholder(firstStatement[triplePart]), possiblePlaceholderPositions)
    highProbabilityForCorrectPlaceholder = template['n_entities'] == 1 & len(possiblePositionsInFirstStatement) == 1
    if highProbabilityForCorrectPlaceholder:
        position = possiblePositionsInFirstStatement[0]
        placeholder = firstStatement[position]
        return placeholder
    return []


def couldBePlaceholder (triplePart):
    isQueryVariable = triplePart.startswith('?')
    return not(isQueryVariable)