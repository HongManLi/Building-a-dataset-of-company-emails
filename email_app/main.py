import time

import pandas as pd

import api_funcs as api
import misc_variables as misc
import util as utils


df = pd.DataFrame(columns=misc.colnames)

query = ''' ENTER QUERY HERE '''

#Here we use the google API to find all instances of our query in NZ
for suburb in misc.nz_suburbs:
    temp_df = pd.DataFrame(columns=misc.colnames)
    temp_df = api.get_details(query + suburb,temp_df,'yes','none')
    df = df.append(temp_df,ignore_index=True)


#Dropping duplicates - as we are looped through every NZ suburb the results usually contain duplicate entries
df = df.drop_duplicates(subset=['Name','Address'])

#Creating two new columns for storing directors and email, then calls the NZBN api to fill these two columns
df['email'] = ''
df['directors'] = ''
for index, row in df.iterrows():
    time.sleep(3)
    temp = api.get_nzbn_details(row['Name'])
    df.loc[index, 'directors'], df.loc[index, 'email'] = temp.directors, temp.email

#Creates an empty column for storing domain, then fills it by scraping google
df['domain'] = ''
for index, row in df.iterrows():
    time.sleep(2)
    if row.email == '':
        temp = api.get_url(row.Name)
        df.loc[index, 'domain'] = temp.Domain

#Here we make the email if we couldn't get one from nzbn and we have the domain name as well as the directors name
df.email = df.apply(utils.make_email, axis=1)

#Finally, we verify the emails we've made/collected
df['email_status'] = ''
for index, row in df.iterrows():
    if pd.notnull(row.email):
        df.email_status.iloc[index] = api.check_email(row.email)


df.to_csv('email_contacts.csv', index=False)