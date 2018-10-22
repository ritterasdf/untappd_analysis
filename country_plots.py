# -*- coding: utf-8 -*-
"""
Created on Wed Oct 17 20:56:38 2018

@author: Andreas Ritter, ritterasdf@gmail.com
goal: get data from exported untappd json, display it differently
"""

#%% obligatory imports
import pandas as pd
import numpy as np
import scipy as sp
import plotly
import plotly.plotly as py
import plotly.graph_objs as go
import plotly.tools as tls
import math
from functools import reduce
import operator

#%% fixed values
#lowest number of ratings to consider a country with
min_ratings = 10; 
#number of columns displayed next to each other
col_num = 8;
#dimensions in pixels of the figure on the website
page_height = 900
page_width = 1800

#%% load json data file
allRatings_df = pd.read_json('./userData.json')
#convert ratings to numeric values
allRatings_df['rating_score'] = allRatings_df['rating_score'].apply(pd.to_numeric,errors='coerce')

#%% find all countries and act on them
allCountries = pd.unique(allRatings_df['brewery_country'])
valid_ratings = np.array(allRatings_df['rating_score'].notnull())
total_ratings = len(allRatings_df[valid_ratings])

#convert weird json strings to proper strings
rating_range = [x/100 for x in range(0,525,25)]
rating_strings = [str(x) for x in rating_range]

#dict to hold all ratings by valid countries
country_ratings = {}
country_ratings['others'] = pd.Series([0] * len(rating_range),index=rating_range)
country_ratings['overall'] = pd.Series([0] * len(rating_range),index=rating_range)

#find occurences of each rating for each country
for country in list(allCountries):
    this_index = np.array(allRatings_df['brewery_country']==country) & valid_ratings
    this_number = len(allRatings_df[this_index])
    print('%s has %i ratings at %0.2f%%' % 
          (country,this_number,this_number/total_ratings*100))
    if this_number >= min_ratings:
        country_ratings[country] = allRatings_df[this_index]['rating_score'].value_counts()
    else:
        country_ratings['others'] = country_ratings['others'].add(allRatings_df[this_index]['rating_score'].value_counts(),fill_value=0)
    country_ratings['overall'] = country_ratings['overall'].add(allRatings_df[this_index]['rating_score'].value_counts(),fill_value=0)
        
#make into one dataframe
country_df = pd.DataFrame(country_ratings,index=rating_range)
country_df = country_df.fillna(0)

#make distinct colors for each country
country_colors = ['hsl('+str(h)+',50%'+',50%)' for h in np.linspace(0, 360, len(country_df.columns))]

#%% plot
#sort column names by total number of ratings
ordered_countries = [country_df.columns[i] for i in 
        np.argsort([sum(vals) for names, vals in country_df.iteritems()])
        ][::-1]
titles = ordered_countries.copy()

#calculate averages and medians
unfolded = dict()
medians = pd.Series()
averages = pd.Series()
percentiles = pd.DataFrame()
for i,country_name in enumerate(ordered_countries):
    unfolded[country_name] = reduce(operator.add,[int(times)*[rating] for j,(rating,times) in enumerate(zip(country_df[country_name].index,country_df[country_name]))])
    medians[country_name] = np.median(unfolded[country_name])
    averages[country_name] = np.average(unfolded[country_name])
    percentiles[country_name] = np.percentile(unfolded[country_name],[25,75])

#make bar charts and add them to list of all of them    
data = list()
for i,country_name in enumerate(ordered_countries):
    data.append(go.Bar(x = rating_range,
                       y = country_df[country_name],
                       name = country_name,
                       marker=dict(color = country_colors[i])))
    titles[i] = (country_name)
    
#make the subplot figure
fig = tls.make_subplots(rows=math.ceil(len(ordered_countries)/col_num)+1, 
                          cols=col_num, 
                          subplot_titles=titles) 
       
#add each bar plot to subplot figure and make it prettier along the way
labels = list()
boxes = list()
for i,country_name in enumerate(ordered_countries):
    fig.append_trace(data[i], math.ceil((i+1)/col_num), i%col_num+1)
    fig['layout']['xaxis'+str(i+1)] = dict(
        anchor = 'y'+str(i+1),
        domain = fig['layout']['xaxis'+str(i+1)]['domain'],
        automargin = True,
        ticks='outside',
        range = [0,5],
        tick0 = 0,
        dtick = 0.5,
        title='rating',
        tickwidth=1,
        tickangle = 45,
        )
    fig['layout']['yaxis'+str(i+1)] = dict(
        anchor = 'x'+str(i+1),
        domain = fig['layout']['yaxis'+str(i+1)]['domain'],
        automargin = True,
        ticks='outside',
        tick0 = 0,
        nticks = 5,
        title='beers',
        tickwidth=1,
        )
    labels.append(dict(
            x=2.5,
            y=1.05*max(country_df[country_name]),
            xref='x' + str(i+1),
            yref='y' + str(i+1),
            text= "n=" + '{:.0f}'.format(sum(country_df[country_name])),
            textangle=00,
            showarrow=False,
            arrowhead=0,
            ax=0,
            ay=0,
            align='center',
            ))
    boxes.append(dict(
            type = 'box',
            y=unfolded[country_name],
            name = country_name,
            marker = dict(
                    color = country_colors[i]),
            boxpoints = False,
            showlegend = False,))
            
#add the box and whisker plot
[fig.append_trace(box,math.ceil(len(ordered_countries)/col_num)+1,1) for box in boxes]
box_axes = math.ceil(len(ordered_countries)/col_num)*col_num
fig['layout']['xaxis'+str(box_axes+1)] = dict(
        anchor = 'y'+str(box_axes+1),
        domain = (0,1),
        automargin = True,
        )
fig['layout']['yaxis'+str(box_axes+1)] = dict(
        anchor = 'x'+str(box_axes+1),
        domain = fig['layout']['yaxis'+str(box_axes+1)]['domain'],
        automargin = True,
        ticks='outside',
        tick0 = 0,
        dtick = 1,
        title='ratings',
        tickwidth=1,
        )

#add the extra labels    
fig['layout']['annotations'] = fig['layout']['annotations'] + tuple(labels) 


#add title
fig['layout'].update(height=page_height, width=page_width, 
   title='Untappd ratings by country',
   showlegend=False)

#plot, save, open website
plotly.offline.plot(fig,auto_open=True)
#plotly.offline.plot(boxes,auto_open=True)


#add box and whisker

