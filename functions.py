import pandas as pd
import matplotlib
from flask import Flask
# prevents GUI output from matlab, since it causes errors and isnt needed
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from functools import wraps
from flask import session, flash, redirect, url_for


def process_data(df):
    """
    applies the new method from pandas which is very usefull for data processing, 
    documentation:

    https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.convert_dtypes.html

    this method is still experimental so it is not the most accurate.

    Args:
    df -> DataFrame: the data set to be processed

    Returns:
    df -> DataFrame: the processed data frame
    """

    # new convenient pandas method
    df = df.convert_dtypes()

    # remove leading spaces from string columns
    for column in df.columns:
        if df[column].dtype == 'string':
            df[column] = df[column].str.strip()

    return df


def get_data_report_data(data):
    """
    analyses the data set and outputs relevant information about the data set to be reported in the
    dashboard

    Args:
    data -> DataFrame: the data set

    Retruns:
    data_report -> dictionary: a dictionary containing  relevant information about the data set
    """
    data_report = {}

    # column names and data types
    data_report['col names'], data_report['col types'] = list(data.columns), list(data.dtypes)
    data_report['col data'] = pd.DataFrame({
        'Column Name': data_report['col names'],
        'Data Type': data_report['col types']
    })
    
    # colum and row numbers
    data_report['row num'], data_report['col num'] = data.shape
    
    return data_report


def generate_and_recommend_visuals(dataset, x_col, y_col, z_col=None):
    """
    Args:
        dataset (pandas.DataFrame): Dataset to visualize.
        x_col, y_col, z_col (str): Columns to visualize.

    Returns:
        visuals (dict): A dictionary with visual names as keys and figure objects as values.
        recommended (str): The recommended visual's key in the visuals dictionary.
    """
    if x_col not in dataset.columns:
        raise ValueError("x_col and y_col must be valid column names in the dataset.")
    if z_col and z_col not in dataset.columns:
        raise ValueError("z_col must be a valid column name in the dataset.")

    x_type, y_type, z_type = dataset[x_col].dtype, dataset[y_col].dtype if z_col else None, dataset[z_col].dtype if z_col else None
    visuals, recommendations = {}, []

    def create_visual(plot_type, plot_func, **kwargs):
        """Helper to create and store visuals with a customized dark theme."""
        # Custom dark theme settings
        plt.style.use("dark_background")  # Base dark background style
        plt.rcParams.update({
            "axes.facecolor": "#2B2B2B",  # Dark gray for plot background
            "axes.edgecolor": "#5A5A5A",  # Light gray for axis edges
            "axes.labelcolor": "white",   # White labels for better readability
            "grid.color": "#444444",      # Medium gray for grid lines
            "xtick.color": "lightgray",   # Light gray for x-tick labels
            "ytick.color": "lightgray",   # Light gray for y-tick labels
            "figure.facecolor": "#1E1E1E",  # Deep gray for figure background
            "text.color": "white",        # White for all text
            "legend.frameon": True,       # Enable legend frame
            "legend.facecolor": "#2E2E2E",  # Dark gray for legend background
            "legend.edgecolor": "#5A5A5A",  # Light gray for legend border
        })

        # Create the plot
        plt.figure(figsize=(10, 6))
        plot_func(**kwargs)
        plt.title(plot_type.replace("_", " ").title(), fontsize=14, color="white", pad=15)  # Title with spacing
        visuals[plot_type] = plt.gcf()
        recommendations.append(plot_type)
        plt.close()

    
    if pd.api.types.is_numeric_dtype(x_type) and pd.api.types.is_numeric_dtype(y_type):
        create_visual("scatter_plot", sns.scatterplot, data=dataset, x=x_col, y=y_col)
        if z_col and pd.api.types.is_numeric_dtype(z_type):
            create_visual("scatter_with_color", plt.scatter, x=dataset[x_col], y=dataset[y_col], c=dataset[z_col], cmap='viridis', alpha=0.7)

    if pd.api.types.is_datetime64_any_dtype(x_type):
        create_visual("line_plot", sns.lineplot, data=dataset, x=x_col, y=y_col)

    if pd.api.types.is_categorical_dtype(x_type) or dataset[x_col].nunique() < 20:
        create_visual("bar_plot", sns.barplot, data=dataset, x=x_col, y=y_col)
        create_visual("box_plot", sns.boxplot, data=dataset, x=x_col, y=y_col)

    if pd.api.types.is_categorical_dtype(x_type) and y_col is None:
        create_visual("count_plot", sns.countplot, data=dataset, x=x_col)

    if pd.api.types.is_numeric_dtype(x_type) and pd.api.types.is_numeric_dtype(y_type):
        create_visual("heatmap", sns.heatmap, data=dataset[[x_col, y_col]].corr(), annot=True, cmap='coolwarm')

    if pd.api.types.is_numeric_dtype(x_type):
        create_visual("histogram", sns.histplot, data=dataset, x=x_col, kde=True)

    if pd.api.types.is_numeric_dtype(x_type) and pd.api.types.is_numeric_dtype(y_type) and z_col:
        create_visual("bubble_chart", plt.scatter, x=dataset[x_col], y=dataset[y_col], s=dataset[z_col] * 50, alpha=0.7)

    if pd.api.types.is_categorical_dtype(x_type):
        create_visual("tree_map", sns.barplot, data=dataset, x=x_col, y=y_col)  # Tree maps would need a custom implementation in matplotlib

    return visuals, recommendations[0] if recommendations else None


