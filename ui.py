import gradio as gr
from converter import Converter
from environment import css, python_code

converter = Converter()


def create_prog_lang_ui(lang, model):
    prog_name = lang["name"]
    extension = lang["extension"]
    fn = lang["fn"]

    with gr.Row():
        with gr.Column():
            convert = gr.Button(f"Convert to {prog_name}")
            converted_code = gr.Textbox(label=f"Converted {prog_name} code:", lines=10)

        with gr.Column():
            prog_run = gr.Button(f"Run {prog_name}")
            prog_out = gr.TextArea(label=f"{prog_name} result:", elem_classes=[extension])

    current_selected = gr.Dropdown([extension], value=extension, visible=False)

    convert.click(converter.optimize, inputs=[python, model, current_selected], outputs=[converted_code])
    prog_run.click(converter.handle_execution, inputs=[converted_code, current_selected], outputs=[prog_out])

with gr.Blocks(css=css) as ui:
    gr.Markdown("# Convert code from Python to any Programming Language")
    with gr.Row():
        with gr.Column():
            python = gr.Textbox(label="Python code:", value=python_code, lines=10)
        with gr.Column():
            python_run = gr.Button(f"Run Python")
            python_out = gr.TextArea(label=f"Python result:", elem_classes=["python"])

    with gr.Row():
        model = gr.Dropdown(["GPT", "Claude"], label="Select model", value="GPT")

    python_run.click(converter.execute_python, inputs=[python], outputs=[python_out])

    for lang in converter.languages:
        create_prog_lang_ui(lang, model)



def launch():
    ui.launch()
