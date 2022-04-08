# metadata-quality-toolkit

This repository contains the Xtract toolkit to automatically evaluate a collection of metadata attributes!

Input: 
A folder containing one type of metadata extractor file. For example, it could be a folder full of `tabular` OR `keyword` metadata formatted as json.  


Here we mine the following metrics: 
- **Completeness:** out of the maximum possible fields in a metadata document, what percentage of them are full? The system automatically defines the 'maximum possible' as the total number of fields in the document with the highest number of fields. 
- **Entropy:** TODO
- **Yield:** TODO

from quality_metric_tool import Summary

path = {path to folder of metadata}

summary = Summary()

all_scores = summary.get_quality_scores(path)
