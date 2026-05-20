from bs4 import BeautifulSoup # html parser
from nltk.stem.snowball import SnowballStemmer # word stemmer
from sklearn.base import BaseEstimator, TransformerMixin
import pandas as pd
from pathlib import Path
from datetime import datetime

class EmailProcessor(BaseEstimator, TransformerMixin): 
    '''
        Will clean and process each email given a Pandas Series of file paths.
        
        @returns: a Pandas DataFrame including the following:
            filename: str -- filename of the given file
            from: str -- domain of email sender
            to: str -- domain of email recipient
            return_path: str -- domain of the return email
            message_id: str -- domain of the 'Message-Id' header
            recieved: int -- number of entries in the 'Recieved' header
            deliver_to: int -- number of entries in the 'Deliver-To' header
            weekday: str -- day of week 
            day: str -- DD
            month: str -- MMM
            year: int -- YYYY
            timezone: str -- timezone of datetime
            subject: object -- array of words within the subject
            body: object -- array of words within the body
    '''

    TIMEZONE_OFFSETS = {
        # North America
        'EST': '-0500', 'EDT': '-0400',
        'CST': '-0600', 'CDT': '-0500',
        'MST': '-0700', 'MDT': '-0600',
        'PST': '-0800', 'PDT': '-0700',
        'AST': '-0400', 'ADT': '-0300',
        'HST': '-1000', 'HDT': '-0900',
        'AKST': '-0900', 'AKDT': '-0800',
        # Europe
        'GMT': '+0000', 'UTC': '+0000',
        'BST': '+0100',
        'CET': '+0100', 'CEST': '+0200',
        'EET': '+0200', 'EEST': '+0300',
        # Asia
        'MSK': '+0300',
        'IST': '+0530',
        'JST': '+0900', 'KST': '+0900',
        # Australia
        'AEST': '+1000', 'AEDT': '+1100',
        'ACST': '+0930', 'ACDT': '+1030',
        'AWST': '+0800',
    }

    def __init__(self): 
        self.stemmer = SnowballStemmer('english')

    def fit(self, X, y=None):
        return self
    
    def transform(self, X: pd.Series, y=None):
        return pd.DataFrame(X.apply(self._process).to_list())
    
    def _process(self, email_path: str):
        # process email
        # print("--- processing: ", email_path)
        filename = Path(email_path).name
        email = dict()
        with open(email_path, 'r', errors='ignore') as f:
            f
            email = self._extract_lines(f.readlines())

        email['headers'] = self._parse_headers(email)
        email['body'] = self._parse_body(email)
        email.update(self._extract_headers(email))
        email['filename'] = filename

        return email

    def _extract_lines(self, lines: str):
        data = {
            'headers': [],
            'body': []
        }

        idx = 0
        
        # determine if we have a from line, if so, we skip. 
        if lines[0][:4] == 'From':
            idx += 1
        
        # extract headers
        # the header and body section are split up by a single \n line.
        # once we reach that line, we can move onto the body section.
        while lines[idx] != '\n':
            data['headers'].append(lines[idx])
            idx += 1

        # body
        while idx < len(lines):
            data['body'].append(lines[idx])
            idx += 1

        return data

    def _parse_header_line(self, line: str):
        if len(line) == 0: return [], False
        # we will need to process a line character by character
        
        # check if line is continuation or new header (is tab or space present?)
        new_header = not (line[0] in {'\t', ' '})

        # single chars to skip over 
        single_char = {',', ';', '<', '>', '\t', '\n', '(', ')', '[', ']'}

        # url to keep track of 
        # we know we have a url when there is http present within the word
        http = ["h", "t", "t", "p"]
        http_idx = 0

        words = []
        curr = "" # current built string

        line += " " # this space ensures we catch the final word
        for c in line:

            # , ; < > 
            if c in single_char:
                continue 

            # USERNAME@<domain>
            if c == "@": # replace username, would be previous word
                curr = ""
                continue
            
            # URL
            if http_idx == 3:
                pass
            elif c == http[http_idx]:
                http_idx += 1
            else:
                http_idx = 0

            # seperate on space (split)
            if c == " ":
                
                if http_idx == 3: # meaning full http found.
                    words.append("URL")
                elif len(curr) > 0: # take care of empty words (double spaces)
                    words.append(curr)
                
                curr = ""
                escape = False
                http_idx = 0
                continue

            # add character if passes all these checks.
            curr += c
            
        return words, new_header

    def _parse_headers(self, data: dict):
        '''
        Will transform a data object's `headers` key into a dictionary containing each header and its
        entries, numbered by order of appearance.
        '''

        d = dict()

        # sometimes lines continue, this is seen typically by a tab
        # we can also tell by determining that there is no header line present; is there <header name>:?

        curr_header = ''
        curr_val = []
        for line in data['headers']:
            # list of words, is new header?
            l, new_header = self._parse_header_line(line)
            
            if new_header:
                # save previous values
                if d.get(curr_header):
                    d[curr_header].append( curr_val )
                else:
                    d[curr_header] = [ curr_val ]

                # rewrite with new values
                curr_header = l[0][:-1] # cut out `:`
                curr_val = l[1:]
            else: # continuation of the previous header
                curr_val += l

        # cleanup
        d.pop('')
        # save previous values
        if d.get(curr_header):
            d[curr_header].append( curr_val )
        else:
            d[curr_header] = [ curr_val ]

        return d
    
    def _parse_body_word(self, word: str):

        # allowed non alnum characters. `@` is included for email checks
        allowed = {' ', '@'} 

        # url to keep track of 
        # we know we have a url when there is http present within the word
        http = ["h", "t", "t", "p"]
        http_idx = 0

        words = []
        curr = ""

        include_period = False # only true if we're currently on an email word.

        word += " " # ensure will run one last time
        for c in word:

            # skip non alphanumeric characters
            if not (c in allowed or c.isalnum()):
                if not (include_period and c == '.'):
                    continue

            # USERNAME@<domain>
            if c == "@": # replace username
                curr = ""
                include_period = True
                continue
            
            # URL
            if http_idx == 3:
                pass
            elif c == http[http_idx]:
                http_idx += 1
            else:
                http_idx = 0

            # seperate
            if c == " ":
                
                if http_idx == 3: # meaning full http found.
                    words.append("URL")
                elif len(curr) > 0: # take care of empty words (double spaces)
                    w = self.stemmer.stem(curr)
                    
                    # alter numbers
                    if w.isnumeric(): w = 'NUMBER'

                    words.append(w)
                
                curr = ""
                http_idx = 0
                continue

            # add character if passes all these checks. (upper case)
            curr += c
            
        return words

    def _parse_body(self, data: dict):

        # first we will combine all lines, then remove all html content. 
        # we must combine all lines within the body to ensure that there is no multi-line html cut off.
        content = ' '.join( data['body'])
        soup = BeautifulSoup(content, 'html.parser')

        text = soup.get_text(separator=' ', strip=True) # converts to one line
        body = text.split(' ') # list of words

        words = []
        for w in body:
            words += self._parse_body_word(w)

        return words
    
    def _extract_headers(self, data: dict):
        d = dict()

        headers = data.pop('headers')
        # only the mandatory lines we can expect, even in spam they are missing sometimes
        # that is why we will use the try.. except blocks for those scenarios.

        # From
        frm = headers['From']
        if frm:
            try:
                frm = frm[0][-1].lower() # there may be a name, the last element will be an email
            except Exception as e:
                frm = None
        d['from'] = frm
        
        # Date:
        # date has two possible formats: either
        # 1. DD, Mon YYYY HH:MM:SS TZ
        # 2. weekday DD Mon YYYY HH:MM:SS TZ
        # by looking ate date[0], we can check if it is numeric (is it format 2?)

        date = headers['Date'][0]
        if date[0].isnumeric():
            d['day'], d['month'], d['year'] = date[0], date[1].lower(), date[2]
            d['hour'] = date[3].split(':')[0] # will result in only the hour portion
            d['timezone'] = date[-1] # always last
            
            timezone = date[-1] # always last
            if not timezone[1:].isnumeric(): # grab numerical offest if abbreviated or wrong.
                d['timezone'] = self.TIMEZONE_OFFSETS.get(timezone)

            # we will find day of week manually
            month_num = datetime.strptime(d['month'], "%b").month # turn month into numeric
            # get numeric weekday, then turn into abreviated name
            weekday = datetime(int(d['year']), month_num, int(d['day'])).strftime('%a')
            d['weekday'] = weekday.lower()

        else:
            d['weekday'], d['day'], d['month'], d['year'] = date[0].lower(), date[1], date[2].lower(), date[3]
            d['hour'] = date[4].split(':')[0] # will result in only the hour portion
            d['timezone'] = date[-1] # always last

            timezone = date[-1] # always last
            if not timezone[1:].isnumeric(): # grab numerical offest if abbreviated or wrong.
                d['timezone'] = self.TIMEZONE_OFFSETS.get(timezone)
    
        # To
        # it is possible for To to contain an empty value.
        to = headers.get('To')
        if to:
            try:
                to = to[0][-1].lower() # the last element is guaranteed to be an email.
            except Exception as e:
                to = None
        d['to'] = to

        # Subject
        subject = headers.get('Subject')
        if subject:
            try:
                words = subject[0]
                subject = []
                for word in words:
                    subject += self._parse_body_word(word)
            except Exception as e:
                subject = None
        d['subject'] = subject

        # Return-Path
        return_path = headers.get('Return-Path')
        if return_path:
            try:
                return_path = return_path[0][-1].lower() # extract email 
            except:
                return_path = None
        d['return_path'] = return_path

        # Recieved
        received = headers.get('Received')
        if received:
            received = len(received)
        else: 
            received = 0
        d['received'] = received

        # Delivered-To
        delivered_to = headers.get('Delivered-To')
        if delivered_to:
            delivered_to = len(delivered_to)
        else:
            delivered_to = 0
        d['delivered_to'] = delivered_to

        # Message-Id
        message_id = headers.get('Message-Id')
        if message_id:
            try:
                message_id = message_id[0][-1].lower() # extract email
            except Exception as e:
                message_id = None
        d['message_id'] = message_id

        return d
    

def extract_filepaths( *dirs ) -> pd.Series:
    '''Will extract all file paths within any given number of directories.'''
    file_paths = []

    for dir in dirs:
        directory = Path(dir)
        for file in directory.iterdir():
            if file.is_file():
                file_paths.append(str(file))

    return pd.Series(file_paths)