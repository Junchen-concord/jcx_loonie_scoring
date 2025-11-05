jsonfilepath = "inputJSON for PlaidUDW_v1.json"
modelfilepath = "ibv_model_clf_python397.pkl"
%run -i model.py jsonfilepath modelfilepath

IBVBand 1: 0 <= ['IBVScore'] < 547
IBVBand 2: 547 <= ['IBVScore'] < 719
IBVBand 3: 719 <= ['IBVScore'] < 820
IBVBand 4: 820 <= ['IBVScore'] < 1000



# Output of ND Model is combined with the Flinks data. And this will be the input of Plaid Model and IsGood Model