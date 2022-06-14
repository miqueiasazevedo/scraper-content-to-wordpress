"""Importações"""
import re
import unicodedata

from urllib.request import urlopen
from bs4 import BeautifulSoup
from requests import get
from io import BytesIO
from PIL import Image
from time import sleep

"""Váriaveis de configuração"""
SOURCE_URL = "https://www.mysite.com.br/"  # Url do site origem dos dados (Ex: "https://www.mysite.com.br")
# Nome da página de origem dos dados conforme a url - (Ex: "news")
SOURCE_PAGE = "pediatras?pagina=1"
POST_CATEGORY = "Notícias"  # Categoria do post no wordpress
initial_post_id = 10000  # Id inicial disponivel para o post no wordpress
WP_ATTACHED_FOLDER = '2022/03/'  # Pasta do wordpress onde serão salvas as imagens
LIMIT_PAGINATION = 0  # Limite de paginas a serem buscadas
LIMIT_POSTS = 0

HEADERS = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Access-Control-Max-Age': '3600',
    'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:52.0) Gecko/20100101 Firefox/52.0'
}

# Url da página acessada inicialmente
initial_url = SOURCE_URL + \
    SOURCE_PAGE if SOURCE_URL[-1] == '/' else SOURCE_URL + "/" + SOURCE_PAGE

# Abre ou cria o arquivo de posts
media_file_import = open('post.WordPress.2022-031.xml', 'a')
# escreve o cabeçalho do arquivo
media_file_import.write("""<rss version="2.0"
	xmlns:excerpt="http://wordpress.org/export/1.2/excerpt/"
	xmlns:content="http://purl.org/rss/1.0/modules/content/"
	xmlns:wfw="http://wellformedweb.org/CommentAPI/"
	xmlns:dc="http://purl.org/dc/elements/1.1/"
	xmlns:wp="http://wordpress.org/export/1.2/"
>

<channel>
	<link>""" + SOURCE_URL + """</link>
	<language>pt-BR</language>
	<wp:wxr_version>1.2</wp:wxr_version>
	<wp:base_site_url>""" + SOURCE_URL + """</wp:base_site_url>
	<wp:base_blog_url>""" + SOURCE_URL + """</wp:base_blog_url>


	<generator>https://wordpress.org/?v=5.8.2</generator>

  </channel>""" + "\n")

# Regex para buscar url de arquivos no conteudo da noticia
RE_FILES_IN_CONTENT = re.compile(
    r'((?:[https]+?://mysite.com.br).+?(?:\.pdf|\.doc|\.docs|\.xls))')

# Regex para buscar url de imagens no conteudo da noticia
RE_IMAGES_IN_CONTENT = re.compile(
    r'((?:[http]+?://mysite.com.br).+?(?:\.jpg|\.jpeg|\.png))')

media_file_in_post = 0  # Variável de controle para recursividade da função create_post

create_thumb_post = False # Variável de controle para criação do item de importação da imagem thumb
big_images = 0


# Variavel global que recebe o html das paginas acessadas durante o processo

def access_page(link):
    global bs_content
    html_content = get(link, headers=HEADERS)
    bs_content = BeautifulSoup(html_content.content, 'html.parser')


access_page(initial_url)

#Varialvel que recebe a lista de links da paignação do site
#Passe como primeiro parametro o seletor css dos itens da páginação
pagination = bs_content.select(
    '.widget-noticia-paginacao li a', limit=LIMIT_PAGINATION if LIMIT_PAGINATION > 0 else None)

global lista


def strip_accents(string):
    return ''.join(c for c in unicodedata.normalize('NFD', string)
                   if unicodedata.category(c) != 'Mn')


def get_url_original_thumb(url):
    # Faz o split da url mantendo as barras
    split_url = re.findall('/|[^/]+', url)
    original_img = split_url.pop()
    original_thumb_url = ''.join(split_url) + 'original_' + original_img
    return original_thumb_url


def get_formated_date(date):
    split_date = date.split('/')[::-1]
    formated_date = '-'.join(split_date)
    return formated_date


def get_content(link):
    access_page(link)
    content = bs_content.find(
        class_='plugdados-widget-noticia-texto')

    imgs = []
    file_urls = []

    for url_img in content.find_all(
            attrs={'src': RE_IMAGES_IN_CONTENT}):
        imgs.append(url_img['src'])

    for url_file in content.find_all(
            attrs={'href': RE_FILES_IN_CONTENT}):
        file_urls.append(url_file['href'])

    return content, file_urls + imgs



def increment_initial_post_id():
    global initial_post_id
    initial_post_id += 1


