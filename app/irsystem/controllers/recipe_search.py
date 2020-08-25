import numpy as np
import json
import re
import math
from sklearn.metrics import jaccard_similarity_score
from app.irsystem.controllers.check_production import filepath
import os
import boto3

aws_id = os.environ.get('AWS_ACCESS_KEY_ID')
aws_key = os.environ.get('AWS_SECRET_ACCESS_KEY')

BUCKET = 'what-to-eat-project'

client = boto3.client('s3',
                       aws_access_key_id=aws_id,
                       aws_secret_access_key=aws_key
                     )

recipe_dict = {}

common_allergens = {}
common_allergens['gluten'] = ['flour', 'wheat', 'bread', 'pasta', 'cracker', 'couscous']
common_allergens['dairy'] = ['milk', 'cream', 'butter', 'half-and-half', 'yogurt', 'cheese', 'mozzarella', 'ricotta', 'parmesan', 'brie', 'cheddar']
common_allergens['cheese'] = ['cheeses', 'parmesan', 'cheddar',  'asiago', 'provolone', 'jack', 'swiss', 'american cheese', 'ricotta', 'brie', 'mozzarella']
common_allergens['shellfish'] = ['shrimp', 'mussels', 'oysters', 'crab', 'lobster', 'clams', 'scallops', 'crayfish', 'prawn', 'squid']
common_allergens['nuts'] = ['walnut', 'peanut', 'pecans', 'pecan', 'cashew', 'pistachio']
common_allergens['soy'] = ['soybean', 'tofu']
common_allergens['fish'] = ['salmon', 'tuna', 'mahi', 'flounder', 'sole', 'cod']
common_allergens['meat'] = ['beef', 'steak', 'sirloin', 'chicken', 'pork', 'lamb', 'mutton', 'ham', 'bacon', 'sausage', 'turkey', 'turkey', 'prosciutto', 'pepperoni', 'ribs', 'brisket']
common_allergens['nut'] = common_allergens['nuts']
common_allergens['pescatarian'] = common_allergens['meat']
common_allergens['vegetarian'] = common_allergens['meat'] + common_allergens['fish'] + common_allergens['shellfish']
common_allergens['vegan'] = common_allergens['vegetarian'] + common_allergens['dairy'] + ['eggs', 'honey']
common_allergens['peanuts'] = ['peanut', 'peanuts']
common_allergens['peanut'] = ['peanut', 'peanuts']

for i in range(1,8):
    with open(filepath() + 'recipes_' + str(i) + '.json') as f:
        recipe_dict.update(json.load(f))

# for i in range(6,10):
#     FILE_TO_READ = 'recipes_' + str(i) +'.json'
#     result = client.get_object(Bucket=BUCKET, Key=FILE_TO_READ)
#     recipe_dict.update(json.loads(result["Body"].read().decode()))


def get_ingredients_dict():
    with open(filepath() + 'ingredients.json') as f:
        ing_dict = json.load(f)

    return ing_dict



# def get_recipe_dict():
#     with open(filepath() + 'recipe_clean_small.json') as f:
#         recipe_dict = json.load(f)

#     return recipe_dict

# recipe_dict = get_recipe_dict()

def get_good_types(recipe_dict):
    good_types = set()
    for key in recipe_dict:
        title = recipe_dict[key]['title']
        lst = tokenize(title)
        for word in lst:
            good_types.add(word)

    return good_types


def tokenize(text):
    return re.findall('[a-z]+', text.lower())

def length_diff(l1, l2):
    if len(l1) > len(l2):
        return len(l1)-len(l2)
    elif len(l1) < len(l2):
        return len(l2)-len(l1)
    else:
        return 0


def jaccard_ing(ingredient):
    score = []
    tokenized_ing = tokenize(ingredient)
    for index in ing_dict['item']:
        tokenized_ing2 = tokenize(ing_dict['item'][index])
        length_dif = length_diff(tokenized_ing, tokenized_ing2)
        if len(tokenized_ing) > len(tokenized_ing2):
            tokenized_ing2.extend([""]*length_dif)
        else:
            tokenized_ing.extend([""]*length_dif)
        ing_score = jaccard_similarity_score(tokenized_ing, tokenized_ing2)
        score.append((index, ing_score))
        if ing_score > 0.7:
            break
    return (sorted(score, key = lambda x: x[1])[-1])

def calc_cost(ing_list):
    total_price = 0
    for ing in ing_list:
        matching_ing = jaccard_ing(ing)
        price = int(ing_dict['price'][matching_ing[0]])
        # print(ing_dict['item'][matching_ing[0]])
        # print(ing_dict['price'][matching_ing[0]])
        total_price += price
    avgcost = round((total_price / (len(ing_list) + 1)), 0)
    # dollar signs based on where the average falls within each quantile of
    # the prices in the recipe database
    # if avgcost < 7.6875:
    #     return ''
    # elif avgcost < 12.99:
    #     return '$'
    # elif avgcost < 19.98:
    #     return '$$'
    # else:
    #     return '$$$'
    return int(avgcost)

def has_allergen(ing_list, allergens):
    for item in allergens:
        for ing in ing_list:
            if item in ing:
                return True

    return False
