# This is a script intending to scrape a retailer site, using Selenium Python framework.

# Writed this with regard to a project in which the client company monitors the prices in the retailer sites where it sells its products online. This is the main goal. 

# It is required to compare of the price of the product with specific SKU (value in the "ItemNumber" field) with the everyday price (value in "IMAPPrice" field). 
# If the price in page is lower than the intended one set by the seller (our client), this is considered as a VIOLATION. 
# There is the boolean field "Violation" informing about this. It has the "YES" value if there is price violation and "NO" if otherwise.


#There is also needed to compare the SKU(ItemNumber) in the input file with the one in the file, in order to make sure that the exact product is matched. If not, an "ErroMessage" is present to inform the client that the SKU in the product page mismatches the right one and it is not the product expected from search.


from selenium import webdriver
from selenium.webdriver.common.by import By 
from selenium.webdriver.common.keys import Keys
import pandas as pd
import time
from datetime import datetime
import pytz


driver=webdriver.Chrome()
driver.get('https://www.internationaltool.com/shop/')

df=pd.read_csv(path_to_inputs_file) #This row converts the CSV file of input list into a pandas dataframe, path can be anywhere in your computer

field_names=df.columns.values # Here we get a list of the column names in the dataframe created

for field_name in field_names: #Here, we create variables named after above column names, ending with the "_list" string. So, this is a technique that uses strings as variable names
    globals()[field_name+"_list"]=df[field_name].tolist()

csv_file='C:\\Users\\armir\\Downloads\\international_tool_results.csv'

def timestamp(): #This function is used to record timestamp of data extraction, in a specific format and timezone 
    return datetime.now().astimezone(pytz.timezone('US/Central')).strftime('%m/%d/%Y, %H:%M:%S %p')

results_df=pd.DataFrame(columns=['UPC','InputInternetNumber','ItemDesc','SellerName','ProductTitle','ProductURL','ItemNumber','ItemNumber-Website','IMAPPrice','RetailPrice','Promo1Price','Promo1Start','Promo1End','Violation','In-OutofStock','GeoLocation','DateExtractedCST','ErrorMessage'])
#The above row creates an dataframe with the defined columns and no values




def add_results(results_dict):  #This function updates the "results_df", by appending rows of each search data to it. It is called in the end of each
    global results_df
    page_results_df=pd.DataFrame(results_dict)
    results_df=pd.concat([results_df,page_results_df],ignore_index=True)
    

