import pandas as pd
import matplotlib
from datetime import datetime, timedelta
# prevents GUI output from matlab, since it causes errors and isnt needed
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from sqlalchemy.sql import text

def generate_and_recommend_visuals(dataset, x_col, y_col, z_col=None):
    """
    Args

    dataset -> pandas dataframe: a data frame object of the dataset to be visualised
    x_col, y_col, z_col -> pandas series: a column from the data set

    Returns

    visuals -> dictionary: a dictionary with keys as a visual names and values as the visual as a figure object
    recommended -> string: the name of the key of the recommended visual in the visuals dictionary
    """

    # check x_col and y_col is in the dataset
    if x_col not in dataset.columns or y_col not in dataset.columns:
        raise ValueError("x_col and y_col must be valid column names in the dataset.")
    
    # if a z axis is desired check its in the data set
    if z_col and z_col not in dataset.columns:
        raise ValueError("z_col must be a valid column name in the dataset.")
    
    # get types
    x_type = dataset[x_col].dtype
    y_type = dataset[y_col].dtype
    z_type = dataset[z_col].dtype if z_col else None # if z was desired
    
    # visual storing variables
    visuals = {}  # empty dict to add plots too
    recommended = None # recommended visual

    # scatter plot, if both columns are numeric and no z
    if pd.api.types.is_numeric_dtype(x_type) and pd.api.types.is_numeric_dtype(y_type):
        plt.figure(figsize=(10, 6))
        sns.scatterplot(data=dataset, x=x_col, y=y_col)
        plt.title("Scatter Plot")

        # save visual (gcf -> get current plot)
        visuals["scatter_plot"] = plt.gcf()
        plt.close()
        
        # if z_col and z_col numeric add color encoding
        if z_col and pd.api.types.is_numeric_dtype(z_type):
            plt.figure(figsize=(10, 6))
            scatter = plt.scatter(dataset[x_col], dataset[y_col], c=dataset[z_col], cmap='viridis', alpha=0.7)
            plt.colorbar(scatter, label=z_col)
            plt.title("Scatter Plot with Color Encoding")

            # save visual as a figure object
            visuals["scatter_with_color"] = plt.gcf()
            plt.close()
            recommended = "scatter_with_color"

    # line Plot for: numerical type against datetime type
    if pd.api.types.is_datetime64_any_dtype(x_type):
        plt.figure(figsize=(10, 6))
        sns.lineplot(data=dataset, x=x_col, y=y_col)
        plt.title("Time Series Line Plot")

        # save visual
        visuals["line_plot"] = plt.gcf()
        plt.close()

        # assign recommended if it hasnt been assigned yet
        recommended = recommended or "line_plot"

    # bar plot
    if pd.api.types.is_categorical_dtype(x_type) or dataset[x_col].nunique() < 20:
        plt.figure(figsize=(10, 6))
        sns.barplot(data=dataset, x=x_col, y=y_col)
        plt.title("Bar Plot")
        visuals["bar_plot"] = plt.gcf()
        plt.close()
        recommended = recommended or "bar_plot"

    # Box Plot
    if pd.api.types.is_numeric_dtype(y_type) and (pd.api.types.is_categorical_dtype(x_type) or dataset[x_col].nunique() < 20):
        plt.figure(figsize=(10, 6))
        sns.boxplot(data=dataset, x=x_col, y=y_col)
        plt.title("Box Plot")
        visuals["box_plot"] = plt.gcf()
        plt.close()
        recommended = recommended or "box_plot"

    # Count Plot
    if pd.api.types.is_categorical_dtype(x_type) and y_col is None:
        plt.figure(figsize=(10, 6))
        sns.countplot(data=dataset, x=x_col)
        plt.title("Count Plot")
        visuals["count_plot"] = plt.gcf()
        plt.close()
        recommended = recommended or "count_plot"

    return visuals, recommended



