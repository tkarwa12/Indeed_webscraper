import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
from matplotlib import pyplot  as plt
from sqlalchemy import create_engine

def url_generator(what, pay_conditional, pay, where):
    what_list=what.split()
    try:
        pay_num=int(pay_conditional)
        what_list.append(pay)
    except:
        pay=''

    url_what='+'.join(what_list)
    #return url_what 
    where_list=where.split()
    url_where='+'.join(where_list)

    if pay=='':
        url =f'https://www.indeed.com/jobs?q={url_what}&l={url_where}'
    elif pay!='':
        url =f'https://www.indeed.com/jobs?q={url_what}&l={url_where}'
    return url

#initialize variables
punc='''!~()-[]{};:\'"/,<>.??@$%^&*'''
x=True
y=True
data=[]
dict_skills={}
column_list=['company', 'location', 'title', 'salary_range', 'Minimum_salary', 'Maximum_salary', 'link']
exist=1
noexist=0
skills=[]

job=input('Please enter a job title you are interested in: ')
location=input('Please enter a location you are interested in, if any:  ')
salary=input('Please enter a minimum salary you are interested in, if any: ')
salary_punc=salary
while y:
    skill_input=input('Please enter a skill you have or are looking for: ')
    #skills=['SQL','NoSQL','Tableau','Python','R']
    skills.append(skill_input)
    anotherskill_input=input('would you like to input another skill? ')
    anotherskill_input=anotherskill_input.lower()
    if anotherskill_input=='yes':
        continue
    else:
        y=False

skills_copy_uppercase=[each_string.upper() for each_string in skills]
skills=[each_stringer.lower() for each_stringer in skills]

for column_name in skills:
    column_list.append(column_name)

for punctuat in salary: #looks at each character in salary
        try:
            if punctuat in punc:
                salary=salary.replace(punctuat,'')
        except:
            break
#salary is without punctuation

URL=url_generator(job, salary, salary_punc, location)
print(URL)


def job_cards_all(link_url):
    response = requests.get(url=link_url)
    time.sleep(6)
    soup = BeautifulSoup(response.content, 'html.parser')
    #print(soup)
    job_cards = soup.find_all('div',class_='jobsearch-SerpJobCard')
    return job_cards, soup


job_cards,soup_ob=job_cards_all(URL)
#for card in job_cards:
#    print(card.h2.a.get('title'))


def scraper(link_job_listing):
    skill_list_attributes=[]

    job_fullpage = requests.get(url=link_job_listing)
    time.sleep(6)
    soup_job_fullpage = BeautifulSoup(job_fullpage.content, 'html.parser')
    job_description=soup_job_fullpage.find('div', id='jobDescriptionText')
    #print(job_description.get_text())

    job_description_text=job_description.get_text().split()
    
    included_skills=set()
    for words in job_description_text:
        for word in words: 
            try:
                if word in punc:
                    words=words.replace(word,'')
            except:
                break
        words=words.lower()
        if words in skills:
            words=words.upper()
            included_skills.add(words)
            if words not in dict_skills:
                dict_skills[words]=1
            elif words in dict_skills:
                dict_skills[words]+=1
    for s in skills_copy_uppercase:
        if s in included_skills:
            skill_list_attributes.append(exist)
        elif s not in included_skills:
            skill_list_attributes.append(noexist)
    return included_skills, skill_list_attributes

def job_headlines(all_jobs):
    
    for job in all_jobs:
        job_link='https://www.indeed.com'+job.h2.a.get('href')
        job_title=job.h2.a.get('title') #title of job
        job_company=job.find('span', class_='company').get_text() #company
        #job location
        try:
            job_location=job.find('span', 'location').get_text()
        except:
            job_location=job_location=job.find('div', 'location').get_text()
        #job salary
        try:
            salary_list=[]
            job_salary=job.find('div', 'salarySnippet holisticSalary').get_text()
            split_job_salary=job_salary.split()
            for element in split_job_salary:
                try:
                    numeric_filter = filter(str.isdigit, element)
                    numeric_string = "".join(numeric_filter)
                    if numeric_string!='':
                        salary_list.append(numeric_string)
                except:
                    break
            if len(salary_list)==1:
                job_salary_max=f'{max(salary_list)}'
                job_salary_min=job_salary_max
                job_salary=job_salary_min
            else:
                job_salary_max=f'{max(salary_list)}'
                job_salary_min=f'{min(salary_list)}'
                job_salary=f'{job_salary_min} - {job_salary_max}'
            #job_salary_max=job_salary.split()[2]
            #job_salary_min=job_salary.split()[0]
        except:
            job_salary='Not specified'
            job_salary_max= 'Not Specified'
            job_salary_min= 'Not Specified'

        record=[job_company,job_title, job_location, job_salary, job_salary_min, job_salary_max, job_link]
        record_cleaned=[string.strip('\n') for string in record]
        skill_list, attribute_list=scraper(job_link)
        #record_cleaned.append(skill_list)
        for attribute in attribute_list:
            record_cleaned.append(attribute)
        if record_cleaned in data:
            break
        else:            
            print(record_cleaned)
            data.append(record_cleaned)

        #print(record_cleaned)

job_headlines(job_cards)

while x:    
    try:
        url_next_page = 'https://www.indeed.com'+soup_ob.find('a',{'aria-label':'Next'}).get('href')
        print(url_next_page)
        job_cards, soup_ob=job_cards_all(url_next_page)
        job_headlines(job_cards)
        url_next_page_split=url_next_page.split('=')
        if '200' in url_next_page_split: #stops the program at 21 pages----------------------------------------------------------------------
            x=False
            break
    except:
        print('end')
        x=False

df=pd.DataFrame(data, columns=column_list)
engine=create_engine('postgresql://postgres:---------@localhost:5432/postgres')
con=engine.connect()
table_name=job+location+salary
#df.to_sql(table_name,con,if_exists='append',index=True)
print(df.head())
#print(dict_skills) #prints how many times the skills were mentioned

#sorts the dictionary list of skills and plots it on a bar graph
sum_values=sum(dict_skills.values())
for key, value in dict_skills.items():
    dict_skills[key]=(value/sum_values)
dict_skills_sorted={}
dict_skills_keys_sorted=sorted(dict_skills, key=dict_skills.get, reverse=True)
for key in dict_skills_keys_sorted:
    dict_skills_sorted[key] = dict_skills[key]    
print(dict_skills_sorted)   
#df.to_csv('job_listings.csv', index=True)
names=list(dict_skills_sorted.keys())
values=list(dict_skills_sorted.values())
#df2=pd.DataFrame(list(dict_skills.items()),columns=skills).sort_values(values)
plt.bar(range(len(dict_skills_sorted)),values,tick_label=names)
plt.show()
