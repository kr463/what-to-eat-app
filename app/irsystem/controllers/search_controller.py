from . import *
from app.irsystem.models.helpers import *
from app.irsystem.models.helpers import NumpyEncoder as NumpyEncoder
from app.irsystem.controllers import rest_script
from app.irsystem.controllers.stop_words import stop_words
from app.irsystem.controllers import recipe_search

import re
import random
project_name = "What To Eat"
net_id = "Komukill Loganathan (kl866), Kyra Ratusnik (kr463), Anish Mohile (am2543), Jasper Krawitt (jwk238), Kate Ryan (kr467)"


def tokenize(text):
    return re.findall('[a-z]+', text.lower())

def filter_words(lst_of_words, stop_words):
    lst = []
    for word in lst_of_words:
        if word not in stop_words:
            lst.append(word)
    return lst

@irsystem.route('/', methods=['GET'])
def search():
	query = request.args.get('search')
	query2 = request.args.get('search2')
	adj_lst = ["yummy!", "delicious!", "fantastic!", "wonderful!", "amazing!", "spectacular!", "scruptious!"]
	if not query:
		data = []
		data2 = []
		output_message = ''
	elif not query2:
		query_toks = filter_words(tokenize(query), stop_words)
		if len(query_toks) > 1:
			pair = query_toks[0] + " " + query_toks[1]
			pairs_true = 1
		else:
			pairs_true = 0
		cap = query.capitalize()
		output_message = cap + "! Sounds " + random.choice(adj_lst)
		# data = range(5)
		data = rest_script.retrieve_restaurants(query_toks, pairs_true)
		data2 = recipe_search.top_ten(query, '')
	else:
		query_toks = filter_words(tokenize(query), stop_words)
		query2_toks = filter_words(tokenize(query2), stop_words)
		if len(query_toks) > 1:
			pair = query_toks[0] + " " + query_toks[1]
			pairs_true = 1
		else:
			pairs_true = 0
		cap = query.capitalize()
		output_message = cap + " with no " + query2 + "! Coming right up!"
		# data = range(5)
		data = rest_script.retrieve_restaurants(query_toks, pairs_true)
		data2 = recipe_search.top_ten(query, query2_toks)

	name_dict = {}
	
	for d in range(0, len(data2)):
		if data2[d]['title'] in name_dict.keys():
			name_dict[data2[d]['title']] += 1
			data2[d]['title'] += ' ' + str(name_dict[data2[d]['title']])
		else:
			name_dict[data2[d]['title']] = 1

	return render_template('search.html', name=project_name, netid=net_id, output_message=output_message, data=data, data2=data2)
