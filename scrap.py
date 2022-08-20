#!/usr/bin/env python
# coding: utf-8

# In[1]:


import requests
import re
import os 
import numpy as np
import cairosvg 

from bs4 import BeautifulSoup
from io import BytesIO
from PIL import Image
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager


# In[2]:


hh = input('input user-agent \n')
header={"user-agent" : hh}

# key = '박은빈'


# In[3]:
def scrapSignalKeyword():
    url = 'https://api.signal.bz/news/realtime'
    resp = requests.get(url=url)
    top10dict = resp.json()['top10']
    return [t['keyword'] for t in top10dict]


def scrapNaverNewsLink(key, sort='0'):
    url = 'https://search.naver.com/search.naver?where=news'
    resp = requests.get(url, params={'sm':'tab_jum', 'query':key, 'sort':sort}) 
    news_search = BeautifulSoup(resp.text, 'html.parser') 
    url_list = [d['href'] for d in news_search.find_all('a', attrs={'class':'info'}) if d.text=='네이버뉴스']
    return url_list


# In[4]:


def cleanArticle(content):
    cleanr_image = re.compile('<em class="img_desc">.*?</em>')
    cleanr_tag = re.compile('<.*?>')
    cleanr_email = re.compile('([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)')          
    cleantext = re.sub(cleanr_image, '', content)
    cleantext = re.sub(cleanr_tag, '', cleantext)
    cleantext = re.sub(cleanr_email, '', cleantext)
    return cleantext.strip()


# In[5]:


def scrapNaverNews(url_list):
    articles = []
    for url in url_list:    
        news = requests.get(url,headers=header) #그 뉴스링크에 다시 접근
        news_html = BeautifulSoup(news.text,"html.parser") #html로 변환
        newstype = news.url.split('.')[0].split('//')[-1]

        if newstype == 'sports':
            title = news_html.find('h4', {'class':'title'}).text
            content = news_html.find_all('div', {'id':'newsEndContents'})  ##스포츠 일때는 sid가 없어서 1순위 확인
            content = str(content)
            content = content.split('<p class="source">') 
            text = content[0]            
        elif newstype == 'entertain':
            title = news_html.find('h2', {'class':'end_tit'}).text
            text = ' '.join([paragraph.text for paragraph in news_html.find_all('div', {'id':'articeBody'})]) 
        else:
            title = news_html.find('h2', {'class':'media_end_head_headline'}).text
            text = ' '.join([paragraph.text for paragraph in news_html.find_all('div', {'class':'go_trans _article_content'})]) 

        cleaned_text = cleanArticle(text)
        articles.append((title, cleaned_text))
    return articles 


# In[6]:


def clean_text(inputString):
    text_rmv = re.sub('[-=+,#/\?:^.@*\"※~ㆍ!』‘|\(\)\[\]`\'…》\”\“\’·]', ' ', inputString)
    return text_rmv.strip()


def scrapNaverNewsKeyword(key, article_num, sort='1'):
    articles = []
    links = [] 
    page_num = 0
    while True:
        url = 'https://search.naver.com/search.naver?where=news'
        page = f'{page_num}1'
        resp = requests.get(url, params={'sm':'tab_jum', 'query':key, 'sort':sort, 'start':page}) 
        news_search = BeautifulSoup(resp.text, 'html.parser') 
        url_list = [d['href'] for d in news_search.find_all('a', attrs={'class':'info'}) if d.text=='네이버뉴스']
        for url in url_list:    
            news = requests.get(url,headers=header) #그 뉴스링크에 다시 접근
            news_html = BeautifulSoup(news.text,"html.parser") #html로 변환
            newstype = news.url.split('.')[0].split('//')[-1]

            if newstype == 'sports':
                title = news_html.find('h4', {'class':'title'}).text
                content = news_html.find_all('div', {'id':'newsEndContents'})  ##스포츠 일때는 sid가 없어서 1순위 확인
                content = str(content)
                content = content.split('<p class="source">') 
                text = content[0]            
            elif newstype == 'entertain':
                title = news_html.find('h2', {'class':'end_tit'}).text
                text = ' '.join([paragraph.text for paragraph in news_html.find_all('div', {'id':'articeBody'})]) 
            else:
                title = news_html.find('h2', {'class':'media_end_head_headline'}).text
                text = ' '.join([paragraph.text for paragraph in news_html.find_all('div', {'class':'go_trans _article_content'})]) 

            cleaned_text = cleanArticle(text)
            if len(cleaned_text) > 400:
                articles.append((title, cleaned_text))
                links.append(url)
            if len(articles) == article_num:
                break
        if len(articles) == article_num:
            break
        page_num+=1  
    return articles, links
