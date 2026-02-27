airports_kenya/
├── airports_strips/          # Existing app - nothing changes
├── obstacle_compliance/      # NEW APP - Aerodrome Obstacle Limitation
│   ├── migrations/
│   ├── templates/              # All the html templates using the jinja2 templating engine
│   │   └── obstacle_compliance/
│   │       ├── dashboard.html          # Main dashboard including property check, bulk analysis and partials
│   │       ├── airport_detail.html      # Single airport view
│   │       ├── property_check.html      # Property lookup - though to be implemented using basemaps or better options as currently no data for the buildings
│   │       ├── bulk_analysis.html       # Bulk tools
│   │       └── partials/
│   │           ├── buffer_slider.html
│   │           ├── stats_panel.html
│   │           └── compliance_report.html
│   ├── static/
│   │   └── obstacle_compliance/
│   │       ├── css/
│   │       ├── js/
│   │       │   ├── dashboard.js
│   │       │   ├── buffer-slider.js
│   │       │   └── map-layers.js
│   │       └── img/
│   ├── models.py              # New models for compliance
│   ├── views.py               # New views
│   ├── urls.py                 # New URLs
│   ├── forms.py                # Forms for property search
│   ├── utils.py                # Helper functions (height calcs, buffers)
│   └── api.py                  # JSON endpoints for AJAX