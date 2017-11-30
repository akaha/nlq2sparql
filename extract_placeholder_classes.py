import argparse
import csv
import collections
import os

from main import extractEntities, readQuads, setSparqlTemplates
from dbpedia import DBPedia


def concatLists( prevList, list ):
    return prevList + list


def read_questions (questionFile):
    questionIDs = []
    with open(questionFile) as file:
        csv_reader = csv.reader(file, delimiter=';')
        for row in csv_reader:
            questionIDs.append(row[0])
    return questionIDs

class Entity:
    def __init__(self, uri, letter, dbpedia=None):
        self.uri = uri
        self.placeholder = letter
        if dbpedia != None:
            self.names = dbpedia.getTypes(uri)


SPORT = [
    'http://dbpedia.org/ontology/SportsClub',
    'http://dbpedia.org/ontology/SportsTeam',
    'http://dbpedia.org/ontology/SportsEvent',
    'http://dbpedia.org/ontology/SportsLeague',
    'http://dbpedia.org/ontology/SportsSeason',
    'http://dbpedia.org/ontology/Sport',
    'http://dbpedia.org/ontology/SportFacility',
    'http://dbpedia.org/ontology/HorseTrainer',
    'http://dbpedia.org/ontology/RaceHorse',
    'http://dbpedia.org/ontology/Coach',
    'http://dbpedia.org/class/yago/Trainer110722575',
    'http://dbpedia.org/ontology/Athlete',
    'http://dbpedia.org/class/yago/WikicatIceHockeyPositions',
    'http://dbpedia.org/class/yago/WikicatAmericanFootballPositions'
    'http://dbpedia.org/class/yago/WikicatBaseballPositions'
    'http://dbpedia.org/class/yago/Position108621598'
]
ART = [
    'http://dbpedia.org/ontology/Artwork',
    'http://dbpedia.org/class/yago/Painting103876519'
    'http://dbpedia.org/ontology/Cartoon',
    'http://dbpedia.org/ontology/LineOfFashion',
    'http://dbpedia.org/ontology/ArchitecturalStructure',
    'http://dbpedia.org/ontology/ComicsCreator',
    'http://dbpedia.org/ontology/FashionDesigner',
    'http://dbpedia.org/ontology/Painter',
    'http://dbpedia.org/ontology/Photographer',
    'http://dbpedia.org/ontology/Sculptor',
    'http://dbpedia.org/ontology/Architect',
    'http://dbpedia.org/ontology/Award',

]
LITERATURE = [
    'http://dbpedia.org/ontology/Writer',
    'http://dbpedia.org/ontology/Philosopher',
    'http://dbpedia.org/ontology/WrittenWork',
    'http://dbpedia.org/ontology/Publisher',
    'http://dbpedia.org/class/yago/Editor110044879'
]
MUSIC = [
    'http://dbpedia.org/ontology/MusicalArtist',
    'http://dbpedia.org/ontology/Instrumentalist',
    'http://dbpedia.org/ontology/MusicalWork',
    'http://dbpedia.org/ontology/Instrument',
    'http://dbpedia.org/ontology/MusicGenre',
    'http://dbpedia.org/ontology/RecordLabel',
    'http://dbpedia.org/ontology/Band',
    'http://dbpedia.org/class/yago/WikicatGuitars',
    'http://dbpedia.org/class/yago/WikicatGuitarAmplifierManufacturers'
]
FILM = [
    'http://dbpedia.org/ontology/Film',
    'http://dbpedia.org/ontology/TelevisionEpisode',
    'http://dbpedia.org/ontology/TelevisionSeason',
    'http://dbpedia.org/ontology/TelevisionShow',
    'http://dbpedia.org/ontology/Actor',
    'http://dbpedia.org/ontology/ScreenWriter',
    'http://dbpedia.org/ontology/Broadcaster',
    'http://dbpedia.org/class/yago/Actor109765278',
    'http://dbpedia.org/class/yago/Entertainer109616922',
    'http://dbpedia.org/class/yago/FilmDirector110088200',
    'http://dbpedia.org/class/yago/FilmMaker110088390',
    'http://dbpedia.org/class/yago/Cameraman109889539'
    'http://dbpedia.org/class/yago/PrizeWinner109627807'

]
GEO = [
    'http://dbpedia.org/ontology/Archipelago',
    'http://dbpedia.org/ontology/Beach',
    'http://dbpedia.org/ontology/Cape',
    'http://dbpedia.org/ontology/Cave',
    'http://dbpedia.org/ontology/Crater',
    'http://dbpedia.org/ontology/Desert',
    'http://dbpedia.org/ontology/Forest',
    'http://dbpedia.org/ontology/Glacier',
    'http://dbpedia.org/ontology/HotSpring',
    'http://dbpedia.org/ontology/Mountain',
    'http://dbpedia.org/ontology/MountainPass',
    'http://dbpedia.org/ontology/MountainRange',
    'http://dbpedia.org/ontology/Valley',
    'http://dbpedia.org/ontology/Volcano',
    'http://dbpedia.org/ontology/Bay',
    'http://dbpedia.org/ontology/Lake',
    'http://dbpedia.org/ontology/Ocean',
    'http://dbpedia.org/ontology/Sea',
    'http://dbpedia.org/ontology/Stream',
    'http://dbpedia.org/ontology/ArchitecturalStructure',
    'http://dbpedia.org/ontology/CelestialBody',
    'http://dbpedia.org/ontology/Cemetery',
    'http://dbpedia.org/ontology/ConcentrationCamp',
    'http://dbpedia.org/ontology/CountrySeat',
    'http://dbpedia.org/ontology/Garden',
    'http://dbpedia.org/ontology/HistoricPlace',
    'http://dbpedia.org/ontology/Mine',
    'http://dbpedia.org/ontology/Monument',
    'http://dbpedia.org/ontology/Park',
    'http://dbpedia.org/ontology/ProtectedArea',
    'http://dbpedia.org/ontology/SiteOfSpecialScientificInterest',
    'http://dbpedia.org/ontology/WineRegion',
    'http://dbpedia.org/ontology/WorldHeritageSite',
    'http://dbpedia.org/ontology/Agglomeration',
    'http://dbpedia.org/ontology/Community',
    'http://dbpedia.org/ontology/Continent',
    'http://dbpedia.org/ontology/Country',
    'http://dbpedia.org/ontology/GatedCommunity',
    'http://dbpedia.org/ontology/Intercommunality',
    'http://dbpedia.org/ontology/Island',
    'http://dbpedia.org/ontology/Locality',
    'http://dbpedia.org/ontology/Region',
    'http://dbpedia.org/ontology/State',
    'http://dbpedia.org/ontology/Street',
    'http://dbpedia.org/ontology/Territory',
    'http://dbpedia.org/ontology/City',
    'http://dbpedia.org/ontology/CityDistrict',
    'http://dbpedia.org/ontology/HistoricalSettlement',
    'http://dbpedia.org/ontology/Town',
    'http://dbpedia.org/ontology/Village'
]

