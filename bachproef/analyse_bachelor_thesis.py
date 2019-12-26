# import necessary libaries
import itertools
import re
import string
import json
import os
import sys
import PyPDF2
import TexSoup
import tabulate

def main():
    analysis_result = dict()
    inputPdf = PyPDF2.PdfFileReader(open("bachproef-tin.pdf", "rb"))
    analysis_result['pages'] = inputPdf.getNumPages()
    document_tree = get_document_tree('bachproef-tin.tex')
    analysis_result['tables'] = get_occurence_amounts('table', document_tree)
    analysis_result['figures'] = get_occurence_amounts('figure', document_tree)
    analysis_result['citations'] = get_occurence_amounts('citation', document_tree)
    text = extract_text(document_tree)
    if len(sys.argv) > 1 and sys.argv[1] == "y":
        save_text(text, 'saved_text.txt')
    analysis_result['word_count'] = get_word_count(text)
    print(json.dumps(analysis_result))
    data = sorted([(k, v) for k, v in analysis_result.items()])
    print(tabulate.tabulate(data, tablefmt="github"))

def extract_text(document_tree):
    remove_unnecessary_nodes(document_tree)
    text_elements = list(document_tree.text)
    text_elements = remove_unnecessary_text(text_elements)
    return " ".join(text_elements)

def save_text(text, file_name):
    with open(file_name, "w") as text_file:
        print(text, file=text_file)
        
def get_occurence_amounts(node, document_tree):
    if node == 'citation':
        return len(get_citations())
    return len(list(document_tree.find_all(node)))
    
def get_document_tree(file_name):
    # merge all tex's into one
    os.system("chmod +x recursivelyMergeTex.awk")
    os.system(f"./recursivelyMergeTex.awk < {file_name} > combined_temp.tex")
    
    with open('combined_temp.tex') as f: data = f.read()
    tree = TexSoup.TexSoup(data)
    # temp file is not needed anymore
    os.remove("combined_temp.tex") 
    
    return tree

def remove_unnecessary_nodes(document_tree):
    nodes_to_remove = [
        # 'autocite',
        'documentclass',
        'usepackage',
        'title',
        'author',
        'promotor',
        'copromotor',
        'instelling',
        'academiejaar',
        'examenperiode',
        'label',
        'tableofcontents',
        'cleardoublepage',
        'pagestyle',
        'listoffigures',
        'listoftables',
        'ref',
        'figure',
        'lstlisting',
        'verbatim',
        'table',
        'printbibliography'
    ]
    for node in nodes_to_remove:
        for found_instance in document_tree.find_all(node):
            found_instance.delete()

def remove_unnecessary_text(text_elements):
    text_elements = filter_appendix_and_rest(text_elements)
    text_elements = remove_comments(text_elements)
    text_elements = remove_unnecessary_words(text_elements)
    text_elements = trim_and_clean_up(text_elements)
    return text_elements
    
def filter_appendix_and_rest(text_elements):
    return text_elements[: text_elements.index('Appendix')]

def remove_comments(text_elements):
    return list(map(lambda text: '' if len(text) > 0 and len(re.findall(r'^%', text)) > 0 else text, text_elements))

def remove_unnecessary_words(text_elements):
    string_to_remove = [
        '\n', 
        '\t',
        '\\',
        '\\\'',
        '~',
        '``',
        '\'\'',
        'IfLanguageName',
        'selectlanguage',
        'chapter*',
        'lipsum',
        'english',
        'chaptername',
    ]
    string_to_remove.extend(get_citations())
    
    temp_result = text_elements
    for string in string_to_remove:
        temp_result = list(map(lambda text: text.replace(string, '') if len(text) > 0 else text, temp_result))
    return temp_result

def get_citations():
    with open('bachproef-tin.bib') as f: bib = f.read()
    return re.findall(r'\n@.*{(.*?),', bib)

def trim_and_clean_up(text_elements):
    temp_result = list(map(lambda text: text.strip(), text_elements))
    return list(filter(lambda text: len(text) > 0, temp_result))

def get_word_count(text):
    return sum(word.strip(string.punctuation).isalnum() for word in text.split())


if __name__== "__main__":
    main()
