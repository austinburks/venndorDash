# %%
# Importing libraries

import os
from flask import (Flask,
                   render_template,
                   stream_with_context,
                   Response)
import pandas as pd
import requests
from bokeh.charts import (Bar,
                          show,
                          output_file,
                          save)
from bokeh.layouts import (layout,
                           widgetbox)
from bokeh.models import (ColumnDataSource,
                          DataRange1d,
                          Range1d,
                          VBox,
                          HBox,
                          Select,
                          HoverTool)
from bokeh.models.widgets import (DataTable,
                                  DateFormatter,
                                  TableColumn,
                                  Panel,
                                  Tabs)
from bokeh.palettes import Blues5
from bokeh.plotting import Figure
from bokeh.resources import INLINE, EMPTY
from bokeh.embed import components
import time
# Defining environment settings
app = Flask(__name__
            #,static_url_path='/static/'
            )
#app._static_folder = 'static'

#app.config.from_object(os.environ['APP_SETTINGS'])

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


    # %% Creating df defining the ratio of right swipes to left swipes
    df_right_left = pd.DataFrame(items)

    # Grouping by, and performing different aggregations
    df_right_left = df_right_left[['category',
                                   'nuSwipesRight',
                                   'nuSwipesLeft']].groupby(
                                      'category', as_index=False
                                          ).agg(
                                               {'nuSwipesRight': 'sum',
                                                'nuSwipesLeft': 'sum'
                                                })

    # Finding the ratio
    df_right_left['RightOverLeft'] = df_right_left['nuSwipesRight'].div(
                                        df_right_left['nuSwipesLeft'])

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
    #show(p1)
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

   # show(p2)
    # Defining dashboard layout

    p1_script, p1_div = components(p1)
    p2_script, p2_div = components(p2)
    
    js_resources = INLINE.render_js()
    css_resources = INLINE.render_css()
    
    tab1 = Panel(child=p1, title='Right-Left Ratio')
    tab2 = Panel(child=p2, title='Time on Controllers')

    tab_plot = Tabs(tabs=[tab1, tab2])    

    #show(tab_plot)
    #script, div = components(dict(plot=tabs))
    script, div = components(dict(plot=tab_plot))
    
    
    
    return(
        render_template(
                    'index.html',
                    script=script,
                    div=div,
                    js_resources=js_resources,
                    css_resources=css_resources


                        )
            )


@app.route('/sales-data')
def sales_data_stream():
    def generate():
        # Obtain both the matches and item JSONS
        matches = getItems(suffix='matches', apiKey=apiKey)
        items = getItems(suffix='items', apiKey=apiKey)

        # Convert both to dataframe
        match_df = pd.DataFrame(matches)
        item_df = pd.DataFrame(items)

        # Filter to only the relevant columns
        item_df = item_df[['_id', 'bought', 'minPrice']]
        item_df = item_df.rename(columns={'bought': 'bought_item'})

        match_df = match_df[['itemID', 'bought', 'matchedPrice', 'dateBought']]
        match_df['dateBought'] = pd.to_datetime(match_df['dateBought'],
                                                yearfirst=True,
                                                exact=False,
                                                format='%y-%m-%d')
        match_df = match_df.rename(columns={'bought': 'bought_match'})

        # Merge DFs on item ids
        matched_items = match_df.merge(item_df,
                                       how='left',
                                       left_on='itemID',
                                       right_on='_id')

        matched_items = matched_items.loc[matched_items['bought_match'] == 1]
        matched_items['Profit'] = (matched_items['matchedPrice'] -
                                   matched_items['minPrice'])
        matched_items = matched_items.reset_index(drop=True)

        output_file('templates/sales-data.html')

        source = ColumnDataSource(matched_items)

        columns = [
            TableColumn(field="dateBought",
                        title="Date",
                        formatter=DateFormatter(format='dd/mm/yy')
                        ),
            TableColumn(field="matchedPrice",
                        title="Matched Price"),
            TableColumn(field="minPrice",
                        title="Posted Price"),
            TableColumn(field="Profit",
                        title="Profit")
        ]
        data_table = DataTable(source=source,
                               columns=columns,
                               width=600,
                               height=500)

        save(widgetbox(data_table))
        #t = app.jinja_environment.get_template(name='sales-data.html')
        #return(t)
        return(render_template('sales-data.html'))

    return(Response(stream_with_context(generate())))

if __name__ == '__main__':
    app.run(debug=True)