art_types = FILM +  MUSIC + LITERATURE + ART
all_types = GEO + SPORT + ART

def filterTypes (types):
    filtered = filter(lambda type: type in all_types, types)
    if not filtered:
        if 'http://dbpedia.org/ontology/Person' in types:
            filtered.append('http://dbpedia.org/ontology/Person')
    return '|'.join(filtered)


def saveTypeInformation (types, outputFile):
    with open(outputFile, 'w') as file:
        csv_writer = csv.writer(file, delimiter=';')
        csv_writer.writerows(types)


def print_statistic( types_counter, filtered_types_counter ):
    ordered = collections.OrderedDict(types_counter.most_common())
    filtered_ordered = collections.OrderedDict(filtered_types_counter.most_common())
    for type in ordered:
        print '{:8d}\t{}'.format(ordered[type], type)

    print '\n\nFiltered:\n\n'
    for type in filtered_ordered:
        print '{:8d}\t{}'.format(ordered[type], type)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--questions', dest='questions', metavar='questionFile', help='file with question ids')
    parser.add_argument('--quads', dest='dataset', metavar='quadFile', help='LC Quad dataset')
    parser.add_argument('--templates', dest='templates', metavar='templateFile', help='templates')
    args = parser.parse_args()
    quadFile = args.dataset
    templateFile = args.templates
    questionFile = args.questions

    questionIDs = read_questions(questionFile)
    outputFile = os.path.splitext(questionFile)[0] + '_types.csv'
    rawQuads = readQuads(quadFile)
    quads = setSparqlTemplates(rawQuads, templateFile)
    filteredQuads = filter(lambda quad : getattr(quad, 'id') in questionIDs, quads)
    filteredQuadIds = map(lambda quad : getattr(quad, 'id'), filteredQuads)
    questions = map(lambda id : filteredQuads[filteredQuadIds.index(id)], questionIDs)

    dbpedia = DBPedia()
    result = []
    types_counter = collections.Counter()
    filtered_types_counter = collections.Counter()

    for quad in questions:
        entityList = set(reduce(concatLists, extractEntities(quad), []))
        types = map(dbpedia.getTypes, entityList)
        types_counter.update(types)
        filtered = map(filterTypes, types)
        filtered_types_counter.update(filtered)
        result.append(filtered)

    saveTypeInformation(result, outputFile)
    dbpedia.saveCache()
    print_statistic(types_counter, filtered_types_counter)