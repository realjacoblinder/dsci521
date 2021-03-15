import dash_html_components as html
import dash_bootstrap_components as dbc

# needed only if running this as a single page app
#external_stylesheets = [dbc.themes.LUX]

#app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

# change to app.layout if running as single page app instead
layout = html.Div([
    dbc.Container([
        dbc.Row([
            dbc.Col(html.H1("DSCI 521 - Chess Analytics", className="text-center")
                    , className="mb-5 mt-5")
        ]),
        dbc.Row([
            dbc.Col(html.H5(children='This data was collected from Lichess.com, a popular competitive chess website.'), className="mb-4")
            ]),

        dbc.Row([
            dbc.Col(html.H5(children='The analysis is split into two overall categories, Player and Pieces. Players is a page dedicted to player oriented analytics. This will contain'
                                        ' things related to ELO and win rates. Pieces focuses on piece level statistics, but can still be filtered on player related values like rating.')
                    , className="mb-5")
        ]),

        dbc.Row([
            dbc.Col(dbc.Card(children=[html.H3(children='Get the original datasets used in this dashboard',
                                               className="text-center"),
                                       dbc.Row([dbc.Col(dbc.Button("Lichess data", href="https://database.lichess.org/",
                                                                   color="primary"),
                                                        className="mt-3"),
                                                dbc.Col(dbc.Button("February 2013", href="https://database.lichess.org/standard/lichess_db_standard_rated_2013-02.pgn.bz2",
                                                                   color="primary"),
                                                        className="mt-3")], justify="center")
                                       ],
                             body=True, color="dark", outline=True)
                    , width=4, className="mb-4"),

            dbc.Col(dbc.Card(children=[html.H3(children='Access the code used to build this dashboard',
                                               className="text-center"),
                                       dbc.Button("GitHub",
                                                  href="https://github.com/realjacoblinder/dsci521",
                                                  color="primary",
                                                  className="mt-3"),
                                       ],
                             body=True, color="dark", outline=True)
                    , width=4, className="mb-4")
    ])

])
])