'''
This file will unzip all of the .tar.bz2 files found within the ./data dictionary.
'''
import tarfile

print('--------------------extracting easy_ham_2--------------------')
with tarfile.open('./20030228_easy_ham_2.tar.bz2', 'r:bz2') as f:
    f.list(verbose=True)
    f.extractall()

print('--------------------extracting hard_ham--------------------')
with tarfile.open('./20030228_hard_ham.tar.bz2', 'r:bz2') as f:
    f.list(verbose=True)
    f.extractall()

print('--------------------extracting spam_2--------------------')
with tarfile.open('./20050311_spam_2.tar.bz2', 'r:bz2') as f:
    f.list(verbose=True)
    f.extractall()