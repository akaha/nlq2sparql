import main
import json

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
        "placeholders": "<%(e_out)s>",
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

def testFindSparqlTemplates():
    templates = json.loads(open('templates.json').read())
    quad = main.LCQuad({
        "verbalized_question": "Who are the <comics characters> whose <painter> is <Bill Finger>?",
        "_id": "f0a9f1ca14764095ae089b152e0e7f12",
        "sparql_template_id": 301,
        "sparql_query": "SELECT DISTINCT ?uri WHERE {?uri <http://dbpedia.org/ontology/creator> <http://dbpedia.org/resource/Bill_Finger>  . ?uri <https://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://dbpedia.org/ontology/ComicsCharacter>}",
        "corrected_question": "Which comic characters are painted by Bill Finger?"})

    result = main.findTemplate(templates, quad)

    assert len(result) >= 1
    assert result[0]['id'] == 301



