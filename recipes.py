#!/usr/bin/python

from io import StringIO
import re

import requests
from lxml import etree

parser = etree.HTMLParser()


host = "https://www.ricardocuisine.com"
#host = "https://www.ricardocuisine.com/en"

def search(pattern):

    if host.endswith("/en"):
        url = "{}/search/key-words/{}/misc/all/sort/score/cat/all/temps/all/ingredient-to-include/all/ingredient-to-exclude/none/tab/recipe/page/1/".format(host, pattern)
    else:
        url = "{}/recherche/mot-cle/{}/all/sort/score/cat/all/temps/all/ingredient-a-inclure/all/ingredient-a-exclure/none/tab/recipe/page/1/".format(host, pattern)

    raw_res = requests.get(url)
    result = StringIO(raw_res.content.decode("utf-8"))
    try:
        tree = etree.parse(result, parser)
    except etree.XMLSyntaxError:
        # TODO better handling
        pass

    div_results = tree.find("""//div[@id="search-results"]/div[@class="item-list"]""")

    results = []
    for recipes_li in div_results.findall("""./ul/li"""):
        title = recipes_li.find("""./div[@class="desc"]/h2[@class="title"]/a""").text
        link = recipes_li.find("""./div[@class="desc"]/h2[@class="title"]/a""").attrib.get('href')
        prep_time = recipes_li.findall("""./div[@class="desc"]/ul/li""")[0].text
        total_time = recipes_li.findall("""./div[@class="desc"]/ul/li""")[1].text
        results.append({"title": title,
                        "link": link,
                        "prep_time": prep_time,
                        "total_time": total_time,
                        })

    return results


def parse_recipe(link):
    if host.endswith("/en"):
        url = "{}{}".format(host[:-3], link)
    else:
        url = "{}{}".format(host, link)

    raw_res = requests.get(url)
    print(url)
    result = StringIO(raw_res.content.decode("utf-8"))
    try:
        tree = etree.parse(result, parser)
    except etree.XMLSyntaxError:
        # TODO better handling
        pass

    # title
    title = tree.find("""//div[@class="recipe-content"]/h1""").text
    meta_data_nodes = tree.find("""//div[@class="recipe-content"]/dl""")
    meta_data = {}
    data_name = None
    for node in meta_data_nodes:
        if node.tag == "dt":
            data_name = node.text
        elif node.tag == "dd" and data_name is not None:
            data = " ".join([i for i in node.itertext()]).strip().lower()
            meta_data[data_name] = data
            data_name = None

    # Ingredients
    form_nodes = tree.findall("""//section[@id="ingredients"]/form[@id="formIngredients"]/""")

    ingredients = {}
    last_item = ""
    for node in form_nodes:
        if node.tag == 'h3':
            last_item = node.text
            ingredients[last_item] = []
        elif node.tag == 'ul':
            # no item means only one item
            if last_item == "":
                ingredients[""] = []

            # Get ingredients
            ingredient_list = [igdt.text for igdt in node.findall("./li/label/span")]
            for raw_igdt in ingredient_list:
                # example: 5 ml (1 c. à thé) de romarin frais, haché
                res = re.match("([0-9][0-9,]* [^ ]*) \(([^)]*)\) (.*)", raw_igdt)
                if res:
                    ingredient = {"si": res.group(1),
                                  "em": res.group(2),
                                  "text": "{} " + res.group(3),
                                  }
                    ingredients[last_item].append(ingredient)
                    continue

                # 1 gigot d'agneau de 3,4 kg (7 livres), désossé + les os
                res = re.match("(.*) ([0-9][0-9,]* [^ ]*) \(([^)]*)\) (.*)", raw_igdt)
                if res:
                    ingredient = {"si": res.group(2),
                                  "em": res.group(3),
                                  "text": res.group(1) + " {} " + res.group(4),
                                  }
                    ingredients[last_item].append(ingredient)
                    continue

                # Sel et poivre
                ingredient = {"si": None,
                              "em": None,
                              "text": raw_igdt,
                              }
                ingredients[last_item].append(ingredient)

    # Instructions
    instructions_nodes = tree.findall("""//section[@id="preparation"]/""")

    instructions = {}
    last_item = ""
    for node in instructions_nodes:
        if node.tag == 'h3':
            last_item = node.text
            instructions[last_item] = []
        elif node.tag == 'ol':
            # no item means only one item
            if last_item == "":
                instructions[""] = []

            step_list = [igdt.text for igdt in node.findall("./li/span")]
            for step in step_list:
                instructions[last_item].append([substep for substep in step.split(". ")])


    recipe = {"title": title,
              "link": link,
              "ingredients": ingredients,
              "instructions": instructions,
              }
    recipe.update(meta_data)
    return recipe


def read_recipe(recipe, system="si"):

    # TODO system in [si, em]
    for item, igdts in recipe.get("ingredients").items():
        print(item)
        for igdt in igdts:
            print(igdt.get('text').format(igdt.get(system)))
        print("")

    for item, steps in recipe.get("instructions").items():
        print(item)
        for step_id, step in enumerate(steps):
            print("Step", step_id + 1)
            for substep in step:
                print(substep)
            print("")
        print("")
        

def start_cooking():
    pass

def get_ingredients():
    pass

def begin_preparation():
    pass

def next_preparation():
    pass

def previous_preparation():
    pass

def repeat():
    pass

def stop_cooking():
    pass

def follow_recipe(recipe):
    pass

results = search("chili")

recipe = parse_recipe(results[0].get('link'))
print(recipe)

read_recipe(recipe, "em")
#import ipdb;ipdb.set_trace()
