from shiny import App, render, ui, reactive
from pathlib import Path
import pandas as pd
import plotly.graph_objects as go
import json
from pyodide.http import open_url

df_ukr_pop_region_all_flows_2021 = pd.read_csv(open_url('./app_files/ukr_pop_region_all_flows_total_2021.csv'))
df_ukr_pop_region_all_flows_2020 = pd.read_csv(open_url('./app_files/ukr_pop_region_all_flows_total_2020.csv'))
df_ukr_pop_region_all_flows_2019 = pd.read_csv(open_url('./app_files/ukr_pop_region_all_flows_total_2019.csv'))
df_ukr_pop_region_inter_state_flows_2021 = pd.read_csv(open_url('./app_files/ukr_pop_region_inter_state_total_2021.csv'))
df_ukr_pop_region_inter_state_flows_2020 = pd.read_csv(open_url('./app_files/ukr_pop_region_inter_state_total_2020.csv'))
df_ukr_pop_region_inter_state_flows_2019 = pd.read_csv(open_url('./app_files/ukr_pop_region_inter_state_total_2019.csv'))
df_ukr_population = pd.read_csv(open_url('./app_files/ukr_pop_present_resident_age.csv'))

with open_url('./app_files/geoBoundaries-UKR-ADM1.geojson', 'r', encoding='utf-8') as geo_file:
    ukraine_geojson = json.load(geo_file)
# base_path = Path('./docs')
# df_ukr_pop_region_all_flows_2021 = pd.read_csv(base_path / 'ukr_pop_region_all_flows_total_2021.csv', sep=",", decimal=".")
# df_ukr_pop_region_all_flows_2020 = pd.read_csv(base_path / 'ukr_pop_region_all_flows_total_2020.csv', sep=",", decimal=".")
# df_ukr_pop_region_all_flows_2019 = pd.read_csv(base_path / 'ukr_pop_region_all_flows_total_2019.csv', sep=",", decimal=".")
# df_ukr_pop_region_inter_state_flows_2021 = pd.read_csv(base_path / 'ukr_pop_region_inter_state_total_2021.csv', sep=",", decimal=".")
# df_ukr_pop_region_inter_state_flows_2020 = pd.read_csv(base_path / 'ukr_pop_region_inter_state_total_2020.csv', sep=",", decimal=".")
# df_ukr_pop_region_inter_state_flows_2019 = pd.read_csv(base_path / 'ukr_pop_region_inter_state_total_2019.csv', sep=",", decimal=".")
# df_ukr_population = pd.read_csv(base_path / 'ukr_pop_present_resident_age.csv', sep=",", decimal=".")

geo_path = base_path / 'geoBoundaries-UKR-ADM1.geojson'
with open(geo_path, 'r', encoding='utf-8') as geo_file:
    ukraine_geojson = json.load(geo_file)

app_ui = ui.page_fluid(
    ui.panel_title("UKRSTAT - Data Visualisation"),
    ui.page_navbar(
        ui.nav_panel("Ukraine population: Present & Resident", 
            ui.input_selectize("selectize_population", "Select view:", {
                "Urban": "Urban Population (present)", 
                "Rural": "Rural Population (present)",
                "By_Gender": "Population by Genders (resident)",
                "age1g": "0-14 years, 15-64 year, 65+",
                "age2g": "0-15 year, 16-59 year, 60+",
                "age3g": "0-17 year, 18+",
                "Total_Present": "Total Present Population",
                "Total_Resident": "Total Resident  Population"
            },  
                selected="Urban"
            ),  
            ui.output_ui("ukraine_population"),
        ),
        ui.nav_panel("Ukraine migration: mapping",
            ui.input_selectize("selectize_migration_region", "Select flow:", {
                "all_flows": "All migration flows",
                "interstate_flows": "Inter-state migration flows"
            },
                selected="all_flows"
            ),
            ui.output_ui("migration_map"),
            ui.input_slider("slider_migration_year", "Select year", 2019, 2021, 2021),
        ),
        id="tab",
    ),
    ui.p("In Accordance: www.ukrstat.gov.ua")
)

