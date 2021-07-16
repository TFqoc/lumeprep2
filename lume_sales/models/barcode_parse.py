import re
import datetime

def parse_code(code):
    if code.split('DAJ')[1][0:2] == 'MI':
        return parse_MI(code)
    dlstring = code
    e = ['DAC', 'DCS', 'DAD', 'DAG', 'DAI', 'DAJ', 'DAK', 'DBB', 'DBA', 'DAQ', 'DBC', 'DAY', 'DAU', 'DBD','DCF']
    expr = '|'.join(e)
    dlstring = dlstring.replace('0010','') # To clear out the newline representation for mac/linux machines
    dlstring = re.split(expr, dlstring)
    dlstring = [line.strip() for line in dlstring]

    for i, dat in enumerate(dlstring):
        print("[%s]: " % i + dat)

    data = {}
    fname = dlstring[3].capitalize()
    lname = dlstring[2].capitalize()
    mname = dlstring[4].capitalize()
    data['full_name'] = " ".join([fname, mname, lname])
    data['first_name'] = fname
    data['middle_name'] = mname
    data['last_name'] = lname

    words = dlstring[10].split(' ')
    street = ""
    for w in words:
        street = " ".join([street,w.capitalize()])
    data['street'] = street[1:]

    words = dlstring[11].split(' ')
    city = ""
    for w in words:
        city = " ".join([city,w.capitalize()])
    data['city'] = city[1:]

    data['state_id'] = dlstring[12]

    data['zip'] = dlstring[13][:5] + '-' + dlstring[13][5:]

    dbb = dlstring[6]
    month = int(dbb[:2])
    day = int(dbb[2:4])
    year = int(dbb[4:])
    data['date_of_birth'] = datetime.date(year, month, day)

    dlx = dlstring[1]
    month = int(dlx[:2])
    day = int(dlx[2:4])
    year = int(dlx[4:])
    data['drivers_license_expiration'] = datetime.date(year,month,day)

    data['drivers_license_number'] = dlstring[14]

    return data

def parse_MI(code):
    print("Parse MI")
    dlstring = code
    e = ['DBA','DCS','DBD','DBB','DBC','DAY','DAU','DAG','DAH','DAI','DAJ','DAK','DAQ','DCF','DCT']
    expr = '|'.join(e)
    dlstring = dlstring.replace('0010','') # To clear out the newline representation for mac/linux machines
    dlstring = dlstring.replace('DAH','')
    dlstring = re.split(expr, dlstring)
    dlstring = [line.strip() for line in dlstring]

    for i, dat in enumerate(dlstring):
        print("[%s]: " % i + dat)

    data = {}
    fname, mname = dlstring[3].split(' ')
    fname = fname.capitalize()
    mname = mname.capitalize()
    lname = dlstring[2].capitalize()
    data['full_name'] = " ".join([fname, mname, lname])
    data['first_name'] = fname
    data['middle_name'] = mname
    data['last_name'] = lname

    words = dlstring[9].split(' ')
    street = ""
    for w in words:
        street = " ".join([street,w.capitalize()])
    data['street'] = street[1:]

    words = dlstring[10].split(' ')
    city = ""
    for w in words:
        city = " ".join([city,w.capitalize()])
    data['city'] = city[1:]

    data['state_id'] = dlstring[11]

    data['zip'] = dlstring[12][:5] + '-' + dlstring[12][5:]

    dbb = dlstring[5]
    month = int(dbb[:2])
    day = int(dbb[2:4])
    year = int(dbb[4:])
    data['date_of_birth'] = datetime.date(year, month, day)

    dlx = dlstring[1]
    month = int(dlx[:2])
    day = int(dlx[2:4])
    year = int(dlx[4:])
    data['drivers_license_expiration'] = datetime.date(year,month,day)

    data['drivers_license_number'] = ''.join(dlstring[13].split())
    return data