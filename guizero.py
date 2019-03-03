from guizero import App, Text, ListBox, PushButton, info, Combo
import requests

def buy_thing():
    info("Ok","Ok!")


app = App(title="Snacks!")

title_message = Text(app, text="Welcome to the snacks-app!", size=17)

r = requests.get(url='https://snacks.4lunch.eu/list-items')
items = r.json()

#listbox = ListBox(app, items=items, height="fill", align="left", width=200)
#listbox.text_size = 15

combo = Combo(app, options=items, width=200)


button = PushButton(app, text="Buy", command=buy_thing)

app.display()