def server(input, output, session):
    @reactive.Calc
    def get_datasets_ukr_pop_region_all_flows():
        return {
            2019: df_ukr_pop_region_all_flows_2019,
            2020: df_ukr_pop_region_all_flows_2020,
            2021: df_ukr_pop_region_all_flows_2021
        }
    @reactive.Calc
    def get_datasets_ukr_pop_region_inter_state_flows():
        return {
            2019: df_ukr_pop_region_inter_state_flows_2019,
            2020: df_ukr_pop_region_inter_state_flows_2020,
            2021: df_ukr_pop_region_inter_state_flows_2021
        }
    @reactive.Calc
    def create_migration_map():
        if input.selectize_migration_region() == 'all_flows':
            datasets = get_datasets_ukr_pop_region_all_flows()
        else:
            datasets = get_datasets_ukr_pop_region_inter_state_flows()

        selected_year = input.slider_migration_year()
        df_ukr_pop_year = datasets[selected_year]

        trace_ukraine = go.Choroplethmapbox(
            geojson=ukraine_geojson,
            locations=df_ukr_pop_year['Region'],
            z=df_ukr_pop_year['migration increase (decrease)'],
            featureidkey="properties.shapeName",
            colorscale="Viridis",
            colorbar_title="Migration Increase/Decrease",
            hovertemplate=(
            "%{location}<br>"
            "Migration: %{z}<extra></extra>"
            ),
            marker_opacity=0.7,
            marker_line_width=1,
            zmin=-10000,  
            zmax=30000
        )
        trace_crimea = go.Choroplethmapbox(
            geojson=ukraine_geojson,
            locations=['Autonomous Republic of Crimea'],
            z=[0],  
            featureidkey="properties.shapeName",
            colorscale=[[0, 'red'], [1, 'red']],
            marker_opacity=0.5,
            marker_line_width=1,
            hovertemplate=(
                "%{location}<br>"
                "Migration (no data)<extra></extra>"
            ),
            showscale=False
        )
        layout = go.Layout(
            mapbox_style="carto-positron",
            mapbox_zoom=4,
            mapbox_center={"lat": 48.3794, "lon": 31.1656},
            title=f"Migration Increase/Decrease by Region (Ukraine) - {selected_year}",
            margin={"r": 0, "t": 0, "l": 0, "b": 0}
        )
        fig = go.Figure(data=[trace_ukraine, trace_crimea], layout=layout)
        return fig
    @output
    @render.ui
    def migration_map():
        fig = create_migration_map()
        return fig
    
    @reactive.Calc
    @output
    @render.ui
    def ukraine_population():
        if input.selectize_population() == "By_Gender":
            trace_male = go.Bar(
                x = df_ukr_population["Year"],
                y = df_ukr_population["Male"] *1000,
                name = "Male",
                marker_color = "#1fc3aa",
                hovertemplate="<b>Year:</b> %{x}<br><b>Males:</b> %{y:,.0f}<extra></extra>"
            )
            trace_female = go.Bar(
                x = df_ukr_population["Year"],
                y = df_ukr_population["Female"] *1000,
                name = "Female",
                marker_color = "#8624f5",
                hovertemplate="<b>Year:</b> %{x}<br><b>Females:</b> %{y:,.0f}<extra></extra>"
            )
            layout = go.Layout(
                title = "Males & Females Population Over Years",
                xaxis = dict(title="Year", tickmode='linear', dtick=2),
                yaxis = dict(title="Population"),
                barmode = "group"
            )
            fig = go.Figure(data=[trace_male, trace_female], layout=layout)
            return fig
        elif input.selectize_population() == "age1g":
            trace_age1g1 = go.Bar(
                x=df_ukr_population["Year"],
                y=df_ukr_population["0-14 year"] * 1000,
                name="0-14 year",
                marker_color="#1fc3aa",
                hovertemplate="<b>Year:</b> %{x}<br><b>0-14 year:</b> %{y:,.0f}<extra></extra>"
            )
            trace_age1g2 = go.Bar(
                x=df_ukr_population["Year"],
                y=df_ukr_population["15-64 year"] * 1000,
                name="15-64 year",
                marker_color="#8624f5",
                hovertemplate="<b>Year:</b> %{x}<br><b>15-64 year:</b> %{y:,.0f}<extra></extra>"
            )
            trace_age1g3 = go.Bar(
                x=df_ukr_population["Year"],
                y=df_ukr_population["65 years and more"] * 1000,
                name="65 years and more",
                marker_color="#f5d024",
                hovertemplate="<b>Year:</b> %{x}<br><b>65 years and more:</b> %{y:,.0f}<extra></extra>"
            )
            layout = go.Layout(
                title="0-14 years, 15-64 year, 65+ Grouped Population Over Years",
                xaxis=dict(title="Year", tickmode='linear', dtick=2),
                yaxis=dict(title="Population"),
                barmode="group"
            )
            fig = go.Figure(data=[trace_age1g1, trace_age1g2, trace_age1g3], layout=layout)
            return fig
        elif input.selectize_population() == "age2g":
            trace_age2g1 = go.Bar(
                x=df_ukr_population["Year"],
                y=df_ukr_population["0-15 year"] * 1000,
                name="0-15 year",
                marker_color="#1fc3aa",
                hovertemplate="<b>Year:</b> %{x}<br><b>0-15 year:</b> %{y:,.0f}<extra></extra>"
            )
            trace_age2g2 = go.Bar(
                x=df_ukr_population["Year"],
                y=df_ukr_population["16-59 year"] * 1000,
                name="16-59 year",
                marker_color="#8624f5",
                hovertemplate="<b>Year:</b> %{x}<br><b>16-59 year:</b> %{y:,.0f}<extra></extra>"
            )
            trace_age2g3 = go.Bar(
                x=df_ukr_population["Year"],
                y=df_ukr_population["60 years and more"] * 1000,
                name="60 years and more",
                marker_color="#f5d024",
                hovertemplate="<b>Year:</b> %{x}<br><b>60 years and more:</b> %{y:,.0f}<extra></extra>"
            )
            layout = go.Layout(
                title="0-15 year, 16-59 year, 60+ Grouped Population Over Years",
                xaxis=dict(title="Year", tickmode='linear', dtick=2),
                yaxis=dict(title="Population"),
                barmode="group"
            )
            fig = go.Figure(data=[trace_age2g1, trace_age2g2, trace_age2g3], layout=layout)
            return fig
        elif input.selectize_population() == "age3g":
            trace_age3g1 = go.Bar(
                x=df_ukr_population["Year"],
                y=df_ukr_population["0-17 year"] * 1000,
                name="0-17 year",
                marker_color="#1fc3aa",
                hovertemplate="<b>Year:</b> %{x}<br><b>0-17 year:</b> %{y:,.0f}<extra></extra>"
            )
            trace_age3g2 = go.Bar(
                x=df_ukr_population["Year"],
                y=df_ukr_population["18 years and more"] * 1000,
                name="18 years and more",
                marker_color="#8624f5",
                hovertemplate="<b>Year:</b> %{x}<br><b>18 years and more:</b> %{y:,.0f}<extra></extra>"
            )
            layout = go.Layout(
                title="0-17 year, 18+ Grouped Population Over Years",
                xaxis=dict(title="Year", tickmode='linear', dtick=2),
                yaxis=dict(title="Population"),
                barmode="group"
            )
            fig = go.Figure(data=[trace_age3g1, trace_age3g2], layout=layout)
            return fig
        else:
            population_type = input.selectize_population()
            y = df_ukr_population[population_type] * 1000
            x = df_ukr_population["Year"]
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=x, 
                y=y, 
                mode='lines+markers',
                name=f'{population_type}',
                line=dict(color="#7CC674"),
                marker=dict(color='#7CC674', size=10),
                hovertemplate="<b>Year:</b> %{x}<br><b>Population:</b> %{y:,.0f}<extra></extra>"
            ))
            fig.update_layout(
                title=f"{population_type} Population Over Time",
                xaxis_title="Year",
                yaxis_title=f"{population_type} Population",
                xaxis=dict(tickmode='linear', dtick=2), 
                hovermode='x unified'
            )
            return ui.HTML(fig.to_html(full_html=False))
    
app = App(app_ui, server)
