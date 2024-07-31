import requests
from bs4 import BeautifulSoup
import json

# Define the user agent
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.90 Safari/537.36',
}

# Function to get Walmart search page content
def get_walmart_search(search_query):
    url = f"https://www.walmart.com/search/?query={search_query}"
    page = requests.get(url, headers=headers)
    if page.status_code == 200:
        return page.content
    else:
        return None

# Function to extract product names and IDs from the search page
def extract_product_info(search_content):
    soup = BeautifulSoup(search_content, 'html.parser')
    product_names = []
    product_ids = []

    for item in soup.findAll('div', {'class': 'search-result-gridview-item-wrapper'}):
        name_tag = item.find('a', {'class': 'product-title-link'})
        if name_tag:
            product_names.append(name_tag.span.text.strip())
            product_ids.append(name_tag['href'].split('/')[-1])

    return product_names, product_ids

# Function to get product page content
def get_product_page(product_id):
    url = f"https://www.walmart.com/ip/{product_id}"
    page = requests.get(url, headers=headers)
    if page.status_code == 200:
        return page.content
    else:
        return None

# Function to extract reviews and ratings from the product page
def extract_reviews_and_ratings(product_content):
    soup = BeautifulSoup(product_content, 'html.parser')
    reviews = []

    review_elements = soup.find_all('div', {'class': 'review'})
    for element in review_elements:
        rating_element = element.find('div', {'class': 'review-rating'})
        review_element = element.find('div', {'class': 'review-text'})

        if rating_element and review_element:
            rating = rating_element.find('span').text.strip()
            review = review_element.text.strip()
            reviews.append({'rating': rating, 'review': review})

    return reviews

# Get search content for 'hand-soap'
search_content = get_walmart_search('hand-soap')

if search_content:
    product_names, product_ids = extract_product_info(search_content)

    # Display extracted product names and IDs for debugging
    print("Extracted Product Names:", product_names)
    print("Extracted Product IDs:", product_ids)

    if product_ids:
        # Get the first product page content
        first_product_content = get_product_page(product_ids[0])
        if first_product_content:
            reviews = extract_reviews_and_ratings(first_product_content)

            # Save reviews to a JSON file
            with open('walmart_reviews.json', 'w', encoding='utf-8') as file:
                json.dump(reviews, file, indent=2)
            
            print("Reviews and ratings have been extracted and saved to walmart_reviews.json")
        else:
            print("Failed to retrieve product page content.")
    else:
        print("No products found in the search results.")
else:
    print("Failed to retrieve search content.")
