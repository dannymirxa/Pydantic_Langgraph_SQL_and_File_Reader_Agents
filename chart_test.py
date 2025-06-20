import plotly.express as px
import pandas as pd
import io 
query_results_json= "[{\"artist_name\": \"U2\", \"sales_count\": 91}, {\"artist_name\": \"Led Zeppelin\", \"sales_count\": 87}, {\"artist_name\": \"Iron Maiden\", \"sales_count\": 54}, {\"artist_name\": \"Deep Purple\", \"sales_count\": 44}, {\"artist_name\": \"Queen\", \"sales_count\": 37}, {\"artist_name\": \"Creedence Clearwater Revival\", \"sales_count\": 37}, {\"artist_name\": \"Kiss\", \"sales_count\": 31}, {\"artist_name\": \"Van Halen\", \"sales_count\": 29}, {\"artist_name\": \"Pearl Jam\", \"sales_count\": 26}, {\"artist_name\": \"Guns N' Roses\", \"sales_count\": 26}]"     

df = pd.read_json(io.StringIO(query_results_json))
# Chart: Total Sales by Artist

# fig = px.bar(df, x='artist_name', y='total_sales', title='Total Sales by Artist', labels={'artist_name': 'Artist', 'total_sales': 'Total Sales'})

# fig.write_html('templates/chart_0.html')

# import plotly.express as px
# # df is assumed to be pre-loaded with the data
# # # Vertical Bar Chart

# fig1 = px.bar(df, x='artist_name', y='total_sales', title='Total Sales by Artist (Vertical Bar Chart)')

# fig1.write_html('templates/chart_0.html')

# import plotly.express as px
# # df is assumed to be pre-loaded with the data
# # # Horizontal Bar Chart
# fig2 = px.bar(df, x='total_sales', y='artist_name', orientation='h', title='Total Sales by Artist (Horizontal Bar Chart)')

# fig2.write_html('templates/chart_1.html')

import plotly.express as px
# df is assumed to be pre-loaded with the data

# Bar chart for sales count by artist
fig1 = px.bar(df, x='artist_name', y='sales_count', title='Sales Count by Artist')
fig1.write_html('templates/chart_0.html')

import plotly.express as px
# df is assumed to be pre-loaded with the data

# Scatter plot for sales count by artist
fig2 = px.scatter(df, x='artist_name', y='sales_count', title='Sales Count by Artist')
fig2.write_html('templates/chart_1.html')