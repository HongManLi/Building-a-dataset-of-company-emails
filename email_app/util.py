def make_email(row):
    if pd.notnull(row.email):
        return row.email
    if pd.isnull(row.directors):
        return 
    if pd.isnull(row.domain):
        return
    return row.directors.split()[0] + '@' + row.domain
