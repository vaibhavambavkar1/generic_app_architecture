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
