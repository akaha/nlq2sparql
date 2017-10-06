import main
import json
import string


def testToNSpMRow():
    quad = main.LCQuad({
        "verbalized_question": "Give me a count of <royalties> whose <buried in> is <Rome>?",
        "_id": "a33350d8ce8d449a9ce52f0ca2451234",
        "sparql_template_id": 401,
        "sparql_query": "SELECT DISTINCT COUNT(?uri) WHERE {?uri <http://dbpedia.org/property/placeOfBurial> <http://dbpedia.org/resource/Rome>  . ?uri <https://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://dbpedia.org/ontology/Royalty>}",
        "corrected_question": "Give me a count of royalties buried in Rome ?"
    })
    template = {
        "triples": [
          {
            "predicate": "<%(e_to_e_out)s>",
            "object": "<%(e_out)s>",
            "subject": "?uri"
          },
          {
            "predicate": "rdf:type",
            "object": "class",
            "subject": "?uri"
          }
        ],
        "n_entities": 1,
        "template": " SELECT DISTINCT COUNT(?uri) WHERE {?uri <%(e_to_e_out)s> <%(e_out)s> . ?uri rdf:type class} ",
        "placeholders": ["<%(e_out)s>"],
        "type": "count",
        "id": 401
      }
    setattr(quad, 'sparqlTemplate', template)

    placeholderQuestion = 'Give me a count of royalties whose buried in is <A>?'
    sparqlQuery = 'SELECT DISTINCT COUNT(?uri) WHERE { ?uri <http://dbpedia.org/property/placeOfBurial> <A> . ?uri a <http://dbpedia.org/ontology/Royalty> }'
    generatorQuery = 'select distinct ?a where { ?uri <http://dbpedia.org/property/placeOfBurial> ?a . ?uri a <http://dbpedia.org/ontology/Royalty> }'

    row = main.toNSpMRow(quad)

    assert row[0] == placeholderQuestion
    assert string.lower(str(row[1])) == string.lower(sparqlQuery)
    assert string.lower(str(row[2])) == string.lower(generatorQuery)


def testExtractEntities():
    quad = main.LCQuad({
        "verbalized_question": "Who are the <comics characters> whose <painter> is <Bill Finger>?",
        "_id": "f0a9f1ca14764095ae089b152e0e7f12",
        "sparql_template_id": 301,
        "sparql_query": "SELECT DISTINCT ?uri WHERE {?uri <http://dbpedia.org/ontology/creator> <http://dbpedia.org/resource/Bill_Finger>  . ?uri <https://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://dbpedia.org/ontology/ComicsCharacter>}",
        "corrected_question": "Which comic characters are painted by Bill Finger?"})
    template = {
        "triples": [
            {
                "predicate": "<%(e_to_e_out)s>",
                "object": "<%(e_out)s>",
                "subject": "?uri"
            },
            {
                "predicate": "rdf:type",
                "object": "class",
                "subject": "?uri"
            }
        ],
        "n_entities": 1,
        "template": " SELECT DISTINCT ?uri WHERE {?uri <%(e_to_e_out)s> <%(e_out)s> . ?uri rdf:type class } ",
        "placeholders": ["<%(e_out)s>"],
        "type": "vanilla",
        "id": 301
    }
    setattr(quad, 'sparqlTemplate', template)
    entities = [['<http://dbpedia.org/resource/Bill_Finger>'], []]

    result = main.extractEntities(quad)

    assert result == entities


def testGetPlaceholderPositions():
    template = {
        "triples": [
            {
                "predicate": "<%(e_to_e_out)s>",
                "object": "<%(e_out_1)s>",
                "subject": "?uri"
            },
            {
                "predicate": "<%(e_to_e_out)s>",
                "object": "<%(e_out_2)s>",
                "subject": "?uri"
            }
        ],
        "n_entities": 2,
        "template": " SELECT DISTINCT ?uri WHERE { ?uri <%(e_to_e_out)s> <%(e_out_1)s> . ?uri <%(e_to_e_out)s> <%(e_out_2)s>} ",
        "placeholders": ["<%(e_out_1)s>", "<%(e_out_2)s>"],
        "type": "vanilla",
        "id": 7
    }
    # list with lists necessary because one triple could hold multiple placeholders
    positions = [['object'], ['object']]

    result = main.getPlaceholderPositions(template)

    assert result == positions


