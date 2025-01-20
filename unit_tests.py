import pytest
import pandas as pd
import matplotlib.pyplot as plt

# personal functions to test
from functions import (
    generate_and_recommend_WIP, 
    process_data, 
    get_data_report_data,
    )

"""
run in terminal to test:

pytest unit_tests.py
"""


"""
data processing and reporting function tests
"""

def test_process_data():

    # case 1: df with mixed column types
    data = {
        'int_column': [1, 2, 3],
        'float_column': [1.1, 2.2, 3.3],
        'string_column': ['  hello', ' world  ', ' foo ']
    }
    df = pd.DataFrame(data)

    # run function
    processed_df = process_data(df)

    # assert no leading / trailing spaces
    assert processed_df['string_column'][0] == 'hello'
    assert processed_df['string_column'][1] == 'world'
    assert processed_df['string_column'][2] == 'foo'

    # assert data types are converted to expected conversions
    assert processed_df['int_column'].dtype == 'Int64'  # should be 'Int64' type
    assert processed_df['float_column'].dtype == 'Float64'  # should be 'Float64' type
    assert processed_df['string_column'].dtype == 'string'  # should be string type

    # case 2: df with only strings
    data2 = {
        'string_column': ['  apple', 'banana ', 'cherry ']
    }
    df2 = pd.DataFrame(data2)

    # run function
    processed_df2 = process_data(df2)

    # assert no leading / trailing spaces
    assert processed_df2['string_column'][0] == 'apple'
    assert processed_df2['string_column'][1] == 'banana'
    assert processed_df2['string_column'][2] == 'cherry'

    # case 3: DataFrame with no string columns
    data3 = {
        'int_column': [10, 20, 30],
        'float_column': [1.1, 2.2, 3.3]
    }
    df3 = pd.DataFrame(data3)

    # run function
    processed_df3 = process_data(df3)

    # ensure types are processed correctly
    assert processed_df3['int_column'].dtype == 'Int64'
    assert processed_df3['float_column'].dtype == 'Float64'



def test_get_data_report_data():
    # case 1: df with mixed column types
    data = {
        'int_column': [1, 2, 3],
        'float_column': [1.1, 2.2, 3.3],
        'string_column': ['hello', 'world', 'foo']
    }
    df = pd.DataFrame(data)

    # process and run function
    processed_df = process_data(df)
    data_report = get_data_report_data(processed_df)

    # assertations, dictionary returned
    assert isinstance(data_report, dict) # data_report is a dictionary

    # asserations, dictionary keys are as expected
    assert 'col names' in data_report    # col names is a key
    assert 'col types' in data_report    # col types is a key
    assert 'col data' in data_report     # col data is a key
    assert 'row num' in data_report      # row num is a key   
    assert 'col num' in data_report      # col num is a key  

    # asserations data shape is correct
    assert data_report['row num'] == 3
    assert data_report['col num'] == 3 

    # assertations, dictionary values are as expected
    assert data_report['col names'] == ['int_column', 'float_column', 'string_column'] # col names are the actual column names
    assert data_report['col types'] == ['Int64', 'Float64', 'string'] # column types are correct
    assert data_report['col data'].shape == (3, 2)  # shape of col data is: 3 rows, 2 columns
    assert list(data_report['col data']['Column Name']) == ['int_column', 'float_column', 'string_column'] # column names in col data are the actual col names
    assert list(data_report['col data']['Data Type']) == ['Int64', 'Float64', 'string'] # column types in col data are the actual col types



    # case 2: df is empty
    df = pd.DataFrame()

    # process and run function
    processed_df = process_data(df)
    data_report = get_data_report_data(processed_df)

    # asserations, data report is empty
    assert data_report['col names'] == []
    assert data_report['col types'] == []
    assert data_report['col data'].shape == (0, 2)
    assert data_report['row num'] == 0
    assert data_report['col num'] == 0




"""
current possible visual generation tests
"""

test_data = process_data(pd.DataFrame({
    'int_col': [1, 2, 3, 4, 5],
    'float_col': [1.1, 2.2, 3.3, 4.4, 5.5],
    'str_col': ['a', 'b', 'c', 'd', 'e'],
    # 'bool_col': [True, False, True, False, True], test once bool plots are implemented
}))


def test_both_columns_none():
    visuals, recommendations = generate_and_recommend_WIP(test_data, None, None)
    
    # assert no visuals are generated
    assert visuals is None
    assert recommendations is None


