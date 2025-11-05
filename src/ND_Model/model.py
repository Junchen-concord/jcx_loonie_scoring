# where to the path: f = open(jsonfilepath)  example:  jsonfilepath = "Data/creditbooksampleJSON.json"
# where to replace the path: clf_nb = joblib.load(modelfilepath)   example: modelfilepath = "saved/NegativeDB_model.pkl"
# where to replace the path: value_to_fillnull = pd.read_csv(datacleanfilepath)  example: datacleanfilepath = 'saved/dataclean_nb_fillna.csv'

import pandas as pd
import numpy as np
from datetime import date
import joblib
import json
from config import logger


def ndmodeling(
    jsonbody,
    modelfilepath="src/ND_Model/NegativeDB_model_V3_Testbed.pkl",
    datacleanfilepath="src/ND_Model/dataclean_nb_fillna.csv",
):
    logger.info("Starting ndmodeling()")
    stepname = "1 Loading Json"

    try:
        if type(jsonbody) is str:
            logger.info("Loading Json as string.")
            nb_dict = json.loads(jsonbody)
        else:
            logger.info("Json already in dict form")
            nb_dict = jsonbody
        if nb_dict["NDB"]["results"] == []:
            return '{"ModelScore":999,"NDBand":' + str(6) + "}"
            # fake model result as 1 to have it pass matrix threshold - the value need to be adusted to correct value
        jsonString = json.dumps(nb_dict["NDB"]["results"])
        df_ = pd.DataFrame(json.loads(jsonString))
        df_["accountnumber"] = nb_dict["NDB"]["accountnumber"]

        # Data Cleaning pre feature engineering
        stepname = "Data Cleaning pre feature engineering"
        df_["amount"] = df_["amount"].replace("", 0).astype(float)
        df_["requestDate"] = pd.to_datetime(df_.requestDate)
        df_["Yeardiff"] = df_.apply(lambda x: (date.today().year - x["requestDate"].date().year), axis=1)
        df_["Monthdiff"] = df_.apply(lambda x: (date.today().month - x["requestDate"].date().month), axis=1)
        df_["Weekdiff"] = df_.apply(
            lambda x: (date.today().isocalendar()[1] - x["requestDate"].isocalendar()[1]),
            axis=1,
        )
        df_["Daydiff"] = df_.apply(lambda x: (date.today() - x["requestDate"].date()).days, axis=1)
        df_["phone1"] = df_["phone1"].fillna("")
        df_["phone2"] = df_["phone2"].fillna("")

        # Feature engineering / feature generation
        stepname = "2 Feature Generation"
        frequency = df_.groupby("accountnumber").size().reset_index()
        frequency.columns = ["accountnumber", "frequency"]

        Loan = df_.groupby("accountnumber")["amount"].agg(["mean", "median", "std"])
        Loan.columns = ["avg_amountReq", "med_amountReq", "std_amountReq"]
        Loan = Loan.reset_index()

        tc_date = df_.groupby("accountnumber")[["Yeardiff", "Monthdiff", "Weekdiff", "Daydiff"]].agg(
            ["max", "min", "mean", "median"]
        )
        tc_date.columns = [
            "Yeardiff_max",
            "Yeardiff_min",
            "Yeardiff_mean",
            "Yeardiff_median",
            "Monthdiff_max",
            "Monthdiff_min",
            "Monthdiff_mean",
            "Monthdiff_median",
            "Weekdiff_max",
            "Weekdiff_min",
            "Weekdiff_mean",
            "Weekdiff_median",
            "Daydiff_max",
            "Daydiff_min",
            "Daydiff_mean",
            "Daydiff_median",
        ]
        tc_date = tc_date.reset_index()

        df_["phone1"] = (
            df_.phone1.astype(str).str.replace(r"[\(\)-]", "", regex=True).str.replace(r"\s", "", regex=True)
        )
        df_["phone2"] = (
            df_.phone2.astype(str).str.replace(r"[\(\)-]", "", regex=True).str.replace(r"\s", "", regex=True)
        )

        df_["cust_cell_number"] = df_.phone1.str.extract("(\d+)").astype(str)
        df_["cust_phone_number"] = df_.phone2.str.extract("(\d+)").astype(str)

        df_["true_phone"] = df_.apply(
            lambda x: 0 if ((len(x["cust_phone_number"]) != 10) & (len(x["cust_cell_number"]) != 10)) else 1,
            axis=1,
        )
        df_["cust_cell_number"] = df_.phone1.apply(lambda x: "nan" if len(x) != 10 else x)
        df_["cust_phone_number"] = df_.phone2.apply(lambda x: "nan" if len(x) != 10 else x)
        df_["phone_cell"] = df_.apply(
            lambda x: 0 if x["cust_phone_number"] == x["cust_cell_number"] else 1,
            axis=1,
        )

        phone = df_.groupby("accountnumber")["true_phone"].agg(["max", "sum", "count"])
        phone["correct_phone_rate"] = phone["sum"] / phone["count"]
        phone.columns = [
            "have_valid_phone",
            "times_valid_phone",
            "total_phone_enter",
            "correct_phone_rate",
        ]
        phone = phone.reset_index()

        phone_count = df_[(df_["true_phone"] == 1) & (df_["cust_cell_number"] != "nan")]
        phone_count = pd.DataFrame(
            phone_count.groupby("accountnumber")[["cust_phone_number", "cust_cell_number"]].apply(
                lambda x: pd.unique(x.values.ravel()).tolist()
            )
        )
        phone_count.columns = ["phone_list"]
        phone_count["num_unique_valid_phone"] = phone_count.phone_list.apply(
            lambda x: len(x) if "nan" not in x else len(x) - 1
        )
        phone_count = phone_count.reset_index()

        phone_features = pd.merge(
            phone,
            phone_count[["accountnumber", "num_unique_valid_phone"]],
            on="accountnumber",
            how="left",
        )
        phone_features["num_unique_valid_phone"] = phone_features["num_unique_valid_phone"].fillna(0)

        df_["refused"] = (df_["status"] == "refused").astype(int)
        df_["fraudster"] = (df_["status"] == "fraudster").astype(int)
        df_["duplicates"] = (df_["status"] == "duplicates").astype(int)
        df_["in-collection"] = (df_["status"] == "in-collection").astype(int)
        df_["loan-pay-in-full"] = (df_["status"] == "loan-pay-in-full").astype(int)

        ### Make sure you change it!!!
        curdate = date.today()
        curdate = df_["requestDate"].max().date()  # remove it before deployment
        df_["within_last_30day"] = df_.apply(lambda x: (curdate - x["requestDate"].date()).days <= 30, axis=1)

        loanspaidoff_count = df_.groupby("accountnumber").apply(lambda x: x["loan-pay-in-full"].sum()).reset_index()
        incollection_count = df_.groupby("accountnumber").apply(lambda x: x["in-collection"].sum()).reset_index()
        try:
            loanspaidoff_count_in30days = (
                df_.groupby("accountnumber")
                .apply(lambda x: x[x.within_last_30day == 1]["loan-pay-in-full"].sum())
                .reset_index()
            )
            incollection_count_in30days = (
                df_.groupby("accountnumber")
                .apply(lambda x: x[x.within_last_30day == 1]["in-collection"].sum())
                .reset_index()
            )
        except:
            loanspaidoff_count_in30days = pd.DataFrame(
                {
                    "accountnumber": [nb_dict["NDB"]["accountnumber"]],
                    "Loanspaidoff_count_in30days": [0],
                }
            )
            incollection_count_in30days = pd.DataFrame(
                {
                    "accountnumber": [nb_dict["NDB"]["accountnumber"]],
                    "Incollection_count_in30days": [0],
                }
            )
        loanspaidoff_rate = (
            df_.groupby("accountnumber")
            .apply(
                lambda x: x["loan-pay-in-full"].sum()
                / (x["loan-pay-in-full"].sum() + x["in-collection"].sum() + 0.00001)
            )
            .reset_index()
        )
        loanspaidoff_count.columns = ["accountnumber", "Loanspaidoff_count"]
        incollection_count.columns = ["accountnumber", "Incollection_count"]
        loanspaidoff_count_in30days.columns = [
            "accountnumber",
            "Loanspaidoff_count_in30days",
        ]
        incollection_count_in30days.columns = [
            "accountnumber",
            "Incollection_count_in30days",
        ]
        loanspaidoff_rate.columns = ["accountnumber", "Loanspaidoff_rate"]

        fraudster_app_count = df_.groupby("accountnumber").apply(lambda x: x["fraudster"].sum()).reset_index()
        fraudster_lender_count = (
            df_.groupby("accountnumber").apply(lambda x: x[x.fraudster == 1]["lender"].nunique()).reset_index()
        )
        if len(df_[df_.within_last_30day == True]) == 0:
            fraudster_app_count_in30days = pd.DataFrame(
                {
                    "accountnumber": [nb_dict["NDB"]["accountnumber"]],
                    "Fraudster_app_count_in30days": [0],
                }
            )
            fraudster_lender_count_in30days = pd.DataFrame(
                {
                    "accountnumber": [nb_dict["NDB"]["accountnumber"]],
                    "Fraudster_lender_count_in30days": [0],
                }
            )
        else:
            fraudster_app_count_in30days = (
                df_.groupby("accountnumber")
                .apply(lambda x: x[x.within_last_30day == 1]["fraudster"].sum())
                .reset_index()
            )
            fraudster_lender_count_in30days = (
                df_.groupby("accountnumber")
                .apply(lambda x: x[(x.within_last_30day == 1) & (x.fraudster == 1)]["lender"].nunique())
                .reset_index()
            )

        fraudster_app_count.columns = ["accountnumber", "Fraudster_app_count"]
        fraudster_lender_count.columns = ["accountnumber", "Fraudster_lender_count"]
        fraudster_app_count_in30days.columns = [
            "accountnumber",
            "Fraudster_app_count_in30days",
        ]
        fraudster_lender_count_in30days.columns = [
            "accountnumber",
            "Fraudster_lender_count_in30days",
        ]

        refused_count = df_.groupby("accountnumber").apply(lambda x: x["refused"].sum()).reset_index()
        refused_rate = (
            df_.groupby("accountnumber")
            .apply(
                lambda x: x["refused"].sum() / (x["refused"].count() - x["duplicates"].sum())
                if (x["refused"].count() - x["duplicates"].sum()) != 0
                else 0
            )
            .reset_index()
        )
        refused_count.columns = ["accountnumber", "Refused_count"]
        refused_rate.columns = ["accountnumber", "Refused_rate"]

        if len(df_[df_.within_last_30day == 1]) == 0:
            refused_count_within30day = pd.DataFrame(
                {
                    "accountnumber": [nb_dict["NDB"]["accountnumber"]],
                    "Refused_count_within30days": [0],
                }
            )
            refused_rate_within30day = pd.DataFrame(
                {
                    "accountnumber": [nb_dict["NDB"]["accountnumber"]],
                    "Refused_rate_within30days": [0],
                }
            )
        else:
            refused_count_within30day = (
                df_[df_.within_last_30day == True]
                .groupby("accountnumber")
                .apply(lambda row: row["refused"].sum())
                .reset_index()
            )
            refused_rate_within30day = (
                df_[df_.within_last_30day == True]
                .groupby("accountnumber")
                .apply(
                    lambda row: row["refused"].sum() / (row["refused"].count() - row["duplicates"].sum())
                    if (row["refused"].count() - row["duplicates"].sum()) != 0
                    else 0
                )
                .reset_index()
            )
        if len(df_[df_.within_last_30day == 0]) == 0:
            refused_count_before30day = pd.DataFrame(
                {
                    "accountnumber": [nb_dict["NDB"]["accountnumber"]],
                    "Refused_count_before30days": [0],
                }
            )
            refused_rate_before30day = pd.DataFrame(
                {
                    "accountnumber": [nb_dict["NDB"]["accountnumber"]],
                    "Refused_rate_before30days": [0],
                }
            )
        else:
            refused_count_before30day = (
                df_[df_.within_last_30day == False]
                .groupby("accountnumber")
                .apply(lambda row: row["refused"].sum())
                .reset_index()
            )
            refused_rate_before30day = (
                df_[df_.within_last_30day == False]
                .groupby("accountnumber")
                .apply(
                    lambda row: row["refused"].sum() / (row["refused"].count() - row["duplicates"].sum())
                    if (row["refused"].count() - row["duplicates"].sum()) != 0
                    else 0
                )
                .reset_index()
            )

        try:
            refused_count_within30day.columns = [
                "accountnumber",
                "Refused_count_within30days",
            ]
            refused_rate_within30day.columns = [
                "accountnumber",
                "Refused_rate_within30days",
            ]
        except:
            refused_count_within30day = pd.DataFrame(
                refused_count_before30day.values,
                columns=["accountnumber", "Refused_count_within30days"],
            )
            refused_rate_within30day = pd.DataFrame(
                refused_rate_before30day.values,
                columns=["accountnumber", "Refused_rate_within30days"],
            )
        try:
            refused_count_before30day.columns = [
                "accountnumber",
                "Refused_count_before30days",
            ]
            refused_rate_before30day.columns = [
                "accountnumber",
                "Refused_rate_before30days",
            ]
        except:
            refused_count_before30day = pd.DataFrame(
                refused_count_within30day.values,
                columns=["accountnumber", "Refused_count_before30days"],
            )
            refused_rate_before30day = pd.DataFrame(
                refused_rate_within30day.values,
                columns=["accountnumber", "Refused_rate_before30days"],
            )

        status_summary = loanspaidoff_count
        for subdf in [
            incollection_count,
            loanspaidoff_count_in30days,
            incollection_count_in30days,
            loanspaidoff_rate,
            fraudster_app_count,
            fraudster_lender_count,
            fraudster_app_count_in30days,
            fraudster_lender_count_in30days,
            refused_count,
            refused_rate,
            refused_count_within30day,
            refused_rate_within30day,
            refused_count_before30day,
            refused_rate_before30day,
        ]:
            status_summary = status_summary.merge(subdf, on="accountnumber", how="left")

        feature_df = frequency
        for d in [Loan, tc_date, phone_features, status_summary]:
            feature_df = pd.merge(feature_df, d, on="accountnumber", how="outer")

        # ND Data Cleaning post feature engineering
        stepname = "3 Data Cleaning Post Feature Gen"
        value_to_fillnull = pd.read_csv(datacleanfilepath)  # 'saved/dataclean_nb_fillna.csv'

        cols = [
            "avg_amountReq",
            "med_amountReq",
            "std_amountReq",
            "times_valid_phone",
            "total_phone_enter",
            "correct_phone_rate",
            "num_unique_valid_phone",
            "Yeardiff_max",
            "Yeardiff_min",
            "Yeardiff_mean",
            "Yeardiff_median",
            "Monthdiff_max",
            "Monthdiff_min",
            "Monthdiff_mean",
            "Monthdiff_median",
            "Weekdiff_max",
            "Weekdiff_min",
            "Weekdiff_mean",
            "Weekdiff_median",
            "Daydiff_max",
            "Daydiff_min",
            "Daydiff_mean",
            "Daydiff_median",
        ]
        feature_df[cols] = feature_df[cols].fillna(value_to_fillnull.loc[0, cols])

        # Model loading and scoring
        stepname = "4 Model Loading and Scoring"

        clf_nb = joblib.load(modelfilepath)  # example: datacleanfilepath = "saved/NegativeDB_model.pkl"

        features_nb = [
            "frequency",
            "avg_amountReq",
            "med_amountReq",
            "std_amountReq",
            "Yeardiff_max",
            "Yeardiff_min",
            "Yeardiff_mean",
            "Yeardiff_median",
            "Monthdiff_max",
            "Monthdiff_min",
            "Monthdiff_mean",
            "Monthdiff_median",
            "Weekdiff_max",
            "Weekdiff_min",
            "Weekdiff_mean",
            "Weekdiff_median",
            "Daydiff_max",
            "Daydiff_min",
            "Daydiff_median",
            "Daydiff_mean",
            "have_valid_phone",
            "times_valid_phone",
            "total_phone_enter",
            "correct_phone_rate",
            "num_unique_valid_phone",
            "Loanspaidoff_count",
            "Incollection_count",
            "Loanspaidoff_count_in30days",
            "Incollection_count_in30days",
            "Loanspaidoff_rate",
            "Fraudster_app_count",
            "Fraudster_lender_count",
            "Fraudster_app_count_in30days",
            "Fraudster_lender_count_in30days",
            "Refused_count",
            "Refused_rate",
            "Refused_count_within30days",
            "Refused_rate_within30days",
            "Refused_count_before30days",
            "Refused_rate_before30days",
        ]

        # Output 1: Prediction of FPD First Attempt
        feature_df["NDScore"] = 1000 - (clf_nb.predict_proba(feature_df[features_nb])[:, 1] * 1000).astype(int)
        # Output 2: Model Band
        feature_df["NDBand"] = np.where(
            feature_df["NDScore"] < 376,
            1,
            np.where(
                feature_df["NDScore"] < 580,
                2,
                np.where(
                    feature_df["NDScore"] < 688,
                    3,
                    np.where(feature_df["NDScore"] < 766, 4, 5),
                ),
            ),
        )

    except Exception as e:
        logger.info(f"There was an error in step {stepname} executing the IsGood_model.")
        logger.exception(e)
        try:
            result = {"AccountID": str(nb_dict["NDB"]["accountnumber"]), "ErrorInStep": stepname}
        except:
            result = {"AccountID": "Not Available", "ErrorInStep": stepname}
        finally:
            return result

    logger.info("Successfully executed ND model")
    return {"ModelScore": int(feature_df["NDScore"].values[0]), "NDBand": int(feature_df["NDBand"].values[0])}