for i in range(len(ItemNumber_list)):
    
    #First, we search for the product by its SKU
    
    driver.find_element(By.CSS_SELECTOR,'li[class="site-search"] input').send_keys(ItemNumber_list[i])
    time.sleep(2)
    driver.find_element(By.CSS_SELECTOR,'li[class="site-search"] input').send_keys(Keys.RETURN)
    time.sleep(2)
    
    
    # This condition executes the code inside it if search redirects us to a PDP (directly to the product page). It extracts all needed information, such as price,stock etc. 
    # Here, of course, check for the product SKU match is done.
     
    if len(driver.find_elements(By.CSS_SELECTOR,'div[class="meta"]'))!=0:
        
        product_title=driver.find_element(By.CSS_SELECTOR,'div[class="name"]').text
        product_url=driver.current_url
        seller_name='International Tool'
        
        if(driver.find_element(By.CSS_SELECTOR,'span[class="vendor-number"] strong').text==ItemNumber_list[i]):
            item_number_website=driver.find_element(By.CSS_SELECTOR,'span[class="vendor-number"] strong').text
            retailer_price=driver.find_element(By.CSS_SELECTOR,'div[class="price text-align-right"] p').text.strip().replace("$","").replace(",","")
            
            if len(driver.find_elements(By.CSS_SELECTOR,'button[id="addToCartButton"]'))!=0:
                stock='In Stock'
            
            else:
                stock='Out of Stock'
            
            print(stock)
            results_dict={'UPC':[UPC_list[i]],'InputInternetNumber':[InputInternetNumber_list[i]],'ItemDesc':ItemDesc_list[i],'SellerName':seller_name,'ProductTitle':product_title,'ProductURL':product_url,'ItemNumber':ItemNumber_list[i],'ItemNumber-Website':item_number_website,'IMAPPrice':IMAPPrice_list[i],'RetailPrice':retailer_price,'Promo1Price':Promo1Price_list[i],'Promo1Start':Promo1Start_list[i],'Promo1End':Promo1End_list[i],'Violation':'','In-OutofStock':stock,'GeoLocation':'','DateExtractedCST':timestamp(),'ErrorMessage':''}
            add_results(results_dict)

            print(results_df)
        
        else:
            error_message='The "ItemNumber" input does not match the one in the pdp.'    
            results_dict={'UPC':[UPC_list[i]],'InputInternetNumber':[InputInternetNumber_list[i]],'ItemDesc':ItemDesc_list[i],'SellerName':seller_name,'ProductTitle':product_title,'ProductURL':product_url,'ItemNumber':ItemNumber_list[i],'ItemNumber-Website':'','IMAPPrice':IMAPPrice_list[i],'RetailPrice':'','Promo1Price':Promo1Price_list[i],'Promo1Start':Promo1Start_list[i],'Promo1End':Promo1End_list[i],'Violation':'','In-OutofStock':'','GeoLocation':'','DateExtractedCST':timestamp(),'ErrorMessage':error_message}
            add_results(results_dict)
            print(results_df)
    
    
    #If no results are found from our search, then the message is added to the "ErrorMessage" column
    
    elif len(driver.find_elements(By.XPATH,'''//div[@class="content__description type--caption"][contains(.,"We're sorry, we couldn't find any results for")]''')):
            error_message=driver.find_elements(By.XPATH,'''//div[@class="content__description type--caption"][contains(.,"We're sorry, we couldn't find any results for")]''')[0].text
            results_dict={'UPC':[UPC_list[i]],'InputInternetNumber':[InputInternetNumber_list[i]],'ItemDesc':ItemDesc_list[i],'SellerName':'','ProductTitle':'','ProductURL':'','ItemNumber':ItemNumber_list[i],'ItemNumber-Website':'','IMAPPrice':IMAPPrice_list[i],'RetailPrice':'','Promo1Price':Promo1Price_list[i],'Promo1Start':Promo1Start_list[i],'Promo1End':Promo1End_list[i],'Violation':'','In-OutofStock':'','GeoLocation':'','DateExtractedCST':timestamp(),'ErrorMessage':error_message}
            add_results(results_dict)
            print(results_df)
    
    
    
    #This is the condition that is applied when the search gives a list of results. A loop through relevant results is applied and then the conditions 
     
    elif len(driver.find_elements(By.XPATH,'//li[@class="product-item"]'))!=0:
        exact_product_xpath='//li[@class="product-item"][.//span[@class="vendor-number"]//strong[text()="{}"]][1]'.format(ItemNumber_list[i])
        relevant_results=driver.find_elements(By.XPATH,exact_product_xpath)
        if len(relevant_results)!=0:
            
            for result in relevant_results:
                
                product_title=result.find_element(By.XPATH,'.//a[@class="name"]').text.strip()
                print(product_title)
                
                if "https://www.internationaltool.com" in result.find_element(By.XPATH,'.//a[@class="name"]').get_attribute('href'):
                    product_url=result.find_element(By.XPATH,'.//a[@class="name"]').get_attribute('href')    
                else:
                    product_url="https://www.internationaltool.com"+result.find_element(By.XPATH,'.//a[@class="name"]').get_attribute('href')
                print(product_url)
                
                retailer_price=result.find_element(By.XPATH,'.//span[@class="list-item-price"]').text.strip().replace("$","").replace("EACH","").replace(",","")
                
                seller_name='International Tool'
                
                if len(result.find_elements(By.XPATH,'.//button[contains(.,"Add to Cart")]'))!=0:
                    stock='In Stock'
                else:
                    stock=''
                
                if result.find_element(By.XPATH,'.//span[@class="vendor-number"]//strong').text.strip().lower()==ItemNumber_list[i].strip().lower():
                    item_number_website=result.find_element(By.XPATH,'.//span[@class="vendor-number"]//strong').text.strip()
                    results_dict={'UPC':[UPC_list[i]],'InputInternetNumber':[InputInternetNumber_list[i]],'ItemDesc':ItemDesc_list[i],'SellerName':seller_name,'ProductTitle':product_title,'ProductURL':product_url,'ItemNumber':ItemNumber_list[i],'ItemNumber-Website':item_number_website,'IMAPPrice':IMAPPrice_list[i],'RetailPrice':retailer_price,'Promo1Price':Promo1Price_list[i],'Promo1Start':Promo1Start_list[i],'Promo1End':Promo1End_list[i],'Violation':'','In-OutofStock':stock,'GeoLocation':'','DateExtractedCST':timestamp(),'ErrorMessage':''}            
                    add_results(results_dict)            
                    print(results_df)
                    
                else:
                    retailer_price=''
                    error_message='The "ItemNumber" input does not match the one in the pdp.'
                    results_dict={'UPC':[UPC_list[i]],'InputInternetNumber':[InputInternetNumber_list[i]],'ItemDesc':ItemDesc_list[i],'SellerName':seller_name,'ProductTitle':product_title,'ProductURL':product_url,'ItemNumber':ItemNumber_list[i],'ItemNumber-Website':item_number_website,'IMAPPrice':IMAPPrice_list[i],'RetailPrice':retailer_price,'Promo1Price':Promo1Price_list[i],'Promo1Start':Promo1Start_list[i],'Promo1End':Promo1End_list[i],'Violation':'','In-OutofStock':stock,'GeoLocation':'','DateExtractedCST':timestamp(),'ErrorMessage':error_message}        
                    add_results(results_dict)
                    print(results_df)
                    
        else:
            error_message='There is no relevant item in the results list.'
            results_dict={'UPC':[UPC_list[i]],'InputInternetNumber':[InputInternetNumber_list[i]],'ItemDesc':ItemDesc_list[i],'SellerName':'','ProductTitle':'','ProductURL':'','ItemNumber':ItemNumber_list[i],'ItemNumber-Website':'','IMAPPrice':IMAPPrice_list[i],'RetailPrice':'','Promo1Price':Promo1Price_list[i],'Promo1Start':Promo1Start_list[i],'Promo1End':Promo1End_list[i],'Violation':'','In-OutofStock':'','GeoLocation':'','DateExtractedCST':timestamp(),'ErrorMessage':error_message}
            add_results(results_dict)
            print(results_df)
    
    
    #This condition, also outputs the message shown from page, if no result is found from search.     
    
    elif len(driver.find_elements(By.CSS_SELECTOR,'p[class="non-stock-topDescription"]'))!=0:
        error_message=driver.find_element(By.CSS_SELECTOR,'p[class="non-stock-topDescription"]').text.strip()
        results_dict={'UPC':[UPC_list[i]],'InputInternetNumber':[InputInternetNumber_list[i]],'ItemDesc':ItemDesc_list[i],'SellerName':'','ProductTitle':'','ProductURL':'','ItemNumber':ItemNumber_list[i],'ItemNumber-Website':'','IMAPPrice':IMAPPrice_list[i],'RetailPrice':'','Promo1Price':Promo1Price_list[i],'Promo1Start':Promo1Start_list[i],'Promo1End':Promo1End_list[i],'Violation':'','In-OutofStock':'','GeoLocation':'','DateExtractedCST':timestamp(),'ErrorMessage':error_message}
        add_results(results_dict)
        print(results_df)
    
    print(i+1)

    print(results_df)


#In the end, the dataframe with all extracted data is turned in to csv by to_csv() method
results_df.to_csv(csv_file,index=False)