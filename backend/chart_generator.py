import matplotlib
matplotlib.use('Agg') # Use non-interactive backend for server-side generation
import matplotlib.pyplot as plt
import seaborn as sns
import os
import pandas as pd
from datetime import datetime

class ChartGenerator:
    def __init__(self, static_folder="static/charts"):
        self.static_folder = static_folder
        os.makedirs(self.static_folder, exist_ok=True)
        
        # Set dark theme styling for Matplotlib/Seaborn
        plt.style.use('dark_background')
        sns.set_theme(style="dark", palette="pastel")
        
        # Customize plot appearance for "Classical Dark" theme
        plt.rcParams.update({
            'figure.facecolor': '#121212',
            'axes.facecolor': '#121212',
            'savefig.facecolor': '#121212',
            'grid.color': '#333333',
            'axes.edgecolor': '#444444',
            'text.color': '#f8fafc',
            'axes.labelcolor': '#f8fafc',
            'xtick.color': '#94a3b8',
            'ytick.color': '#94a3b8',
            'font.family': 'sans-serif'
        })

    def generate_chart(self, data, config):
        
        try:
            df = pd.DataFrame(data)
            chart_type = config.get('type', 'bar').lower()
            x = config.get('x_axis')
            y = config.get('y_axis')
            title = config.get('title', 'Data Insights')

            if not x or not y or x not in df.columns or y not in df.columns:
                return None

            plt.figure(figsize=(10, 6))
            
            if chart_type == 'bar':
                sns.barplot(data=df, x=x, y=y)
            elif chart_type == 'line':
                sns.lineplot(data=df, x=x, y=y, marker='o', linewidth=2.5, color='#4f46e5')
            elif chart_type == 'pie':
                plt.pie(df[y], labels=df[x], autopct='%1.1f%%', colors=sns.color_palette("husl", len(df)))
            elif chart_type == 'area':
                plt.fill_between(range(len(df)), df[y], color="#ec4899", alpha=0.3)
                plt.plot(df[y], color="#ec4899", linewidth=2)
                plt.xticks(range(len(df)), df[x])
            elif chart_type == 'scatter':
                sns.scatterplot(data=df, x=x, y=y, s=100, color='#3b82f6')
            else:
                sns.barplot(data=df, x=x, y=y)

            plt.title(title, fontsize=16, pad=20, fontweight='bold', color='#f8fafc')
            plt.xticks(rotation=45)
            plt.tight_layout()

            # Save to static folder
            filename = f"chart_{datetime.now().strftime('%Y%m%d%H%M%S%f')}.png"
            filepath = os.path.join(self.static_folder, filename)
            plt.savefig(filepath, dpi=120, transparent=True)
            plt.close()
            print("CHART CREATED:", filename)
            return f"/api/charts/{filename}"
        except Exception as e:
            print(f"Error generating chart: {str(e)}")
            return None
            import traceback
            traceback.print_exc()
            print("CHART FAILED:", e)
