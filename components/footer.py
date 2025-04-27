import streamlit as st

def footer():
    """
    Displays the application footer
    """
    
    # Auto-refresh script if enabled
    if st.session_state.get("auto_refresh", False):
        interval = st.session_state.get("refresh_interval", 60) * 1000  # Convert to milliseconds
        
        # JavaScript for auto-refresh
        js = f"""
        <script>
            let timeout = null;
            function refreshPage() {{
                timeout = setTimeout(function() {{ 
                    window.location.reload();
                }}, {interval});
            }}
            refreshPage();
        </script>
        """
        st.components.v1.html(js)