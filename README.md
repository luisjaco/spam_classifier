# Email Spam Classification Pipeline
> There are no smart and quirky names for this project, lets get straight to the point.

## Background
Spam has existed for as long as emails have. Where there are emails there exists spam. Pesky spam 
will always attempt to take our attention, our time, and even our money if we aren't paying enough
attention. Thus, the need for spam classification is always present; don't figure out if an email is
spam on your own, let an algorithm do it for you.

## Overview
This repository features multiple notebooks, seperating our workflow into a set of steps:
1. **Extract, transform, load**; [data_cleaning.ipynb](data_cleaning.ipynb)
2. **Exploratory data analysis**; [exploratory_data_analysis.ipynb](exploratory_data_analysis.ipynb)
3. **Feature selection & preprocessing**; [preprocessing.ipynb](preprocessing.ipynb)
4. **Model selection & optimization**; [model.ipynb](model.ipynb)

These four notebooks take an email from a raw `.txt` file to a classification in a simple end-to-end
pipeline.
> Data was gathered from the **Apache SpamAssassin** Public Mail Corpus directory. You can find the
directory [here](https://spamassassin.apache.org/old/publiccorpus/).

## Extract, transform, load
Before starting, we unpacked the email files using the [extract.py](/helpers/extract.py) helper 
script. Our files consist of *spam* and *ham* (ham being a real email). Some *ham* is labeled as
*hard ham*, meaning there is HTML or oddities within the email present.

After, we then had to transform a raw-email `.txt` file into a record within a `DataFrame` to 
prepare for preprocessing. With domain-specific research and studying of patterns within our data, 
we can make deduce how to implement a **custom class** aimed to process and email into a 
`DataFrame`. Within [data_cleaning.ipynb](data_cleaning.ipynb), we step-by-step discuss and 
implement the process of cleaning an email, which is then completed into an `EmailProcessor` class
seen in [email_processor.py](/helpers/email_processor.py). Given an input of a *filepath* string(s), we
take the following steps, per email file:
1. Extract file content.
2. Read all lines, seperating on whether a line is a *header* or a *body* line.
3. Process headers.
    a. Seperate header lines into *keys* (header names) and *values* (header contents). 
    b. Parse header *values* by performing the following:
        - Split all words into an array.
        - Strip all newlines, tabs, commas, chevrons, semicolons (`\t`, `\n`, `,`, `;`, `<`, `>`, `(`, `)`, `[`, `]`).
        - Replace all email usernames with `@<domain>`.
        - Replace all found urls with `URL`.
        - Transform all characters into lowercase.
4. Process body.
    a. Combine all lines, remove `HTML` content using `BeautifulSoup4` (`bs4`).
    b. Parse each word within the body by performing the following:
        - Split all words into entries within an array.
        - Remove word endings using `Natural Language Toolkit` (`nltk`).
        - Strip all newlines, tabs, and non-alphanumeric characters, allowing (` `) only.
        - Replace all email usernames with `@<domain>`.
        - Replace all found urls with `URL`.
        - Transform all characters into lowercase.
        - Replace numerical instances with `NUMBER`.
5. Extract valuable headers.
    a. Keep only the `From`, `To`, `Subject` (as array of words), and `Return path` headers.
    b. Split the `Date` header into *weekday*, *day*, *month*, *year*, *hour*, and *timezone*.
    c. Track the number of entries for path headers (`Received` and `Delivered-To`).
6. Combine into `DataFrame` records, containing valuable headers and parsed body.

Ultimately, we result with the `EmailProcessor` class, enabling pipeline-ready processing.
```python
from helpers.email_processor import EmailProcessor, extract_filepaths

extractor = EmailProcessor()

# extract filepaths using helper function.
ham_filepaths = extract_filepaths('./data/easy_ham_2', './data/hard_ham')
spam_filepaths = extract_filepaths('./data/spam_2')

# process emails into records within a DataFrame.
ham_df = extractor.fit_transform(ham_filepaths)
spam_df = extractor.fit_transform(spam_filepaths)
```

## Exploratory Data Analysis
Within [exploratory_data_analysis.ipynb](exploratory_data_analysis.ipynb), we use the processed 
emails to explore and compare different attributes and their relationship to *spam*. Using some
feature engineering, we test some engineered features, like path length (the sum of `recieved` and 
`delivered-to`), subject and body word counts, as well as tokenizing the subject and body in order 
to find word frequencies.

<p align="center">
  <img src="/resources/img/path_length_viz.png" width="80%">
  <br>
  <em>Distribution comparision between path length on ham and spam.</em>
</p>

<p align="center">
  <img src="/resources/img/weekday_viz.png" width="80%">
  <br>
  <em>Heatmap and barchart comparing weekday and spam.</em>
</p>

In conclusion, after creating visualizations and finding statistics for **all** available 
attributes, we made the following conclusions on which features to retain for preprocessing:

| Column | Dtype | Description | Retain | Note |
|---|---|---|---|---|
| filename | str | Filename of the given file | ✅ | Used as index |
| from | str | Domain of email sender | ❌ | Selection bias |
| to | str | Domain of email recipient | ❌ | Selection bias |
| return_path | str | Domain of the return email | ❌ | Selection bias |
| message_id | str | Domain of the 'Message-Id' header | ❌ | Selection bias |
| recieved | int | Number of entries in the 'Received' header | ✅ | |
| deliver_to | int | Number of entries in the 'Deliver-To' header | ✅ | |
| weekday | str | Day of week (Mon, Tue, Wed, etc.) | ✅ | |
| day | str | DD | ✅ | |
| month | str | MMM | ✅ | |
| year | int | YYYY | ❌ | Irrelevant due to nature of problem |
| timezone | str | Timezone of datetime, in UTC offset format | ❌ | Selection bias |
| subject | object | Array of words within the subject, stemmed | ✅ | |
| body | object | Array of words within the body, stemmed | ✅ | |

### License
[MIT](https://choosealicense.com/licenses/mit/)