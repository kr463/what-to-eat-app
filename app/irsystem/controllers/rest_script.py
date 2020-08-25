import json  # from nltk.corpus import stopwords
import boto3
import os
from app.irsystem.controllers.check_production import filepath
import os
import boto3

# aws_id = os.environ.get('AWS_ACCESS_KEY_ID')
# aws_key = os.environ.get('AWS_SECRET_ACCESS_KEY')

# BUCKET = 'what-to-eat-project'

# client = boto3.client('s3',
#                       aws_access_key_id=aws_id,
#                       aws_secret_access_key=aws_key
#                       )

# result = client.get_object(Bucket=BUCKET, Key='inverted_idx_300_business.json')
# inverted_idx = json.loads(result["Body"].read().decode())

# result = client.get_object(Bucket=BUCKET, Key = 'rate_of_word_occurences_all.json')
# word_occ_dict = json.loads(result["Body"].read().decode())

# print(inverted_idx['good'])

with open((filepath() + 'business_montreal.json'), 'r') as inp:
    business_dict = json.load(inp)

for bus_id in business_dict:
    business_dict[bus_id]['stars'] = round(business_dict[bus_id]['stars'], 2)

with open((filepath() + 'filtered_idx.json'), 'r') as inp:
    inverted_idx = json.load(inp)

with open((filepath() + 'filtered_idx_pairs.json'), 'r') as inp:
    inverted_idx_pairs = json.load(inp)

with open((filepath() + 'pos_rev_dict.json'), 'r') as inp:
    review_dict = json.load(inp)

with open((filepath() + 'review_dict_pairs.json'), 'r') as inp:
    review_dict_pairs = json.load(inp)

# with open((filepath() + 'rate_filtered.json'), 'r') as inp:
#     rate = json.load(inp)

# with open((filepath() + 'rate_pairs.json'), 'r') as inp:
#     rate_pairs = json.load(inp)


def boolean_and_search(lst_of_words, inv_idx):
    """
    lst-of-words is of type list with len > 1.
    inv_idx is a dictionary of words to (business_id, count).

    Returns list of [top 5] restaurants_ids where reviews mention lst_input words
    after performing
    """
    restaurants_array = []

    for word in lst_of_words:
        lst = list(inv_idx[word].keys())
        lst.sort()
        restaurants_array.append(lst)

    intermediate = restaurants_array[0]

    for lst in range(1, len(restaurants_array)):
        i, j = 0, 0
        temp = []
        while i < len(intermediate) and j < len(restaurants_array[lst]):
            if intermediate[i] == restaurants_array[lst][j]:
                temp.append(intermediate[i])
                i += 1
                j += 1
            elif intermediate[i] < restaurants_array[lst][j]:
                i += 1
            else:
                j += 1
        intermediate = temp
    return intermediate


def search_restaurants(lst_input, inv_idx):
    """
    lst_input is of type list. Contains user input broken down by whitespace
    inv_idx is a dictionary of words to (business_id, count).
     Returns list of [top 5] restaurants_ids where reviews mention lst_input words.
    """
    rest_ids = []
    if len(lst_input) == 0:
        return []
    if len(lst_input) == 1:
        if lst_input[0] in inv_idx:
            rest_ids = list(inv_idx[lst_input[0]].keys())
    else:
        food = lst_input[0] + " " + lst_input[1]
        if food in inverted_idx_pairs:
            rest_ids = list(inverted_idx_pairs[lst_input[0] + " " + lst_input[1]].keys())
        else: 
            rest_ids = boolean_and_search(lst_input, inverted_idx)

    return rest_ids[:5]

def restSort(input_list, rest_list, bool_pair):
    scoreDict = {}
    for rest in rest_list:
        total_frac = 0
        if bool_pair:
            word = input_list[0] + " " + input_list[1]
            total_frac += rate_pairs[word][rest]
        else:
            for word in input_list:
                total_frac += rate[word][rest]
        avg_frac = total_frac / len(input_list)
        scoreDict[rest] = 0.8*(avg_frac) + 0.4*(business_dict[rest]['stars'])
    return sorted(scoreDict, key=scoreDict.get, reverse = True)[:5]


def retrieve_restaurants(lst_of_input, bool_pair):
    lst_of_input = [x for x in lst_of_input if x in inverted_idx]
    if len(lst_of_input) == 1 and bool_pair:
        bool_pair = False
    if bool_pair:
        result_lst = search_restaurants(lst_of_input, inverted_idx_pairs)
    else:
        result_lst = search_restaurants(lst_of_input, inverted_idx)
    # sorted_lst = restSort(lst_of_input, result_lst, bool_pair)
    return_lst = []
    return_dict = {}
    for result in result_lst: #sorted_lst:
        bus_name = business_dict[result]["name"]
        if bool_pair:
            if result not in review_dict_pairs[lst_of_input[0] + " " + lst_of_input[1]]:
                review = ""
            else:
                review = review_dict_pairs[lst_of_input[0] + " " + lst_of_input[1]][result]
        else:
            if result not in review_dict[lst_of_input[0]]:
                review = ""
            else:
                review = review_dict[lst_of_input[0]][result]
        return_dict[result] = business_dict[result]
        return_dict[result]['review'] = review
        return_lst.append(return_dict[result])

    return return_lst


# print(retrieve_restaurants(["burger"], inverted_idx))
# print('IhNASEZ3XnBHmuuVnWdIwA' in search_restaurants(
#     ["japanese", "crepe"], inverted_idx))
#print(search_restaurants(["shrimp", "tamale"], inverted_idx))