# ##### ---------
#     ing_set = set()
#     for ing in ing_list:
#         ing_tokens = tokenize(ing)
#         for token in ing_tokens:
#             # ing_token_l = lemmatizer.lemmatize(token)
#             ing_token_l = token
#             ing_set.add(ing_token_l)
#     for a in allergens:
#         for ing in ing_set:
#             if a in ing:
#                 return True
#     return False

def preprocess():
    # inv_idx
    inv_idx = {}
    for word in good_types:
        inv_idx[word] = []

    for key in recipe_dict:
        title = recipe_dict[key]['title']
        lst = tokenize(title)
        for word in lst:
            inv_idx[word].append((key, lst.count(word)))

    # idf
    n_docs = len(recipe_dict)
    idf_dict = {}
    for word in inv_idx:
        wdocs = len(inv_idx[word])
        idf_dict[word] = math.log((n_docs/(1+wdocs)), 2)

    # doc norms
    norms = np.zeros(n_docs)
    for term in inv_idx:
        if term in idf_dict:
            tdocs = inv_idx[term]
            for tpl in tdocs:
                norms[int(tpl[0])] += ((tpl[1] * idf_dict[term]) ** 2)
    norms = np.sqrt(norms)

    return(inv_idx, idf_dict, norms)


def index_search(query, index, idf, doc_norms):
    results = []

    q_tokens = tokenize(query.lower())
    q_tfidf = {}
    qnorm = 0
    for word in set(q_tokens):
        if word in idf:
            q_tfidf[word] = q_tokens.count(word) * idf[word]
            qnorm += ((q_tokens.count(word) * idf[word]) ** 2)

    qnorm = math.sqrt(qnorm)

    d_scores = np.zeros(len(doc_norms))
    for word in q_tfidf:
        wd_idx = index[word]
        for tpl in wd_idx:
            d_scores[int(tpl[0])] += q_tfidf[word] * tpl[1] * idf[word]

    #     print(np.sort(d_scores)[::-1][:10])
    #     print(qnorm)
    #     print(doc_norms[26768])
    #     print(doc_norms[26691])

    for doc_idx in range(0, len(d_scores)):
        if d_scores[doc_idx] != 0:
            d_scores[doc_idx] /= (qnorm * doc_norms[doc_idx])

    for doc_idx in range(0, len(d_scores)):
        results.append((d_scores[doc_idx], doc_idx))

    sorted_results = sorted(results)[::-1]
    final = []
    for x in sorted_results:
        final.append(recipe_dict[str(x[1])])

    return final


def boolean_search(query_word, not_word):
    query_word = query_word.lower()
    not_word = not_word.lower()

    mlist = []
    q_list = inverted_index[query_word]
    n_list = inverted_index[not_word]
    qptr = 0
    nptr = 0
    while qptr < len(q_list):
        qdoc = q_list[qptr][0]
        if nptr < len(n_list):
            ndoc = n_list[nptr][0]
        if qdoc == ndoc:
            qptr += 1
            nptr += 1
        elif qdoc < ndoc or nptr == len(n_list):
            mlist.append(qdoc)
            qptr += 1
        else:
            nptr += 1
    return mlist


#recipe_dict = get_recipe_dict()
good_types = get_good_types(recipe_dict)

metrics = preprocess()
inv_idx = metrics[0]
idf_dict = metrics[1]
norms = metrics[2]
ing_dict = get_ingredients_dict()


def boolean_search(query_word, not_word):
    query_word = query_word.lower()
    not_word = not_word.lower()

    mlist = []
    q_list = inv_idx[query_word]
    n_list = inv_idx[not_word]
    qptr = 0
    nptr = 0
    while qptr < len(q_list):
        qdoc = q_list[qptr][0]
        if nptr < len(n_list):
            ndoc = n_list[nptr][0]
        if qdoc == ndoc:
            qptr += 1
            nptr += 1
        elif qdoc < ndoc or nptr == len(n_list):
            mlist.append(qdoc)
            qptr += 1
        else:
            nptr += 1
    return mlist


def top_ten(query, allergens):
    allergens_l = []

    for a in allergens:
        if a in common_allergens.keys():
            allergens_l += common_allergens[a]
        if a[-1] == 's':
            allergens_l.append(a[:-1])
    allergens_l.extend(allergens)
    # for a in allergens:
    #     #al = lemmatizer.lemmatize(a)
    #     al = a
    #     allergens_l.append(al)

    #print(index_search(query, inv_idx, idf_dict, norms)[:10])
    top_five = index_search(query, inv_idx, idf_dict, norms)[:25]
    rec_list = []
    for recipe in top_five:
        ing_list = recipe['ingredients']
        if not has_allergen(ing_list, allergens_l):
            cost = calc_cost(ing_list)
            recipe['cost'] = cost
            rec_list.append(recipe)
    lst_recipe_rank = []
    for recipe in rec_list:
        title_len = len(recipe['title'])
        query_len = len(query)
        ratio = query_len / title_len
        lst_recipe_rank.append((recipe, ratio))
    sorted_recipe = sorted(lst_recipe_rank[:8], key=lambda tup: tup[1], reverse=True)
    sorted_recipe = [i[0] for i in sorted_recipe]
    if len(sorted_recipe) < 5:
        return sorted_recipe
    return sorted_recipe[:5]



# for x in top10:
    # print('Score: ' + str(x[0]))
    # print(recipe_dict[str(x[1])]['title'])