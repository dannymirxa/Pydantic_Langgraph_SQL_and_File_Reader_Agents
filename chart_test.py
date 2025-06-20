import plotly.express as px
import pandas as pd
import io 
query_results_json= """[
                        {
                            "artist_id": 150,
                            "artist_name": "U2",
                            "total_sales": 91
                        },
                        {
                            "artist_id": 22,
                            "artist_name": "Led Zeppelin",
                            "total_sales": 87
                        },
                        {
                            "artist_id": 90,
                            "artist_name": "Iron Maiden",
                            "total_sales": 54
                        },
                        {
                            "artist_id": 58,
                            "artist_name": "Deep Purple",
                            "total_sales": 44
                        },
                        {
                            "artist_id": 76,
                            "artist_name": "Creedence Clearwater Revival",
                            "total_sales": 37
                        },
                        {
                            "artist_id": 51,
                            "artist_name": "Queen",
                            "total_sales": 37
                        },
                        {
                            "artist_id": 52,
                            "artist_name": "Kiss",
                            "total_sales": 31
                        },
                        {
                            "artist_id": 152,
                            "artist_name": "Van Halen",
                            "total_sales": 29
                        },
                        {
                            "artist_id": 88,
                            "artist_name": "Guns N Roses",
                            "total_sales": 26
                        },
                        {
                            "artist_id": 118,
                            "artist_name": "Pearl Jam",
                            "total_sales": 26
                        },
                        {
                            "artist_id": 144,
                            "artist_name": "The Who",
                            "total_sales": 19
                        },
                        {
                            "artist_id": 142,
                            "artist_name": "The Rolling Stones",
                            "total_sales": 18
                        },
                        {
                            "artist_id": 84,
                            "artist_name": "Foo Fighters",
                            "total_sales": 17
                        },
                        {
                            "artist_id": 127,
                            "artist_name": "Red Hot Chili Peppers",
                            "total_sales": 17
                        },
                        {
                            "artist_id": 139,
                            "artist_name": "The Cult",
                            "total_sales": 16
                        },
                        {
                            "artist_id": 1,
                            "artist_name": "AC/DC",
                            "total_sales": 16
                        },
                        {
                            "artist_id": 132,
                            "artist_name": "Soundgarden",
                            "total_sales": 15
                        },
                        {
                            "artist_id": 124,
                            "artist_name": "R.E.M.",
                            "total_sales": 14
                        },
                        {
                            "artist_id": 114,
                            "artist_name": "Ozzy Osbourne",
                            "total_sales": 14
                        },
                        {
                            "artist_id": 100,
                            "artist_name": "Lenny Kravitz",
                            "total_sales": 13
                        },
                        {
                            "artist_id": 111,
                            "artist_name": "O Terço",
                            "total_sales": 13
                        },
                        {
                            "artist_id": 110,
                            "artist_name": "Nirvana",
                            "total_sales": 12
                        },
                        {
                            "artist_id": 59,
                            "artist_name": "Santana",
                            "total_sales": 12
                        },
                        {
                            "artist_id": 134,
                            "artist_name": "Stone Temple Pilots",
                            "total_sales": 10
                        },
                        {
                            "artist_id": 3,
                            "artist_name": "Aerosmith",
                            "total_sales": 10
                        },
                        {
                            "artist_id": 126,
                            "artist_name": "Raul Seixas",
                            "total_sales": 10
                        },
                        {
                            "artist_id": 130,
                            "artist_name": "Skank",
                            "total_sales": 10
                        },
                        {
                            "artist_id": 82,
                            "artist_name": "Faith No More",
                            "total_sales": 9
                        },
                        {
                            "artist_id": 94,
                            "artist_name": "Jimi Hendrix",
                            "total_sales": 8
                        },
                        {
                            "artist_id": 105,
                            "artist_name": "Men At Work",
                            "total_sales": 8
                        },
                        {
                            "artist_id": 115,
                            "artist_name": "Page & Plant",
                            "total_sales": 8
                        },
                        {
                            "artist_id": 55,
                            "artist_name": "David Coverdale",
                            "total_sales": 8
                        },
                        {
                            "artist_id": 4,
                            "artist_name": "Alanis Morissette",
                            "total_sales": 8
                        },
                        {
                            "artist_id": 141,
                            "artist_name": "The Police",
                            "total_sales": 7
                        },
                        {
                            "artist_id": 5,
                            "artist_name": "Alice In Chains",
                            "total_sales": 7
                        },
                        {
                            "artist_id": 78,
                            "artist_name": "Def Leppard",
                            "total_sales": 7
                        },
                        {
                            "artist_id": 92,
                            "artist_name": "Jamiroquai",
                            "total_sales": 6
                        },
                        {
                            "artist_id": 8,
                            "artist_name": "Audioslave",
                            "total_sales": 6
                        },
                        {
                            "artist_id": 153,
                            "artist_name": "Velvet Revolver",
                            "total_sales": 6
                        },
                        {
                            "artist_id": 128,
                            "artist_name": "Rush",
                            "total_sales": 6
                        },
                        {
                            "artist_id": 102,
                            "artist_name": "Marillion",
                            "total_sales": 5
                        },
                        {
                            "artist_id": 117,
                            "artist_name": "Paul DIanno",
                            "total_sales": 5
                        },
                        {
                            "artist_id": 179,
                            "artist_name": "Scorpions",
                            "total_sales": 5
                        },
                        {
                            "artist_id": 136,
                            "artist_name": "Terry Bozzio, Tony Levin & Steve Stevens",
                            "total_sales": 5
                        },
                        {
                            "artist_id": 2,
                            "artist_name": "Accept",
                            "total_sales": 5
                        },
                        {
                            "artist_id": 23,
                            "artist_name": "Frank Zappa & Captain Beefheart",
                            "total_sales": 4
                        },
                        {
                            "artist_id": 95,
                            "artist_name": "Joe Satriani",
                            "total_sales": 4
                        },
                        {
                            "artist_id": 120,
                            "artist_name": "Pink Floyd",
                            "total_sales": 4
                        },
                        {
                            "artist_id": 140,
                            "artist_name": "The Doors",
                            "total_sales": 4
                        },
                        {
                            "artist_id": 200,
                            "artist_name": "The Posies",
                            "total_sales": 1
                        },
                        {
                            "artist_id": 157,
                            "artist_name": "Dread Zeppelin",
                            "total_sales": 1
                        }
                            ]"""       

df = pd.read_json(io.StringIO(query_results_json))
# Chart: Total Sales by Artist

fig = px.bar(df, x='artist_name', y='total_sales', title='Total Sales by Artist', labels={'artist_name': 'Artist', 'total_sales': 'Total Sales'})

fig.write_html('templates/chart_0.html')

import plotly.express as px
# df is assumed to be pre-loaded with the data
# # Vertical Bar Chart

fig1 = px.bar(df, x='artist_name', y='total_sales', title='Total Sales by Artist (Vertical Bar Chart)')

fig1.write_html('templates/chart_0.html')

import plotly.express as px
# df is assumed to be pre-loaded with the data
# # Horizontal Bar Chart
fig2 = px.bar(df, x='total_sales', y='artist_name', orientation='h', title='Total Sales by Artist (Horizontal Bar Chart)')

fig2.write_html('templates/chart_1.html')