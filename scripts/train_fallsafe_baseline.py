"""Reproducible research-only NHIS 2023 fall-history classification baseline."""
from pathlib import Path
import json
import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (average_precision_score, roc_auc_score, precision_score, recall_score, accuracy_score, confusion_matrix, brier_score_loss)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

ROOT = Path(__file__).resolve().parent
TARGET = 'BFALL12M_A'
FEATURES = ['AGEP_A','SEX_A','HEARINGDF_A','VISIONDF_A','ARTHEV_A','HYPEV_A']
CATEGORICAL = [x for x in FEATURES if x != 'AGEP_A']
VALID = {'SEX_A':[1,2], 'HEARINGDF_A':[1,2,3,4], 'VISIONDF_A':[1,2,3,4], 'ARTHEV_A':[1,2], 'HYPEV_A':[1,2]}

def main():
    df = pd.read_csv(ROOT / 'adult23.csv', usecols=FEATURES+[TARGET], low_memory=False)
    df = df.loc[df[TARGET].isin([1,2])].copy()
    y = (df[TARGET] == 1).astype(int)
    X = df[FEATURES].copy()
    for col, allowed in VALID.items():
        X[col] = X[col].where(X[col].isin(allowed), np.nan)
    X['AGEP_A'] = X['AGEP_A'].where(X['AGEP_A'].between(18,85), np.nan)
    X[CATEGORICAL] = X[CATEGORICAL].astype('object')
    X_train, X_test, y_train, y_test = train_test_split(X,y,test_size=0.2,stratify=y,random_state=42)
    def preprocessing():
        return ColumnTransformer([
            ('age', Pipeline([('impute',SimpleImputer(strategy='median')),('scale',StandardScaler())]), ['AGEP_A']),
            ('categorical', Pipeline([('impute',SimpleImputer(strategy='most_frequent')),('encode',OneHotEncoder(handle_unknown='ignore'))]), CATEGORICAL)
        ])
    models = {
        'Logistic Regression': LogisticRegression(max_iter=1500,random_state=42),
        'Random Forest': RandomForestClassifier(n_estimators=200,min_samples_leaf=10,random_state=42,n_jobs=-1)
    }
    results={}
    for name,estimator in models.items():
        pipeline=Pipeline([('prep',preprocessing()),('model',estimator)])
        pipeline.fit(X_train,y_train)
        scores=pipeline.predict_proba(X_test)[:,1]
        predictions=(scores>=0.5).astype(int)
        results[name]={
            'roc_auc':round(float(roc_auc_score(y_test,scores)),4),
            'pr_auc':round(float(average_precision_score(y_test,scores)),4),
            'precision_at_0_5':round(float(precision_score(y_test,predictions,zero_division=0)),4),
            'recall_at_0_5':round(float(recall_score(y_test,predictions)),4),
            'accuracy_at_0_5':round(float(accuracy_score(y_test,predictions)),4),
            'brier_score':round(float(brier_score_loss(y_test,scores)),4),
            'confusion_matrix_tn_fp_fn_tp':confusion_matrix(y_test,predictions).ravel().tolist()
        }
        joblib.dump(pipeline,ROOT / ('fallsafe_'+name.lower().replace(' ','_')+'.joblib'))
    report={'source':'CDC NHIS 2023 Sample Adult public-use CSV','target':TARGET,'target_meaning':'self-reported fall during past 12 months (1 yes; 2 no)','features':FEATURES,'eligible_records':int(len(y)),'fall_history_yes':int(y.sum()),'fall_history_no':int((1-y).sum()),'train_records':len(y_train),'test_records':len(y_test),'test_prevalence':round(float(y_test.mean()),4),'random_state':42,'limitations':'Retrospective cross-sectional fall history, not prospective inpatient fall prediction. Unweighted illustrative ML evaluation; NHIS survey weights/design not incorporated. 0.5 threshold not optimized; no clinical validation.','results':results}
    (ROOT/'fallsafe_model_report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))
if __name__=='__main__':main()
