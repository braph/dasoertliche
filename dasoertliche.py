#!/usr/bin/python3

import re
import json
import requests
from lxml import html

url = 'https://www.dasoertliche.de/'

def mk_regex(r):
    ''' make two spaces meaning arbitrary whitespace '''
    return r.replace('  ', '\\s*')

phoneData_regex = re.compile(mk_regex(
    'var  phoneData  =  (\\[.*\\])  ;'
))
contactData_regex = re.compile(mk_regex(
    'var  handlerData  = (\\[.*\\])  ;'
))

def load_var(regex, string):
    match = regex.search(string)
    if match:
        return json.loads(match[1].replace("'", '"'))

def search(forename, city, radius, maxpages=-1):
    params = dict(
        buab=71100198,
        zvo_ok=1,
        choose='true',
        buc='2249',
        page=1,
        context=1,
        action=43,
        form_name='search_nat_umg',
        zbuab=',,',
        fn=forename,
        ci=city,
        radius=radius
    )

    return collect_contactData(url, params, maxpages=maxpages)

contactData_headers = ['id', '1', '2', '3', 'website', 'city', '6', '7', '8', 'postal', 'street', 'street_nr', '12', 'vorwahl', 'name', '15']

def collect_contactData(url, params=None, maxpages=-1):
    if not params:
        params = dict()

    res = requests.get(url, params=params)
    tree = html.fromstring(res.text)

    try:
        phoneData, contactData = None, None

        for script in tree.xpath('//script'):
            if script.text:
                if not phoneData:
                    phoneData = load_var(phoneData_regex, script.text)

                if not contactData:
                    contactData = load_var(contactData_regex, script.text)

                if contactData and phoneData:
                    break

        if not phoneData:   raise Exception("no phoneData")
        if not contactData: raise Exception("no contactData")

        for i, row in enumerate(contactData):
            dict_obj = dict(zip(contactData_headers, row))
            dict_obj['number'] = ''

            for number_array in phoneData[i]:
                try:
                    dict_obj['number'] = number_array[0].replace('#', '')
                    break
                except:
                    pass

            yield dict_obj

    except Exception as e:
        print(e)

    maxpages -= 1
    if maxpages != 0:
        try:
            next_page = tree.xpath('//a[@title="zur nächsten Seite"]')[0].attrib['href']
            for r in collect_contactData(next_page, maxpages):
                yield r
        except:
            pass


def get_surname(full_name):
    return full_name.split(' ')[0]

# csv export
import csv

forenames = open('forenames')
csvfile = open('identities.csv', 'w', newline='')
fieldnames = ['forename', 'surname', 'street', 'street_nr', 'city', 'postal', 'number']
writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction='ignore')
writer.writeheader()

for forename in forenames:
    forename = forename.strip()
    result = search(forename, 'Leonberg', '50', maxpages=1)

    for r in result:
        r['surname'] = get_surname(r['name'])
        r['forename'] = forename
        writer.writerow(r)
