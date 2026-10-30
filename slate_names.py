import unicodedata
ALIAS = {'bobby portis jr': 'bobby portis', 'nicolas claxton': 'nic claxton'}

def norm(s):
    s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode().lower().replace('.', '').replace("'", '').strip()
    return ALIAS.get(s, s)


