import dash
import dash_bootstrap_components as dbc
from dash import html, dcc, Input, Output, State, callback, ctx

import pandas
from pages import about
import connection
from collections import defaultdict
import re

about= html.Div([dcc.Markdown('''
Авторы-составители:
__М.Я. Гловинская, Е.И. Голанова, О.П. Ермакова, А.В. Занадворова, Е.В. Какорина, М.В. Китайгородская, Л.П. Крысин, С.М. Кузьмина, И.В. Нечаева, А.Р. Пестова, 
Н.Н. Розанова, Р.И. Розина__
Ответственный редактор
__Л.П. Крысин__
Рецензенты:
__доктор филологических наук, профессор Саратовского гос. университета В.Е. Гольдин__
__доктор филологических наук, заведующий отделом Института русского языка им. В.В. Виноградова РАН__
__А.Ф. Журавлёв__


''')],
     style={'margin':'50px'}
      )


# Создание списка кнопок
letters=['А','Б','В','Г','Д','Е,Ё','Ж','З','И','К','Л','М','Н','О','П','Р','С','Т','У','Ф','Х','Ц','Ч','Ш','Щ','Э','Ю','Я']
letter_buttons_lst = [dbc.Button(letter, id=letter, color="dark", n_clicks=0, href="/") for letter in letters]


search_bar = dbc.Row(
    [
        dbc.Col(dbc.Input(id='search_input', type="search", placeholder="Поиск", debounce=True), style={"padding-right": "25px"}),
        dbc.Col(
            dbc.Button(
                "Поиск", id='search_button',color="primary", className="ms-2", n_clicks=0
            ),
            width="auto",
        ),
    ],
    className="g-0 ms-auto flex-nowrap mt-3 mt-md-0",
    align="center",
)

navbar = dbc.NavbarSimple(
    children=[
        dbc.NavItem(dbc.NavLink("На главную", href="/"), style={"padding-right": "30px"}),
        dbc.NavItem(dbc.NavLink("О словаре", href="/about"), style={"padding-right": "30px"}),
        search_bar
    ],
    brand="Толковый словарь русской разговорной речи",
    color="primary",
    dark=True,
    style={"height": "96px"},
)

letter_button_group = dbc.ButtonGroup(

    letter_buttons_lst,
    style={"width": "100%"},
    size='sm'
)

top = html.Div([navbar, letter_button_group, html.Span(id="def_output", style={"verticalAlign": "middle"})])

modal = dbc.Modal([dbc.ModalHeader(dbc.ModalTitle("Результат поиска")), dbc.ModalBody(id ='search_output')],
            id="modal",
            size="xl",
            is_open=False,
        )

layout=html.Div([ html.Div([ top, modal, about]) ])

#Создание списка входных параметров для колбэка
letters_inputs = [Input(letter, "n_clicks") for letter in letters]


def make_good_string(st):
    new_st=st
    new_st=new_st.replace('1', '¹')
    new_st=new_st.replace('2', '²')
    new_st=new_st.replace('3', '³')
    new_st=new_st.replace('4', '⁴')
    for i in range(len(new_st)):
        if new_st[i] in ['\'', '´', '′', '’', 'ˊ', chr(42891), 'Ꞌ', 'ʹ']:
            new_st=new_st[0:i]+'\u0301'+new_st[i+1:]

    return(new_st)


def words_list(letter):

    if letter == 'Е,Ё':
        letter = 'Е'

    with connection.collection.find({'letter':letter}).hint('letter_1').sort('id', 1) as cursor:
        documents_list = []

        for element in cursor:
            if element['head'] != None:
                element['head'] = make_good_string(element['head']).upper()
                documents_list.append(element)

    return documents_list


def sorting_documents(documents_list):
    homonyms = defaultdict(list)

    for document in documents_list:
        homonyms[document['id']].append(document)

    return homonyms


def make_def(lst):
    marks_lst=["DEF", "MORPH", "SYNT", "STYL", "SYN", "ANT", "CONV", "ANALOG", "PHRAS", "PRAGM"]
    all_defs=[]
    for element in lst:
        w_def=[]
        word=dict(element).items()
        for el in list(word)[1:]:
            if el[0] in marks_lst:
                txt=el[1].replace(el[0]+': ','')
                dict_zone=('**'+el[0]+'**', txt)
                w_def.append(dict_zone)
            elif el[0]=='UNTITLED':
                txt=str(el[1]).replace(el[0]+': ','')
                dict_zone=('** DEF **', txt)
                w_def.append(dict_zone)

        if len(w_def)>0:
            all_defs.append(w_def)

    return(all_defs)


def make_modal(defs, w_def, def_lst, n):
    n-=1
    full_def=[]
    for zone in w_def:
        md_z=dcc.Markdown(zone[0])
        row = html.Tr([html.Td(md_z), html.Td(zone[1])])
        full_def.append(row)
    if len(def_lst)>1:
        defs.append(html.H3('Определение №'+str(len(def_lst)-n)))
    defs.append(dbc.Table(full_def))

    return defs


# Декоратор для колбэка, связывающий выходной компонент и входные параметры
@callback(
    Output("def_output", "children"),
    letters_inputs
)

def on_button_click(*args):
    if ctx.triggered_id is None:
        return None

    words_ac_items=[]
    documents_list=words_list(ctx.triggered_id)[1:]
    sorted_list = sorting_documents(documents_list)

    for key in sorted_list:
        item_title = ''
        word_values = []
        first_iteration = True
        for value in sorted_list[key]:
            word_values.append(value)
            if first_iteration:
                item_title = value['head']
                item_title = re.sub(r"\.$", "", item_title)
                first_iteration = False

        word_def_list = make_def(word_values)

        n = len(word_def_list)
        defs = []
        for w_def in word_def_list:
            make_modal(defs, w_def, word_def_list, n)
            n-=1
        ac_item=dbc.AccordionItem(html.Div(defs) , title=item_title)
        words_ac_items.append(ac_item)
    accordion=html.Div(dbc.Accordion(words_ac_items, start_collapsed=True))
    return html.Div(accordion)


def makeid(st: str):
    if st is not None:
        id=st
        for sym in st:
            if not (( sym >= 'а' and sym <= 'я' ) or ( sym >= 'А' and sym <= 'Я' ) or sym == ',' or sym == '-' or sym == 'ё' or sym == 'Ё'):
                id=id.replace(sym,'')
        return id.upper()


def find_def_for_search(word_id):
    with connection.collection.find({'id':word_id}).hint('id_1') as documents:
        definitions = make_def(documents)

    return definitions


@callback (
    Output("modal", 'is_open'),
    Output("search_output", "children"),

    [Input('search_button', 'n_clicks' ),
     Input('search_input', 'n_submit')],
    [State('search_input', 'value')]
    )

def search_result(n_clicks, n_submit, value):
    defs=[]
    if n_clicks or n_submit:
        if value == '':
            defs = 'Введите слово!'

        def_lst=find_def_for_search(makeid(str(value)))
        n=len(def_lst)

        for word_def in def_lst:
            make_modal(defs, word_def, def_lst, n)
            n-=1
            n_clicks=0
        if defs==[]:
            defs=f'Введенное вами слово "{value}" не было найдено в словаре!'
        return  True, defs
    else:
        return False, ''