# In[7]:


def saveArticles(articles, path):
    for title, content in articles:
        f = open(os.path.join(path, clean_text(title) + '.txt'), 'w', encoding='utf8')
        f.write(content)
        f.close()


# In[8]:


# # os.mkdir('./txt')
# path ='.\\txt'
# tmp = scrapNaverNews(scrapNaverNewsLink(key))
# saveArticles(tmp, path)


# In[9]:


# def set_chrome_driver():
#     chrome_options = webdriver.ChromeOptions()
# #     chrome_options.add_argument('--headless')
#     chrome_options.add_argument("--disable-gpu")
#     chrome_options.add_argument(header['user-agent'])
#     driver = webdriver.Chrome(options=chrome_options)
#     return driver

def set_chrome_driver():
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument("user-agent="+hh)
    driver = webdriver.Chrome('chromedriver', options=chrome_options)
    return driver
# In[10]:


def scrapNamuImg(key, path, namuKeyword_kind='person'):
    driver = set_chrome_driver()

    url = 'https://namu.wiki/w/'+key
    driver.get(url=url)
    html = driver.page_source
    driver.close()
    soup = BeautifulSoup(html, 'lxml')

    if namuKeyword_kind == 'person':
        imglink = [d['src'] for d in soup.find_all('img', attrs={'class':'dVTtICxy'}) if not d.find_parent('dd')]
        for i, link in enumerate(imglink):
            res=requests.get("https:"+link,headers=header)
            if 'svg' not in res.text and 'video' not in res.text:
                urlopen_img = Image.open(BytesIO(res.content))
                counts = np.unique(np.array(urlopen_img.split()[-1]), return_counts=True)[1]
                ratio = counts[0]/np.sum(counts)
                if urlopen_img.size[1]*urlopen_img.size[0] > 100000 and ratio<0.3 :
                    print(res.url)
                    urlopen_img.save(path,'png')
                    break
    else :
        imglink = [d['src'] for d in soup.find_all('img', attrs={'class':'dVTtICxy'}) 
                            if not d.find_parent('dd') and (key in  d['alt']) and
                            ('로고' in  d['alt'] or'logo' in  d['alt']or 'CI' in  d['alt'] or 'ci' in  d['alt'] or '휘장' in d['alt']) ]
        if len(imglink) < 1:
            imglink = [d['src'] for d in soup.find_all('img', attrs={'class':'dVTtICxy'}) 
                            if not d.find_parent('dd') and ('로고' in  d['alt'] or'logo' in  d['alt']or 'CI' in  d['alt'] or 'ci' in  d['alt'] or '휘장' in d['alt']) ]
        for i, link in enumerate(imglink):
            res=requests.get("https:"+link,headers=header)
            # print(i)
            try:
                urlopen_img = Image.open(BytesIO(cairosvg.svg2png(res.content)))
                print(res.url)
                urlopen_img.save(path,'png')
                break
            except:
                urlopen_img = Image.open(BytesIO(res.content))
                print(res.url)
                urlopen_img.save(path,'png')
                break


# In[11]:


# # os.mkdir('./img')
# path ='.\\img'
# scrapNamuImg(key,path)


# In[ ]:




