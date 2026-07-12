import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

class GraphGenerator:
    """Generates highly interactive Plotly graphs as raw HTML strings for seamless HTMX insertion."""
    
    @staticmethod
    def _get_base_layout():
        """Standardizes the look and feel of all charts to match the ERP's Tailwind theme."""
        return {
            'template': 'plotly_white',
            'paper_bgcolor': 'rgba(0,0,0,0)',
            'plot_bgcolor': 'rgba(0,0,0,0)',
            'margin': dict(l=40, r=40, t=50, b=40),
            'font': dict(family="Inter, sans-serif", color="#6b7280"), # Tailwind Gray-500
            'title_font': dict(family="Inter, sans-serif", color="#111827", size=18) # Tailwind Gray-900
        }

    @staticmethod
    def generate_bar_chart(queryset, x_field, y_field, title="Bar Chart", labels=None):
        """Generates an interactive bar chart from a Django queryset."""
        df = pd.DataFrame(list(queryset.values(x_field, y_field)))
        if df.empty:
            return "<div class='text-gray-500 p-6 text-center'>No data available for chart.</div>"
            
        fig = px.bar(df, x=x_field, y=y_field, title=title, labels=labels)
        fig.update_layout(**GraphGenerator._get_base_layout())
        fig.update_traces(marker_color='#3b82f6', marker_line_color='#2563eb', marker_line_width=1.5, opacity=0.9)
        
        # Returns raw HTML script block that HTMX can directly swap into a div
        return fig.to_html(full_html=False, include_plotlyjs='cdn', config={'displayModeBar': False})
        
    @staticmethod
    def generate_line_chart(queryset, x_field, y_field, title="Line Chart", labels=None):
        df = pd.DataFrame(list(queryset.values(x_field, y_field)))
        if df.empty:
            return "<div class='text-gray-500 p-6 text-center'>No data available for chart.</div>"
            
        fig = px.line(df, x=x_field, y=y_field, title=title, labels=labels)
        fig.update_layout(**GraphGenerator._get_base_layout())
        fig.update_traces(line_color='#10b981', line_width=3)
        
        return fig.to_html(full_html=False, include_plotlyjs='cdn', config={'displayModeBar': False})

    @staticmethod
    def generate_pie_chart(queryset, names_field, values_field, title="Pie Chart"):
        if isinstance(queryset, list):
            df = pd.DataFrame(queryset)
            # Fill missing names with 'Draft' if None
            if not df.empty and names_field in df.columns:
                df[names_field] = df[names_field].fillna('Draft')
        else:
            df = pd.DataFrame(list(queryset.values(names_field, values_field)))
            
        if df.empty:
            return "<div class='text-gray-500 p-6 text-center'>No data available for chart.</div>"
            
        fig = px.pie(df, names=names_field, values=values_field, title=title, hole=0.4) # Donut chart style
        fig.update_layout(**GraphGenerator._get_base_layout())
        # Use a nice palette matching Tailwind
        fig.update_traces(marker=dict(colors=['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6']))
        
        return fig.to_html(full_html=False, include_plotlyjs='cdn', config={'displayModeBar': False})

    @staticmethod
    def generate_area_chart(queryset, x_field, y_field, title="Area Chart", labels=None):
        df = pd.DataFrame(list(queryset.values(x_field, y_field)))
        if df.empty:
            return "<div class='text-base-content/50 p-6 text-center'>No data available for chart.</div>"
            
        fig = px.area(df, x=x_field, y=y_field, title=title, labels=labels)
        fig.update_layout(**GraphGenerator._get_base_layout())
        fig.update_traces(line_color='#6366f1', fillcolor='rgba(99, 102, 241, 0.2)')
        return fig.to_html(full_html=False, include_plotlyjs='cdn', config={'displayModeBar': False})

    @staticmethod
    def generate_scatter_plot(queryset, x_field, y_field, title="Scatter Plot", color_field=None, labels=None):
        fields = [x_field, y_field]
        if color_field:
            fields.append(color_field)
        df = pd.DataFrame(list(queryset.values(*fields)))
        if df.empty:
            return "<div class='text-base-content/50 p-6 text-center'>No data available for chart.</div>"
            
        fig = px.scatter(df, x=x_field, y=y_field, color=color_field, title=title, labels=labels)
        fig.update_layout(**GraphGenerator._get_base_layout())
        fig.update_traces(marker=dict(size=10, opacity=0.8, line=dict(width=1, color='DarkSlateGrey')))
        return fig.to_html(full_html=False, include_plotlyjs='cdn', config={'displayModeBar': False})

    @staticmethod
    def generate_histogram(queryset, x_field, nbins=20, title="Histogram", labels=None):
        df = pd.DataFrame(list(queryset.values(x_field)))
        if df.empty:
            return "<div class='text-base-content/50 p-6 text-center'>No data available for chart.</div>"
            
        fig = px.histogram(df, x=x_field, nbins=nbins, title=title, labels=labels)
        fig.update_layout(**GraphGenerator._get_base_layout())
        fig.update_traces(marker_color='#f59e0b', marker_line_color='#d97706', marker_line_width=1)
        return fig.to_html(full_html=False, include_plotlyjs='cdn', config={'displayModeBar': False})

    @staticmethod
    def generate_heatmap(z_data, x_labels, y_labels, title="Heatmap"):
        if not z_data:
            return "<div class='text-base-content/50 p-6 text-center'>No data available for chart.</div>"
            
        fig = px.imshow(z_data, x=x_labels, y=y_labels, labels=dict(x="X Axis", y="Y Axis", color="Value"), title=title)
        fig.update_layout(**GraphGenerator._get_base_layout())
        fig.update_traces(colorscale='Blues')
        return fig.to_html(full_html=False, include_plotlyjs='cdn', config={'displayModeBar': False})

    @staticmethod
    def generate_radar_chart(categories, values, title="Radar Chart"):
        if not categories or not values:
            return "<div class='text-base-content/50 p-6 text-center'>No data available for chart.</div>"
            
        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(
            r=values,
            theta=categories,
            fill='toself',
            name=title,
            line_color='#8b5cf6'
        ))
        
        layout = GraphGenerator._get_base_layout()
        layout.update({
            'polar': dict(
                radialaxis=dict(visible=True, range=[0, max(values) * 1.1 if values else 100])
            ),
            'title': title
        })
        fig.update_layout(**layout)
        return fig.to_html(full_html=False, include_plotlyjs='cdn', config={'displayModeBar': False})

    @staticmethod
    def generate_gauge_chart(value, min_val=0, max_val=100, title="KPI Gauge"):
        fig = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = value,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': title, 'font': {'size': 18}},
            gauge = {
                'axis': {'range': [min_val, max_val]},
                'bar': {'color': "#3b82f6"},
                'steps': [
                    {'range': [min_val, (max_val - min_val) * 0.5], 'color': "lightgray"},
                    {'range': [(max_val - min_val) * 0.5, (max_val - min_val) * 0.85], 'color': "gray"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': max_val * 0.9
                }
            }
        ))
        fig.update_layout(**GraphGenerator._get_base_layout())
        return fig.to_html(full_html=False, include_plotlyjs='cdn', config={'displayModeBar': False})

    @staticmethod
    def generate_forecast_chart(historical_data, x_field, y_field, title="Demand Forecast"):
        """
        Generates a line chart displaying historical data and an appended trend line
        representing a moving average forecast.
        """
        df = pd.DataFrame(historical_data)
        if df.empty:
            return "<div class='text-base-content/50 p-6 text-center text-sm italic'>No historical ordering data available for demand forecasting.</div>"
            
        df = df.sort_values(by=x_field)
        df['Moving Average'] = df[y_field].rolling(window=min(len(df), 3), min_periods=1).mean()
        
        fig = go.Figure()
        
        # Actual Line
        fig.add_trace(go.Scatter(
            x=df[x_field],
            y=df[y_field],
            mode='lines+markers',
            name='Actual Demand',
            line=dict(color='#6366f1', width=3)
        ))
        
        # Forecast Trend Line
        fig.add_trace(go.Scatter(
            x=df[x_field],
            y=df['Moving Average'],
            mode='lines',
            name='3-Period Moving Avg Trend',
            line=dict(color='#f59e0b', width=2, dash='dash')
        ))
        
        layout = GraphGenerator._get_base_layout()
        layout.update({'title': title})
        fig.update_layout(**layout)
        
        return fig.to_html(full_html=False, include_plotlyjs='cdn', config={'displayModeBar': False})