def testReadJSON():
    result = main.readQuads('test_data_set.json')
    attributes = ['verbalizedQuestion', 'id', 'sparqlQuery', 'correctedQuestion', 'sparqlTemplateID']

    assert len(result) > 0
    for attribute in attributes:
        assert hasattr(result[0], attribute) == True


def testFindSparqlTemplate():
    templates = json.loads(open('templates.json').read())
    quad = main.LCQuad({
        "verbalized_question": "Who are the <comics characters> whose <painter> is <Bill Finger>?",
        "_id": "f0a9f1ca14764095ae089b152e0e7f12",
        "sparql_template_id": 301,
        "sparql_query": "SELECT DISTINCT ?uri WHERE {?uri <http://dbpedia.org/ontology/creator> <http://dbpedia.org/resource/Bill_Finger>  . ?uri <https://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://dbpedia.org/ontology/ComicsCharacter>}",
        "corrected_question": "Which comic characters are painted by Bill Finger?"})

    result = main.findTemplate(templates, quad)

    assert len(result) >= 1
    assert result['id'] == 301


def testExtractNLTemplateQuestion():
    question = 'Who are the <comics characters> whose <painter> is <Bill Finger>?'
    entities = [main.Entity('<http://dbpedia.org/resource/Bill_Finger>', 'A')]
    templateQuestion = 'Who are the comics characters whose painter is <A>?'

    result = main.extractNLTemplateQuestion(question, entities)

    assert result == templateQuestion


def testExtractSparqlTemplateQuery():
    query = 'SELECT DISTINCT ?uri WHERE {?uri <http://dbpedia.org/ontology/creator> <http://dbpedia.org/resource/Bill_Finger>.?uri <https://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://dbpedia.org/ontology/ComicsCharacter>}'
    entities = [main.Entity('<http://dbpedia.org/resource/Bill_Finger>', 'A')]
    templateQuery = 'SELECT DISTINCT ?uri where { ?uri <http://dbpedia.org/ontology/creator> <A> . ?uri a <http://dbpedia.org/ontology/ComicsCharacter> }'

    result = str(main.extractSparqlTemplateQuery(query, entities))

    assert result == templateQuery


def testExtractGeneratorQuery():
    entities = [main.Entity('<http://dbpedia.org/resource/Bill_Finger>', 'A'), main.Entity('foo', 'B')]
    templateQuery = 'SELECT DISTINCT ?uri where { ?uri <http://dbpedia.org/ontology/creator> <A> . ?uri a <B> }'
    sparqlQuery = main.SparqlQuery(templateQuery)
    generatorQuery = 'select distinct ?a, ?b where { ?uri <http://dbpedia.org/ontology/creator> ?a . ?uri a ?b }'

    result = str(main.extractGeneratorQuery(sparqlQuery, entities))

    assert result == generatorQuery


def testMostSimilarPlaceholder():
    words = ['comics characters', 'painter', 'Bill Finger']
    entity = '<http://dbpedia.org/resource/Bill_Finger>'

    result = main.mostSimilarPlaceholder(words, entity)

    assert result == words[2]


def testShorten():
    query = '?toolong or not ?toolong is the ?question'
    shortened = '?x or not ?x is the ?y'
    result = main.shortenVariableNames(query)
    assert result == shortened


def testQueryObjectToString():
    originalQuery = 'SELECT DISTINCT ?uri WHERE { ?uri <http://dbpedia.org/ontology/creator> <http://dbpedia.org/resource/Bill_Finger> . ?uri <https://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://dbpedia.org/ontology/ComicsCharacter> }'
    obj = main.SparqlQuery(originalQuery)

    result = str(obj)

    assert string.lower(result) == string.lower(originalQuery)
