import time
import re
import requests
import json

import pandas as pd
from lxml import etree

import conf


def get_details(query, df, types='None', cont="yes", key='none'):
    ''' Collects data using the Google place search API

        params string query: this is the keyword we use for our search, ie. Mt Roskill Parks
        params pandas dataframe df: this is the dataframe that we are appending our results to
        params string types: type of establishment/place we are interested in, as defined here: "https://developers.google.com/places/supported_types"
        params string cont: this helps us decide whether there are more results in the next page,
        params string key: if there is a next page, this will be the next page token

        Returns a Dataframe containing the results of our search, the columns will be ['Name','Address','Latitude','Longitude','Rating','Number of user ratings']
        '''
    
    url='https://maps.googleapis.com/maps/api/place/textsearch/json'
    query = str(query) 
    query = query.lower().replace(' ltd','').replace(' limited','')
    
    if key=='none':
        params = {
        'query': query + ' New Zealand',
        'key' : conf.GOOGLE_API_KEY,
        'type' : types
        }
    else:
        params = {
        'pagetoken':key,
        'key' : conf.GOOGLE_API_KEY,
        'type' : types
        }

    
    time.sleep(4)
    response = requests.get(url,params=params).json()
    
    if response['status'] == 'ZERO_RESULTS':
        return pd.DataFrame(columns=['Name','Address','Latitude','Longitude','Rating','Number of user ratings'])
    
    if 'next_page_token' not in response.keys():
        cont="no"
    
    
    nameslist = []
    addresslist = []
    latlist = []
    lnglist = []
    ratings = []
    ratingnumbers = []
    
    if cont=="no":
        for i in response['results']:
            nameslist.append(i['name'])
            addresslist.append(i['formatted_address'])
            latlist.append(i['geometry']['location']['lat'])
            lnglist.append(i['geometry']['location']['lng'])
            ratings.append(i.get('rating', None))
            ratingnumbers.append(i.get('user_ratings_total', None))

        return df.append(pd.DataFrame(
            {'Name':nameslist,'Address':addresslist,'Latitude':latlist,'Longitude':lnglist,'Rating':ratings,'Number of user ratings':ratingnumbers}),ignore_index=True)
    
    elif cont=="yes":
        for i in response['results']:
            nameslist.append(i['name'])
            addresslist.append(i['formatted_address'])
            latlist.append(i['geometry']['location']['lat'])
            lnglist.append(i['geometry']['location']['lng'])
            ratings.append(i.get('rating', None))
            ratingnumbers.append(i.get('user_ratings_total', None))

        return get_details(query,
                           df.append(pd.DataFrame({'Name':nameslist,'Address':addresslist,'Latitude':latlist,'Longitude':lnglist
                                                        ,'Rating':ratings,'Number of user ratings':ratingnumbers}),ignore_index=True),
                           types=types,
                           cont='yes',
                          key=response['next_page_token'])





headers_Get = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.106 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }


def google(q):
    '''Passes a query to google search, then parse the google results page'''
    s = requests.Session()
    q = '+'.join(q.replace('#', " ").replace('&'," ").replace('@'," ").split())
    url = 'https://www.google.co.nz/search?q=' + q + '&ie=utf-8&oe=utf-8'
    r = s.get(url, headers=headers_Get)
    return r.text


def return_domain(address):
    '''Given a web url, this function extracts the domain name'''
    if address is None:
        return None
    
    if address[-1] == '/':
        address = address[:-1]
    
    if re.search(r'(\w+.co.nz)',address):
        return re.search(r'(\w+.co.nz)',address).group(1)
    elif re.search(r'(\w+.com.au)',address):
        return re.search(r'(\w+.com.au)',address).group(1)
    elif re.search(r'(\w+.com)',address):
        return re.search(r'(\w+.com)',address).group(1)
    elif re.search(r'(\w+.net.nz)',address):
        return re.search(r'(\w+.net.nz)',address).group(1)   
    else:
        return None




def get_url(query):
    '''
        Takes a query as input, then using the google function and the return_domain function defined above, extracts the domain name of our interested query.
        An example, passing in 'Strike Electrical Auckland Electricians' to this function will return the domain 'strike.net.nz'
    '''
    time.sleep(2)
    
    query = str(query)
    html_results = google(query)
    
    tree = etree.HTML(html_results)
    
    try:
        url = tree.xpath('//a[@class="ab_button" and contains(@ping, "url?")]/@href')[0]
        return pd.Series({'Name': query, 'Domain': return_domain(url)})
    
    except:
        return pd.Series({'Name': query, 'Domain': None})
    


def check_email(email, key=conf.EMAIL_KEY):
    '''
        Call the whoisxml api to verify an email address.
        params string email: email we want to verify
        params string key: key to the api
        
        If the email is valid and not a catchall, this will return 'Valid',
        if the email is valid but is a catchall, this will return 'Valid catchall',
        else, the email is invalid and 'False' would be returned.
    '''
    print(email)
    url = 'https://emailverification.whoisxmlapi.com/api/v1?'
    params = {'apiKey':key,
             'emailAddress':email}
    response = requests.get(url,params=params)

    if response.status_code != 200:
        return False
    
    response = response.json()

    
    try:
        if response['smtpCheck'] == response['dnsCheck'] == response['catchAllCheck'] == 'true':
            return "Valid catchall"

        elif response['smtpCheck'] == response['dnsCheck'] == 'true':
            return "Valid"
        else:
            return "False"
    except:
        return False



def get_nzbn_details(company_name):
    '''Takes company name as input, calls the NZCOMPANIESOFFICE API, and returns name of director and email as output'''
    time.sleep(1)

    url = f'https://api.business.govt.nz/services/v4/nzbn/entities?search-term={company_name}&entity-status=registered'

    headers = {'Accept': 'application/json',
               'Authorization':conf.NZBN_KEY,
               'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.105 Safari/537.36'}
    r = requests.get(url, headers=headers)

    data = json.loads(r.text)
    
    directors=''
    email=''
    
    if 'items' not in data.keys():
        return pd.Series({'directors':directors, 'email':email})

    if len(data['items']) > 0:
        if 'nzbn' in data['items'][0].keys():
            nzbn = data['items'][0]['nzbn']

            #########################################################

            nzbn_url = f'https://api.business.govt.nz/services/v4/nzbn/entities/{nzbn}'
            time.sleep(1)
            r = requests.get(nzbn_url, headers=headers)
            data = json.loads(r.text)
            
            if 'emailAddresses' in data.keys():
                email = data.get('emailAddresses','')
                if isinstance(email, list) and len(email) > 0:
                    email = email[0]
                    if 'emailAddress' in email.keys():
                        email = email['emailAddress']
            
            directors = []
            
            if 'roles' in data.keys():
                staff = data['roles']
                if not(staff is None):
                
                    
                    for member in staff:
                        if member['roleType'] == 'Director' and member['roleStatus'] == 'ACTIVE':
                            firstname = member['rolePerson']['firstName']
                            lastname = member['rolePerson']['lastName']
                            director = firstname + " " + lastname
                            directors.append(director)

                    
                    
    if len(directors) > 0:
        directors = directors[0]
    else:
        directors = ''
    if isinstance(email, list):
        email = ''
    
    return pd.Series({'directors':directors, 'email':email})