from barcode.writer import ImageWriter
import barcode
import base64
import io
from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters.html import HtmlFormatter
import latex2mathml.converter
import markdown 
import random
import string
import urllib.request
import os

def latexEquations(equation):
    return latex2mathml.converter.convert(equation)

def table2html(tableMD):
    return markdown.markdown(tableMD,encoding='utf-8', extensions=['markdown.extensions.tables'])

def highlight_code(code, lang):
    if lang.startswith('python'):
        lexer = get_lexer_by_name('python', stripall=True)
    elif lang.startswith('javascript'):
        lexer = get_lexer_by_name('javascript', stripall=True)
    else:
        lexer = get_lexer_by_name('text', stripall=True)

    formatter = HtmlFormatter()
    style_defs = formatter.get_style_defs('.highlight')
    highlighted_code = highlight(code, lexer, formatter)
    html_code = f'<style>{style_defs}</style>{highlighted_code}'
    return html_code

def graph(data,filename):
    APP_ROOT = os.path.dirname(os.path.abspath(__file__))
    UPLOAD_FOLDER = os.path.join(APP_ROOT, 'static', 'images')
    graphbytes = data.encode("ascii")
    base64_bytes = base64.urlsafe_b64encode(graphbytes)
    image_url = "https://mermaid.ink/img/"+base64_bytes.decode("ascii")
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36"}
    req = urllib.request.Request(image_url, headers=headers)
    with urllib.request.urlopen(req) as url:
        image_data = url.read()
    filepath = os.path.join(UPLOAD_FOLDER, f"{filename}.jpeg")
    with open(filepath, 'wb') as file:
        file.write(image_data)
    
    return f'<img src="/static/images/{filename}.jpeg" class="img-fluid" alt="mermaid image">'
def codeGen(length=8):
    # Define the character set for the random string
    chars = string.ascii_letters + string.digits

    # Generate the random string
    random_string = ''.join(random.choice(chars) for i in range(length))

    return random_string

def md2html(mdString,code=None):
    htmlCode = ""
    lines = mdString.split('\n')
    mermaid_lines = []
    in_mermaid_block = False
    table_lines = []
    in_table_block = False
    code_lines = []
    in_code_block = False
    codeType = ""
    for line in lines:
        line = line.strip('\r')
        # Starting mermaid block
        if '```mermaid' in line:
            in_mermaid_block = True
            continue
        # Ending code block
        elif '```' in line and in_mermaid_block:
            in_mermaid_block = False
            htmlCode += graph('\n'.join(mermaid_lines),code)
            continue
        # Adding lines while in mermaid block
        if in_mermaid_block:
            mermaid_lines.append(line.rstrip('\n'))
            continue

        # Starting code block
        if '```js' in line or '```python' in line or '```java' in line or '```php' in line:
            in_code_block = True
            if 'js' in line:
                codeType = "javascript"
            if 'python' in line:
                codeType = "python"
            if 'java' in line:
                codeType = "java"
            if 'php' in line:
                codeType = "php"
            continue
        # Ending Code block
        if '```' in line and in_code_block:
            in_code_block = False
            htmlCode += highlight_code('\n'.join(code_lines),codeType)
            continue
        # Adding lines while in code block
        if in_code_block:
            code_lines.append(line.rstrip('\n'))
            continue
        
        # starting table block
        if '```table' in line:
            in_table_block = True
            continue
        # Ending code block
        elif '```' in line and in_table_block:
            in_table_block = False
            tableHTML = table2html('\n'.join(table_lines))
            htmlCode += tableHTML.replace('<table>', '<table class="table table-bordered">')
            continue

        # Adding lines while in table block
        if in_table_block:
            table_lines.append(line)
            continue
        if '$' in line:
            line = line.strip()
        print(line)
        if line.startswith("$") and line.endswith("$"):
            line = line.strip("$")
            htmlCode += latexEquations(line) + "<br>"
            continue
        
        htmlCode += markdown.markdown(line)

    return htmlCode

def randomNumbers(total, ranges):
    numbers = []
    ranges = [(int(x),int(y)) for (x,y) in ranges]
    for r in ranges:
        numbers.append(random.randint(*r))
    while sum(numbers) != total:
        index = random.randint(0, len(numbers)-1)
        numbers[index] = random.randint(*ranges[index])
    return numbers



def barcode_image(number):
    # Generate the barcode image using the EAN13 format
    ean = barcode.get('ean13', number, writer=ImageWriter())

    # Save the image to a BytesIO object
    image_bytes = io.BytesIO()
    ean.write(image_bytes)
    image_bytes.seek(0)

    # Convert the image to base64 encoding
    image_base64 = base64.b64encode(image_bytes.getvalue()).decode()
    return f'<div class="container"><img style="height: 50px;float: right;" src="data:image/png;base64,{ image_base64 }"></div>'