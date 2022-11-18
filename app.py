from flask import Flask, render_template, send_from_directory, request
import requests
from bs4 import BeautifulSoup
from lxml import etree, html
import csv
from pathlib import Path

app = Flask(__name__)

@app.route("/")
def main():
  url = 'https://cn.nytimes.com/rss/zh-hant/'
  raw_data = requests.get(url)
  soup = BeautifulSoup(raw_data.text, features="xml")
  items = soup.find_all('item')
  [last_build_time] = soup.find('lastBuildDate')
  links = []
  for id, item in enumerate(items):
    data = {}
    data['zh_title'] = item.find('title').text
    zh_link = item.find('link').text.replace('?utm_source=RSS', '')
    data['zh_link'] = zh_link
    res = requests.get(zh_link + '/dual/').text
    article_soup = BeautifulSoup(res, 'html.parser')
    dom = etree.HTML(str(article_soup))
    en_link = dom.xpath('/html/body/main/div[2]/div[1]/div[2]/div/div[1]/ul/li[3]/a/@href')[0]

    [en_title] = article_soup.select('.en-title')
    data['en_title'] = en_title.text
    data['en_link'] = en_link
    data['id'] = id
    links.append(data)
  return render_template('index.html', links=links, last_build_time=last_build_time)

@app.route('/download')
def download():
  url = request.args.get('url')
  article_soup = BeautifulSoup(requests.get(url).text, 'html.parser')
  zh_title = article_soup.find_all('h1')[1].get_text()
  [en_title] = article_soup.select('.en-title')
  en_title = en_title.get_text()
  paragraphs = article_soup.select('.article-paragraph')
  paragraphs = [*map(lambda p: p.get_text(), paragraphs)]


  path = Path.cwd()
  path = path / 'download' / (en_title + '.csv')
  print(path)

  with path.open('w', newline='', encoding='utf-8') as csvfile:
    csvfile.write('\ufeff')
    writer = csv.writer(csvfile)

    writer.writerow([en_title, zh_title])

    row = []
    idx = 0
    for p in paragraphs:
      if idx % 2 == 0:
        row.append(p)
        idx += 1
      else:
        row.append(p)
        writer.writerow(row)
        row = []
        idx += 1
  return send_from_directory('download', en_title + '.csv', as_attachment=True)

