import re
import datetime

def parse_all(code):
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
    data['name'] = "%s %s %s" % (fname, mname, lname)

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
    data['name'] = "%s %s %s" % (fname, mname, lname)

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

# G610368 # Jannelle's

data_a = '@ANSI 636032030102DL00410205ZM02460027DLDCADCBDCDDBA02012025DCSSAJDCTADAM JACOBDBD02192021DBB02011983DBC1DAYDAUDAG33000 HEES STDAILIVONIADAJMIDAK481503774  DAQS 200 031 356 086DCFDCGDCHDAHDCKS200031356086198302012025DDANZMZMARev 01-21-2011ZMB01'
data_j = '@ANSI 636032030002DL00410226ZM02670027DLDCADCBDCDDBA08132023DCSGARVEYDCTJANELLE ELIZABETHDBD08102019DBB08131989DBC2DAYDAUDAG49320 CARLOS ST APT 139DAHDAICHESTERFIELDDAJMIDAK480513150  DAQG 610 368 210 633DCFDCGDCHDCKG610368210633198908132308ZMZMARev 07-01-2012ZMB01'
data_ohio = '@ANSI 636045080101DL00310377DLDCANONEDCBBDCDNONEDBA06182022DCSDARRELCARLSONOSCARLONGERNESTBERRYBRIANHADACPTONOLIVEMCDONALDVICKIECASTROJODYTORRRESDADONNIEBOWMANTONILEONARDBETTYGRAVESSODBD01192017DBB06181990DBC1DAYBRODAU071 inDAG645 WOODLAND SQUARE LOOP SEDAILACEYDAJWADAK985031045  DAQDARREPO101LQDCFDARREPO101LQ31170194F1154DCGUSADDETDDFTDDGTDCJ31170194F1154DDB02092016DAW140DDK1'
print(parse_all(data_ohio))
#regex [A-Z]{3}
# e = ['DAC', 'DCS', 'DAD', 'DAG', 'DAI', 'DAJ', 'DAK', 'DBB', 'DBA', 'DAQ', 'DBC', 'DAY', 'DAU', 'DBD','DCT', 'DCF', 'DAH','DCG','DCH','DCK','ZMZ']
# for tag in e:
#     data = data_a.split(tag)
#     if len(data) > 1:
#         data = data[1]
#     else:
#         data=''
#     print("[%s]: %s" % (tag,data))
# data = re.split('D[A-Z]{2}', data_a)
# print(data)
# data = re.split('D[A-Z]{2}', data_j)
# print(data)