def login_required(f):
    """
    login required decorater for later use
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('You must be logged in to access this page.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function









def generate_and_recommend_WIP(dataset, x_col=None, y_col=None):
    """
    Args:
        dataset (pandas.DataFrame): Dataset to visualize.
        x_col, y_col, z_col (str): Columns to visualize.

    Returns:
        visuals (dict): A dictionary with visual names as keys and figure objects as values.
        recommended (str): The recommended visual's key in the visuals dictionary.
    """
    # at least x_col or y_col should be selected
    if x_col not in dataset.columns and y_col not in dataset.columns:
        raise ValueError("x_col or y_col must be valid column names in the dataset.")

    visuals, recommendations = {}, []

    # helper sub functions
    def create_visual(plot_type, plot_func, **kwargs):
        """Helper to create and store visuals with a customized dark theme."""
        # Custom dark theme settings
        plt.style.use("dark_background")  # Base dark background style
        plt.rcParams.update({
            "axes.facecolor": "#2B2B2B",  # Dark gray for plot background
            "axes.edgecolor": "#5A5A5A",  # Light gray for axis edges
            "axes.labelcolor": "white",   # White labels for better readability
            "grid.color": "#444444",      # Medium gray for grid lines
            "xtick.color": "lightgray",   # Light gray for x-tick labels
            "ytick.color": "lightgray",   # Light gray for y-tick labels
            "figure.facecolor": "#1E1E1E",  # Deep gray for figure background
            "text.color": "white",        # White for all text
            "legend.frameon": True,       # Enable legend frame
            "legend.facecolor": "#2E2E2E",  # Dark gray for legend background
            "legend.edgecolor": "#5A5A5A",  # Light gray for legend border
        })

        # Create the plot
        plt.figure(figsize=(10, 6))
        plot_func(**kwargs)

        # get column names for axis names
        if 'x' in kwargs and isinstance(kwargs['x'], str):
            plt.xlabel(kwargs['x'], fontsize=12, color='white')
        if 'y' in kwargs and isinstance(kwargs['y'], str):
            plt.ylabel(kwargs['y'], fontsize=12, color='white')

        # Title with spacing
        plt.title(plot_type.replace("_", " ").title(), fontsize=14, color="white", pad=15)

        visuals[plot_type] = plt.gcf()
        recommendations.append(plot_type)
        plt.close()

    def is_integer_column(col):
        return pd.api.types.is_integer_dtype(col)
    
    def is_string_column(col):
        return pd.api.types.is_string_dtype(col)
    
    def is_float_column(col):
        return pd.api.types.is_float_dtype(col)
    
    def is_bool_column(col):
        return pd.api.types.is_bool(col)
    
    def is_date_time_column(col):
        return pd.api.types.is_datetime64_any_dtype(col)
    

    """
    1 dimensional cases
    """
    if (y_col == None) or (x_col == None) :
        print("Attempting 1D plotting")
        """
        x_col or y_col is an interger
        """
        # Histogram
        if x_col and is_integer_column(dataset[x_col]):
            create_visual(f"Histogram of {x_col}", sns.histplot, data=dataset, x=x_col)
        if y_col and is_integer_column(dataset[y_col]):
            create_visual(f"Histogram of {y_col}", sns.histplot, data=dataset, x=y_col)

        # Violin Plot
        if x_col and is_integer_column(dataset[x_col]):
            create_visual(f"Violin Plot of {x_col}", sns.violinplot, data=dataset, x=x_col)
        if y_col and is_integer_column(dataset[y_col]):
            create_visual(f"Violin Plot of {y_col}", sns.violinplot, data=dataset, x=y_col)

        # Count Plot (more suitable for categorical values, but can be applied to integers as well)
        if x_col and is_integer_column(dataset[x_col]):
            create_visual(f"Count Plot of {x_col}", sns.countplot, data=dataset, x=x_col)
        if y_col and is_integer_column(dataset[y_col]):
            create_visual(f"Count Plot of {y_col}", sns.countplot, data=dataset, x=y_col)

        """
        x_col or y_col is a string
        """

        # Countplot (Seaborn)
        if x_col and is_string_column(dataset[x_col]):
            create_visual(f"Count Plot of {x_col}", sns.countplot, data=dataset, x=x_col)
        if y_col and is_string_column(dataset[y_col]):
            create_visual(f"Count Plot of {y_col}", sns.countplot, data=dataset, x=y_col)


        """
        x_col or y_col is a float
        """
        # Histogram
        if x_col and is_float_column(dataset[x_col]):
            create_visual(f"Histogram of {x_col}", sns.histplot, data=dataset, x=x_col)
        if y_col and is_integer_column(dataset[y_col]):
            create_visual(f"Histogram of {y_col}", sns.histplot, data=dataset, x=y_col)

        # Boxplot
        if x_col and is_float_column(dataset[x_col]):
            create_visual(f"Boxplot of {x_col}", sns.boxplot, data=dataset, x=x_col)
        if y_col and is_integer_column(dataset[y_col]):
            create_visual(f"Boxplot of {y_col}", sns.boxplot, data=dataset, x=y_col)

        """
        x_col or y_col is a bool
        """
        # count Plot
        if x_col and is_bool_column(x_col):
            create_visual(f"Count Plot of {x_col}", sns.countplot, data=dataset, x=x_col)
        if y_col and is_integer_column(y_col):
            create_visual(f"Count Plot of {y_col}", sns.countplot, data=dataset, x=y_col)

        # histogram
        if x_col and is_bool_column(x_col):
            create_visual(f"Historgram of {x_col}", sns.histplot, data=dataset, x=x_col)
        if y_col and is_integer_column(y_col):
            create_visual(f"Histogram of {y_col}", sns.histplot, data=dataset, x=y_col)

        # Piechart
        if x_col and is_bool_column(x_col):
            create_visual(f"Piechart of {x_col}", plt.pie, data=dataset, x=x_col)
        if y_col and is_integer_column(y_col):
            create_visual(f"Piechart of {y_col}", plt.pie, data=dataset, x=y_col)

    return visuals, recommendations[0] if recommendations else None