from bs4 import BeautifulSoup
from enum import Enum, auto

class ReplaceUrlType(Enum):
    KEEP_WEB = 1
    REPLACE = 2
    KEEP_ALL = 3


class EmailProcessorV1:
    '''The first working implementation of the email processor. Refer to `spam2.ipynb` for more.'''
    def __init__(self):
        return self
    
    def _extract_lines(self, lines: str):
        data = {
            'frm': [],
            'headers': [],
            'body': []
        }

        idx = 0
        
        # determine if we have a from line
        if ':' not in lines[0].split()[0]:
            data['frm'].append(lines[0])
            idx += 1
        
        # headers...
        # the header and body section are split up by a single \n line. Therefore, '' entry in our split
        while lines[idx] != '\n':
            data['headers'].append(lines[idx])
            idx += 1

        # body
        while idx < len(lines):
            data['body'].append(lines[idx])
            idx += 1

        return data
    
    def _filter_line_header(self, line: str):
        if len(line) == 0: return [], False
        # we will need to process a line character by character
        
        # check if line is continuation or new header (is tab or space present?)
        new_header = not (line[0] in {'\t', ' '})

        # single chars to skip over 
        single_char = {',', ';', '<', '>', '\t', '\n'}

        # url to keep track of 
        # we know we have a url when there is http present within the word
        http = ["h", "t", "t", "p"]
        http_idx = 0

        words = []
        curr = ""

        line += " " # ensure will run one last time
        for c in line:

            # , ; < > 
            if c in single_char:
                continue 

            # USERNAME@<domain>
            if c == "@": # replace username
                curr = "USERNAME@"
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
                    words.append(curr)
                
                curr = ""
                escape = False
                http_idx = 0
                continue

            # add character if passes all these checks.
            curr += c
            
        return words, new_header
    
    def _extract_headers(self, data: dict):
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
            l, new_header = self._filter_line_header(line)
            
            # process, if `:` present, it is a header title
            if new_header:
                # save previous values

                if d.get(curr_header):
                    d[curr_header].append( curr_val )
                else:
                    d[curr_header] = [ curr_val ]

                curr_header = l[0][:-1] # cut out `:`
                curr_val = l[1:]
            else: # means it is a continuation of the previous header
                curr_val += l

        # cleanup
        # save previous values
        if d.get(curr_header):
            d[curr_header].append( curr_val )
        else:
            d[curr_header] = [ curr_val ]

        return d
    
    def _extract_body(self, data: dict):
        # first we will combine all lines, then remove all html content. 
        # we must combine all lines within the body to ensure that there is no multi-line html cut off.

        content = ' '.join( data['body'])
        soup = BeautifulSoup(content, 'html.parser')
        text = soup.get_text(separator=' ', strip=True)

        # now, it will all be in one line...
        # allowed non alnum characters. `@` is included for email checks
        allowed = {' ', '@'} 

        # url to keep track of 
        # we know we have a url when there is http present within the word
        http = ["h", "t", "t", "p"]
        http_idx = 0

        words = []
        curr = ""

        text += " " # ensure will run one last time
        for c in text:

            # skip non alphanumeric characters
            if not (c in allowed or c.isalnum()):
                continue

            # USERNAME@<domain>
            if c == "@": # replace username
                curr = "USERNAME@"
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
                    words.append(curr.upper())
                
                curr = ""
                http_idx = 0
                continue

            # add character if passes all these checks. (upper case)
            curr += c
            
        return words
    
    def process_email(self,email_path: str):

        filename = email_path.split('/')[-1]
        lines = []

        with open(email_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()

        unprocessed_email = self._extract_lines(lines)

        processed_headers = self._extract_headers(unprocessed_email)
        processed_body = self._extract_body(unprocessed_email)

        processed_email = {
            'name': filename,
            'frm' : unprocessed_email['frm'],
            'headers' : processed_headers,
            'body': processed_body
        }

        return processed_email
    
class EmailProcessorV2:
    def __init__(self, 
                retain_headers: bool=True, 
                lower: bool=True,
                drop_punct: bool=True,
                replace_url: ReplaceUrlType=ReplaceUrlType.KEEP_WEB,
                replace_numbers: bool=True,
                stem: bool=True
           ):
        self.retain_headers = retain_headers
        self.lower = lower
        self.drop_punct = drop_punct
        self.replace_url = replace_url
        self.replace_numbers = replace_numbers
        self.stem = stem
        return self
    
    def process_email(self, path: str):
        # continue pipeline work
        return self