# This script aims to scrape a retailer site. For this purpose, the Selenium Python library is used.

# Wrote this with regard to a work project, in which the client company monitors the prices in retailer sites where it sells its products online. 
# This is the main goal. 


# It is required to compare the price of the product with specific SKU (value in the "ItemNumber" field) with the everyday price (value in "IMAPPrice" field). 
# If the price in page is lower than the intended one set by the seller (our client), this is considered as a VIOLATION. 
# There is the boolean field "Violation" informing about this. It has the "YES" value if there is price violation and "NO" if otherwise.


#There is also needed to compare the SKU(ItemNumber) in the input file with the one in the reults file, in order to make sure that the exact product is matched. If not, an "ErroMessage" is present to inform the client that the SKU in the product page mismatches the right one and it is not the product expected from search.


from selenium import webdriver
from selenium.webdriver.common.by import By 
from selenium.webdriver.common.keys import Keys
import pandas as pd
import time
from datetime import datetime
import pytz
from concurrent.futures import ThreadPoolExecutor



df=pd.read_csv('/home/armir/Downloads/Milwaukee_August_Inputs_No_Zip.csv').fillna('')

#With input is meant the list of initial values provided by the client, which are the data we refer to, in order to carry out the process and match the client's requests.
#For example, the value of "ItemNumber" field is always used as search term for each product. Also, 

input_rows_list=[[row.UPC,row.ItemNumber,row.ItemDesc,row.IMAPPrice,row.Promo1Price,row.Promo1Start,row.Promo1End] for row in df.itertuples()] #elegant pythonic way to get a list of lists, with all input rows.
print(input_rows_list)

csv_file='/home/armir/Downloads/international_tool_results.csv'


#We need to record the timestamp to fill the field "DateofScrape", which is required to belong to the US/Central timezone
def timestamp():
    return datetime.now().astimezone(pytz.timezone('US/Central')).strftime('%m/%d/%Y, %H:%M:%S %p')


#This one is the most important for the client. It serves the need to check if the price captured is lower than promo price (if we are in the promo period) or the everyday price (if there is no promotion period)
#If so, this is considered a price VIOLATION to them. This is the essence of the project.

def violation_check(retailer_price,imap_price,promo1price,promo1start,promo1end):
    
    if promo1start!='' and promo1end!='': #if there is a promotion period for the product
        format="%m/%d/%Y"
        current_date=datetime.strptime(datetime.now().strftime(format),format)
        start_date=datetime.strptime(promo1start,format)
        end_date=datetime.strptime(promo1end,format)
        if current_date>start_date and current_date<end_date: #if we are within the promotion period, e compare the extracted price with the promotion one, else we do with the everyday price.
            if float(retailer_price)<float(promo1price):  
                return "YES"
            return "NO"            
        else:
            if float(retailer_price)<float(imap_price):
                return "YES"
            return "NO"

    else:
        if float(retailer_price)<float(imap_price):
            return "YES"
        return "NO"


#The below row creates an empty dataframe, with the fields specified, as client requested them.
ouptut_columns_list=['UPC','ItemDesc','SellerName','ProductTitle','ProductURL','ItemNumber','ItemNumber-Website','IMAPPrice','RetailPrice','Promo1Price','Promo1Start','Promo1End','Violation','In-OutofStock','GeoLocation','DateExtractedCST','ErrorMessage']
results_df=pd.DataFrame(columns=ouptut_columns_list)
print(results_df)



#This function will be used to update the above dataframe with every row extracting from scraping process.
def add_results(results_list):
    global results_df,ouptut_columns_list
    page_results_df=pd.DataFrame(results_list,columns=ouptut_columns_list)
    results_df=pd.concat([results_df,page_results_df],ignore_index=True)
    

