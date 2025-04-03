from flask import Flask, render_template, request
import csv
import os
from database import Supermarkets, init_db, db
import plotly.express as px
import pandas as pd

app = Flask(__name__)

# Country to continent mapping
country_to_continent = {
    'Japan': 'Asia',
    'Germany': 'Europe',
    'Netherlands': 'Europe',
    'France': 'Europe',
    'Thailand': 'Asia',
    'Austria': 'Europe',
    'Turkey': 'Asia',
    'United States': 'North America',
    'Chile': 'South America',
    'Mexico': 'North America',
    'Italy': 'Europe',
    'Denmark': 'Europe',
    'Hungary': 'Europe',
    'United Kingdom': 'Europe',
    'Switzerland': 'Europe',
    'Canada': 'North America',
    'South Korea': 'Asia',
    'Portugal': 'Europe',
    'Ireland': 'Europe',
    'Spain': 'Europe',
    'Australia': 'Oceania',
    'New Zealand': 'Oceania',
    'Brazil': 'South America',
    'Poland': 'Europe',
    'Romania': 'Europe',
    'Sweden': 'Europe',
    'Norway': 'Europe',
    'Finland': 'Europe',
    'Belgium': 'Europe',
    'Czech Republic': 'Europe',
    'Greece': 'Europe',
    'Russia': 'Europe',
    'India': 'Asia',
    'Indonesia': 'Asia',
    'Malaysia': 'Asia',
    'Singapore': 'Asia',
    'Taiwan': 'Asia',
    'Vietnam': 'Asia',
    'China': 'Asia',
    'Hong Kong': 'Asia',
    'Philippines': 'Asia',
    'Israel': 'Asia',
    'South Africa': 'Africa',
    'Egypt': 'Africa',
    'Kenya': 'Africa',
    'Argentina': 'South America',
    'Colombia': 'South America',
    'Peru': 'South America',
    'Ecuador': 'South America',
    'Puerto Rico': 'North America',
    'Iceland': 'Europe',
    'Slovenia': 'Europe',
    'Croatia': 'Europe',
    'Serbia': 'Europe',
    'Bulgaria': 'Europe',
    'Lithuania': 'Europe',
    'Latvia': 'Europe',
    'Estonia': 'Europe',
    'Slovakia': 'Europe',
    'Luxembourg': 'Europe',
    'Monaco': 'Europe',
    'Andorra': 'Europe',
    'San Marino': 'Europe',
    'Malta': 'Europe',
    'Cyprus': 'Europe',
    'Liechtenstein': 'Europe',
    'Montenegro': 'Europe',
    'Bosnia and Herzegovina': 'Europe',
    'North Macedonia': 'Europe',
    'Albania': 'Europe',
    'Kosovo': 'Europe',
    'Ukraine': 'Europe',
    'Belarus': 'Europe',
    'Moldova': 'Europe',
    'Kazakhstan': 'Asia',
    'Uzbekistan': 'Asia',
    'Pakistan': 'Asia',
    'Qatar': 'Asia',
    'United Arab Emirates': 'Asia',
    'Saudi Arabia': 'Asia',
    'Jordan': 'Asia',
    'Lebanon': 'Asia',
    'Oman': 'Asia',
    'Kuwait': 'Asia',
    'Bahrain': 'Asia',
    'Morocco': 'Africa',
    'Tunisia': 'Africa',
    'Algeria': 'Africa',
    'Senegal': 'Africa',
    'Côte d’Ivoire': 'Africa',
    'Mauritania': 'Africa',
    'Cameroon': 'Africa',
    'Madagascar': 'Africa',
    'Mauritius': 'Africa',
    'Reunion': 'Africa',
    'Namibia': 'Africa',
    'Zambia': 'Africa',
    'Zimbabwe': 'Africa',
    'Uganda': 'Africa',
    'Botswana': 'Africa'
}

# Load CSV into database
def load_csv_to_db(filepath):
    try:
        db.drop_tables([Supermarkets], safe=True)  # Drop the table to ensure the schema is correct
        db.create_tables([Supermarkets], safe=True)  # Recreate the table with the new schema
        with open(filepath, 'r') as f:
            reader = csv.DictReader(f)
            # Check if all required headers are present
            required_headers = {'Company', 'Headquarters', 'Served countries', 'Number of locations', 'Number of employees'}
            if not required_headers.issubset(reader.fieldnames):
                missing = required_headers - set(reader.fieldnames)
                raise ValueError(f"CSV file is missing required headers: {missing}")
            for row in reader:
                # Handle 'N/A' and other invalid data
                num_locations_str = row['Number of locations']
                num_employees_str = row['Number of employees']
                # Convert 'N/A' or empty strings to 0, otherwise try to convert to int
                try:
                    num_locations = 0 if num_locations_str == 'N/A' or not num_locations_str else int(num_locations_str)
                    num_employees = 0 if num_employees_str == 'N/A' or not num_employees_str else int(num_employees_str)
                except ValueError:
                    num_locations = 0
                    num_employees = 0
                Supermarkets.create(
                    company=row['Company'],
                    headquarters=row['Headquarters'],
                    served_countries=row['Served countries'],
                    num_locations=num_locations,
                    num_employees=num_employees
                )
        return "CSV Uploaded and Data Loaded!"
    except Exception as e:
        return f"Error loading CSV: {str(e)}"

