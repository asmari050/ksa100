import dash
from dash import html, dcc, callback, Output, Input, State
import dash_bootstrap_components as dbc
import flask
from datetime import datetime
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
from zigzag import peak_valley_pivots
import dash_table


# قراءة ملف CSV
df = pd.read_csv('ksa/src/data/SR.csv')

# تحميل بيانات السعر
def get_stock_data(symbol):
    stock_data = yf.download(symbol, period="3y", interval="1wk")
    return stock_data


server = flask.Flask(__name__)
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, server=server, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server

app.layout = html.Div(
    [
        
        html.Div([
            html.H1("فلتر الأسهم السعودية")
        ], style={'textAlign': 'center'}),
        
        html.Div([
            html.Button(id='search-button', n_clicks=0, children="عرض بيانات الأسهم"),
           
        ], className='row1'),
        
        
        
        
        html.Div([
            html.Div(
            f"تاريخ اليوم: {datetime.now().strftime('%Y-%m-%d')} -   {datetime.now().strftime('%A')}"),
        ],className='row3'),

        
        html.Div(id='output-table', style={'text-align': 'center'})
        
    ],className='main')


#--------------------------------------------------------------------------------------------------------

@app.callback(
    Output('output-table', 'children'),
    Input('search-button', 'n_clicks')
)
def display_table(n_clicks):
    if n_clicks > 0:
        filtered_stocks = []
        for index, row in df.iterrows():
            stock_symbol = row['stock_symbol']
            stock_data = get_stock_data(stock_symbol)
            pivotsh = peak_valley_pivots(stock_data['High'], 0.14, -0.14)
            pivotsl = peak_valley_pivots(stock_data['Low'], 0.14, -0.14)
            peaks = stock_data.loc[pivotsh == 1, 'High']
            valleys = stock_data.loc[pivotsl == -1, 'Low']
            latest_peaks = peaks.tail(6)
            latest_valleys = valleys.tail(6)

            if (latest_peaks.shape[0] >= 2 and latest_valleys.shape[0] >= 2
            and latest_peaks.iloc[-2] > latest_valleys.iloc[-1] 
            and latest_valleys.iloc[-1] > latest_valleys.iloc[-2] 
            and (latest_valleys.iloc[-1] <= ((latest_peaks.iloc[-2]-latest_valleys.iloc[-2])/2)+latest_valleys.iloc[-2])
            and latest_peaks.iloc[-1] >=  latest_peaks.iloc[-2]
            and stock_data['Close'].iloc[-1] >= latest_peaks.iloc[-2]
            and (len(latest_valleys) == 0 or stock_data['Close'].iloc[-1] < (latest_valleys.iloc[-1] - ((200 / 100) * (latest_valleys.iloc[-2] - latest_peaks.iloc[-2]))))):  # إضافة الشرط الجديد هنا
                filtered_stocks.append(row)
            
        if filtered_stocks:
            for stock in filtered_stocks:
                stock_symbol = stock['stock_symbol']
                stock_data = get_stock_data(stock_symbol.upper())
                pivotsh = peak_valley_pivots(stock_data['High'], 0.14, -0.14)
                pivotsl = peak_valley_pivots(stock_data['Low'], 0.14, -0.14)
                latest_peaks = stock_data.loc[pivotsh == 1, 'High'].tail(6)
                latest_valleys =stock_data.loc[pivotsl == -1, 'Low'].tail(6)
                
                if latest_peaks.shape[0] >= 2:
                    stock['سعر الدخول'] = '{:.2f}'.format(latest_peaks.iloc[-2])
                    target_y1 = latest_valleys.iloc[-1] -100 / 100 * (latest_valleys.iloc[-2] - latest_peaks.iloc[-2])
                    stock['الهدف الأول'] = '{:.2f}'.format(target_y1)
                    target_y2 = latest_valleys.iloc[-1] - ((161.8 / 100) * (latest_valleys.iloc[-2] - latest_peaks.iloc[-2]))
                    stock['الهدف الثاني'] = '{:.2f}'.format(target_y2)
                    target_y3 = latest_valleys.iloc[-1] - ((180.90 / 100) * (latest_valleys.iloc[-2] - latest_peaks.iloc[-2]))
                    stock['الهدف الثالث'] = '{:.2f}'.format(target_y3)
                    target_y4 = latest_valleys.iloc[-1] - ((200 / 100) * (latest_valleys.iloc[-2] - latest_peaks.iloc[-2]))
                    stock['الهدف الرابع'] = '{:.2f}'.format(target_y4)
                else:
                    stock['سعر الدخول'] = '0.00'  # أو أي قيمة تريدها في حالة عدم وجود قيمة كافية

                # إضافة سعر الإغلاق للجدول
                stock_data_close = stock_data['Close']
                stock['سعر الإغلاق'] = '{:.2f}'.format(stock_data_close.iloc[-1])

                # إضافة سعر الدخول لحساب نسبة الربح
                stock['سعر الدخول'] = '{:.2f}'.format(latest_peaks.iloc[-2])

                # حساب نسبة الربح
                profit_percentage = ((stock_data['Close'].iloc[-1] - latest_peaks.iloc[-2]) / latest_peaks.iloc[-2]) * 100
                stock['نسبة الربح'] = '{:.2f}%'.format(profit_percentage)

                # إضافة نسبة الربح إلى الجدول
                table_data = [
                    dash_table.DataTable(
                        id='table',
                        columns=[
                               
                            {'name': 'نسبة الربح', 'id': 'نسبة الربح'},  # إضافة عمود نسبة الربح
                            {'name': 'الهدف الرابع', 'id': 'الهدف الرابع'},
                            {'name': 'الهدف الثالث', 'id': 'الهدف الثالث'},
                            {'name': 'الهدف الثاني', 'id': 'الهدف الثاني'},
                            {'name': 'الهدف الأول', 'id': 'الهدف الأول'},
                            {'name': 'سعر الدخول', 'id': 'سعر الدخول'},
                            {'name': 'سعر الإغلاق', 'id': 'سعر الإغلاق'},
                            {'name': 'اسم الشركة', 'id': 'name_stock'},
                            {'name': 'رمز الشركة', 'id': 'stock_symbol'}
                           
                        ],
                        data=[row.to_dict() for row in filtered_stocks],
                        style_cell={'textAlign': 'right', 'fontWeight': 'bold', 'fontSize': '14px'},
                        style_header={'backgroundColor': 'GREEN', 'color': 'white', 'fontWeight': 'bold'},
                        style_data_conditional=[
                            {
                                'if': {'column_id': 'stock_symbol'},
                                'backgroundColor': '#C3FDB8',
                                'color': 'BLACK',
                                'fontWeight': 'bold',  
                                'fontSize': '14px',  
                            },
                            {
                                'if': {'column_id': 'name_stock'},
                                'backgroundColor': '#E0FFFF',
                                'color': 'BLACK',
                                'fontWeight': 'bold',  
                                'fontSize': '14px',  
                            },
                            {
                                'if': {'column_id': 'نسبة الربح'},  # تطبيق التنسيق على عمود نسبة الربح
                                'backgroundColor': '#FFF8C6',
                                'color': 'BLACK',
                                'fontWeight': 'bold',  
                                'fontSize': '14px',  
                            }
                        ],
                        style_cell_conditional=[
                            {
                                'if': {'column_id': 'stock_symbol'},
                                'minWidth': '150px', 'width': '150px', 'maxWidth': '100px',
                                'textAlign': 'center'
                            },
                            {
                                'if': {'column_id': 'name_stock'},
                                'minWidth': '200px', 'width': '200px', 'maxWidth': '200px',
                                'textAlign': 'center',
                                'color': 'balck',
                                'backgroundColor': '#EBDDE2'
                            },
                            {
                                'if': {'column_id': 'نسبة الربح'},  # تطبيق التنسيق على عمود نسبة الربح
                                'minWidth': '150px', 'width': '150px', 'maxWidth': '100px',
                                'textAlign': 'center'
                            }
                        ],
                        style_table={'font-family': 'Arial', 'font-size': '14px'}
                    )
                ]

                # حساب عدد الرموز التي ظهرت نتيجة البحث
            symbols_count = len(filtered_stocks)

            # إضافة صف لعرض عدد الرموز التي ظهرت نتيجة البحث
            table_data.append(html.Tr([
                html.Hr(),  # خط فاصل بين الصفحتين
                html.Td(f'عدد الشركات المحققة للشروط: {symbols_count }شركة', colSpan='9', style={'backgroundColor': 'green', 'color': 'white', 'textAlign': 'right', 'direction': 'rtl','fontSize': '15px'})
            ]))

            return table_data
        else:
            return html.H2('لا توجد أسهم تحقق الشرط', style={'color': 'white', 'background-color': 'black', 'text-align': 'right'})
    else:
        return None





if __name__ == '__main__':
    app.run_server(debug=True)
