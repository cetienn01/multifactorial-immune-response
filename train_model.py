#!/usr/bin/env python

################################################################################
# SETUP
################################################################################
# Load required modules
import sys, os, argparse, logging, pandas as pd, numpy as np, json
from sklearn.model_selection import *

# Load our modules
from models import MODEL_NAMES, init_model, RF, EN, FEATURE_CLASSES
from metrics import compute_metrics, RMSE, MAE, MSE
from i_o import getLogger

# Parse command-line arguments
parser = argparse.ArgumentParser()
parser.add_argument('-ff', '--feature_file', type=str, required=True)
parser.add_argument('-fcf', '--feature_class_file', type=str, required=True)
parser.add_argument('-of', '--outcome_file', type=str, required=True)
parser.add_argument('-op', '--output_prefix', type=str, required=True)
parser.add_argument('-m', '--model', type=str, required=True, choices=MODEL_NAMES)
parser.add_argument('-mi', '--max_iter', type=int, required=False,
    default=1000000,
    help='ElasticNet only. Default is parameter used for the paper submission.')
parser.add_argument('-t', '--tol', type=float, required=False,
    default=1e-7,
    help='ElasticNet only. Default is parameter used for the paper submission.')
parser.add_argument('-v', '--verbosity', type=int, required=False, default=logging.INFO)
parser.add_argument('-nj', '--n_jobs', type=int, default=1, required=False)
parser.add_argument('-efc', '--excluded_feature_classes', type=str, required=False,
    nargs='*', default=[], choices=FEATURE_CLASSES)
parser.add_argument('-rs', '--random_seed', type=int, default=12345, required=False)
args = parser.parse_args(sys.argv[1:])

# Set up logger
logger = getLogger(args.verbosity)

# Load the input data
X = pd.read_csv(args.feature_file, index_col=0, sep='\t')
y = pd.read_csv(args.outcome_file, index_col=0, sep='\t')
feature_classes = pd.read_csv(args.feature_class_file, index_col=0, sep='\t')

# Align the features and outcomes
patients = X.index
X = X.reindex(index = patients)
y = y.reindex(index = patients)
outcome_name = y.columns[0]

# Create some data structures to hold our output
json_output = dict(patients=list(map(float, patients)), params=vars(args))

################################################################################
# TRAIN A MODEL ON ALL THE DATA
################################################################################
# Choose which feature classes to use in training;
# to use all feature classes set
#     selected_feature_classes = ['Clinical','Tumor','Blood']
selected_feature_classes = set(map(str.capitalize, set(FEATURE_CLASSES) - set(args.excluded_feature_classes)))
training_cols = feature_classes.loc[feature_classes['Class'].isin(selected_feature_classes)].index.tolist()
json_output['training_features'] = training_cols

# Set up nested validation for parameter selection and eventual evaluation
# Define parameter selection protocol
pipeline, gscv = init_model(args.model, args.n_jobs, args.random_seed, args.max_iter, args.tol)

# Produce held-out predictions for parameter-selected model
# using outer loop of CV
logger.info('* Performing LOO cross-validation...')
outer_cv = LeaveOneOut()
preds = pd.Series(cross_val_predict(estimator = gscv,
                                   X=X.loc[:,training_cols],
                                    y=y[outcome_name], cv=outer_cv,
                                    n_jobs = args.n_jobs,
                                    verbose=61 if args.verbosity > 0 else 0),
                 index = patients)

# Visualize and asses held-out predictions
# 1) Subset predictions and ground truth to relevant indices
sub_y = y.loc[patients][outcome_name].values
sub_preds = preds.loc[patients].values
metric_vals, var_explained = compute_metrics(sub_y, sub_preds)
rmses = metric_vals[RMSE]
mses = metric_vals[MSE]
maes = metric_vals[MAE]

# 2) Compare held-out RMSE to baseline RMSE obtained by predicting mean
logger.info('[Held-out RMSE, Baseline RMSE]: {}'.format([rmses['held-out'], rmses['baseline']]))
logger.info('[Held-out MSE, Baseline MSE]: {}'.format([mses['held-out'], mses['baseline']]))
logger.info('[Held-out MAE, Baseline MAE]: {}'.format([maes['held-out'], maes['baseline']]))
logger.info('Variance explained: {}'.format(var_explained))

# 3) Record the data into our plots dictionary
json_output.update({
    "preds": sub_preds.tolist(),
    "true": sub_y.tolist(),
    "variance_explained": var_explained,
    "rmse": rmses,
    "mse": mses,
    "mae": maes
})

################################################################################
# EVALUATE FEATURE IMPORTANCE
################################################################################
# Train each model on full dataset
logger.info('* Training model on all the data...')
pipeline.named_steps['estimator'].set_params(verbose=1 if args.verbosity else 0)
model = pipeline.fit(X.loc[:,training_cols], y[outcome_name])

# Examine variable importance or coefficients in each model.
# Weight raw variable coefficients by associated variable standard deviations;
# this places all variables on the same scale.
if args.model == RF:
    variable_scores = model.named_steps['estimator'].feature_importances_
elif args.model == EN:
    variable_scores = model.named_steps['estimator'].coef_ * X.loc[:,training_cols].fillna(X.loc[:,training_cols].median()).std()
else:
    raise NotImplementedError('Model "%s" not implemented.' % args.model)
variable_scores = pd.Series(variable_scores, index = X.loc[:, training_cols].columns, name='Score')

# Associate feature classes with scores
variable_scores = pd.concat([variable_scores, feature_classes], axis = 1)

# Sort scores by importance magnitude
variable_scores = variable_scores.reindex(variable_scores['Score'].abs().sort_values(ascending=False).index)

# Output a pretty summary of feature importances
var_importance_tbl = variable_scores.to_string()
rows = var_importance_tbl.split('\n')
logger.info('-' * len(rows[0]))
logger.info('RandomForest feature importances' if args.model == RF else 'ElasticNet coefficients')
logger.info('-' * len(rows[0]))
for row in rows:
    logger.info(row)
logger.info('')

################################################################################
# OUTPUT TO FILE
################################################################################
# Output plot data to JSON
with open(args.output_prefix + '-results.json', 'w') as OUT:
    json.dump( json_output, OUT )

# Output results summary to TSV
variable_scores.to_csv(args.output_prefix + '-coefficients.tsv', sep='\t', index=True)
