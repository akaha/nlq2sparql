import utils

def testExtractTriples():
    query = 'SELECT DISTINCT ?uri WHERE {?uri <http://dbpedia.org/ontology/creator> <http://dbpedia.org/resource/Bill_Finger>  . ?uri <https://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://dbpedia.org/ontology/ComicsCharacter>}'
    queryTriples = [{
            'subject': '?uri',
            'predicate': '<http://dbpedia.org/ontology/creator>',
            'object': '<http://dbpedia.org/resource/Bill_Finger>'
        }, {
            'subject': '?uri',
            'predicate': '<https://www.w3.org/1999/02/22-rdf-syntax-ns#type>',
            'object': '<http://dbpedia.org/ontology/ComicsCharacter>'
        }
    ]

    templateQuery = 'SELECT DISTINCT ?uri WHERE {?uri <%(e_to_e_out)s> <%(e_out)s> . ?uri rdf:type class }'
    templateQueryTriples = [{
            'subject': '?uri',
            'predicate': '<%(e_to_e_out)s>',
            'object': '<%(e_out)s>'
        }, {
            'subject': '?uri',
            'predicate': 'rdf:type',
            'object': 'class'
        }
    ]

    queryResultTriples = utils.extractTriples(query)
    templateQueryResultTriples = utils.extractTriples(templateQuery)

    assert queryResultTriples == queryTriples
    assert templateQueryResultTriples == templateQueryTriples

def testSplitIntoTriples():
    firstTriple = {
        'subject': '?uri',
        'predicate': '<http://dbpedia.org/ontology/creator>',
        'object': '<http://dbpedia.org/resource/Bill_Finger>'
    }
    secondTriple = {
        'subject': '?uri',
        'predicate': '<https://www.w3.org/1999/02/22-rdf-syntax-ns#type>',
        'object': '<http://dbpedia.org/ontology/ComicsCharacter>'
    }
    whereStatement = '?uri <http://dbpedia.org/ontology/creator> <http://dbpedia.org/resource/Bill_Finger>  . ?uri <https://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://dbpedia.org/ontology/ComicsCharacter>'
    result = utils.splitIntoTriples(whereStatement)

    assert len(result) == 2
    assert result[0] == firstTriple
    assert result[1] == secondTriple

def testSplitIntoTripleParts():
    subject = '?uri'
    predicate = '<http://dbpedia.org/ontology/creator>'
    object = '<http://dbpedia.org/resource/Bill_Finger>'
    triple = subject + ' ' + predicate + ' ' + object

    result = utils.splitIntoTripleParts(triple)

    assert result['subject'] == subject
    assert result['predicate'] == predicate
    assert result['object'] == object


def testExtractSelect():
    query = 'SELECT DISTINCT ?uri WHERE {?uri <http://dbpedia.org/ontology/creator> <http://dbpedia.org/resource/Bill_Finger>  . ?uri <https://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://dbpedia.org/ontology/ComicsCharacter>}'
    select = 'SELECT DISTINCT ?uri'

    result = utils.extractSelect(query)

    assert result == select
