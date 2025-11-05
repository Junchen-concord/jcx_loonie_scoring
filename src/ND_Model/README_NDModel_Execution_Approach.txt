jsonfilepath = "inputJSON for NegativeDBModelLP_v1.json"
modelfilepath = 'NegativeDB_model_v3_Testbed.pkl'
datacleanfilepath = 'dataclean_nb_fillna.csv'
%run -i model.py jsonfilepath modelfilepath datacleanfilepath

NDBand 1:   0 <= ['NDScore'] < 376
NDBand 2: 376 <= ['NDScore'] < 582
NDBand 3: 582 <= ['NDScore'] < 688
NDBand 4: 688 <= ['NDScore'] < 766
NDBand 5: 766 <= ['NDScore'] < 1000

Knock Out Rules for Scoring Matrix: knock out the customers in Band 1 who shows ['NDScore'] < 688.