"""
1 dimensional plot tests
"""
def test_int_column_plot():

    # run function
    x_col = 'int_col'
    y_col = None
    visuals, recommendations = generate_and_recommend_WIP(test_data, x_col, y_col)

    # assert plots were generated
    assert visuals is not None
    assert recommendations is not None
    assert len(visuals) > 0

    # assert at least the recomended plot is in visuals
    assert f"Histogram of {x_col}" in visuals

    # assert the value in visuals is a Figure object
    assert isinstance(visuals[f"Histogram of {x_col}"], plt.Figure)

def test_str_column_plot():

    # run function
    x_col = 'str_col'
    y_col = None
    visuals, recommendations = generate_and_recommend_WIP(test_data, x_col, y_col)

    # assert plots were generated
    assert visuals is not None
    assert recommendations is not None
    assert len(visuals) > 0

    # assert at least the recomended plot is in visuals
    assert f"Pie Chart of {x_col}" in visuals

    # assert the value in visuals is a Figure object
    assert isinstance(visuals[f"Pie Chart of {x_col}"], plt.Figure)

def test_float_column_plot():

    # run function
    x_col = 'float_col'
    y_col = None
    visuals, recommendations = generate_and_recommend_WIP(test_data, x_col, y_col)

    # assert plots were generated
    assert visuals is not None
    assert recommendations is not None
    assert len(visuals) > 0

    # assert at least the recomended plot is in visuals
    assert f"Histogram of {x_col}" in visuals

    # assert the value in visuals is a Figure object
    assert isinstance(visuals[f"Histogram of {x_col}"], plt.Figure)

"""
2 dimensional same type plot tests
"""

def test_int_int_column_plot():

    # run function
    x_col = 'int_col'
    y_col = 'int_col'
    visuals, recommendations = generate_and_recommend_WIP(test_data, x_col, y_col)

    # assert plots were generated
    assert visuals is not None
    assert recommendations is not None
    assert len(visuals) > 0

    # assert at least the recomended plot is in visuals
    assert f"Scatter plot of {x_col} against {y_col}" in visuals

    # assert the value in visuals is a Figure object
    assert isinstance(visuals[f"Scatter plot of {x_col} against {y_col}"], plt.Figure)

def test_str_str_column_plot():

    # run function
    x_col = 'str_col'
    y_col = 'str_col'
    visuals, recommendations = generate_and_recommend_WIP(test_data, x_col, y_col)

    # assert plots were generated
    assert visuals is not None
    assert recommendations is not None
    assert len(visuals) > 0

    # assert at least the recomended plot is in visuals
    assert f"Stacked bar plot of {x_col} against {y_col}" in visuals

    # assert the value in visuals is a Figure object
    assert isinstance(visuals[f"Stacked bar plot of {x_col} against {y_col}"], plt.Figure)

def test_float_float_column_plot():

    # run function
    x_col = 'float_col'
    y_col = 'float_col'
    visual_title = f"Scatter plot of {x_col} against {y_col}"
    visuals, recommendations = generate_and_recommend_WIP(test_data, x_col, y_col)

    # assert plots were generated
    assert visuals is not None
    assert recommendations is not None
    assert len(visuals) > 0

    # assert at least the recomended plot is in visuals
    assert visual_title in visuals

    # assert the value in visuals is a Figure object
    assert isinstance(visuals[visual_title], plt.Figure)

"""
2 dimensional seperate type plot tests
"""
def test_int_str_column_plot():

    # run function
    x_col = 'int_col'
    y_col = 'str_col'
    visual_title = f"Bar plot of {x_col} against {y_col}"
    visuals, recommendations = generate_and_recommend_WIP(test_data, x_col, y_col)

    # assert plots were generated
    assert visuals is not None
    assert recommendations is not None
    assert len(visuals) > 0

    # assert at least the recomended plot is in visuals
    assert visual_title in visuals

    # assert the value in visuals is a Figure object
    assert isinstance(visuals[visual_title], plt.Figure)

def test_int_float_column_plot():

    # run function
    x_col = 'int_col'
    y_col = 'float_col'
    visual_title = f"Scatter plot of {x_col} against {y_col}"
    visuals, recommendations = generate_and_recommend_WIP(test_data, x_col, y_col)

    # assert plots were generated
    assert visuals is not None
    assert recommendations is not None
    assert len(visuals) > 0

    # assert at least the recomended plot is in visuals
    assert visual_title in visuals

    # assert the value in visuals is a Figure object
    assert isinstance(visuals[visual_title], plt.Figure)






