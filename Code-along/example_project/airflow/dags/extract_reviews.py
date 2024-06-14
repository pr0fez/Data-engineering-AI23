from airflow.decorators import dag, task
from pendulum import datetime
from airflow.io.path import ObjectStoragePath
from bs4 import BeautifulSoup
import requests
import pandas as pd

@dag(
    start_date=datetime(2024, 1, 1),
    schedule=None,
    catchup=False,
    doc_md=__doc__
)
def review_extractor():
    @task
    def extract_imdb_review(imdb_id):
        base_url = 'https://www.imdb.com/'
        review_url=f'title/tt{imdb_id}/reviews'
        print(base_url + review_url)
        resp = requests.get(base_url + review_url)
        if(resp):
            base = ObjectStoragePath("s3://data-lake/imdb-reviews/", conn_id="s3")
            base.mkdir(exist_ok=True, parents=True)
            soup = BeautifulSoup(resp.content, 'html.parser')
            df = pd.DataFrame([r.get_text() for r in soup.find_all(attrs={'class':'text show-more__control'})])
            path = base / f'{imdb_id}.csv'
            with path.open('wb') as file:
                df.to_csv(file)
    
    @task
    def extract_tmdb_review(tmdb_id, language='en-US'):
        base_url = 'https://themoviedb.org'
        review_url = f'/movie/{tmdb_id}/reviews?language={language}'
        resp = requests.get(base_url + review_url)
        if (resp):
            base = ObjectStoragePath("s3://data-lake/tmdb-reviews/", conn_id="s3")
            base.mkdir(exist_ok=True, parents=True)
            soup = BeautifulSoup(resp.content, 'html.parser')
            info = soup.find_all(attrs={'class': 'info'})
            reviews = list()
            for i in info:
                a = i.find('a')
                ref = a.attrs['href']
                resp = requests.get(base_url + ref)
                s = BeautifulSoup(resp.content, 'html.parser')
                review = s.find(attrs={'class': 'content column pad'})
                reviews += [review.get_text()]
            df = pd.DataFrame(reviews)
            path = base / f"{tmdb_id}.csv"
            with path.open('wb') as file:
                df.to_csv(file)

    [extract_imdb_review('0114885'), extract_tmdb_review('862')]

review_extractor()