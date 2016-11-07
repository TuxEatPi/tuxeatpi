"""Clock skill module"""

from datetime import datetime
from queue import Queue, Empty

from tuxeatpi.skills.common import ThreadedSkill, capability, can_transmit, threaded
from tuxeatpi.libs.lang import gtt
from tuxeatpi.skills.cook import common


class Cook(ThreadedSkill):
    """Skill about clock, timer, ..."""

    def __init__(self, settings):
        ThreadedSkill.__init__(self, settings)
        self.user_answer_queue = Queue()

    def help_(self):
        """Return skill help"""
        return gtt("talk about time")

    @capability(gtt("Accept positive user answer"))
    @can_transmit
    def positive_answer(self):
        self.user_answer_queue.put(True)

    @capability(gtt("Accept negative user answer"))
    @can_transmit
    def negative_answer(self):
        self.user_answer_queue.put(False)

    @capability(gtt("Search recipe"))
    @threaded
    @can_transmit
    def search_recipe(self, pattern):  # pylint: disable=R0201
        """Return current time"""
        print(pattern)
        # Search recipe
        recipes = common.search_recipe(pattern, self.settings['speech']['language'])
        user_recipe = None
        # Browser search result (recipe list)
        for recipe in recipes:
            tts = gtt("I found a recipe of {}. Do you want this recipe ?").format(recipe['title'])
            tmn = self.create_transmission("search_recipe",
                                           "aptitudes.speak.say",
                                           {"arguments": {"tts": tts}})
            self.wait_for_answer(tmn.id_)
            # Wait for answer
            self.user_answer = self.user_answer_queue.get()
            if self.user_answer:
                tts = gtt("We are going to cook a recipe of {}").format(recipe['title'])
                tmn = self.create_transmission("search_recipe",
                                               "aptitudes.speak.say",
                                               {"arguments": {"tts": tts}})
                self.wait_for_answer(tmn.id_)
                user_recipe = recipe
                break

        if user_recipe is not None:
            # start cooking
            user_recipe = common.parse_recipe(user_recipe.get('link'))
            self.cooking(user_recipe)

    def cooking(self, recipe):
# {'Préparation': '30 min', 'instructions': {'Enrobage': [['Dans un autre bol, mélanger la farine, la poudre à pâte, \r\nles épices et le sel.'], ['Retirer le poulet du lait de beurre', 'Enrober les pilons du mélange de farine', 'Secouer pour retirer l’excédent', 'Déposer sur une plaque', 'Une fois tous les pilons panés, tremper une seconde fois dans le lait de beurre, puis enrober à nouveau dans le mélange de farine.'], ['Préchauffer la graisse végétale dans la friteuse à 185\xa0°C (365\xa0°F)', 'Tapisser une plaque de cuisson de papier absorbant.'], ['Déposer la moitié des pilons de poulet à la fois dans la graisse chaude et les cuire environ 15\xa0minutes ou jusqu’à ce qu’un thermomètre inséré au centre d’un pilon sans toucher l’os indique 82\xa0°C (180\xa0°F), en les retournant à quelques reprises durant la cuisson', 'Attention aux éclaboussures', 'Égoutter sur le papier absorbant', 'Saler.']], 'Marinade': [['Dans un bol, mélanger le poulet et le lait de beurre', '\r\nCouvrir et réfrigérer 12\xa0heures.']]}, 'link': '/recettes/7012-poulet-frit', 'Cuisson': '35 min', 'title': ' Poulet frit', 'ingredients': {'Enrobage': [{'em': '1 1/2 tasse', 'text': '{} de farine tout usage non blanchie', 'si': '210 g'}, {'em': '1 c. à thé', 'text': '{} de poudre à pâte', 'si': '5 ml'}, {'em': '1 c. à thé', 'text': '{} de paprika', 'si': '5 ml'}, {'em': '1 c. à thé', 'text': '{} de poivre de Cayenne', 'si': '5 ml'}, {'em': '1 c. à thé', 'text': '{} de poudre d’ail', 'si': '5 ml'}, {'em': '1 c. à thé', 'text': '{} de poudre d’oignon', 'si': '5 ml'}, {'em': '1 c. à thé', 'text': '{} de moutarde sèche', 'si': '5 ml'}, {'em': '1 c. à thé', 'text': '{} de sel', 'si': '5 ml'}, {'em': '3 tasses', 'text': '{} de graisse végétale, pour la friture', 'si': '675 g'}], 'Marinade': [{'em': None, 'text': '8  pilons de poulet avec ou sans la peau', 'si': None}, {'em': '2 tasses', 'text': '{} de lait de beurre', 'si': '500 ml'}]}, 'Macération': '12 h', 'Portions': '4'} 

        # List stuff to do
        if len(user_recipe.get("ingredients")) == 1:
            tts = gtt("We have one thing to do").format(len(user_recipe.get("ingredients")))
        elif len(user_recipe.get("ingredients")) > 1:
            tts = gtt("We have {} things to do").format(len(user_recipe.get("ingredients")))
        else:
            raise Exception("Nothing to do")
        tmn = self.create_transmission("search_recipe",
                                       "aptitudes.speak.say",
                                       {"arguments": {"tts": tts}})
        self.wait_for_answer(tmn.id_)

        for item_name, ingredients in user_recipe.get("ingredients").items():
            # List ingredients for each thing to do
            tts = gtt("This is the ingredient list for {}").format(item_name)
            tmn = self.create_transmission("search_recipe",
                                           "aptitudes.speak.say",
                                           {"arguments": {"tts": tts}})
            self.wait_for_answer(tmn.id_)
            for ingredient in ingredients:
                try:
                    self.user_answer = self.user_answer_queue.get(timeout=1)
                    if not self.user_answer:
                        self.user_answer_queue.get()
                except Empty:
                    pass

                if ingredient.get("em"):
                    tts = ingredient.get("text").format(ingredient.get("em"))
                else:
                    tts = ingredient.get("text")
                tmn = self.create_transmission("search_recipe",
                                               "aptitudes.speak.say",
                                               {"arguments": {"tts": tts}})
                self.wait_for_answer(tmn.id_)

        tts = gtt("Do you have all ingredients ?")
        tmn = self.create_transmission("search_recipe",
                                       "aptitudes.speak.say",
                                       {"arguments": {"tts": tts}})
        self.wait_for_answer(tmn.id_)
        self.user_answer = self.user_answer_queue.get()
        if not self.user_answer:
            return

        tts = gtt("Are you ready to begin ?")
        tmn = self.create_transmission("search_recipe",
                                       "aptitudes.speak.say",
                                       {"arguments": {"tts": tts}})
        self.wait_for_answer(tmn.id_)
        self.user_answer = self.user_answer_queue.get()
        if not self.user_answer:
            return


        for item_name, instructions in user_recipe.get("instructions").items():
            tts = gtt("Instructions for {}").format(item_name)
            tmn = self.create_transmission("search_recipe",
                                           "aptitudes.speak.say",
                                           {"arguments": {"tts": tts}})
            self.wait_for_answer(tmn.id_)
            for index, step in enumerate(instructions):
                tts = gtt("Step number {}").format(index)
                tmn = self.create_transmission("search_recipe",
                                               "aptitudes.speak.say",
                                               {"arguments": {"tts": tts}})
                self.wait_for_answer(tmn.id_)
                for substep in step:
                    tmn = self.create_transmission("search_recipe",
                                                   "aptitudes.speak.say",
                                                   {"arguments": {"tts": substep}})
                    self.wait_for_answer(tmn.id_)


#                tmn = self.create_transmission("search_recipe",
#                                               "aptitudes.speak.say",
#                                               {"arguments": {"tts": ingredient}})
#                self.wait_for_answer(tmn.id_)       
            
#        command = "aptitude.speak.say"
#        content = {"arguments": {"tts": ""}}
#        tmn = self.create_transmission("search_recipe", command, {})
#        answer = self.wait_for_answer(tmn.id_)
#
#        common.search_recipe()
#        now = datetime.now()
#        time_text = now.strftime(gtt("%I:%M %p"))
#        tts = gtt("It's {}").format(time_text)
        return {"tts": pattern, "result": {"time": time_text}}
