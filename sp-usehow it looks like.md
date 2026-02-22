airports_kenya/
├── airports_strips/          # Existing app - keep as is
├── obstacle_compliance/      # NEW APP - Aerodrome Obstacle Limitation
│   ├── migrations/
│   ├── templates/
│   │   └── obstacle_compliance/
│   │       ├── dashboard.html          # Main dashboard
│   │       ├── airport_detail.html      # Single airport view
│   │       ├── property_check.html      # Property lookup
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