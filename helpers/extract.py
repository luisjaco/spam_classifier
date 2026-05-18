'''
This file will unzip all of the .tar.bz2 files found within the ./data dictionary.
Errors unchecked, will give error if script cannot read data or create new dictionaries.
'''
import os
import tarfile

'''
easy_ham: 2500 non-spam messages.  These are typically quite easy to
differentiate from spam, since they frequently do not contain any spammish
signatures (like HTML etc). -- unused

easy_ham_2: 1400 non-spam messages.  A more recent addition to the set.
'''
print('--------------------extracting easy_ham_2--------------------')
with tarfile.open('./data/20030228_easy_ham_2.tar.bz2', 'r:bz2') as f:
    f.list(verbose=True)
    f.extractall('./data')
    os.remove('./data/easy_ham_2/cmds') # remove unecessary file

#

''' 
hard_ham: 250 non-spam messages which are closer in many respects to
typical spam: use of HTML, unusual HTML markup, coloured text,
"spammish-sounding" phrases etc.
'''
print('--------------------extracting hard_ham--------------------')
with tarfile.open('./data/20030228_hard_ham.tar.bz2', 'r:bz2') as f:
    f.list(verbose=True)
    f.extractall('./data')
    os.remove('./data/hard_ham/cmds') # remove unecessary file

#

'''
spam: 500 spam messages, all received from non-spam-trap sources. -- unused.

spam_2: 1397 spam messages.  Again, more recent.
'''
print('--------------------extracting spam_2--------------------')
with tarfile.open('./data/20050311_spam_2.tar.bz2', 'r:bz2') as f:
    f.list(verbose=True)
    f.extractall('./data')
    os.remove('./data/spam_2/cmds') # remove unecessary file