#This is the main function, that executes the extraction process.
#If the search gets us directly to the product page or in a results list page and there are relevant results, we get the necessary data and check for price VIOLATION.
#Else, we 
def extract_data(input_row):
    
    global results_df #we need this to access the dataframe we created, in order to update this with the data rows.

    #we declare and assign in a single row the variables, dedicated to field values in inputs list, for simple use in below rows.
    upc,item_number,item_desc,imap_price,promo1price,promo1start,promo1end=input_row[0],input_row[1],input_row[2],input_row[3],input_row[4],input_row[5],input_row[6]
   
    driver=webdriver.Chrome()
    driver.get('https://www.internationaltool.com/shop/')    
    driver.find_element(By.CSS_SELECTOR,'li[class="site-search"] input').send_keys(item_number)
    time.sleep(2)
    driver.find_element(By.CSS_SELECTOR,'li[class="site-search"] input').send_keys(Keys.RETURN)
    time.sleep(2)
    
    
    #if we are inside a product page and the result matches the intended searched product, we extract the needed data, else we add an error message for the mismatch encountered.
    if len(driver.find_elements(By.CSS_SELECTOR,'div[class="meta"]'))!=0: 
        print(len(driver.find_elements(By.CSS_SELECTOR,'div[class="meta"]'))!=0)
        product_title=driver.find_element(By.CSS_SELECTOR,'div[class="name"]').text
        product_url=driver.current_url
        seller_name='International Tool'
         
        if(driver.find_element(By.CSS_SELECTOR,'span[class="vendor-number"] strong').text==item_number):
            item_number_website=driver.find_element(By.CSS_SELECTOR,'span[class="vendor-number"] strong').text
            print(item_number)
            retailer_price=driver.find_element(By.CSS_SELECTOR,'div[class="price text-align-right"] p').text.strip().replace("$","").replace(",","")
            violation=violation_check(retailer_price,imap_price,promo1price,promo1start,promo1end)            
            print(type(violation))

            if len(driver.find_elements(By.CSS_SELECTOR,'button[id="addToCartButton"]'))!=0:
                stock='In Stock'
            
            else:
                stock='Out of Stock'
                
            print(stock) 
            results_list=[upc,item_desc,seller_name,product_title,product_url,item_number,item_number_website,imap_price,retailer_price,promo1price,promo1start,promo1end,violation,stock,'',timestamp(),'']
            add_results([results_list])

            print(results_df)
        
        else:
            error_message='The "ItemNumber" input does not match the one in the pdp.'    
            results_list=[upc,item_desc,seller_name,product_title,product_url,item_number,'',imap_price,'',promo1price,promo1start,promo1end,"NO",'','',timestamp(),error_message]
            add_results([results_list])
            print(results_df)
    
    
    
    #if no result is found for search only the error message appeared is extracted.
    elif len(driver.find_elements(By.XPATH,'''//div[@class="content__description type--caption"][contains(.,"We're sorry, we couldn't find any results for")]'''))!=0:
            error_message=driver.find_elements(By.XPATH,'''//div[@class="content__description type--caption"][contains(.,"We're sorry, we couldn't find any results for")]''')[0].text
            results_list=[upc,item_desc,'','','',item_number,'',imap_price,'',promo1price,promo1start,promo1end,'NO','','',timestamp(),error_message]
            add_results([results_list])
            print(results_df)
    
                    
    
    #if search shows a list of result, a check for relevant ones is performed and if so, necessary data are got directly in this page.    
    elif len(driver.find_elements(By.XPATH,'//li[@class="product-item"]'))!=0:
        
        exact_product_xpath='//li[@class="product-item"][.//span[@class="vendor-number"]//strong[text()="{}"]][1]'.format(item_number)
        relevant_results=driver.find_elements(By.XPATH,exact_product_xpath)
        
        #if there are relevant results (ones of a product with the item number searched with), the needed data are extracted for all of them.
        if len(relevant_results)!=0:
            
            for result in relevant_results:
                
                product_title=result.find_element(By.XPATH,'.//a[@class="name"]').text.strip()
                
                if "https://www.internationaltool.com" in result.find_element(By.XPATH,'.//a[@class="name"]').get_attribute('href'):
                    product_url=result.find_element(By.XPATH,'.//a[@class="name"]').get_attribute('href')    
                
                else:
                    product_url="https://www.internationaltool.com"+result.find_element(By.XPATH,'.//a[@class="name"]').get_attribute('href')
                
                
                retailer_price=result.find_element(By.XPATH,'.//span[@class="list-item-price"]').text.strip().replace("$","").replace("EACH","").replace(",","")
                violation=violation_check(retailer_price,imap_price,promo1price,promo1start,promo1end)
                print(violation)
                seller_name='International Tool'
                

                if len(result.find_elements(By.XPATH,'.//button[contains(.,"Add to Cart")]'))!=0:
                    stock='In Stock'
                else:
                    stock=''
                
                if result.find_element(By.XPATH,'.//span[@class="vendor-number"]//strong').text.strip().lower()==item_number.strip().lower():
                    item_number_website=result.find_element(By.XPATH,'.//span[@class="vendor-number"]//strong').text.strip()
                    results_list=[upc,item_desc,seller_name,product_title,product_url,item_number,item_number_website,imap_price,retailer_price,promo1price,promo1start,promo1end,violation,stock,'',timestamp(),'']            
                    add_results([results_list])           
                    print(results_df)        
                
                else:
                    retailer_price=''
                    error_message='The "ItemNumber" input does not match the one in the pdp.'
                    results_list=[upc,item_desc,seller_name,product_title,product_url,item_number,item_number_website,imap_price,retailer_price,promo1price,promo1start,promo1end,'NO',stock,'',timestamp(),error_message]        
                    add_results([results_list])
                    print(results_df)

        #if there is no relevant result, the below error message is used to indicate that the product we searched for is not present.
        else:
            error_message='There is no relevant item in the results list.'
            results_list=[upc,item_desc,'','','',item_number,'',imap_price,'',promo1price,promo1start,promo1end,'NO','','',timestamp(),error_message]
            add_results([results_list])
            print(results_df)
    
    #if product is not available, the error message appeared is also extracted here.
    elif len(driver.find_elements(By.CSS_SELECTOR,'p[class="non-stock-topDescription"]'))!=0:
        error_message=driver.find_element(By.CSS_SELECTOR,'p[class="non-stock-topDescription"]').text.strip()
        results_list=[upc,item_desc,'','','',item_number,'',imap_price,'',promo1price,promo1start,promo1end,'NO','','',timestamp(),error_message]
        add_results([results_list])
        print(results_df)
    

    print(results_df)



#This is the most interesting part, which ensures that the site is opened and harvested multiple times simultaneosly, to make the process faster.
with ThreadPoolExecutor(max_workers=1) as executor:
    executor.map(extract_data,input_rows_list)


#In the end, we create a csv results file from the final dataframe we obtained.
results_df.to_csv(csv_file,index=False)
 