def create_post(post, media=False):

    global create_thumb_post
    global media_file_import
    global media_file_in_post

    post_item = """<item>
        <title><![CDATA[""" + post["title"] + """]]></title>
        <link>""" + post["link"] + """</link>
        <pubDate>Wed, 01 Sep 2021 09:00:00 +0000</pubDate>
        <dc:creator><![CDATA[Miqueias]]></dc:creator>
        <guid isPermaLink="false">""" + post["link"] + """</guid>
        <description></description>
        <content:encoded><![CDATA[""" + (str(post["content"][0]) if media == False else """ """) + """]]></content:encoded>
        <wp:initial_post_id>""" + str(initial_post_id) + """</wp:initial_post_id>
        <wp:post_date><![CDATA[""" + post["publish_date"] + """ 09:00:00]]></wp:post_date>
        <wp:post_date_gmt><![CDATA[""" + post["publish_date"] + """ 12:00:00]]></wp:post_date_gmt>
        <wp:post_modified><![CDATA[""" + post["publish_date"] + """ 09:00:00]]></wp:post_modified>
        <wp:post_modified_gmt><![CDATA[""" + post["publish_date"] + """ 12:00:00]]></wp:post_modified_gmt>
        <wp:comment_status><![CDATA[open]]></wp:comment_status>
        <wp:ping_status><![CDATA[""" + ("""open""" if media == False else """closed""") + """]]></wp:ping_status>
        <wp:post_name><![CDATA[""" + '-'.join(re.findall(r'(?:[a-zA-Z]+)', post["title"])) + str(initial_post_id) + """]]></wp:post_name>
        <wp:status><![CDATA[""" + ("""publish""" if media == False else """inherit""") + """]]></wp:status>
        <wp:post_parent>0</wp:post_parent>
        <wp:menu_order>0</wp:menu_order>
        <wp:post_type><![CDATA[""" + ("""post""" if media == False else """attachment""") + """]]></wp:post_type>
        <wp:post_password><![CDATA[]]></wp:post_password>
        <wp:is_sticky>0</wp:is_sticky> """

    if media == True:
        """ print('Arquivo: ' + str(media_file_in_post) +
              ' - ' + post["content"][1][media_file_in_post]) """
        post_item += """<wp:attachment_url><![CDATA[""" + (post["thumb"] if post["thumb"] and not create_thumb_post else post["content"][1][media_file_in_post]) + """]]></wp:attachment_url>
            <wp:postmeta>
            <wp:meta_key><![CDATA[_wp_attached_file]]></wp:meta_key>
            <wp:meta_value><![CDATA[""" + WP_ATTACHED_FOLDER + post["link"].split('/')[-1] + """]]></wp:meta_value>
            </wp:postmeta>"""

        file_url = post["thumb"] if post["thumb"] and not create_thumb_post else post["content"][1][media_file_in_post]

        if re.findall(RE_IMAGES_IN_CONTENT, file_url):
            image_raw = get(file_url)
            image = Image.open(BytesIO(image_raw.content))
            width, height = image.size
            if width > 1440 or height > 960:
                global big_images
                post_item += """<!-- :O IMAGEM GRANDE !!!! -->"""
                big_images += 1

        if create_thumb_post:
            media_file_in_post += 1

        create_thumb_post = True

    else:
        post_item += """<category domain="category" nicename=""" + '"' + strip_accents(POST_CATEGORY).lower() + '"' + """><![CDATA[""" + POST_CATEGORY + """]]></category>
            <wp:postmeta>
            <wp:meta_key><![CDATA[_thumbnail_id]]></wp:meta_key>
            <wp:meta_value><![CDATA[""" + str(initial_post_id+1) + """]]></wp:meta_value>
            </wp:postmeta>"""

    post_item += """</item>""" + '\n\n'

    media_file_import.write(post_item)  # insira seu conteúdo

    increment_initial_post_id()

    print(post["thumb"])
    if post["thumb"] and not create_thumb_post:
        create_post(post, media=True)

    if media_file_in_post + 1 <= len(post["content"][1]):
        print('entrou')
        create_post(post, media=True)


print('Lendo a lista de posts...')
print("Numero total de paginas: " + str(len(pagination)))
for page in pagination:
    access_page(page.get('href'))
    print("\n Página número: " + str(pagination.index(page) + 1) +
          " - " + page.get('href'))
    lista = bs_content.select(
        '.widget-noticia-lista-itens > li', limit=LIMIT_POSTS if LIMIT_POSTS > 0 else None)
    print("  Numero de posts " + str(len(lista)))
    for li in lista:
        print("   Post número " + str(lista.index(li) + 1))
        noticia = {
            'title': li.find(
                class_='plugdados-widget-noticia-titulo').get_text(),
            'link': li.find(class_='plugdados-widget-noticia-titulo').get('href'),
            'thumb': get_url_original_thumb(li.find(class_='plugdados-widget-link-miniatura').find('img').get('src'))
            if li.find(class_='plugdados-widget-link-miniatura')
            else None,
            'publish_date': get_formated_date(li.find(class_='plugdados-widget-noticia-data').get_text()),
            'content': get_content(li.find(class_='plugdados-widget-noticia-titulo').get('href')),
        }

        create_post(noticia, media=False)
        create_thumb_post = False
        media_file_in_post = 0

        sleep(1.0)

# Insere as tags de fechamento no arquivo de medias.
media_file_import.write('</channel>\n</rss>')

media_file_import.close()

print('Arquivo de importação gerado com sucesso! :)')

print('Quantidade de imagens grandes: ' + str(big_images))
