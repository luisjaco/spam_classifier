# Email Spam Classification Pipeline
> There are no smart and quirky names for this project, let's get straight to the point.

## Background
Spam has existed for as long as emails have. Where there are email, there is spam. Pesky spam 
will always attempt to take our attention, our time, and even our money if we aren't paying enough
attention. Thus, the need for spam classification is always present; don't figure out if an email is
spam on your own, let an algorithm do it for you.

> Data was gathered from the **Apache SpamAssassin** Public Mail Corpus directory. You can find the
directory [here](https://spamassassin.apache.org/old/publiccorpus/).

## Overview
This repository features multiple notebooks, separating our workflow into a set of steps:
1. **Extract, transform, load**; [data_cleaning.ipynb](data_cleaning.ipynb).
2. **Exploratory data analysis**; [exploratory_data_analysis.ipynb](exploratory_data_analysis.ipynb).
3. **Feature selection & preprocessing**; [preprocessing.ipynb](preprocessing.ipynb).
4. **Model selection & optimization**; [model.ipynb](model.ipynb).

These four notebooks take an email from a raw `.txt` file to a classification in a simple end-to-end
pipeline. After all steps are taken, we result in a **Random Forest Classifier**, achieving an 
accuracy score of **~.96** and an F1 score of **~.96** on validation data.

> If you want to run any of these notebooks, ensure you uncomment the top cell. This top cell will 
install all requirements for the project

```python
# use this cell to install all requirements for this project.
!pip install -r requirements.txt
```

## Extract, Transform, Load
Before starting, we unpacked the email files using the [extract.py](/helpers/extract.py) helper 
script. Our files consist of *spam* and *ham* (ham being a real email). Some *ham* is labeled as
*hard ham*, meaning there is HTML or oddities within the email present.

After, we then had to transform a raw-email `.txt` file into a record within a `DataFrame` to 
prepare for preprocessing. With domain-specific research and studying of patterns within our data, 
we can determine how to implement a **custom class** aimed to process and email into a 
`DataFrame`. Within [data_cleaning.ipynb](data_cleaning.ipynb), we step-by-step discuss and 
implement the process of cleaning an email, which is then completed into an `EmailProcessor` class
seen in [email_processor.py](/helpers/email_processor.py). Given an input of a *filepath* string(s), we
take the following steps, per email file:
1. Extract file content.
2. Read all lines, separating on whether a line is a *header* or a *body* line.
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
feature engineering, we test some engineered features, like path length (the sum of `received` and 
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
| received | int | Number of entries in the 'Received' header | ✅ | |
| deliver_to | int | Number of entries in the 'Delivered-To' header | ✅ | |
| weekday | str | Day of week (Mon, Tue, Wed, etc.) | ✅ | |
| day | str | DD | ✅ | |
| month | str | MMM | ✅ | |
| year | int | YYYY | ❌ | Irrelevant due to nature of problem |
| timezone | str | Timezone of datetime, in UTC offset format | ❌ | Selection bias |
| subject | object | Array of words within the subject, stemmed | ✅ | |
| body | object | Array of words within the body, stemmed | ✅ | |

## Feature Selection & Preprocessing
Once a set of informative features had been determined, we can begin preprocessing and feature 
engineering to achieve a performative model. After preprocessing the selected features, we are left
with the following processed features, ready for training:

| Name | Null Response | Transformation | Notes |
|---|---|---|---|
| received | 0 | Standardization | - |
| delivered_to | 0 | Standardization | - |
| path_length | - | Standardization | Derived from the equation: *path_length = received + delivered_to* |
| day_sin | - | Cyclical Encoding | Derived from *day* |
| day_cos | - | Cyclical Encoding | Derived from *day* |
| hour_sin | - | Cyclical Encoding | Derived from *hour* |
| hour_cos | - | Cyclical Encoding | Derived from *hour* |
| weekday_sin | Most frequent | Cyclical Encoding | Derived from *weekday* |
| weekday_cos | Most frequent | Cyclical Encoding | Derived from *weekday* |
| body features | - | TF-IDF Vectorization | Turned into a *sparse matrix* |
| subject features | - | TF-IDF Vectorization | Turned into a *sparse matrix* |

Numerical features were imputed with zero values. Features like **day** and **hour** were encoded 
cyclically to ensure that the cyclical nature of days and hours are accounted for *(the hour 00:00 
is equally as close to the hour 23:00 as 01:00)*. 

<p align="center">
  <img src="/resources/img/cyclical_encoding.png" width="80%">
  <br>
  <em>Cyclically encoded variables visualization.</em>
</p>

For **body** and **subject**, using `TfidfVectorizer` from `sklearn`, we are able to turn these 
features into sparse matrices. These sparse matrices expand our total number of features, giving 
new features for each of the most common words found during training. Each feature contains a 
normalized value, indicating the frequency of the word within an email.

```python
-------- example record frequencies --------
NUMBER    0.266248
URL       0.325673
a         0.065723
about     0.000000
ad        0.000000
            ...   
would     0.327969
wrote     0.071305
year      0.000000
you       0.000000
your      0.000000
```

## Model Selection & Optimization
Finally, with a processed set of information-rich features, we train a set of models in
[model.ipynb](model.ipynb). We tested our dataset under **four** different types of models using 
*cross-validation*: Logistic Regression, Stochastic Gradient Descent, Support Vector Machine, 
and Random Forest. Seeking a balance between **precision** and **recall**, we compared their mean
*F1 score* across five testing folds.

| Model | F1 Mean |
|---|---|
| Logistic Regression | 0.9453 |
| SGD Classifier | 0.9432 |
| SVM | 0.9528 |
| Random Forest | 0.9612 |

After model selection, we result with Random Forest being the most optimal model to continue
development. Using `RandomizedSearchCV`, the Random Forest model can be fine-tuned to optimize its
*F1 score*. 

Evaluating the optimized Random Forest model with our validation set, we end up with an *F1 score*
of **~.96**. The optimized model results with the following metric scores as well:

| Metric | Score |
|---|---|
| Accuracy | 0.9639 |
| Precision | 0.9422 |
| Recall | 0.9775 |
| F1 | 0.9596 |
| ROC AUC | 0.9956 |

<p align="center">
  <img src="/resources/img/roc_auc.png" width="60%">
  <br>
  <em>Random Forest Classifier ROC curve.</em>
</p>

## Conclusion
Our model generalizes very well against new data, it is very accurate (**~.96**), therefore it can
predict whether an email is spam or ham with great confidence. The feature transformation pipeline
can be accessed using `cloudpickle` on [feature_pipeline.pkl](objects/feature_pipeline.pkl). The 
model pipeline can be imported similarly on the file [rf_classifier.pkl](objects/rf_classifier.pkl).
This project is a great step towards concepts like **model evaluation**, **feature processing**, 
and **natural language processing**. 


### License
[MIT](https://choosealicense.com/licenses/mit/)
