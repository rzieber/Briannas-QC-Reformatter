from pathlib import Path
import pickle as pkl
import pandas as pd

# opening a pickle file
example = Path("/Users/rzieber/Downloads/B03_GoldenRidge_example_df.pkl")

with open(example, 'rb') as f:
    df_example = pkl.load(f)
    print(df_example.columns)
    print(df_example.head(20))
f.close()

# # writing to a pickle file
# export_df = Path('/Path/to/file/name_of_station_dataframe.pkl')

# with open(export_df, 'wb') as f: 
#     pkl.dump(df, f) # the dataframe to be exported as a pickle file
# f.close()