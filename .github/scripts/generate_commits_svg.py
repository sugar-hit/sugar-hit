#!/usr/bin/env python3
"""Generate GitHub commits calendar SVG for the README."""

import os
import json
from datetime import datetime
import urllib.request

def get_contributions():
    """Fetch contribution data using GitHub GraphQL API."""
    token = os.environ.get('GH_TOKEN')
    if not token:
        # Fallback to unauthenticated if no token (limited)
        token = 'dummy'

    query = """
    query($login: String!) {
      user(login: $login) {
        contributionsCollection {
          contributionCalendar {
            totalContributions
            weeks {
              contributionDays {
                date
                contributionCount
                contributionLevel
              }
            }
          }
        }
      }
    }
    """

    variables = {"login": "sugar-hit"}

    payload = json.dumps({"query": query, "variables": variables}).encode('utf-8')

    req = urllib.request.Request(
        'https://api.github.com/graphql',
        data=payload,
        headers={
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
            'User-Agent': 'sugar-hit-commits-calendar'
        }
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode('utf-8'))
            if 'errors' in data:
                print(f"GraphQL errors: {data['errors']}")
                return None
            return data
    except Exception as e:
        print(f"Error fetching contributions: {e}")
        return None


def generate_svg(contributions):
    """Generate SVG calendar from contributions data."""
    if not contributions or 'data' not in contributions:
        print("No contribution data available")
        return None

    calendar = contributions['data']['user']['contributionsCollection']['contributionCalendar']
    weeks = calendar['weeks']

    # Color scheme (GitHub dark theme)
    colors = {
        'none': '#161b22',
        'first': '#0e4429',
        'second': '#006d32',
        'third': '#26a641',
        'fourth': '#39d353'
    }

    # Cell size
    cell_size = 11
    cell_gap = 3
    day_labels = ['', 'Mon', '', 'Wed', '', 'Fri', '']
    month_labels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

    # Calculate dimensions
    num_weeks = len(weeks)
    width = num_weeks * (cell_size + cell_gap) + 30
    height = 7 * (cell_size + cell_gap) + 50

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <style>
    .cell {{ width: {cell_size}px; height: {cell_size}px; rx: 2; }}
    .mon-label {{ font-family: -apple-system, BlinkMacSystemFont, sans-serif; font-size: 9px; fill: #8b949e; }}
    .month-label {{ font-family: -apple-system, BlinkMacSystemFont, sans-serif; font-size: 9px; fill: #8b949e; }}
    .total-count {{ font-family: -apple-system, BlinkMacSystemFont, sans-serif; font-size: 12px; font-weight: bold; fill: #c9d1d9; }}
    .total-label {{ font-family: -apple-system, BlinkMacSystemFont, sans-serif; font-size: 9px; fill: #8b949e; }}
  </style>
  <rect width="{width}" height="{height}" fill="#0d1117" rx="6"/>

  <!-- Day labels -->
'''
    for i, label in enumerate(day_labels):
        y = 30 + i * (cell_size + cell_gap) + cell_size / 2 + 3
        svg += f'  <text x="20" y="{y}" class="mon-label">{label}</text>\n'

    # Month labels
    current_month = -1
    for week_idx, week in enumerate(weeks):
        first_day = week['contributionDays'][0]
        date = datetime.strptime(first_day['date'], '%Y-%m-%d')
        if date.month != current_month:
            current_month = date.month
            x = 30 + week_idx * (cell_size + cell_gap)
            svg += f'  <text x="{x}" y="20" class="month-label">{month_labels[current_month - 1]}</text>\n'

        for day_idx, day in enumerate(week['contributionDays']):
            level = day['contributionLevel']
            color = colors.get(level, colors['none'])
            x = 30 + week_idx * (cell_size + cell_gap)
            y = 30 + day_idx * (cell_size + cell_gap)
            svg += f'  <rect x="{x}" y="{y}" class="cell" fill="{color}" />\n'

    # Total count
    total = calendar['totalContributions']
    svg += f'''
  <!-- Total contributions -->
  <text x="{width - 10}" y="{height - 25}" class="total-count" text-anchor="end">{total} contributions</text>
  <text x="{width - 10}" y="{height - 10}" class="total-label" text-anchor="end">in the last year</text>
'''

    svg += '</svg>'
    return svg


def main():
    print("Fetching contributions...")
    data = get_contributions()
    if not data:
        print("Failed to fetch contributions")
        return

    print("Generating SVG...")
    svg = generate_svg(data)
    if not svg:
        print("Failed to generate SVG")
        return

    # Save to assets directory (relative path for GitHub Actions)
    os.makedirs('assets', exist_ok=True)
    output_path = 'assets/github-commits-calendar.svg'
    with open(output_path, 'w') as f:
        f.write(svg)

    print(f"SVG saved to {output_path}")


if __name__ == '__main__':
    main()
