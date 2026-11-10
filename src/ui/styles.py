"""UI style definitions and CSS templates for the Streamlit dashboard."""


def get_custom_css() -> str:
    """Returns custom CSS design system for dark mode dashboard."""
    return """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    .main { background-color: #0f172a; }
    .block-container { padding-top: 2rem; padding-bottom: 2rem; }

    h1 { color: #f1f5f9 !important; font-weight: 700; }
    h2 { color: #e2e8f0 !important; font-weight: 600; }
    h3 { color: #cbd5e1 !important; }

    .metric-card {
        background: linear-gradient(135deg, #1e293b, #0f172a);
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 1.2rem 1.5rem;
        margin-bottom: 1rem;
    }

    .stMetric {
        background: #1e293b;
        border: 1px solid #334155;
        border-radius: 10px;
        padding: 1rem;
    }

    .stMetric label { color: #94a3b8 !important; }
    .stMetric [data-testid="metric-container"] { color: #f1f5f9; }

    .highlight-box {
        background: linear-gradient(135deg, rgba(30, 64, 175, 0.15), #0f172a);
        border-left: 4px solid #3b82f6;
        border-radius: 8px;
        padding: 1rem 1.2rem;
        margin: 0.75rem 0;
        color: #e2e8f0;
    }

    .highlight-box-warning {
        background: linear-gradient(135deg, rgba(146, 64, 14, 0.15), #0f172a);
        border-left: 4px solid #f59e0b;
        border-radius: 8px;
        padding: 1rem 1.2rem;
        margin: 0.75rem 0;
        color: #e2e8f0;
    }

    .sidebar .sidebar-content { background-color: #1e293b; }
    </style>
    """

