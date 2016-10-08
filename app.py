# %%
# Importing libraries

import os
from flask import Flask, render_template
import pandas as pd
import requests
from bokeh.charts import Bar, show, output_file, save
from bokeh.layouts import layout
from bokeh.models import ColumnDataSource, DataRange1d, Range1d, VBox, HBox, Select, HoverTool
from bokeh.palettes import Blues5
from bokeh.plotting import Figure

# Defining environment settings
app = Flask(__name__)
app.config.from_object(os.environ['APP_SETTINGS'])

# %%
# Defining the function that gets the API Key


def getKey():
    try:
        with open('key.txt') as file:
            key = file.readlines()
    except:
        os.chdir(__file__)
        with open('key.txt') as file:
            key = file.readlines()

    return key


def getItems(suffix,
             apiKey,
             base_url=('http://bitnami-dreamfactory-000b.cloudapp.net/' +
                       'api/v2/venndor/_table/')
             ):
    if suffix not in ['items', 'matches', 'posts', 'seenposts', 'users']:
        raise ValueError('%s not in list of approved tables' % suffix)
    else:
        response = requests.get(base_url + suffix + '?api_key=%s' % apiKey)
        response_dict = response.json()
        if len(response_dict.keys()) > 1:
            return(response_dict)
        elif len(response_dict.keys()) == 1:
            response_key = [key for key in response_dict.keys()][0]
            return(response_dict[response_key])

# %%
apiKey = getKey()[0]


# %%
url_items = ('http://bitnami-dreamfactory-000b.cloudapp.net/' +
             'api/v2/venndor/_table/' +
             'items?api_key=' + apiKey)

url_matches = ('http://bitnami-dreamfactory-000b.cloudapp.net/' +
               'api/v2/venndor/_table/' +
               'matches?api_key=' + apiKey)
               
url_posts = ('http://bitnami-dreamfactory-000b.cloudapp.net/' +
             'api/v2/venndor/_table/' +
             'posts?api_key=' + apiKey)

url_seenPosts = ('http://bitnami-dreamfactory-000b.cloudapp.net/' +
                 'api/v2/venndor/_table/' +
                 'seenposts?api_key=' + apiKey)

url_users = ('http://bitnami-dreamfactory-000b.cloudapp.net/' +
             'api/v2/venndor/_table/' +
             'users?api_key=' + apiKey)

#y = getItems(url_items)
#y = getItems(url_matches)
#y = getItems(url_posts)
#y = getItems(url_seenPosts)

# %%


@app.route('/')
def dashboard():
    # Creating all the queries
    items = getItems(suffix='items', apiKey=apiKey)
    users = getItems(suffix='users', apiKey=apiKey)

    # Generating the output file name
    output_file("templates/bar.html")

    # %% Creating df defining the ratio of right swipes to left swipes
    df_right_left = pd.DataFrame(items)

    # Finding the ratio
    df_right_left['RightOverLeft'] = df_right_left['nuSwipesRight'].div(
                                        df_right_left['nuSwipesLeft'])

    # Grouping by, and performing different aggregations
    df_right_left = df_right_left[['category',
                                   'nuSwipesRight',
                                   'nuSwipesLeft',
                                   'RightOverLeft']].groupby(
                                      'category', as_index=False
                                          ).agg(
                                               {'nuSwipesRight': 'sum',
                                                'nuSwipesLeft': 'sum',
                                                'RightOverLeft': 'mean'})

    # Creating the first bar chart
    p1 = Bar(data=df_right_left,
             label='category',
             values='RightOverLeft',
             title="Category vs Right-Left Ratio",
             color='category',
             tools='hover',
             ylabel='Right / Left Swipes',
             agg='mean',
             legend=False)

    # Defining the hover tools
    hover = p1.select(dict(type=HoverTool))

    # Defining p1 tooltips
    hover.tooltips = [('Value', '@y'),
                      ('Category', '@x')]

    # %% Creating df of time-per-controller variables
    df_users = pd.io.json.json_normalize(users)
    df_users = df_users.filter(regex='timePerController')
    cols = [col.split('.')[1] for col in df_users.columns.values]
    df_users.columns = cols

    # Melting df
    df_users = pd.melt(df_users,
                       value_name='TimeSpent',
                       var_name='Variable')

    # Creating p2
    p2 = Bar(data=df_users,
             label='Variable',
             values='TimeSpent',
             title='Average Time Spent on Controllers',
             color='Variable',
             tools='hover',
             agg='mean',
             legend=False)

    # Defining the hover tools
    hover = p2.select(dict(type=HoverTool))

    # Defining p1 tooltips
    hover.tooltips = [('Value', '@y'),
                      ('Controller Type', '@x')]

    # Defining dashboard layout
    l = layout([
            [p1, p2]
            
                ], sizing_mode='stretch_both')
    save(l)

    return(
        render_template(
                    'bar.html'
                        )
            )

if __name__ == '__main__':
    app.run(debug=True)
