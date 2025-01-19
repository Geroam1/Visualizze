import pandas as pd
import matplotlib
# prevents GUI output from matlab, since it causes errors and isnt needed
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd


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
        return None, None

    print(x_col)
    x = dataset[x_col] if x_col in dataset.columns else None
    y = dataset[y_col] if y_col in dataset.columns else None
    visuals, recommendations = {}, []

    # helper sub functions
    def create_visual(plot_title, plot_func, **kwargs):
        """ 
        plotting function to that will be run a lot, so it is used to simplify the code to just one line

        Args:
        plot_title -> str: The title of the plot

        plot_func -> function: the plotting function this function will use

        **kwargs -> dictionary of arguments: 
        **kwargs allows me to input any number of arguments I want, these
        arguments will the arguements for the plotting function. Since there are many different plotting functions
        they dont all use the same args, some want x as a column name, some what x as a column itself, some plots
        want unusal args. this allows me to just keep everything within this create visual function and simplify
        the codes readability.
        """

        # styling for the visual, written by chatgpt to not waste time on python art
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

        # initialize size of the plot
        plt.figure(figsize=(10, 6))

        # run the plot function with its arguments
        plot_func(**kwargs)

        # set the columns names as the labels if applicable
        if 'x' in kwargs:
            # if kwargs has a col name as input
            if isinstance(kwargs['x'], str):
                plt.xlabel(kwargs['x'], fontsize=12, color='white')

            # if kawrgs has the panda series column itself as input
            elif isinstance(kwargs['x'], pd.Series) and kwargs['x'].name:
                plt.xlabel(kwargs['x'].name, fontsize=12, color='white')

        if 'y' in kwargs:
            if isinstance(kwargs['y'], str):
                plt.ylabel(kwargs['y'], fontsize=12, color='white')
            elif isinstance(kwargs['y'], pd.Series) and kwargs['y'].name:
                plt.ylabel(kwargs['y'].name, fontsize=12, color='white')


        # set the title with some styling
        plt.title(plot_title.replace("_", " ").title(), fontsize=14, color="white", pad=15)

        # add the created visual to the visuals dictionary to send to the route server
        visuals[plot_title] = plt.gcf()
        recommendations.append(plot_title) # append it to the recomendations list, the first plot in this list will be "recommended"
        plt.close()

    # 1 dimension type checking functions
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
        """
        x_col or y_col is an interger
        """
        # histogram
        if x_col and is_integer_column(x):
            create_visual(f"Histogram of {x_col}", sns.histplot, data=dataset, x=x_col)
        if y_col and is_integer_column(y):
            create_visual(f"Histogram of {y_col}", sns.histplot, data=dataset, x=y_col)

        # violin Plot
        if x_col and is_integer_column(x):
            create_visual(f"Violin Plot of {x_col}", sns.violinplot, data=dataset, x=x_col)
        if y_col and is_integer_column(y):
            create_visual(f"Violin Plot of {y_col}", sns.violinplot, data=dataset, x=y_col)

        # count plot (more suitable for categorical values but can be applied to integers as well)
        if x_col and is_integer_column(x):
            create_visual(f"Count Plot of {x_col}", sns.countplot, data=dataset, x=x_col)
        if y_col and is_integer_column(y):
            create_visual(f"Count Plot of {y_col}", sns.countplot, data=dataset, x=y_col)

        # box plot
        if x_col and is_integer_column(x):
            create_visual(f"Box Plot of {x_col}", sns.boxplot, data=dataset, x=x_col)
        if y_col and is_integer_column(y):
            create_visual(f"Box Plot of {y_col}", sns.boxplot, data=dataset, x=y_col)

        # strip plot
        if x_col and is_integer_column(x):
            create_visual(f"Strip Plot of {x_col}", sns.stripplot, data=dataset, x=x_col)
        if y_col and is_integer_column(y):
            create_visual(f"Strip Plot of {y_col}", sns.stripplot, data=dataset, x=y_col)

        # KDE (Kernel Density Estimator)
        if x_col and is_integer_column(x):
            create_visual(f"KDE Plot of {x_col}", sns.kdeplot, data=dataset, x=x_col)
        if y_col and is_integer_column(y):
            create_visual(f"KDE Plot of {y_col}", sns.kdeplot, data=dataset, x=y_col)

        # rug plot
        if x_col and is_integer_column(x):
            create_visual(f"Rug Plot of {x_col}", sns.rugplot, data=dataset, x=x_col)
        if y_col and is_integer_column(y):
            create_visual(f"Rug Plot of {y_col}", sns.rugplot, data=dataset, x=y_col)

        # swarm plot
        if x_col and is_integer_column(x):
            create_visual(f"Swarm Plot of {x_col}", sns.swarmplot, data=dataset, x=x_col)
        if y_col and is_integer_column(y):
            create_visual(f"Swarm Plot of {y_col}", sns.swarmplot, data=dataset, x=y_col)

        # ECDF plot (Empirical Cumulative Distribution Function)
        if x_col and is_integer_column(x):
            create_visual(f"ECDF Plot of {x_col}", sns.ecdfplot, data=dataset, x=x_col)
        if y_col and is_integer_column(y):
            create_visual(f"ECDF Plot of {y_col}", sns.ecdfplot, data=dataset, x=y_col)


        """
        x_col or y_col is a string
        """
        # pie chart
        if x_col and is_string_column(x):
            create_visual(f"Pie Chart of {x_col}", plt.pie, x=x.value_counts(), labels = x.value_counts().index, autopct='%1.1f%%', startangle=90, wedgeprops={'edgecolor': 'black'}, textprops={'color': 'gray'})
        if y_col and is_string_column(y):
            create_visual(f"Pie Chart of {y_col}", plt.pie, x=y.value_counts(), labels = y.value_counts().index, autopct='%1.1f%%', startangle=90, wedgeprops={'edgecolor': 'black'}, textprops={'color': 'gray'})
        
        # countplot
        if x_col and is_string_column(x):
            create_visual(f"Count Plot of {x_col}", sns.countplot, data=dataset, x=x_col)
        if y_col and is_string_column(y):
            create_visual(f"Count Plot of {y_col}", sns.countplot, data=dataset, x=y_col)

        # strip plot
        if x_col and is_string_column(x):
            create_visual(f"Strip Plot of {x_col}", sns.stripplot, data=dataset, x=x_col, y=dataset[x_col])
        if y_col and is_string_column(y):
            create_visual(f"Strip Plot of {y_col}", sns.stripplot, data=dataset, x=y_col, y=dataset[y_col])

        # swarm plot
        if x_col and is_string_column(x):
            create_visual(f"Swarm Plot of {x_col}", sns.swarmplot, data=dataset, x=x_col, y=dataset[x_col])
        if y_col and is_string_column(y):
            create_visual(f"Swarm Plot of {y_col}", sns.swarmplot, data=dataset, x=y_col, y=dataset[y_col])


        """
        x_col or y_col is a float
        """
        # histogram
        if x_col and is_float_column(x):
            create_visual(f"Histogram of {x_col}", sns.histplot, data=dataset, x=x_col)
        if y_col and is_integer_column(y):
            create_visual(f"Histogram of {y_col}", sns.histplot, data=dataset, x=y_col)

        # boxplot
        if x_col and is_float_column(x):
            create_visual(f"Boxplot of {x_col}", sns.boxplot, data=dataset, x=x_col)
        if y_col and is_integer_column(y):
            create_visual(f"Boxplot of {y_col}", sns.boxplot, data=dataset, x=y_col)

        # violin plot
        if x_col and is_float_column(x):
            create_visual(f"Violin Plot of {x_col}", sns.violinplot, data=dataset, x=x_col)
        if y_col and is_float_column(y):
            create_visual(f"Violin Plot of {y_col}", sns.violinplot, data=dataset, x=y_col)

        # KDE plot
        if x_col and is_float_column(x):
            create_visual(f"Density Plot of {x_col}", sns.kdeplot, data=dataset, x=x_col)
        if y_col and is_float_column(y):
            create_visual(f"KDE Plot of {y_col}", sns.kdeplot, data=dataset, x=y_col)

        # barplot
        if x_col and is_float_column(x):
            create_visual(f"Bar Plot of {x_col} against the mean", sns.barplot, data=dataset, x=x_col, y=dataset[x_col].mean())
        if y_col and is_float_column(y):
            create_visual(f"Bar Plot of {y_col}", sns.barplot, data=dataset, x=y_col, y=dataset[y_col].mean())

        # swarm plot
        if x_col and is_float_column(x):
            create_visual(f"Swarm Plot of {x_col}", sns.swarmplot, data=dataset, x=x_col)
        if y_col and is_float_column(y):
            create_visual(f"Swarm Plot of {y_col}", sns.swarmplot, data=dataset, x=y_col)

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
            create_visual(f"Scatter plot of {x_col} against {y_col}", plot_func=sns.scatterplot, data=dataset, x=x_col, y=y_col)
            # line plot
            create_visual(f"Line plot of {x_col} against {y_col}", plot_func=sns.lineplot, data=dataset, x=x, y=y)
            # bar plot
            create_visual(f"Bar plot of {x_col} against {y_col}", plot_func=sns.barplot, data=dataset, x=x, y=y)
            # correlation matrix heatmap
            correlation_matrix = dataset[[x_col, y_col]].corr()
            create_visual(f"correlation matrix heatmap of {x_col} and {y_col}", sns.heatmap, data=correlation_matrix, annot=True, cmap='coolwarm', linewidths=0.5)
            # box plot
            create_visual(f"Boxplot of {x_col} and {y_col}", sns.boxplot, data=dataset, x=x_col, y=y_col)
            # violin plot
            create_visual(f"Violin Plot of {x_col} and {y_col}", sns.violinplot, data=dataset, x=x_col, y=y_col)
            # linear regression plot
            create_visual(f"Linear Regression Plot of {x_col} and {y_col}", sns.regplot, data=dataset, x=x_col, y=y_col)

        """
        x_col and y_col is float
        """
        if is_float_column(x) and is_float_column(y):
            # scatter plot
            create_visual(f"Scatter plot of {x_col} against {y_col}", plot_func=sns.scatterplot, data=dataset, x=x_col, y=y_col)
            # hexbin plot
            create_visual(f"Hexbin plot of {x_col} against {y_col}", plot_func=plt.hexbin, x=x, y=y, gridsize=30, cmap='viridis')
            # KDE plot (kernal density estimator)
            create_visual(f"KDE plot of {x_col} against {y_col}", plot_func=sns.kdeplot, x=x, y=y, cmap="Blues", fill=True, thresh=0, levels=100)
            # correlation matrix heatmap
            correlation_matrix = dataset[[x_col, y_col]].corr()
            create_visual(f"Correlation Matrix Heatmap of {x_col} and {y_col}", sns.heatmap, data=correlation_matrix, annot=True, cmap='coolwarm', linewidths=0.5)
            # line plot
            create_visual(f"Line Plot of {x_col} against {y_col}", plot_func=sns.lineplot, data=dataset, x=x_col, y=y_col)
            # linear regression plot
            create_visual(f"Linear Regression Plot of {x_col} and {y_col}", sns.regplot, data=dataset, x=x_col, y=y_col)
            # violin plot
            create_visual(f"Violin Plot of {x_col} and {y_col}", sns.violinplot, data=dataset, x=x_col, y=y_col)
            # boxplot
            create_visual(f"Boxplot of {x_col} and {y_col}", sns.boxplot, data=dataset, x=x_col, y=y_col)

        """
        x_col and y_col is string
        """
        if is_string_column(x) and is_string_column(y):
            # stacked bar plot, very hard to think of any other plots with just two string columns
            cross_tab = pd.crosstab(x, y)
            cross_tab.plot(kind='bar', stacked=True, colormap='viridis')
            create_visual(f"Stacked bar plot of {x_col} against {y_col}", plot_func=cross_tab.plot, kind='bar', stacked=True, colormap='viridis')
            # hue count plot
            create_visual(f"Count Plot of {x_col} with {y_col} as Hue", sns.countplot, data=dataset, x=x_col, hue=y_col)
            # heatmap categorical correlation
            cross_tab = pd.crosstab(x, y)
            create_visual(f"Heatmap of Categorical Correlation between {x_col} and {y_col}", sns.heatmap, data=cross_tab, annot=True, cmap='Blues')
            # swarm plot
            create_visual(f"Swarm Plot of {x_col} and {y_col}", sns.swarmplot, data=dataset, x=x_col, y=y_col)
            # stacked area plot
            cross_tab = pd.crosstab(x, y)
            create_visual(f"Stacked Area Plot of {x_col} against {y_col}", plot_func=cross_tab.plot, kind='area', stacked=True, colormap='viridis')
            # categorical scatter plot
            create_visual(f"Categorical Scatterplot of {x_col} and {y_col}", sns.stripplot, data=dataset, x=x_col, y=y_col, jitter=True)

        """
        x_col and y_col is bool
        """
        if is_bool_column(x) and is_bool_column(y):
            # couldnt think of or find any relevant plots for two booleans
            pass
    

        """
        x_col and y_col are int and str non-respectufully or float and str non respectfully
        """
        if is_int_str(x, y) or is_str_float(x, y):
            # bar plot
            create_visual(f"Bar plot of {x_col} against {y_col}", plot_func=sns.barplot, data=dataset, x=x_col, y=y_col)
            # box plot
            create_visual(f"Box plot of {x_col} against {y_col}", plot_func=sns.boxplot, data=dataset, x=x_col, y=y_col)
            # violin plot
            create_visual(f"violin plot of {x_col} against {y_col}", plot_func=sns.violinplot, data=dataset, x=x_col, y=y_col)
            # strip plot
            create_visual(f"Strip Plot of {x_col} against {y_col}", sns.stripplot, data=dataset, x=x_col, y=y_col)
            # swarm plot
            create_visual(f"Swarm Plot of {x_col} against {y_col}", sns.swarmplot, data=dataset, x=x_col, y=y_col)
            # line plot
            create_visual(f"Line Plot of {x_col} against {y_col}", sns.lineplot, data=dataset, x=x_col, y=y_col)
            

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
            # line plot
            create_visual(f"Line Plot of {x_col} against {y_col}", plot_func=sns.lineplot, data=dataset, x=x_col, y=y_col)
            # heatmap
            correlation = dataset[[x_col, y_col]].corr()
            create_visual(f"Correlation Heatmap of {x_col} and {y_col}", plot_func=sns.heatmap, data=correlation, annot=True, cmap='coolwarm')
            # violin plot
            create_visual(f"Violin Plot of {x_col} against {y_col}", plot_func=sns.violinplot, data=dataset, x=x_col, y=y_col)
            # boxplot
            create_visual(f"Boxplot of {x_col} against {y_col}", plot_func=sns.boxplot, data=dataset, x=x_col, y=y_col)


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