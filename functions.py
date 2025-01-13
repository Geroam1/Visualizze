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
    
    x = dataset[x_col] if x_col else None
    y = dataset[y_col] if y_col else None
    z = dataset[z_col] if z_col else None

    x_type, y_type, z_type = x.dtype, y.dtype if z_col else None, dataset[z_col].dtype if z_col else None
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
            create_visual("scatter_with_color", plt.scatter, x=x, y=y, c=dataset[z_col], cmap='viridis', alpha=0.7)

    if pd.api.types.is_datetime64_any_dtype(x_type):
        create_visual("line_plot", sns.lineplot, data=dataset, x=x_col, y=y_col)

    if pd.api.types.is_categorical_dtype(x_type) or x.nunique() < 20:
        create_visual("bar_plot", sns.barplot, data=dataset, x=x_col, y=y_col)
        create_visual("box_plot", sns.boxplot, data=dataset, x=x_col, y=y_col)

    if pd.api.types.is_categorical_dtype(x_type) and y_col is None:
        create_visual("count_plot", sns.countplot, data=dataset, x=x_col)

    if pd.api.types.is_numeric_dtype(x_type) and pd.api.types.is_numeric_dtype(y_type):
        create_visual("heatmap", sns.heatmap, data=dataset[[x_col, y_col]].corr(), annot=True, cmap='coolwarm')

    if pd.api.types.is_numeric_dtype(x_type):
        create_visual("histogram", sns.histplot, data=dataset, x=x_col, kde=True)

    if pd.api.types.is_numeric_dtype(x_type) and pd.api.types.is_numeric_dtype(y_type) and z_col:
        create_visual("bubble_chart", plt.scatter, x=x, y=y, s=dataset[z_col] * 50, alpha=0.7)

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
    using the dataset and the column names, this function will generate every hard coded plot code for each situation,
    such as attempting a scatter plot when both columns are int, or a bar plot when one is int and one is str, etc...

    so far only 4 column types are supported:
    int
    float
    str
    bool

    I tried my best to order the code optimally, whilest keeping it as simple as possible

    Args:
        dataset (pandas.DataFrame): dataset to visualize.
        x_col, y_col: column names to visualize.

    Returns:
        visuals (dict): A dictionary with visual names as keys and figure objects as values.
        recommended (str): A recommended visual's key in the visuals dictionary. (The first visual created in a case)
    """
    # at least x_col or y_col should be selected
    if x_col not in dataset.columns and y_col not in dataset.columns:
        raise ValueError("x_col or y_col must be valid column names in the dataset.")

    x = dataset[x_col] if x_col else None
    y = dataset[y_col] if y_col else None
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
    
    # 2 dimension seperate type checking functions
    def is_int_str(col1, col2):
        if is_integer_column(col1) and is_string_column(col2):
            return True
        elif is_integer_column(col2) and is_string_column(col1):
            return True
        return False
    
    def is_int_float(col1, col2):
        if is_integer_column(col1) and is_float_column(col2):
            return True
        elif is_integer_column(col2) and is_float_column(col1):
            return True
        return False

    def is_int_bool(col1, col2):
        if is_integer_column(col1) and is_bool_column(col2):
            return True
        elif is_integer_column(col2) and is_bool_column(col1):
            return True
        return False
    
    def is_str_float(col1, col2):
        if is_string_column(col1) and is_float_column(col2):
            return True
        elif is_string_column(col2) and is_float_column(col1):
            return True
        return False

    def is_str_bool(col1, col2):
        if is_string_column(col1) and is_bool_column(col2):
            return True
        elif is_string_column(col2) and is_bool_column(col1):
            return True
        return False

    def is_float_bool(col1, col2):
        if is_float_column(col1) and is_bool_column(col2):
            return True
        elif is_float_column(col2) and is_bool_column(col1):
            return True
        return False


    """
    1 dimensional cases
    """
    if (y_col == None) or (x_col == None) :
        print("Attempting 1D plotting")
        """
        x_col or y_col is an interger
        """
        # Histogram
        if x_col and is_integer_column(x):
            create_visual(f"Histogram of {x_col}", sns.histplot, data=dataset, x=x_col)
        if y_col and is_integer_column(y):
            create_visual(f"Histogram of {y_col}", sns.histplot, data=dataset, x=y_col)

        # Violin Plot
        if x_col and is_integer_column(x):
            create_visual(f"Violin Plot of {x_col}", sns.violinplot, data=dataset, x=x_col)
        if y_col and is_integer_column(y):
            create_visual(f"Violin Plot of {y_col}", sns.violinplot, data=dataset, x=y_col)

        # Count Plot (more suitable for categorical values, but can be applied to integers as well)
        if x_col and is_integer_column(x):
            create_visual(f"Count Plot of {x_col}", sns.countplot, data=dataset, x=x_col)
        if y_col and is_integer_column(y):
            create_visual(f"Count Plot of {y_col}", sns.countplot, data=dataset, x=y_col)

        """
        x_col or y_col is a string
        """
        # Pie chart
        if x_col and is_string_column(x):
            create_visual(f"Pie Chart of {x_col}", plt.pie, x=x.value_counts(), labels = x.value_counts().index, autopct='%1.1f%%', startangle=90, wedgeprops={'edgecolor': 'black'}, textprops={'color': 'gray'})
        if y_col and is_string_column(y):
            create_visual(f"Pie Chart of {y_col}", plt.pie, x=y.value_counts(), labels = y.value_counts().index, autopct='%1.1f%%', startangle=90, wedgeprops={'edgecolor': 'black'}, textprops={'color': 'gray'})
        
        # Countplot
        if x_col and is_string_column(x):
            create_visual(f"Count Plot of {x_col}", sns.countplot, data=dataset, x=x_col)
        if y_col and is_string_column(y):
            create_visual(f"Count Plot of {y_col}", sns.countplot, data=dataset, x=y_col)
        

        """
        x_col or y_col is a float
        """
        # Histogram
        if x_col and is_float_column(x):
            create_visual(f"Histogram of {x_col}", sns.histplot, data=dataset, x=x_col)
        if y_col and is_integer_column(y):
            create_visual(f"Histogram of {y_col}", sns.histplot, data=dataset, x=y_col)

        # Boxplot
        if x_col and is_float_column(x):
            create_visual(f"Boxplot of {x_col}", sns.boxplot, data=dataset, x=x_col)
        if y_col and is_integer_column(y):
            create_visual(f"Boxplot of {y_col}", sns.boxplot, data=dataset, x=y_col)

        """
        x_col or y_col is a bool
        """
        # count Plot
        if x_col and is_bool_column(x):
            create_visual(f"Count Plot of {x_col}", sns.countplot, data=dataset, x=x_col)
        if y_col and is_integer_column(y):
            create_visual(f"Count Plot of {y_col}", sns.countplot, data=dataset, x=y_col)

        # histogram
        if x_col and is_bool_column(x):
            create_visual(f"Historgram of {x_col}", sns.histplot, data=dataset, x=x_col)
        if y_col and is_integer_column(y):
            create_visual(f"Histogram of {y_col}", sns.histplot, data=dataset, x=y_col)

        # piechart
        if x_col and is_bool_column(x):
            create_visual(f"Piechart of {x_col}", plt.pie, data=dataset, x=x_col)
        if y_col and is_integer_column(y):
            create_visual(f"Piechart of {y_col}", plt.pie, data=dataset, x=y_col)

    """
    2 dimensional same type cases (4 cases) and 2 dimensional different type cases (6 cases)
    """
    if x_col and y_col:
        """
        x_col and y_col is interger
        """
        if is_integer_column(x) and is_integer_column(y):
            # scatter plot
            create_visual(f"Scatter plot of {x_col} against {y_col}", plot_func=plt.scatter, x=x, y=y)
            # line plot
            create_visual(f"Line plot of {x_col} against {y_col}", plot_func=sns.lineplot, data=dataset, x=x, y=y)
            # bar plot
            create_visual(f"Bar plot of {x_col} against {y_col}", plot_func=sns.barplot, data=dataset, x=x, y=y)

        """
        x_col and y_col is float
        """
        if is_float_column(x) and is_float_column(y):
            # scatter plot
            create_visual(f"Scatter plot of {x_col} against {y_col}", plot_func=plt.scatter, x=x, y=y)
            # hexbin plot
            create_visual(f"Hexbin plot of {x_col} against {y_col}", plot_func=plt.hexbin, x=x, y=y, gridsize=30, cmap='viridis')
            # KDE plot (kernal density estimator)
            create_visual(f"KDE plot of {x_col} against {y_col}", plot_func=sns.kdeplo, x=x, y=y, cmap="Blues", fill=True, thresh=0, levels=100)

        """
        x_col and y_col is string
        """
        if is_string_column(x) and is_string_column(y):
            # stacked bar plot, very hard to think of any other plots with just two string columns
            cross_tab = pd.crosstab(x, y)
            cross_tab.plot(kind='bar', stacked=True, colormap='viridis')
            create_visual(f"Stacked bar plot of {x_col} against {y_col}", plot_func=cross_tab.plot, kind='bar', stacked=True, colormap='viridis')

        """
        x_col and y_col is bool
        """
        if is_bool_column(x) and is_bool_column(y):
            # couldnt think or find any relevant plots for two booleans
            pass
    

        """
        x_col and y_col are int and str non-respectufully
        """
        if is_int_str(x, y):
            # bar plot
            create_visual(f"Bar plot of {x_col} against {y_col}", plot_func=sns.barplot, data=dataset, x=x_col, y=y_col)
            # box plot
            create_visual(f"Box plot of {x_col} against {y_col}", plot_func=sns.boxplot, data=dataset, x=x_col, y=y_col)
            # violin plot
            create_visual(f"violin plot of {x_col} against {y_col}", plot_func=sns.violinplot, data=dataset, x=x_col, y=y_col)

        """
        x_col and y_col are int and float non-respectufully
        """
        if is_int_float(x, y):
            # scatter plot
            create_visual(f"Scatter plot of {x_col} against {y_col}", plot_func=sns.scatterplot, data=dataset, x=x_col, y=y_col)
            # hexbin plot
            create_visual(f"Hexbin plot of {x_col} against {y_col}", plot_func=plt.hexbin, x=x, y=y, gridsize=30, cmap='Blues')
            # regression plot
            create_visual(f"Regression plot of {x_col} against {y_col}", plot_func=sns.regplot, data=dataset, x=x_col, y=y_col, line_kws={'color': 'red'})

        """
        x_col and y_col are int and bool non-respectufully
        """
        if is_int_bool(x, y):
            # bar plot
            create_visual(f"Bar plot of {x_col} against {y_col}", plot_func=sns.barplot, data=dataset, x=x_col, y=y_col)
            # box plot
            create_visual(f"Box plot of {x_col} against {y_col}", plot_func=sns.boxplot, data=dataset, x=x_col, y=y_col)
            # violin plot
            create_visual(f"violin plot of {x_col} against {y_col}", plot_func=sns.violinplot, data=dataset, x=x_col, y=y_col)

        """
        x_col and y_col are string and float non-respectufully
        """
        if is_str_float(x, y):
            # bar plot
            create_visual(f"Bar plot of {x_col} against {y_col}", plot_func=sns.barplot, data=dataset, x=x_col, y=y_col)
            # box plot
            create_visual(f"Box plot of {x_col} against {y_col}", plot_func=sns.boxplot, data=dataset, x=x_col, y=y_col)
            # violin plot
            create_visual(f"violin plot of {x_col} against {y_col}", plot_func=sns.violinplot, data=dataset, x=x_col, y=y_col)

        """
        x_col and y_col are string and bool non-respectufully
        """
        if is_str_bool(x, y):
            # count plot
            create_visual(f"Count plot of {x_col} against {y_col}", plot_func=sns.countplot, data=dataset, x=x_col, y=y_col)
            # bar plot
            create_visual(f"Bar plot of {x_col} against {y_col}", plot_func=sns.barplot, data=dataset, x=x_col, y=y_col)
            # stacked bar plot
            crosstab = pd.crosstab(x, y)
            create_visual(f"Bar plot of {x_col} against {y_col}", plot_func=crosstab.plot.bar, stacked=True)

        """
        x_col and y_col are float and bool non-respectufully
        """
        if is_float_bool(x, y):
            # bar plot
            create_visual(f"Bar plot of {x_col} against {y_col}", plot_func=sns.barplot, data=dataset, x=x_col, y=y_col)
            # box plot
            create_visual(f"Box plot of {x_col} against {y_col}", plot_func=sns.boxplot, data=dataset, x=x_col, y=y_col)
            # violin plot
            create_visual(f"violin plot of {x_col} against {y_col}", plot_func=sns.violinplot, data=dataset, x=x_col, y=y_col)



        
    return visuals, recommendations[0] if recommendations else None