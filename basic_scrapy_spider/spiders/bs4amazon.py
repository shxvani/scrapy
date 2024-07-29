import requests
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime
import re


headers = {
    'authority': 'www.amazon.com',
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'accept-language': 'en-US,en;q=0.9,bn;q=0.8',
    'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="102", "Google Chrome";v="102"',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36'
}

reviews_url = 'https://www.amazon.com/product-reviews/B0C8VHZR14/'

len_page = 10


def reviewsHtml(url, len_page):
    soups = []
    for page_no in range(1, len_page + 1):
        paginated_url = f"{url}?ie=UTF8&reviewerType=all_reviews&pageNumber={page_no}"
        response = requests.get(paginated_url, headers=headers)
        soup = BeautifulSoup(response.text, 'lxml')
        soups.append(soup)
    return soups

def getReviews(html_data):

    data_dicts = []

    product_brandtag = html_data.select('[data-hook="cr-product-byline"]')
    if product_brandtag:
        product_brand = product_brandtag[0].select_one('.a-size-base.a-link-normal').text.strip()
    else:
        product_brand ='N/A'

    boxes = html_data.select('div[data-hook="review"]')

    for box in boxes:

        try:
            name = box.select_one('[class="a-profile-name"]').text.strip()
        except Exception as e:
            name = 'N/A'

        try:
            stars = box.select_one('[data-hook="review-star-rating"]').text.strip().split(' out')[0]
        except Exception as e:
            stars = 'N/A'

        try:
            title = box.select_one('[data-hook="review-title"]').text.strip()
        except Exception as e:
            title = 'N/A'

        try:
            review_element = box.select_one('[data-hook="review-title"]')
            title = review_element.text.strip()
            href = review_element.get('href', 'N/A')
            if href != 'N/A':
                reviews_url = 'https://www.amazon.com' + href
            else:
                reviews_url = 'N/A'
        except Exception as e:
            title = 'N/A'
            reviews_url = 'N/A'



        try:
            datetime_str = box.select_one('[data-hook="review-date"]').text.strip().split(' on ')[-1]
            date = datetime.strptime(datetime_str, '%B %d, %Y').strftime("%d/%m/%Y")
        except Exception as e:
            date = 'N/A'
        
        try:
            review_date_text = box.select_one('[data-hook="review-date"]').text.strip()
            country = review_date_text.split('Reviewed in ')[1].split(' on ')[0]
        
        except Exception as e:
            country = 'N/A'

        try:
            description = box.select_one('[data-hook="review-body"]').text.strip()
        except Exception as e:
            description = 'N/A'

        try:
            helpful = box.select_one('[data-hook="helpful-vote-statement"]').text.strip()
        except Exception as e:
            helpful = 'N/A'

        try:
            avp_badge = box.select_one('[data-hook="avp-badge"]').text.strip()
            if avp_badge=="Verified Purchase":
                verified_purchase = 'Yes'
            if avp_badge and avp_badge!="Verified Purchase":
                verified_purchase = 'No'
            else:
                verified_purchase = 'N/A'
        except Exception as e:
            verified_purchase = 'N/A'

        review_id_match = re.search(r'/gp/customer-reviews/([^/?]+)', reviews_url)
        review_id = review_id_match.group(1) if review_id_match else 'N/A'
    
        asin_match = re.search(r'ASIN=([A-Z0-9]{10})', reviews_url)
        asin = asin_match.group(1) if asin_match else 'N/A'



        data_dict = {
            'Product URL' : 'https://www.amazon.com/dp/'+asin,
            'Product Brand' : product_brand,
            'Product ID' : asin,
            'Country' : country,
            'Review URL' : reviews_url,
            'Unnique Review ID' : review_id,
            'Name of Reviewer' : name,
            'Stars' : stars,
            'Title' : title,
            'Date' : date,
            'Description' : description,
            'Helpful votes' : helpful,
            'Verified Purchase' : verified_purchase
        }

        data_dicts.append(data_dict)

    return data_dicts

html_datas = reviewsHtml(reviews_url, len_page)
reviews = []

for html_data in html_datas:
    review = getReviews(html_data)
    reviews += review

df_reviews = pd.DataFrame(reviews)
df_reviews.to_csv('reviewsllllll.csv', index=False)