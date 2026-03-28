import json 
import csv

prediction_file = "NA_Super49B_instruct_few_870.jsonl"

with open(prediction_file, 'r') as json_file:
    json_list = list(json_file)

total = 0


pairs = {}
number = 0
test_idx = set()
for json_str in json_list:
    result = json.loads(json_str)
    number += 1
    test_idx.add(result["idx"])
    if result["commit_id"] in pairs:
        pairs[result["commit_id"]]["ground_truth"].append(result["ground_truth"])
        pairs[result["commit_id"]]["idx"].append(result["idx"])
        pairs[result["commit_id"]]["prediction"].append(result["vuln"])
    else:
        pairs[result["commit_id"]] = {"ground_truth": [result["ground_truth"]], "idx": [result["idx"]], "prediction": [result["vuln"]] }




results = {"pc":0, "pv":0, "pb": 0, "pr":0}
#check pair
pair_count = 0
code_total = 0
for commit in pairs:
   idx_i = 0
   while idx_i+1 < len(pairs[commit]["ground_truth"]):
        try:
            pair_count += 1
            code_total += 2
            #   print()
            pair_1_label = pairs[commit]["ground_truth"][idx_i]
            pair_2_label = pairs[commit]["ground_truth"][idx_i+1]
            pair_1_predict = pairs[commit]["prediction"][idx_i]
            pair_2_predict = pairs[commit]["prediction"][idx_i+1]
            if pair_1_label == pair_1_predict and pair_2_label == pair_2_predict:
                results["pc"]+=1
            elif pair_1_predict == 1 and pair_2_predict == 1:
                results["pv"]+=1
            elif pair_1_predict == 0 and pair_2_predict == 0:
                results["pb"]+=1
            elif pair_1_predict == 0 and pair_2_predict == 1:
                results["pr"] +=1
        except Exception as e:
            print(pairs[commit]["idx"][idx_i])
            print(pairs[commit]["idx"][idx_i+1])
            print("NOT FOUND IN RESULT")
        
        idx_i += 2

divider = 0
for i in results:
   divider += results[i]
print("Pair: "+str(pair_count))
print("Codes: "+str(code_total))
for i in results:
   print(i)
   print((results[i]/divider)*100)

