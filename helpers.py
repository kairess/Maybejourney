from streamlit.components.v1 import html

def focus():
    html(f"""<script>
        var input = window.parent.document.querySelectorAll("input[type=text]");
        for (var i = 0; i < input.length; ++i) {{
            input[i].focus();
        }}
    </script>""", height=0)

def toggle_diabled(disabled=True):
    disabled_text = "false"
    if disabled:
        disabled_text = "true"
    html(f"""<script>
        var input = window.parent.document.querySelectorAll("input[type=text]");
        for (var i = 0; i < input.length; ++i) {{
            input[i].disabled = {disabled_text};
        }}
    </script>""", height=0)