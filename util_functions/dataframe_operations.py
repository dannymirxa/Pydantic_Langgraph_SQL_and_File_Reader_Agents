import pandas as pd
from sqlalchemy import Engine, create_engine
import json
    
def create_dataframe_pd_json(engine: Engine, query: str):
    try:
        # The engine.connect() establishes a connection from the pool
        with engine.connect() as conn:
            # pd.read_sql executes the query against the connection
            # and returns the results as a Pandas DataFrame.
            df = pd.read_sql(sql=query, con=conn)
            return df.to_json()
    except Exception as e:
        # It's good practice to handle potential errors
        # and return a consistent error format.
        return json.dumps({"error": f"Error processing query results: {str(e)}", "data": []})

def create_dataframe_pd(engine: Engine, query: str):
    try:
        # The engine.connect() establishes a connection from the pool
        with engine.connect() as conn:
            # pd.read_sql executes the query against the connection
            # and returns the results as a Pandas DataFrame.
            df = pd.read_sql(sql=query, con=conn)
            return df
    except Exception as e:
        # It's good practice to handle potential errors
        # and return a consistent error format.
        return json.dumps({"error": f"Error processing query results: {str(e)}", "data": []})
    
# db_engine = create_engine('postgresql+psycopg2://chinook:chinook@localhost:5433/chinook_auto_increment')
    
# print(create_dataframe_pd(db_engine, "SELECT artist.name AS artist_name, SUM(invoice_line.unit_price * invoice_line.quantity) AS total_sales FROM artist JOIN album ON artist.artist_id = album.artist_id JOIN track ON album.album_id = track.album_id JOIN invoice_line ON track.track_id = invoice_line.track_id GROUP BY artist.name ORDER BY total_sales DESC;"))