# Load the default CSV file on startup if the database is empty
def load_default_data():
    # Check if the database is empty
    if Supermarkets.select().count() == 0:
        csv_path = os.path.join(os.path.dirname(__file__), 'supermarkets.csv')
        if os.path.exists(csv_path):
            load_csv_to_db(csv_path)
        else:
            print("Warning: supermarkets.csv not found. Please place the file in the project directory.")

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        file = request.files['file']
        file.save('supermarkets.csv')
        result = load_csv_to_db('supermarkets.csv')
        return result
    return render_template('index.html')

@app.route('/data')
def data():
    # Get filter and pagination parameters
    headquarters = request.args.get('headquarters', '')
    page = int(request.args.get('page', 1))
    per_page = 10  # Number of items per page

    # Build the query
    if headquarters:
        query = Supermarkets.select().where(Supermarkets.headquarters == headquarters)
    else:
        query = Supermarkets.select()

    # Get total count for pagination
    total = query.count()
    pages = (total + per_page - 1) // per_page  # Ceiling division
    if page < 1:
        page = 1
    if page > pages:
        page = pages

    # Get the paginated data
    supermarkets = query.paginate(page, per_page)

    # Prepare data with logo paths
    supermarkets_data = []
    for s in supermarkets:
        # Generate logo filename (replace spaces with hyphens, lowercase)
        logo_filename = s.company.lower().replace(' ', '-') + '.png'
        logo_path = f'logos/{logo_filename}'
        # Check if logo exists, otherwise use placeholder
        if not os.path.exists(os.path.join(app.static_folder, logo_path)):
            logo_path = 'logos/placeholder.png'

        supermarkets_data.append({
            'company': s.company,
            'headquarters': s.headquarters,
            'served_countries': s.served_countries,
            'num_locations': s.num_locations,
            'num_employees': s.num_employees,
            'logo_path': logo_path
        })

    return render_template('data.html', supermarkets=supermarkets_data, page=page, pages=pages, total=total, headquarters=headquarters)

@app.route('/visualizations')
def visualizations():
    # Fetch data from the database
    data = list(Supermarkets.select().dicts())
    
    # Check if the database is empty
    if not data:
        return render_template('viz.html', bar_html="<p>No data available. Please upload a CSV file first.</p>",
                              hist_html="", pie_htmls={})

    # Convert to DataFrame
    df = pd.DataFrame(data)

    # Bar chart: Total num_locations by headquarters
    bar_fig = px.bar(df.groupby('headquarters')['num_locations'].sum().reset_index(),
                     x='headquarters', y='num_locations', title="Total `num_locations` by Headquarters")
    bar_fig.update_layout(
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(size=14),
        margin=dict(l=40, r=40, t=60, b=40)
    )
    bar_html = bar_fig.to_html(full_html=False)

    # Histogram: Distribution of num_employees
    hist_fig = px.histogram(df, x='num_employees', title="Distribution of `num_employees`",
                            nbins=20, range_x=[0, df['num_employees'].max()])
    hist_fig.update_layout(
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(size=14),
        margin=dict(l=40, r=40, t=60, b=40)
    )
    hist_html = hist_fig.to_html(full_html=False)

    # Pie charts by continent
    pie_htmls = {}
    continents = ['Asia', 'Europe', 'North America', 'South America', 'Oceania', 'Africa']
    for continent in continents:
        # Filter data for the continent
        continent_df = df[df['headquarters'].map(lambda x: country_to_continent.get(x, 'Unknown') == continent)]
        if not continent_df.empty:
            # Calculate total locations for the continent
            total_locations = continent_df['num_locations'].sum()
            # Group by headquarters and sum num_locations
            continent_grouped = continent_df.groupby('headquarters')['num_locations'].sum().reset_index()
            # Create pie chart if there are multiple headquarters with locations
            if len(continent_grouped) > 1:  # Ensure at least two slices for a meaningful pie chart
                pie_fig = px.pie(continent_grouped, names='headquarters', values='num_locations',
                                title=f"Locations by Headquarters in {continent}")
                pie_fig.update_layout(
                    plot_bgcolor='white',
                    paper_bgcolor='white',
                    font=dict(size=12),
                    margin=dict(l=40, r=40, t=40, b=40)
                )
                # Add customization: labels with percent and slight pull effect
                pie_fig.update_traces(textinfo='percent+label', pull=[0.1] * len(continent_grouped))
                pie_htmls[continent] = {
                    'html': pie_fig.to_html(full_html=False),
                    'total_locations': total_locations
                }
            else:
                pie_htmls[continent] = {
                    'html': f"<p>No significant data for pie chart in {continent} (fewer than 2 headquarters).</p>",
                    'total_locations': total_locations
                }

    return render_template('viz.html', bar_html=bar_html, hist_html=hist_html, pie_htmls=pie_htmls)
if __name__ == '__main__':
    init_db()
    load_default_data()  # Load the default CSV data on startup
    app.run(debug=True)